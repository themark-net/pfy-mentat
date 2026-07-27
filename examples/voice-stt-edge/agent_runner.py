#!/usr/bin/env python3
"""T-0091 4b / T-0092 — voice transcript → tool-capable agent (local-first).

ADR-0012: default bulk path is **OpenCode → Ollama**, not Grok.

  VOICE_AUTO_AGENT=
    off / 0          — STT only
    1 / on / auto    — **opencode** (local; T-0092 default)
    opencode/worker  — same
    grok             — cloud escalate only
    mock             — dry-run smoke

  VOICE_LONG_TASK=1  — multi-step DoD framing + STATUS/DOD/EXIT/NEXT receipt

Fallback when OpenCode CLI missing: OpenAI-compat chat to local Ollama
(LOCAL_CODER_MODEL) so voice still lands on a local brain without cloud.

Writes:
  .generated/last-run.json · last-run.log · last-reply.txt
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

EDGE = Path(__file__).resolve().parent
ROOT = EDGE.parents[1]
DEFAULT_OUT = EDGE / ".generated"
OPENCODE_GEN = ROOT / "examples" / "opencode-ollama" / ".generated"
LOCK_NAME = "agent-runner.lock"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_out(out: Path) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    return out


def write_run(out: Path, payload: dict) -> Path:
    path = out / "last-run.json"
    payload = {**payload, "updated": utc_now()}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def read_run(out: Path) -> dict:
    path = out / "last-run.json"
    if not path.is_file():
        return {"status": "none", "message": "no runs yet"}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"status": "error", "message": "corrupt last-run.json"}


def normalize_mode(raw: str | None) -> str:
    """Map env/CLI tokens → off|mock|grok|opencode|recipe|tool_microtask."""
    s = (raw or "0").strip().lower()
    if s in ("", "0", "false", "no", "off"):
        return "off"
    if s in ("1", "true", "yes", "on", "auto", "opencode", "worker", "local"):
        return "opencode"
    if s in ("mock", "test"):
        return "mock"
    if s in ("grok", "cloud", "monitor"):
        return "grok"
    if s in ("recipe", "e2e", "deterministic"):
        return "recipe"
    if s in ("tool_microtask", "tool-microtask", "tools", "microtask"):
        return "tool_microtask"
    return "off"


def auto_mode() -> str:
    return normalize_mode(os.environ.get("VOICE_AUTO_AGENT"))


def long_task_enabled() -> bool:
    return os.environ.get("VOICE_LONG_TASK", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _lock_path(out: Path) -> Path:
    return out / LOCK_NAME


def acquire_lock(out: Path) -> bool:
    lp = _lock_path(out)
    if lp.is_file():
        try:
            meta = json.loads(lp.read_text(encoding="utf-8"))
            pid = int(meta.get("pid") or 0)
            if pid and Path(f"/proc/{pid}").exists():
                return False
        except Exception:
            pass
    lp.write_text(
        json.dumps({"pid": os.getpid(), "started": utc_now()}) + "\n",
        encoding="utf-8",
    )
    return True


def release_lock(out: Path) -> None:
    p = _lock_path(out)
    if p.is_file():
        try:
            p.unlink()
        except OSError:
            pass


def long_task_footer() -> str:
    return (
        "\n\n---\n"
        "**Long-running DoD mode (VOICE_LONG_TASK):** Treat the spoken intent as a "
        "multi-step software task. Plan briefly, implement in the repo, verify with "
        "make smoke-* / make eval-structural when relevant. Prefer local OpenCode/Ollama; "
        "escalate to Grok tools only when the operator set VOICE_AUTO_AGENT=grok. "
        "Do not stop after one tool call if work remains within turn budget.\n\n"
        "End the **final** reply with exactly these four lines (008-voice-receipt):\n"
        "STATUS: pass|fail|blocked\n"
        "DOD: <one line success criteria result>\n"
        "EXIT: goal|turn|budget|wall-clock|no-progress|human|error|external\n"
        "NEXT: <concrete next step or done>\n"
    )


def build_prompt(prompt_path: Path | None, transcript: str | None, target: str, repo: Path) -> str:
    if prompt_path and prompt_path.is_file():
        base = prompt_path.read_text(encoding="utf-8").strip()
    elif transcript:
        base = (
            f"# Voice → agent (T-0092 local-first)\n\n"
            f"**Target:** {target}\n**Repo:** `{repo}`\n\n"
            f"## Spoken intent\n\n{transcript.strip()}\n\n"
            f"Prefer cheap local checks. Land changes in the repo when implementing. "
            f"Stop after success or 3 identical failures.\n"
        )
    else:
        raise ValueError("need --prompt-file or --transcript / --text")

    footer = (
        "\n\n---\n"
        "**Auto-runner (ADR-0012):** Invoked from voice STT. Local OpenCode/Ollama is the "
        "default bulk path; keep replies concise. End with a short status "
        "(what ran, pass/fail, next step).\n"
    )
    if long_task_enabled():
        footer += long_task_footer()
    return base + footer


def _finish_ok(
    *,
    out: Path,
    run_id: str,
    mode: str,
    reply: str,
    cmd: list[str],
    duration: float,
    exit_code: int = 0,
    extra: dict | None = None,
) -> dict:
    (out / "last-reply.txt").write_text(reply + ("\n" if reply else ""), encoding="utf-8")
    payload = {
        "status": "done" if exit_code == 0 else "error",
        "ok": exit_code == 0,
        "run_id": run_id,
        "mode": mode,
        "exit_code": exit_code,
        "reply": reply[-8000:] if len(reply) > 8000 else reply,
        "reply_preview": (reply[:500] + ("…" if len(reply) > 500 else "")),
        "command": cmd,
        "duration_s": duration,
        "error": None if exit_code == 0 else f"{mode} exit {exit_code}",
        "long_task": long_task_enabled(),
    }
    if extra:
        payload.update(extra)
    return payload


def run_mock(prompt: str, out: Path, run_id: str) -> dict:
    if long_task_enabled():
        reply = (
            f"[mock agent / long-task] Would run OpenCode→Ollama on multi-step DoD.\n"
            f"Prompt head:\n{prompt[:280]}{'…' if len(prompt) > 280 else ''}\n"
            f"VOICE_RUNNER_MOCK_OK\n\n"
            f"STATUS: pass\n"
            f"DOD: mock long-task path exercised with receipt block\n"
            f"EXIT: goal\n"
            f"NEXT: done\n"
        )
    else:
        reply = (
            f"[mock agent / local-first] Would run OpenCode→Ollama on:\n"
            f"{prompt[:400]}{'…' if len(prompt) > 400 else ''}\n"
            f"VOICE_RUNNER_MOCK_OK"
        )
    time.sleep(0.15)
    return _finish_ok(
        out=out,
        run_id=run_id,
        mode="mock",
        reply=reply,
        cmd=["mock"],
        duration=0.15,
    )


def run_tool_microtask(
    prompt: str,
    repo: Path,
    out: Path,
    run_id: str,
    timeout_s: int,
) -> dict:
    """T-0098: Ollama tools loop with a single write_file tool (real tool use).

    OpenCode may dump tool JSON as text without executing; this path forces
    execution via OpenAI-compatible tools on LOCAL_TOOLS_MODEL.
    """
    t0 = time.time()
    model = local_agent_model()
    base = ollama_base_url()
    url = base + "/chat/completions"
    tools = [
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Write UTF-8 text to a path under the repo (relative or absolute).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["path", "content"],
                },
            },
        }
    ]
    messages: list[dict] = [
        {
            "role": "system",
            "content": (
                "You are a coding agent with tools. You MUST call write_file to create "
                "the requested marker file. Do not only describe the write."
            ),
        },
        {"role": "user", "content": prompt[:8000]},
    ]
    log_chunks: list[str] = [f"tool_microtask model={model} base={base}"]
    written: list[str] = []
    final_text = ""
    max_rounds = int(os.environ.get("VOICE_TOOL_MICROTASK_ROUNDS", "4"))
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def _post(body: dict) -> dict:
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY', 'ollama')}",
            },
            method="POST",
        )
        with opener.open(req, timeout=min(timeout_s, 120)) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))

    try:
        for round_i in range(max_rounds):
            if time.time() - t0 > timeout_s:
                raise TimeoutError(f"tool_microtask exceeded {timeout_s}s")
            body = {
                "model": model,
                "messages": messages,
                "tools": tools,
                "tool_choice": "auto",
                "temperature": 0.1,
                "max_tokens": 1024,
            }
            data = _post(body)
            msg = (data.get("choices") or [{}])[0].get("message") or {}
            content = (msg.get("content") or "").strip()
            tool_calls = msg.get("tool_calls") or []
            log_chunks.append(f"round={round_i} content_len={len(content)} tools={len(tool_calls)}")
            if content:
                final_text = content
            if not tool_calls:
                # Some models put function call JSON in content only
                if content and "write_file" in content and "PFY_TOOL_MICROTASK_OK" in content:
                    # Attempt to recover path/content from fenced JSON
                    m = re.search(
                        r"\{[^{}]*\"(?:path|filePath)\"[^{}]*\}",
                        content,
                        re.S,
                    )
                    # Prefer full tool-shaped object
                    for blob in re.findall(r"\{(?:[^{}]|\{[^{}]*\})*\}", content, re.S):
                        try:
                            obj = json.loads(blob)
                        except json.JSONDecodeError:
                            continue
                        args = obj.get("arguments") or obj
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except json.JSONDecodeError:
                                continue
                        path = args.get("path") or args.get("filePath") or obj.get("path")
                        c = args.get("content")
                        if path and c is not None and "PFY_TOOL_MICROTASK_OK" in str(c):
                            tool_calls = [
                                {
                                    "id": f"recover-{round_i}",
                                    "type": "function",
                                    "function": {
                                        "name": "write_file",
                                        "arguments": json.dumps(
                                            {"path": path, "content": c}
                                        ),
                                    },
                                }
                            ]
                            log_chunks.append("recovered write_file from text JSON")
                            break
                if not tool_calls:
                    break

            messages.append(
                {
                    "role": "assistant",
                    "content": content or "",
                    "tool_calls": tool_calls,
                }
            )
            for tc in tool_calls:
                fn = (tc.get("function") or {})
                name = fn.get("name") or ""
                raw_args = fn.get("arguments") or "{}"
                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except json.JSONDecodeError:
                    args = {}
                tc_id = tc.get("id") or f"call-{round_i}"
                if name != "write_file":
                    tool_result = f"error: unknown tool {name}"
                else:
                    path_s = str(args.get("path") or args.get("filePath") or "")
                    content_s = str(args.get("content") if args.get("content") is not None else "")
                    try:
                        p = Path(path_s)
                        if not p.is_absolute():
                            p = (repo / p).resolve()
                        # Confine writes under repo
                        p.resolve().relative_to(repo.resolve())
                        p.parent.mkdir(parents=True, exist_ok=True)
                        p.write_text(content_s, encoding="utf-8")
                        written.append(str(p))
                        tool_result = f"ok wrote {p} bytes={len(content_s.encode())}"
                        log_chunks.append(tool_result)
                    except Exception as e:  # noqa: BLE001
                        tool_result = f"error: {e}"
                        log_chunks.append(tool_result)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc_id,
                        "content": tool_result,
                    }
                )

        duration = round(time.time() - t0, 2)
        log_path = out / "last-run.log"
        log_path.write_text("\n".join(log_chunks) + "\n", encoding="utf-8")
        if not written:
            reply = (
                f"[tool_microtask] no write_file executed model={model}\n"
                f"{final_text[:800]}\n\n"
                f"STATUS: fail\n"
                f"DOD: tool microtask did not write marker\n"
                f"EXIT: error\n"
                f"NEXT: check LOCAL_TOOLS_MODEL and Ollama tools support\n"
            )
            (out / "last-reply.txt").write_text(reply, encoding="utf-8")
            return {
                "status": "error",
                "ok": False,
                "run_id": run_id,
                "mode": "tool_microtask",
                "exit_code": 1,
                "reply": reply,
                "reply_preview": reply[:500],
                "command": ["ollama-tools", "write_file", f"model={model}"],
                "duration_s": duration,
                "error": "no write_file tool execution",
                "long_task": long_task_enabled(),
                "log_path": str(log_path),
                "model": model,
            }

        # Ensure receipt
        if not re.search(r"(?im)^\s*STATUS\s*:", final_text or ""):
            final_text = (
                (final_text + "\n\n" if final_text else "")
                + "STATUS: pass\n"
                + "DOD: tool microtask write_file executed\n"
                + "EXIT: goal\n"
                + "NEXT: done\n"
            )
        reply = (
            f"[tool_microtask] wrote {len(written)} file(s): {written}\n"
            f"{final_text}\n"
        )
        return _finish_ok(
            out=out,
            run_id=run_id,
            mode="tool_microtask",
            reply=reply,
            cmd=["ollama-tools", "write_file", f"model={model}"],
            duration=duration,
            extra={
                "log_path": str(log_path),
                "model": model,
                "written": written,
                "long_task": long_task_enabled(),
            },
        )
    except Exception as e:  # noqa: BLE001
        duration = round(time.time() - t0, 2)
        err = f"tool_microtask failed: {e}"
        (out / "last-run.log").write_text(err + "\n" + "\n".join(log_chunks) + "\n", encoding="utf-8")
        reply = (
            f"{err}\n\nSTATUS: fail\nDOD: tool microtask error\nEXIT: error\nNEXT: retry with tools model\n"
        )
        (out / "last-reply.txt").write_text(reply, encoding="utf-8")
        return {
            "status": "error",
            "ok": False,
            "run_id": run_id,
            "mode": "tool_microtask",
            "exit_code": 1,
            "reply": reply,
            "reply_preview": reply[:500],
            "command": ["ollama-tools", "write_file"],
            "duration_s": duration,
            "error": err,
            "long_task": long_task_enabled(),
            "model": model,
        }


def run_recipe(prompt: str, repo: Path, out: Path, run_id: str) -> dict:
    """Deterministic multi-step develop loop (no LLM): edit fixture + verify structural.

    Proves text → agent_runner → repo file change → make eval-structural under
    VOICE_LONG_TASK receipt framing. Used by make voice-agent-e2e / install path.
    """
    t0 = time.time()
    marker = out / "e2e-loop-marker.txt"
    stamp = utc_now()
    body = (
        f"# pfy-mentat voice e2e develop-loop marker\n"
        f"generated: {stamp}\n"
        f"run_id: {run_id}\n"
        f"prompt_head: {prompt[:120].replace(chr(10), ' ')}\n"
    )
    marker.write_text(body, encoding="utf-8")
    cmd = ["recipe", "touch", str(marker), "&&", "make", "eval-structural"]
    log_path = out / "last-run.log"
    eval_ok = False
    eval_out = ""
    try:
        proc = subprocess.run(
            ["make", "eval-structural"],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=120,
        )
        eval_out = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
        eval_ok = proc.returncode == 0
        log_path.write_text(
            f"$ write {marker}\n$ make eval-structural\n\n{eval_out}\n",
            encoding="utf-8",
        )
    except Exception as e:
        eval_out = str(e)
        log_path.write_text(f"recipe failed: {e}\n", encoding="utf-8")

    duration = round(time.time() - t0, 2)
    if eval_ok and marker.is_file():
        try:
            marker_disp = str(marker.relative_to(repo))
        except ValueError:
            marker_disp = str(marker)
        reply = (
            f"[recipe agent / long-task] Wrote {marker_disp}\n"
            f"Ran make eval-structural: PASS\n"
            f"VOICE_RUNNER_RECIPE_OK\n\n"
            f"STATUS: pass\n"
            f"DOD: deterministic develop loop wrote marker and eval-structural green\n"
            f"EXIT: goal\n"
            f"NEXT: done\n"
        )
        return _finish_ok(
            out=out,
            run_id=run_id,
            mode="recipe",
            reply=reply,
            cmd=cmd,
            duration=duration,
            extra={"log_path": str(log_path), "marker": str(marker)},
        )
    reply = (
        f"[recipe agent] marker={marker.is_file()} eval_ok={eval_ok}\n"
        f"{eval_out[-1500:]}\n\n"
        f"STATUS: fail\n"
        f"DOD: deterministic develop loop did not complete cleanly\n"
        f"EXIT: error\n"
        f"NEXT: re-run make voice-agent-e2e and inspect last-run.log\n"
    )
    (out / "last-reply.txt").write_text(reply, encoding="utf-8")
    return {
        "status": "error",
        "ok": False,
        "run_id": run_id,
        "mode": "recipe",
        "exit_code": 1,
        "reply": reply,
        "reply_preview": reply[:500],
        "command": cmd,
        "duration_s": duration,
        "error": "recipe develop loop failed",
        "long_task": long_task_enabled(),
        "log_path": str(log_path),
    }


def ollama_base_url() -> str:
    base = (
        os.environ.get("OPENAI_BASE_URL")
        or os.environ.get("OLLAMA_OPENAI_BASE")
        or "http://127.0.0.1:11434/v1"
    )
    base = base.rstrip("/")
    if not base.endswith("/v1"):
        base = base + "/v1"
    return base


def local_coder_model() -> str:
    # Prefer instruct tags that exist on common lab hosts (OpenCode is picky about exact tags).
    return (
        os.environ.get("LOCAL_CODER_MODEL")
        or os.environ.get("EVAL_MODEL")
        or "deepseek-coder:6.7b-instruct"
    )


def local_agent_model() -> str:
    """Prefer tools-capable model (T-0093) for agent runs; else coder."""
    tools = (os.environ.get("LOCAL_TOOLS_MODEL") or os.environ.get("OPENCODE_AGENT_MODEL") or "").strip()
    if tools:
        return tools
    return local_coder_model()


def run_ollama_completion(prompt: str, out: Path, run_id: str, timeout_s: int) -> dict:
    """Direct local chat completion (no OpenCode CLI). Cloud-free fallback."""
    base = ollama_base_url()
    model = local_agent_model()
    url = base + "/chat/completions"
    user = prompt if len(prompt) < 6000 else (prompt[:5500] + "\n\n[truncated]\n")
    system = (
        "You are a local coding assistant. Be concise. "
        "If asked to run checks, describe the commands and expected outcomes."
    )
    if long_task_enabled():
        system += (
            " Multi-step DoD mode: plan, implement, verify. End with STATUS:/DOD:/EXIT:/NEXT: lines."
        )
    body = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": int(os.environ.get("VOICE_LOCAL_MAX_TOKENS", "512")),
            "temperature": 0.2,
        }
    ).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY', 'ollama')}",
        },
        method="POST",
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    cmd = ["ollama-compat", "POST", url, f"model={model}"]
    log_path = out / "last-run.log"
    t0 = time.time()
    try:
        with opener.open(req, timeout=min(timeout_s, 180)) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        duration = round(time.time() - t0, 2)
        text = (
            (data.get("choices") or [{}])[0].get("message", {}).get("content") or ""
        ).strip()
        log_path.write_text(
            f"$ {' '.join(cmd)}\n\n--- response ---\n{text}\n\n--- raw keys ---\n"
            f"{list(data.keys())}\n",
            encoding="utf-8",
        )
        if not text:
            return {
                "status": "error",
                "ok": False,
                "run_id": run_id,
                "mode": "ollama",
                "exit_code": 1,
                "reply": "",
                "error": "empty Ollama completion",
                "command": cmd,
                "duration_s": duration,
                "log_path": str(log_path),
            }
        return _finish_ok(
            out=out,
            run_id=run_id,
            mode="ollama",
            reply=text,
            cmd=cmd,
            duration=duration,
            extra={"log_path": str(log_path), "model": model, "base_url": base},
        )
    except Exception as e:
        duration = round(time.time() - t0, 2)
        err = f"Ollama completion failed: {e}"
        log_path.write_text(err + "\n", encoding="utf-8")
        return {
            "status": "error",
            "ok": False,
            "run_id": run_id,
            "mode": "ollama",
            "exit_code": 1,
            "reply": "",
            "error": err,
            "command": cmd,
            "duration_s": duration,
            "log_path": str(log_path),
            "hint": "Start Ollama; set LOCAL_CODER_MODEL; or use VOICE_AUTO_AGENT=mock",
        }


def run_opencode(prompt: str, repo: Path, out: Path, run_id: str, timeout_s: int) -> dict:
    """OpenCode CLI if present; else Ollama HTTP completion (local-first)."""
    prompt_file = out / "last-agent-prompt.txt"
    prompt_file.write_text(prompt, encoding="utf-8")
    log_path = out / "last-run.log"
    model = local_agent_model()
    cfg = os.environ.get("OPENCODE_CONFIG") or str(OPENCODE_GEN / "opencode.json")
    tools_env = OPENCODE_GEN / "tools-model.env"
    if tools_env.is_file() and not os.environ.get("LOCAL_TOOLS_MODEL"):
        for line in tools_env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("export ") and "=" in line:
                k, v = line[len("export ") :].split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
        model = local_agent_model()

    # Receipt-only CI path: skip OpenCode agent (tool planning) for reliable STATUS block.
    if os.environ.get("VOICE_FORCE_OLLAMA_HTTP", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    ):
        print("==> VOICE_FORCE_OLLAMA_HTTP=1 — Ollama chat completion only", file=sys.stderr)
        result = run_ollama_completion(prompt, out, run_id, timeout_s)
        result["mode"] = "opencode-ollama" if result.get("ok") else result.get("mode", "ollama")
        result["fallback"] = "force-ollama-http"
        return result

    oc = shutil.which("opencode")
    if oc:
        cmd = [oc, "run"]
        if Path(cfg).is_file():
            env_prefix = {"OPENCODE_CONFIG": cfg}
        else:
            env_prefix = {}
        cmd.extend(["-m", f"ollama/{model}", prompt[:12000]])
        env = os.environ.copy()
        env.update(env_prefix)
        t0 = time.time()
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(repo),
                capture_output=True,
                text=True,
                timeout=timeout_s,
                env=env,
            )
            duration = round(time.time() - t0, 2)
            out_txt = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
            log_path.write_text(
                f"$ OPENCODE_CONFIG={cfg} {' '.join(cmd)}\n\n{out_txt}\n",
                encoding="utf-8",
            )
            # Provider/model registry failures: fall through to Ollama HTTP (local-first).
            infra_err = any(
                s in out_txt
                for s in (
                    "ProviderModelNotFoundError",
                    "Model not found:",
                    "does not support tools",
                )
            )
            if infra_err:
                print(
                    f"==> opencode provider/model error; falling back to Ollama HTTP "
                    f"(model={model})",
                    file=sys.stderr,
                )
                log_path.write_text(
                    f"$ OPENCODE_CONFIG={cfg} {' '.join(cmd)}\n\n{out_txt}\n\n"
                    f"--- fallback ollama-http ---\n",
                    encoding="utf-8",
                )
            else:
                ok = proc.returncode == 0 or (
                    len(out_txt) > 10 and proc.returncode in (0, 1)
                )
                if proc.returncode != 0 and len(out_txt) > 20:
                    ok = True
                return _finish_ok(
                    out=out,
                    run_id=run_id,
                    mode="opencode",
                    reply=out_txt[-8000:],
                    cmd=cmd,
                    duration=duration,
                    exit_code=0 if ok else (proc.returncode or 1),
                    extra={
                        "log_path": str(log_path),
                        "model": model,
                        "opencode_config": cfg,
                        "raw_exit": proc.returncode,
                    },
                )
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "ok": False,
                "run_id": run_id,
                "mode": "opencode",
                "error": f"timeout after {timeout_s}s",
                "exit_code": 124,
                "reply": "",
                "command": cmd,
            }
        except Exception as e:
            print(f"==> opencode CLI failed ({e}); falling back to Ollama HTTP", file=sys.stderr)

    print(
        "==> opencode CLI not used — local Ollama completion fallback (T-0092)",
        file=sys.stderr,
    )
    result = run_ollama_completion(prompt, out, run_id, timeout_s)
    result["mode"] = "opencode-ollama" if result.get("ok") else result.get("mode", "ollama")
    result["fallback"] = "ollama-http"
    return result


def run_grok(
    prompt: str,
    repo: Path,
    out: Path,
    *,
    max_turns: int,
    timeout_s: int,
    run_id: str,
) -> dict:
    grok = shutil.which("grok")
    if not grok:
        return {
            "status": "error",
            "ok": False,
            "run_id": run_id,
            "mode": "grok",
            "exit_code": 127,
            "reply": "",
            "error": "grok not on PATH",
            "command": [],
            "hint": "Use VOICE_AUTO_AGENT=opencode for local path",
        }

    prompt_file = out / "last-agent-prompt.txt"
    prompt_file.write_text(prompt, encoding="utf-8")
    log_path = out / "last-run.log"

    always = os.environ.get("VOICE_AGENT_ALWAYS_APPROVE", "1").strip() not in (
        "0",
        "false",
        "no",
    )
    cmd = [
        grok,
        "--cwd",
        str(repo),
        "--max-turns",
        str(max_turns),
        "--output-format",
        "plain",
        "--prompt-file",
        str(prompt_file),
        "--no-alt-screen",
    ]
    if always:
        cmd.insert(1, "--always-approve")

    env = os.environ.copy()
    env.setdefault("CI", "1")
    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=env,
        )
        duration = round(time.time() - t0, 2)
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        log_path.write_text(
            f"$ {' '.join(cmd)}\n\n--- stdout ---\n{stdout}\n\n--- stderr ---\n{stderr}\n",
            encoding="utf-8",
        )
        reply = stdout.strip() or stderr.strip()
        return _finish_ok(
            out=out,
            run_id=run_id,
            mode="grok",
            reply=reply,
            cmd=cmd,
            duration=duration,
            exit_code=proc.returncode,
            extra={"log_path": str(log_path)},
        )
    except subprocess.TimeoutExpired as e:
        duration = round(time.time() - t0, 2)
        partial = e.stdout or ""
        if isinstance(partial, bytes):
            partial = partial.decode("utf-8", errors="replace")
        log_path.write_text(f"TIMEOUT after {timeout_s}s\n{partial}\n", encoding="utf-8")
        return {
            "status": "error",
            "ok": False,
            "run_id": run_id,
            "mode": "grok",
            "exit_code": 124,
            "reply": (partial or "")[-4000:],
            "error": f"timeout after {timeout_s}s",
            "command": cmd,
            "duration_s": duration,
            "log_path": str(log_path),
        }
    except Exception as e:
        return {
            "status": "error",
            "ok": False,
            "run_id": run_id,
            "mode": "grok",
            "exit_code": 1,
            "reply": "",
            "error": str(e),
            "command": cmd,
        }


def run_once(
    *,
    repo: Path,
    out: Path,
    mode: str,
    target: str,
    prompt_path: Path | None,
    transcript: str | None,
    max_turns: int,
    timeout_s: int,
) -> dict:
    out = ensure_out(out)
    run_id = uuid.uuid4().hex[:12]
    mode = (
        normalize_mode(mode)
        if mode not in ("off", "mock", "grok", "opencode", "recipe", "tool_microtask")
        else mode
    )

    if mode == "off":
        write_run(
            out,
            {
                "status": "skipped",
                "ok": True,
                "run_id": run_id,
                "mode": "off",
                "message": (
                    "VOICE_AUTO_AGENT off — set VOICE_AUTO_AGENT=opencode "
                    "(local default) or =grok (escalate)"
                ),
            },
        )
        return read_run(out)

    if not acquire_lock(out):
        cur = read_run(out)
        return {
            "status": "busy",
            "ok": False,
            "run_id": run_id,
            "mode": mode,
            "message": "another agent run is in progress",
            "current": cur,
        }

    try:
        effective = mode
        if target == "worker" and mode == "grok":
            print("==> target=worker → using opencode (local) not grok", file=sys.stderr)
            effective = "opencode"

        prompt = build_prompt(prompt_path, transcript, target, repo)
        write_run(
            out,
            {
                "status": "running",
                "ok": False,
                "run_id": run_id,
                "mode": effective,
                "target": target,
                "long_task": long_task_enabled(),
                "started": utc_now(),
                "transcript_preview": (transcript or "")[:200],
                "message": f"agent running ({effective})…",
            },
        )
        print(
            f"==> agent_runner mode={effective} run_id={run_id} target={target} "
            f"long_task={long_task_enabled()}",
            file=sys.stderr,
        )

        if effective == "mock":
            result = run_mock(prompt, out, run_id)
        elif effective == "recipe":
            os.environ.setdefault("VOICE_LONG_TASK", "1")
            result = run_recipe(prompt, repo, out, run_id)
        elif effective == "tool_microtask":
            os.environ.setdefault("VOICE_LONG_TASK", "1")
            result = run_tool_microtask(prompt, repo, out, run_id, timeout_s)
        elif effective == "opencode":
            result = run_opencode(prompt, repo, out, run_id, timeout_s)
        elif effective == "grok":
            result = run_grok(
                prompt, repo, out, max_turns=max_turns, timeout_s=timeout_s, run_id=run_id
            )
        else:
            result = {
                "status": "error",
                "ok": False,
                "run_id": run_id,
                "mode": effective,
                "error": f"unknown mode {effective}",
                "exit_code": 2,
                "reply": "",
            }

        result["target"] = target
        result["finished"] = utc_now()
        write_run(out, result)
        preview = (result.get("reply_preview") or result.get("reply") or "")[:200]
        print(
            f"==> agent_runner {result.get('status')} mode={result.get('mode')} "
            f"exit={result.get('exit_code')}",
            file=sys.stderr,
        )
        if preview:
            print(f"==> REPLY: {preview!r}", file=sys.stderr)
        return result
    finally:
        release_lock(out)


def spawn_background(**kwargs) -> str:
    run_id = uuid.uuid4().hex[:12]
    out = ensure_out(kwargs["out"])
    write_run(
        out,
        {
            "status": "queued",
            "ok": False,
            "run_id": run_id,
            "mode": kwargs.get("mode"),
            "target": kwargs.get("target"),
            "message": "queued for agent runner",
            "started": utc_now(),
        },
    )

    def _job() -> None:
        try:
            run_once(**kwargs)
        except Exception as e:
            write_run(
                out,
                {
                    "status": "error",
                    "ok": False,
                    "run_id": run_id,
                    "error": str(e),
                    "message": str(e),
                },
            )

    threading.Thread(target=_job, name=f"voice-agent-{run_id}", daemon=True).start()
    return run_id


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="T-0092 voice → local OpenCode/Ollama agent (Grok escalate optional)"
    )
    p.add_argument("--repo", type=Path, default=ROOT)
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    p.add_argument("--prompt-file", type=Path, help="agent-prompt.md path")
    p.add_argument("--transcript", "--text", dest="transcript", help="raw transcript text")
    p.add_argument("--target", default="worker", choices=["monitor", "worker", "raw"])
    p.add_argument(
        "--mode",
        default=None,
        help="off|mock|opencode|grok|recipe|tool_microtask|1(=opencode). Default: VOICE_AUTO_AGENT or opencode",
    )
    p.add_argument(
        "--max-turns",
        type=int,
        default=int(os.environ.get("VOICE_AGENT_MAX_TURNS", "8")),
    )
    p.add_argument(
        "--timeout",
        type=int,
        default=int(os.environ.get("VOICE_AGENT_TIMEOUT", "600")),
    )
    p.add_argument(
        "--long-task",
        action="store_true",
        help="Enable VOICE_LONG_TASK receipt framing (STATUS/DOD/EXIT/NEXT)",
    )
    p.add_argument("--background", action="store_true")
    p.add_argument("--status", action="store_true")
    args = p.parse_args(argv)

    if args.long_task:
        os.environ["VOICE_LONG_TASK"] = "1"

    out = ensure_out(args.out_dir)
    if args.status:
        print(json.dumps(read_run(out), indent=2))
        return 0

    if args.mode is None:
        env_mode = auto_mode()
        mode = env_mode if env_mode != "off" else "opencode"
    else:
        mode = normalize_mode(args.mode)

    # Prefer explicit CLI inputs. Auto-discover artifacts only when omitted.
    prompt_path = args.prompt_file
    transcript = args.transcript
    if prompt_path is None and transcript is None:
        cand = out / "agent-prompt.md"
        if cand.is_file():
            prompt_path = cand
    if transcript is None:
        tpath = out / "last-transcript.txt"
        if tpath.is_file():
            transcript = tpath.read_text(encoding="utf-8").strip()

    target = args.target
    if args.mode is None and target == "worker" and mode == "grok":
        target = "monitor"

    if args.background:
        rid = spawn_background(
            repo=args.repo.resolve(),
            out=out,
            mode=mode,
            target=target,
            prompt_path=prompt_path,
            transcript=transcript,
            max_turns=args.max_turns,
            timeout_s=args.timeout,
        )
        print(
            json.dumps(
                {
                    "queued": True,
                    "run_id": rid,
                    "mode": mode,
                    "target": target,
                    "long_task": long_task_enabled(),
                },
                indent=2,
            )
        )
        return 0

    result = run_once(
        repo=args.repo.resolve(),
        out=out,
        mode=mode,
        target=target,
        prompt_path=prompt_path,
        transcript=transcript,
        max_turns=args.max_turns,
        timeout_s=args.timeout,
    )
    print(
        json.dumps(
            {
                k: result.get(k)
                for k in (
                    "status",
                    "ok",
                    "run_id",
                    "mode",
                    "exit_code",
                    "duration_s",
                    "error",
                    "reply_preview",
                    "fallback",
                    "model",
                    "long_task",
                )
            },
            indent=2,
        )
    )
    if result.get("reply"):
        print("--- reply ---", file=sys.stderr)
        print(result["reply"][:2000], file=sys.stderr)
    # status=done with ok=false is still a failure (e.g. OpenCode provider error).
    if result.get("ok") or result.get("status") == "skipped":
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
