"""JSONL audit log for write-guard (no file contents)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


def append_event(
    audit_log: str,
    *,
    op: str,
    path: str,
    allow: bool,
    reason: str,
    mode: str,
    extra: dict[str, Any] | None = None,
) -> None:
    path_p = Path(audit_log)
    try:
        path_p.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return
    event = {
        "ts": time.time(),
        "op": op,
        "path": path,
        "allow": allow,
        "reason": reason,
        "mode": mode,
        "pid": os.getpid(),
    }
    if extra:
        event.update(extra)
    try:
        with path_p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError:
        pass


def tail_events(audit_log: str, n: int = 20) -> list[dict[str, Any]]:
    p = Path(audit_log)
    if not p.is_file():
        return []
    try:
        lines = p.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out: list[dict[str, Any]] = []
    for line in lines[-n:]:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out
