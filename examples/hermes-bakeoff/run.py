#!/usr/bin/env python3
"""Hermes vs current-local-path bake-off driver.

Offline: --check fails closed when Ollama is down or the tag is missing.
Live: sequential arms, one request in flight, scrubbed env, HERMES_HOME under ./tmp.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from mcp_server import parse_ts
from peak import PeakSampler
from preflight import MEM_FLOOR_KIB, check_ollama, mem_available_kib
from score import aggregate, count_attempts, intervals_overlap, margin_verdict, normalize_client_calls, score_task

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEFAULT_TASKS = ROOT / "data" / "decision-gates" / "hermes-bakeoff.tasks.v0.json"
DEFAULT_OUT = ROOT / "pipelines" / "dogfood" / "hermes-bakeoff" / "results.json"


def scrubbed(extra: dict | None = None) -> dict[str, str]:
    home = os.environ.get("HOME") or str(Path.home())
    env = {
        "HOME": home,
        "PATH": f"{home}/.local/bin:/usr/local/bin:/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "USER": os.environ.get("USER", "mark"),
        "LOGNAME": os.environ.get("LOGNAME", "mark"),
        "TMPDIR": "/tmp",
    }
    if extra:
        env.update({key: str(value) for key, value in extra.items()})
    return env


def load_server_log(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def ollama_ps_body(base_url: str) -> list[dict]:
    from preflight import ollama_root

    url = ollama_root(base_url) + "/api/ps"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            body = json.loads(response.read().decode("utf-8"))
    except Exception:
        return []
    rows = []
    for item in body.get("models") or []:
        if isinstance(item, dict) and item.get("name"):
            rows.append(
                {
                    "name": item.get("name"),
                    "size": item.get("size"),
                    "context_length": item.get("context_length"),
                }
            )
    return rows


def ollama_ps(base_url: str) -> list[str]:
    return [row["name"] for row in ollama_ps_body(base_url)]


def _text(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, timeout=15).strip()
    except Exception as exc:  # noqa: BLE001
        return type(exc).__name__


def _ollama_version(base_url: str) -> str:
    from preflight import ollama_root

    try:
        with urllib.request.urlopen(ollama_root(base_url) + "/api/version", timeout=5) as response:
            body = json.loads(response.read().decode("utf-8"))
        return str(body.get("version") or body)
    except Exception as exc:  # noqa: BLE001
        return type(exc).__name__


def unload_model(base_url: str, model: str) -> None:
    from preflight import ollama_root

    root = ollama_root(base_url)
    data = json.dumps({"model": model, "keep_alive": 0, "prompt": ""}).encode("utf-8")
    request = urllib.request.Request(
        root + "/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        response.read()


def wait_for_memory(required_kib: int | None = None) -> int:
    need = MEM_FLOOR_KIB if required_kib is None else required_kib
    deadline = time.time() + 20 * 60
    while True:
        kib = mem_available_kib()
        if kib >= need:
            return kib
        if time.time() >= deadline:
            raise SystemExit(
                f"FAIL: MemAvailable {kib} KiB stayed under {need} KiB for 20 min"
            )
        time.sleep(60)


def _run_sampled(cmd: list[str], env: dict, timeout: float, pid_file: Path | None) -> dict:
    proc = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
        text=True,
    )
    if pid_file is not None:
        with pid_file.open("a", encoding="utf-8") as handle:
            handle.write(str(proc.pid) + "\n")
    sampler = PeakSampler(proc.pid)
    sampler.start()
    started = time.time()
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except OSError:
            proc.kill()
        try:
            stdout, stderr = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            stdout, stderr = proc.communicate(timeout=5)
    finally:
        sampler.stop()
    wall = time.time() - started
    return {
        "returncode": proc.returncode,
        "stdout": stdout or "",
        "stderr": stderr or "",
        "wall_s": wall,
        "timed_out": timed_out,
        "peak": sampler.summary(),
        "started": started,
    }


def _arm_cmd(arm: str, args, task_id: str, log_path: Path, out_path: Path, num_ctx: int) -> tuple[list[str], dict]:
    common = [
        "--task-file", str(args.tasks),
        "--task-id", task_id,
        "--system", args.system,
        "--log", str(log_path),
        "--base-url", args.base_url,
        "--model", args.model,
        "--num-ctx", str(num_ctx),
        "--out", str(out_path),
    ]
    bakeoff_python = os.environ.get("BAKEOFF_PYTHON") or sys.executable
    if arm == "hermes":
        cmd = [args.hermes_python, str(HERE / "hermes_arm.py"), *common]
        env = scrubbed(
            {
                "HERMES_HOME": args.hermes_home,
                "HERMES_CHECKOUT": args.hermes_checkout,
                "HERMES_REDACT_SECRETS": "true",
                "HERMES_WRITE_SAFE_ROOT": args.write_root,
                "BAKEOFF_PYTHON": bakeoff_python,
                "HERMES_MAX_ITERATIONS": "6",
                "PYTHONPATH": args.hermes_checkout,
                "PYTHONNOUSERSITE": "1",
            }
        )
    else:
        cmd = [sys.executable, str(HERE / "opencode_arm.py"), *common]
        env = scrubbed(
            {
                "BAKEOFF_PYTHON": bakeoff_python,
                "PYTHONNOUSERSITE": "1",
                "BAKEOFF_OPENCODE_DATA": str(ROOT / "tmp" / "opencode-xdg" / "data"),
                "BAKEOFF_OPENCODE_CACHE": str(ROOT / "tmp" / "opencode-xdg" / "cache"),
            }
        )
    return cmd, env


def score_one(task: dict, arm_result_path: Path, log_path: Path, sampled: dict) -> dict:
    client = {"final_text": "", "assistant_text": "", "client_calls": [], "error": None, "driver": ""}
    if arm_result_path.exists():
        try:
            client = json.loads(arm_result_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            client["error"] = "arm result was not JSON"
    elif sampled.get("stderr") or sampled.get("returncode") not in (0, None):
        client["error"] = ((sampled.get("stderr") or sampled.get("stdout") or "arm exited without a result"))[-800:]
    if sampled["timed_out"]:
        client["error"] = (client.get("error") or "") + " FAIL: timeout"
    server_calls = load_server_log(log_path)
    baked_calls, meta_calls = normalize_client_calls(client.get("client_calls") or [])
    client = dict(client)
    client["client_calls"] = baked_calls
    client["meta_calls"] = meta_calls
    text = (client.get("assistant_text") or "") + "\n" + (client.get("final_text") or "")
    if sampled["stderr"]:
        text += "\n" + sampled["stderr"][-1000:]
    verdict = score_task(task, server_calls, text)
    attempts, valid = count_attempts(server_calls, client.get("client_calls") or [])
    ttft = None
    if server_calls and server_calls[0].get("ts"):
        ttft = max(0.0, parse_ts(server_calls[0]["ts"]) - sampled["started"])
    peak = sampled["peak"]
    return {
        "task_id": task["id"],
        "kind": task["kind"],
        "requires_call": bool(task.get("requires_call", True)),
        "pass": verdict["pass"],
        "reason": verdict["reason"],
        "narrate": verdict["narrate"],
        "attempts": attempts,
        "valid": valid,
        "server_calls": [
            {
                "name": call.get("name"),
                "arguments": call.get("arguments"),
                "schema_valid": call.get("schema_valid"),
                "error": call.get("error") or "",
            }
            for call in server_calls
        ],
        "client_call_count": len(client.get("client_calls") or []),
        "meta_calls": int(client.get("meta_calls") or 0),
        "final_text": (client.get("final_text") or "")[:500],
        "error": client.get("error"),
        "driver": client.get("driver"),
        "wall_s": round(sampled["wall_s"], 3),
        "ttft_s": None if ttft is None else round(ttft, 3),
        "peak_rss_bytes": peak["agent_peak_rss_bytes"],
        "ollama_peak_rss_bytes": peak["ollama_peak_rss_bytes"],
        "timed_out": sampled["timed_out"],
        "returncode": sampled["returncode"],
    }


def run_live(args) -> int:
    code, message = check_ollama(args.base_url, args.model)
    if code != 0:
        print(message)
        return code
    loaded_at_start = ollama_ps(args.base_url)
    model_was_loaded = args.model in loaded_at_start
    # The 22+25 GiB floor is the pre-load gate. Once this model is already
    # resident, another 22 GiB is not allocated; keep 8 GiB free and continue.
    if model_was_loaded:
        mem_before = wait_for_memory(8 * 1024 * 1024)
    else:
        mem_before = wait_for_memory()
    bundle = json.loads(Path(args.tasks).read_text(encoding="utf-8"))
    tasks = bundle["tasks"]
    if args.task_ids:
        wanted = set(args.task_ids.split(","))
        tasks = [task for task in tasks if task["id"] in wanted]
    if args.limit:
        tasks = tasks[: args.limit]
    args.system = bundle["system_prompt"]
    args.tasks = str(Path(args.tasks).resolve())
    args.hermes_home = str(Path(args.hermes_home).resolve())
    args.hermes_checkout = str(Path(args.hermes_checkout).resolve())
    args.write_root = str(Path(args.write_root).resolve())
    work = Path(args.work).resolve()
    work.mkdir(parents=True, exist_ok=True)
    pid_file = work / "pids.txt"
    num_ctx = args.num_ctx
    if num_ctx >= 64000:
        ctx_note = (
            f"{num_ctx} on both arms. Hermes refuses 32768 (minimum 64000), "
            "so a scored run at 65536 does not retry 32768. "
            "Ollama /api/ps context_length is the observed runtime window."
        )
    else:
        ctx_note = f"requested {num_ctx}"
    if not args.skip_ctx_probe and num_ctx < 64000:
        probe = {
            "id": "ctx-probe",
            "kind": "negative",
            "requires_call": False,
            "negative_mode": "contains",
            "expect_text": "pong",
            "prompt": "Reply with the single word pong. Do not call any tool.",
            "oracle": {"required": []},
        }
        probe_bundle = {"tasks": [probe], "system_prompt": bundle["system_prompt"]}
        probe_file = work / "ctx-probe-tasks.json"
        probe_file.write_text(json.dumps(probe_bundle), encoding="utf-8")
        saved_tasks = args.tasks
        args.tasks = probe_file
        log_path = work / "ctx-probe.jsonl"
        out_path = work / "ctx-probe.json"
        cmd, env = _arm_cmd("hermes", args, "ctx-probe", log_path, out_path, num_ctx)
        sampled = _run_sampled(cmd, env, args.timeout, pid_file)
        args.tasks = saved_tasks
        (out_path.with_suffix(".stderr")).write_text(sampled["stderr"][-12000:], encoding="utf-8")
        blob = ""
        if out_path.exists():
            blob = out_path.read_text(encoding="utf-8")
        blob += sampled["stderr"][-4000:]
        low = blob.lower()
        refused = (
            "needs at least" in low
            or "runtime context too small" in low
            or "below the minimum" in low
            or "64000" in blob
            or "64,000" in blob
        )
        if refused:
            num_ctx = 65536
            ctx_note = "32768 refused by Hermes minimum 64000; both arms use 65536"
        elif sampled["returncode"] not in (0, None) or not out_path.exists():
            ctx_note = (
                "32768 probe exited "
                f"{sampled['returncode']} without an acceptance; both arms stay at {num_ctx}"
            )
        else:
            ctx_note = "32768 accepted by the Hermes probe; both arms use 32768"
    rows = {"hermes": [], "baseline": []}
    arms = ["hermes", "baseline"] if args.arm == "both" else [args.arm]
    for task in tasks:
        for arm in arms:
            log_path = work / arm / f"{task['id']}.jsonl"
            out_path = work / arm / f"{task['id']}.json"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            if log_path.exists():
                log_path.unlink()
            cmd, env = _arm_cmd(arm, args, task["id"], log_path, out_path, num_ctx)
            sampled = _run_sampled(cmd, env, args.timeout, pid_file)
            (out_path.with_suffix(".stderr")).write_text(sampled["stderr"][-12000:], encoding="utf-8")
            rows[arm].append(score_one(task, out_path, log_path, sampled))
            print(f"{arm} {task['id']} pass={rows[arm][-1]['pass']} wall={rows[arm][-1]['wall_s']}s", flush=True)
            partial = Path(args.out)
            partial.parent.mkdir(parents=True, exist_ok=True)
            partial.write_text(
                json.dumps({"partial": True, "num_ctx": num_ctx, "rows": rows}, indent=2) + "\n",
                encoding="utf-8",
            )
    summary = {}
    for arm in arms:
        summary[arm] = aggregate(rows[arm])
        summary[arm]["wilson95"] = list(summary[arm]["wilson95"])
    verdict = "NO-WIN"
    reasons: list[str] = []
    overlap = None
    if "hermes" in summary and "baseline" in summary:
        verdict, reasons = margin_verdict(summary["hermes"], summary["baseline"])
        overlap = intervals_overlap(
            tuple(summary["hermes"]["wilson95"]),
            tuple(summary["baseline"]["wilson95"]),
        )
    mem_after = mem_available_kib()
    payload = {
        "meta": {
            "model": args.model,
            "base_url": args.base_url,
            "num_ctx": num_ctx,
            "num_ctx_note": ctx_note,
            "temperature": 0,
            "seed": 1,
            "timeout_s": args.timeout,
            "max_iterations": 6,
            "think": False,
            "hermes_sha": _text(["git", "-C", args.hermes_checkout, "rev-parse", "HEAD"]),
            "hermes_driver": "AIAgent.run_conversation",
            "opencode_version": _text(["opencode", "--version"]),
            "ollama_version": _ollama_version(args.base_url),
            "baseline_driver": "opencode run",
            "baseline_note": (
                "./pfy attach opencode execs the opencode binary with OPENAI_BASE_URL set to the "
                "local engine. It is not a headless tool loop. This bake-off drives `opencode run` "
                "against the same MCP server, with XDG_CONFIG_HOME under ./tmp. A one-task probe "
                "called submit_choice through that server. opencode run does not expose Ollama "
                "temperature, seed, or options.num_ctx; model limit.context is set to num_ctx. "
                "Hermes sends temperature 0, seed 1, think false, and options.num_ctx. "
                "baseline_arm.py remains the direct /v1/chat/completions loop and is not the scored arm."
            ),
            "mem_available_before_kib": mem_before,
            "mem_available_after_kib": mem_after,
            "model_loaded_at_start": model_was_loaded,
            "ollama_ps_at_start": loaded_at_start,
            "ollama_ps_after_tasks": ollama_ps_body(args.base_url),
            "started": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "verdict": verdict,
        "verdict_failures": reasons,
        "wilson_overlap": overlap,
        "summary": summary,
        "rows": rows,
    }
    if not model_was_loaded and not args.keep_model:
        try:
            unload_model(args.base_url, args.model)
            payload["meta"]["model_unloaded"] = True
        except Exception as exc:  # noqa: BLE001
            payload["meta"]["model_unloaded"] = False
            payload["meta"]["unload_error"] = type(exc).__name__
    else:
        payload["meta"]["model_unloaded"] = False
        payload["meta"]["model_left_loaded"] = model_was_loaded
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"verdict {verdict} wrote {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hermes bake-off")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--base-url", default="http://127.0.0.1:11434/v1")
    parser.add_argument("--model", default="qwen3.6:35b")
    parser.add_argument("--tasks", default=str(DEFAULT_TASKS))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--work", default=str(ROOT / "tmp" / "bakeoff"))
    parser.add_argument("--arm", choices=("both", "hermes", "baseline"), default="both")
    parser.add_argument("--num-ctx", type=int, default=32768)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--task-ids", default="")
    parser.add_argument("--hermes-python", default="")
    parser.add_argument("--hermes-checkout", default=str(ROOT / "tmp" / "hermes-agent"))
    parser.add_argument("--hermes-home", default=str(ROOT / "tmp" / "hermes-home"))
    parser.add_argument("--write-root", default=str(ROOT / "tmp" / "bakeoff"))
    parser.add_argument("--skip-ctx-probe", action="store_true")
    parser.add_argument("--keep-model", action="store_true")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if args.check:
        code, message = check_ollama(args.base_url, args.model)
        print(message)
        return code
    if not args.live:
        print("FAIL: pass --live to run models, or --check to probe Ollama")
        return 2
    if not args.hermes_python:
        root = Path(args.hermes_checkout).resolve().parent
        candidates = [
            Path(args.hermes_checkout) / ".venv" / "bin" / "python",
            root / ".venv-hermes" / "bin" / "python",
        ]
        home = Path(args.hermes_home)
        candidates.extend(sorted(home.glob("installs/*/environments/*/venv/bin/python")))
        found = next((path for path in candidates if path.exists()), None)
        if found is None:
            print("FAIL: Hermes venv python missing under the checkout or HERMES_HOME")
            return 2
        args.hermes_python = str(found)
    return run_live(args)


if __name__ == "__main__":
    raise SystemExit(main())
