#!/usr/bin/env python3
"""Run the MVP2 local-vs-cloud trial. Logs go under tmp/. Stdout is short."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "997d89264495861a178713ccf7d4447ea828afc4"
RUNS = ROOT / "tmp" / "mvp2-runs"
GATES = ROOT / "eval" / "mvp2" / "gates"
TASKS_DIR = ROOT / "eval" / "mvp2" / "tasks"
RESULTS = ROOT / "eval" / "mvp2" / "results"
PATCHES = ROOT / "eval" / "mvp2" / "patches"
SCRATCH = ROOT / "tmp" / "mvp2-trial-tmp"
MODEL = "qwen3.6:35b"
CLOUD_TIMEOUT = 40 * 60
# Wrapper only. The local agent timeout stays the tool default (1200s).
LOCAL_WRAPPER_TIMEOUT = 60 * 60

TASKS = [
    {
        "id": "t1-smolvm-stderr-first",
        "level": "trivial",
        "gate_name": "test_mvp2_t1_smolvm_evidence.py",
        "gate": "python3 -m unittest tests.test_mvp2_t1_smolvm_evidence",
        "writable": [],
    },
    {
        "id": "t2-tree-sig-119",
        "level": "trivial",
        "gate_name": "test_mvp2_t2_tree_sig_119.py",
        "gate": "python3 -m unittest tests.test_mvp2_t2_tree_sig_119",
        "writable": [],
    },
    {
        "id": "t3-daemon-stop-fail",
        "level": "medium",
        "gate_name": "test_mvp2_t3_daemon_stop.py",
        "gate": (
            "python3 -m unittest tests.test_mvp2_t3_daemon_stop "
            "tests.test_x_intake_smoke_112_114.XIntakeSmoke112114Tests.test_overtime_daemon_stop_timeout_uses_shared_text"
        ),
        "writable": [],
    },
    {
        "id": "t4-timeout-substep",
        "level": "medium",
        "gate_name": "test_mvp2_t4_timeout_step.py",
        "gate": (
            "python3 -m unittest tests.test_mvp2_t4_timeout_step "
            "tests.test_x_intake_smoke_112_114.XIntakeSmoke112114Tests.test_overtime_timeout_reason_is_shared_text "
            "tests.test_x_intake_smoke_112_114.XIntakeSmoke112114Tests.test_festival_timeout_reason_is_shared_text "
            "tests.test_x_intake_smoke_112_114.XIntakeSmoke112114Tests.test_overtime_daemon_stop_timeout_uses_shared_text"
        ),
        "writable": ["tests/test_x_intake_smoke_112_114.py"],
    },
    {
        "id": "t5-receipts-outside-repo",
        "level": "slightly-hard",
        "gate_name": "test_mvp2_t5_receipts.py",
        "gate": "python3 -m unittest tests.test_mvp2_t5_receipts",
        "writable": [
            "tests/test_x_intake_smoke_117_118.py",
            "tests/test_x_intake_smoke_119_121.py",
        ],
    },
    {
        "id": "t6-tree-sig-three",
        "level": "slightly-hard",
        "gate_name": "test_mvp2_t6_tree_sig_three.py",
        "gate": "python3 -m unittest tests.test_mvp2_t6_tree_sig_three",
        "writable": [],
    },
]


def _log(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)
        if not text.endswith("\n"):
            handle.write("\n")


def _say(line: str) -> None:
    print(line, flush=True)


def _git(cwd: Path, args: list[str], timeout: float = 60) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = "pfy-local-build"
    env["GIT_AUTHOR_EMAIL"] = "pfy-local-build@localhost"
    env["GIT_COMMITTER_NAME"] = "pfy-local-build"
    env["GIT_COMMITTER_EMAIL"] = "pfy-local-build@localhost"
    return subprocess.run(
        ["git", *args], cwd=str(cwd), env=env, text=True, capture_output=True, timeout=timeout, check=False,
    )


def _meminfo() -> dict[str, int]:
    out = {}
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        num = val.strip().split()[0]
        if num.isdigit():
            out[key] = int(num)
    return out


def _free_gib() -> float:
    info = _meminfo()
    kb = info.get("MemAvailable", 0) + info.get("SwapFree", 0)
    return kb / (1024.0 * 1024.0)


def _loaded_models() -> list[str]:
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (OSError, json.JSONDecodeError, TimeoutError):
        return ["unreadable"]
    names = []
    for row in data.get("models") or []:
        name = row.get("name") or row.get("model") or ""
        if name:
            names.append(str(name))
    return names


def _load_local():
    spec = importlib.util.spec_from_file_location("pfy_build_local", ROOT / "scripts" / "pfy_build_local.py")
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _task(task_id: str) -> dict:
    for task in TASKS:
        if task["id"] == task_id:
            return task
    raise SystemExit("unknown task " + task_id)


def _remove_worktree(path: Path) -> None:
    if path.exists():
        _git(ROOT, ["worktree", "remove", "--force", str(path)], timeout=120)
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
        _git(ROOT, ["worktree", "prune"], timeout=60)


def _plant(task: dict, dest: Path) -> str:
    _remove_worktree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    added = _git(ROOT, ["worktree", "add", "--detach", str(dest), BASE], timeout=120)
    if added.returncode != 0:
        raise SystemExit("worktree add failed: " + (added.stderr or added.stdout))
    gate_src = GATES / task["gate_name"]
    gate_dst = dest / "tests" / task["gate_name"]
    shutil.copyfile(gate_src, gate_dst)
    _git(dest, ["add", "--", str(Path("tests") / task["gate_name"])])
    committed = _git(dest, ["commit", "-m", "test: red gate for " + task["id"]])
    if committed.returncode != 0:
        raise SystemExit("plant commit failed: " + (committed.stderr or committed.stdout))
    sha = _git(dest, ["rev-parse", "HEAD"])
    return (sha.stdout or "").strip()


def _gate_env(worktree: Path) -> dict[str, str]:
    home = worktree / "tmp" / "gate-home"
    tmp = worktree / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    home.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["TMPDIR"] = str(tmp)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("PFY_SMOKE_RECEIPT_DIR", None)
    return env


def _run_gate(module, worktree: Path, gate: str) -> dict:
    state = module.State()
    return module.run_tests(
        gate,
        worktree,
        _gate_env(worktree),
        600,
        state,
        repo=worktree,
        unsafe=False,
    )


def _diff_stat(worktree: Path, base: str) -> dict:
    proc = _git(worktree, ["diff", "--numstat", base])
    files = 0
    ins = 0
    dels = 0
    for line in (proc.stdout or "").splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        files += 1
        if parts[0].isdigit():
            ins += int(parts[0])
        if parts[1].isdigit():
            dels += int(parts[1])
    return {"files": files, "insertions": ins, "deletions": dels}


def _write_patch(worktree: Path, base: str, dest: Path) -> None:
    proc = _git(worktree, ["diff", base], timeout=60)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(proc.stdout or "", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _canonical_gate(module, task: dict, worktree: Path) -> dict:
    """Re-run the gate with the canonical acceptance test restored, then put the tree back."""
    gate_path = worktree / "tests" / task["gate_name"]
    saved = gate_path.read_bytes() if gate_path.is_file() else None
    canonical = (GATES / task["gate_name"]).read_bytes()
    same = saved == canonical
    if not same:
        gate_path.write_bytes(canonical)
    try:
        record = _run_gate(module, worktree, task["gate"])
    finally:
        if saved is None:
            if gate_path.exists() and not same:
                gate_path.unlink()
        elif not same:
            gate_path.write_bytes(saved)
    return {
        "acceptance_test_unchanged": same,
        "exit": record.get("exit"),
        "passed": record.get("passed"),
        "failed": record.get("failed"),
        "errors": record.get("errors"),
    }


def _usage_counts(cwd: Path) -> dict:
    """Session turn and model-call counts only. No token fields."""
    spec = importlib.util.spec_from_file_location("pfy_build_p", ROOT / "scripts" / "pfy_build_p.py")
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    session_id = module.find_latest_session(cwd)
    usage = module.read_usage(cwd, session_id) if session_id else {}
    session = usage.get("session") or {}
    return {
        "session_present": bool(session_id),
        "turn_count": session.get("turnCount"),
        "model_calls": session.get("modelCalls"),
    }


def prove_red(only: str | None) -> int:
    module = _load_local()
    bad = []
    for task in TASKS:
        if only and task["id"] != only:
            continue
        dest = RUNS / (task["id"] + "-prove")
        log = RUNS / "logs" / (task["id"] + "-prove.log")
        try:
            planted = _plant(task, dest)
            record = _run_gate(module, dest, task["gate"])
        except Exception as exc:
            _say("PROVE_FAIL " + task["id"] + " harness " + type(exc).__name__)
            _log(log, str(exc))
            bad.append(task["id"])
            continue
        failed = int((record.get("counts") or {}).get("failed") or 0)
        errors = int((record.get("counts") or {}).get("errors") or 0)
        exit_code = record.get("exit")
        tail = record.get("tail") or ""
        if not isinstance(tail, str):
            tail = "\n".join(str(part) for part in tail)
        _log(log, "planted " + planted + "\nexit " + str(exit_code) + "\n" + tail)
        if exit_code not in (0, None) and (failed + errors) > 0 and record.get("counts"):
            _say("PROVE_RED " + task["id"] + " failed=" + str(failed) + " errors=" + str(errors))
        else:
            _say("PROVE_FAIL " + task["id"] + " exit=" + str(exit_code) + " failed=" + str(failed))
            bad.append(task["id"])
        _remove_worktree(dest)
    if bad:
        _say("PROVE_DONE bad=" + ",".join(bad))
        return 1
    _say("PROVE_DONE ok")
    return 0


def _result_path(task_id: str, arm: str) -> Path:
    return RESULTS / (task_id + "-" + arm + ".json")


def _save_result(payload: dict) -> None:
    path = _result_path(payload["task"], payload["arm"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _arm_dir(task_id: str, arm: str) -> Path:
    return RUNS / (task_id + "-" + arm)


def run_local(task: dict, keep_model: bool) -> dict:
    module = _load_local()
    dest = _arm_dir(task["id"], "L")
    log = RUNS / "logs" / (task["id"] + "-L.log")
    planted = _plant(task, dest)
    pre = _run_gate(module, dest, task["gate"])
    pre_failed = int((pre.get("counts") or {}).get("failed") or 0) + int((pre.get("counts") or {}).get("errors") or 0)
    if pre.get("exit") == 0 or pre_failed == 0:
        payload = _blank(task, "L", planted)
        payload["status"] = "BLOCKED"
        payload["reason"] = "gate-not-red"
        payload["gate_exit"] = pre.get("exit")
        _save_result(payload)
        _say("ARM_DONE " + task["id"] + " L BLOCKED gate-not-red")
        return payload
    free = _free_gib()
    loaded = _loaded_models()
    others = [name for name in loaded if MODEL.split(":")[0] not in name]
    if loaded == ["unreadable"] or (others and loaded != ["unreadable"]):
        # A different loaded model is busy-host. The requested model is allowed.
        foreign = [name for name in loaded if not name.startswith(MODEL.split(":")[0])]
        if loaded == ["unreadable"] or foreign:
            payload = _blank(task, "L", planted)
            payload["status"] = "BLOCKED"
            payload["reason"] = "busy-or-unreadable-ps"
            payload["loaded_models"] = len(loaded)
            payload["free_gib"] = round(free, 3)
            _save_result(payload)
            _say("ARM_DONE " + task["id"] + " L BLOCKED ps")
            return payload
    if free < 32:
        payload = _blank(task, "L", planted)
        payload["status"] = "BLOCKED"
        payload["reason"] = "mem"
        payload["free_gib"] = round(free, 3)
        _save_result(payload)
        _say("ARM_DONE " + task["id"] + " L BLOCKED mem")
        return payload
    receipt_dir = RUNS / "receipts" / (task["id"] + "-L")
    if receipt_dir.exists():
        shutil.rmtree(receipt_dir)
    cmd = [
        str(ROOT / "pfy"), "build", "--local",
        "--prompt-file", str(TASKS_DIR / (task["id"] + ".md")),
        "--repo", str(dest),
        "--base", planted,
        "--test-cmd", task["gate"],
        "--receipt-dir", str(receipt_dir),
        "--keep-worktree",
        "--model", MODEL,
    ]
    if keep_model:
        cmd.append("--keep-model")
    for glob in task["writable"]:
        cmd.extend(["--writable-test", glob])
    _say("ARM_START " + task["id"] + " L")
    started = time.monotonic()
    timed_out = False
    try:
        proc = subprocess.run(
            cmd, cwd=str(ROOT), text=True, capture_output=True, timeout=LOCAL_WRAPPER_TIMEOUT, check=False,
            env={**os.environ, "TMPDIR": str(SCRATCH), "PYTHONDONTWRITEBYTECODE": "1"},
        )
        out_text = proc.stdout or ""
        err_text = proc.stderr or ""
        code = proc.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        out_text = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", "replace")
        err_text = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", "replace")
        code = 124
    wall = round(time.monotonic() - started, 3)
    _log(log, out_text)
    _log(log, err_text)
    receipt_path = receipt_dir / "receipt.json"
    receipt = {}
    if receipt_path.is_file():
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    inner = receipt.get("worktree")
    diff_root = Path(inner) if inner else dest
    diff_base = BASE
    stat = _diff_stat(diff_root, diff_base) if diff_root.exists() else {"files": 0, "insertions": 0, "deletions": 0}
    patch = PATCHES / (task["id"] + "-L.patch")
    if diff_root.exists():
        _write_patch(diff_root, diff_base, patch)
    canonical = {"acceptance_test_unchanged": None, "exit": None}
    if diff_root.exists() and (diff_root / "tests" / task["gate_name"]).exists():
        canonical = _canonical_gate(module, task, diff_root)
    elif (dest / "tests" / task["gate_name"]).exists():
        canonical = _canonical_gate(module, task, dest)
    payload = _blank(task, "L", planted)
    payload.update({
        "status": "TIMEOUT" if timed_out else (receipt.get("status") or ("PASS" if code == 0 else "FAIL")),
        "reason": "wrapper-timeout" if timed_out else receipt.get("reason"),
        "exit_code": code,
        "wall_seconds": wall,
        "agent_seconds": receipt.get("agent_seconds"),
        "diff": stat,
        "attempts": 1,
        "free_gib_before": round(free, 3),
        "receipt_status": receipt.get("status"),
        "receipt_reason": receipt.get("reason"),
        "branch": receipt.get("branch"),
        "commit": receipt.get("commit"),
        "sandbox": receipt.get("sandbox"),
        "tests_before": _brief_tests(receipt.get("tests_before")),
        "tests_after": _brief_tests(receipt.get("tests_after")),
        "canonical_gate": canonical,
        "patch": str(patch.relative_to(ROOT)) if patch.exists() else None,
        "mem": receipt.get("mem"),
    })
    _save_result(payload)
    _say("ARM_DONE " + task["id"] + " L " + str(payload["status"]) + " " + str(payload["reason"]))
    return payload


def _brief_tests(row: dict | None) -> dict | None:
    if not row:
        return None
    return {key: row.get(key) for key in ("exit", "passed", "failed", "errors", "seconds")}


def _blank(task: dict, arm: str, planted: str) -> dict:
    return {
        "task": task["id"],
        "level": task["level"],
        "arm": arm,
        "base_sha": BASE,
        "planted_sha": planted,
        "gate": task["gate"],
        "status": None,
        "reason": None,
        "attempts": 0,
        "quality_accept": None,
        "quality_why": "pending review",
        "gaming": None,
        "scope_creep": None,
    }


def run_cloud(task: dict, attempt: int) -> dict:
    module = _load_local()
    dest = _arm_dir(task["id"], "C" if attempt == 1 else "C" + str(attempt))
    if attempt > 1:
        # Retry in a fresh worktree. Keep the first tree for the patch.
        dest = _arm_dir(task["id"], "C-retry")
    log = RUNS / "logs" / (task["id"] + "-C-" + str(attempt) + ".log")
    planted = _plant(task, dest)
    pre = _run_gate(module, dest, task["gate"])
    pre_failed = int((pre.get("counts") or {}).get("failed") or 0) + int((pre.get("counts") or {}).get("errors") or 0)
    if pre.get("exit") == 0 or pre_failed == 0:
        payload = _blank(task, "C", planted)
        payload["status"] = "BLOCKED"
        payload["reason"] = "gate-not-red"
        payload["attempts"] = attempt
        _save_result(payload)
        _say("ARM_DONE " + task["id"] + " C BLOCKED gate-not-red")
        return payload
    prompt = (TASKS_DIR / (task["id"] + ".md")).read_text(encoding="utf-8")
    _say("ARM_START " + task["id"] + " C attempt=" + str(attempt))
    started = time.monotonic()
    timed_out = False
    try:
        proc = subprocess.run(
            ["grok", "-p", prompt, "--cwd", str(dest), "--always-approve", "--no-alt-screen"],
            cwd=str(dest), text=True, capture_output=True, timeout=CLOUD_TIMEOUT, check=False,
            env={**os.environ, "TMPDIR": str(SCRATCH)},
        )
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        code = proc.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", "replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", "replace")
        code = 124
    wall = round(time.monotonic() - started, 3)
    _log(log, ("TIMEOUT\n" if timed_out else "") + stdout + "\n" + stderr)
    gate = _run_gate(module, dest, task["gate"])
    canonical = _canonical_gate(module, task, dest)
    stat = _diff_stat(dest, BASE)
    patch_name = task["id"] + ("-C.patch" if attempt == 1 else "-C-retry.patch")
    patch = PATCHES / patch_name
    _write_patch(dest, BASE, patch)
    passed = gate.get("exit") == 0 and int((gate.get("counts") or {}).get("failed") or 0) == 0 and int((gate.get("counts") or {}).get("errors") or 0) == 0
    usage = _usage_counts(dest)
    status = "TIMEOUT" if timed_out else ("PASS" if passed else "FAIL")
    payload = _blank(task, "C", planted)
    payload.update({
        "status": status,
        "reason": "timeout" if timed_out else ("gate-pass" if passed else "gate-fail"),
        "exit_code": code,
        "wall_seconds": wall,
        "diff": stat,
        "attempts": attempt,
        "gate_exit": gate.get("exit"),
        "gate_passed": gate.get("passed"),
        "gate_failed": gate.get("failed"),
        "gate_errors": gate.get("errors"),
        "canonical_gate": canonical,
        "patch": str(patch.relative_to(ROOT)),
        "usage": usage,
        "prior_attempt": _prior_cloud(task["id"]) if attempt > 1 else None,
        "grok_stdout_bytes": len(stdout),
        "grok_stderr_bytes": len(stderr),
    })
    _save_result(payload)
    _say("ARM_DONE " + task["id"] + " C " + status + " attempt=" + str(attempt))
    return payload


def _prior_cloud(task_id: str) -> dict | None:
    path = _result_path(task_id, "C")
    if not path.is_file():
        return None
    try:
        prior = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    prior.pop("prior_attempt", None)
    return prior


def _auth_exists() -> bool:
    return (Path.home() / ".grok" / "auth.json").is_file() and (Path.home() / ".grok" / "auth.json").stat().st_size > 0


def main(argv: list[str]) -> int:
    os.environ["TMPDIR"] = str(SCRATCH)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    RUNS.mkdir(parents=True, exist_ok=True)
    if len(argv) < 2:
        raise SystemExit("usage: run_trial.py prove-red [task] | arm L|C task | all-local | all-cloud")
    action = argv[1]
    if action == "prove-red":
        return prove_red(argv[2] if len(argv) > 2 else None)
    if action == "arm":
        arm = argv[2]
        task = _task(argv[3])
        if arm == "L":
            run_local(task, keep_model=True)
            return 0
        if arm == "C":
            first = run_cloud(task, 1)
            if first["status"] != "PASS":
                run_cloud(task, 2)
            return 0
        raise SystemExit("arm is L or C")
    if action == "all-local":
        _say("AUTH " + ("present" if _auth_exists() else "missing"))
        _say("FREE_GIB " + str(round(_free_gib(), 3)))
        for task in TASKS:
            run_local(task, keep_model=True)
        _say("ALL_LOCAL_DONE")
        return 0
    if action == "all-cloud":
        _say("AUTH " + ("present" if _auth_exists() else "missing"))
        for task in TASKS:
            first = run_cloud(task, 1)
            if first["status"] != "PASS":
                run_cloud(task, 2)
        _say("ALL_CLOUD_DONE")
        return 0
    raise SystemExit("unknown action")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
