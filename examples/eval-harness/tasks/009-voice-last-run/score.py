#!/usr/bin/env python3
"""Deterministic scorer: agent_runner last-run.json contract (voice stack).

Gates the machine-readable receipt that remote UI, smokes, and CI poll.
Accepts either a .json file path or raw JSON text.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

STATUS_OK = frozenset(
    {"done", "error", "running", "queued", "busy", "skipped", "none"}
)
MODE_OK = frozenset(
    {
        "mock",
        "recipe",
        "opencode",
        "opencode-ollama",
        "ollama",
        "grok",
        "off",
        "none",
    }
)


def score(text: str) -> tuple[bool, str]:
    text = (text or "").strip()
    if not text:
        return False, "empty"
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return False, f"json parse error: {e}"
    if not isinstance(data, dict):
        return False, "root must be object"
    status = data.get("status")
    if status not in STATUS_OK:
        return False, f"status not in contract: {status!r}"
    # Terminal success path must be explicit
    if status == "done":
        if data.get("ok") is not True:
            return False, "status=done requires ok=true"
        if "mode" not in data:
            return False, "status=done requires mode"
        mode = str(data.get("mode") or "")
        if mode not in MODE_OK:
            return False, f"mode not recognized: {mode!r}"
        # long_task flag recommended for long-task product path
        if "long_task" in data and not isinstance(data["long_task"], bool):
            return False, "long_task must be bool when present"
        return True, f"ok status=done mode={mode} long_task={data.get('long_task')}"
    if status == "error":
        if data.get("ok") is True:
            return False, "status=error must not have ok=true"
        return True, f"ok status=error mode={data.get('mode')}"
    if status in ("running", "queued", "busy"):
        return True, f"ok in-flight status={status}"
    if status in ("skipped", "none"):
        return True, f"ok idle status={status}"
    return False, f"unhandled status {status!r}"


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] == "-":
        text = sys.stdin.read()
    else:
        text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    ok, detail = score(text)
    print(f"SCORE: {'PASS' if ok else 'FAIL'} ({detail})")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
