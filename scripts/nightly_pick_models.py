#!/usr/bin/env python3
"""Pick Ollama models present on host for nightly matrix."""
from __future__ import annotations
import json
import os
import urllib.request

prefer = [
    "deepseek-coder:6.7b-instruct",
    "deepseek-coder:6.7b",
    "qwen2.5-coder:7b-instruct",
    "qwen2.5:7b-instruct",
]

def main() -> int:
    forced = (os.environ.get("EVAL_MODELS") or "").strip()
    if forced:
        print(forced)
        return 0
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5) as r:
            data = json.loads(r.read().decode())
    except Exception:
        print("")
        return 1
    names = [m.get("name", "") for m in data.get("models") or []]
    pick = [p for p in prefer if p in names]
    if not pick:
        pick = [n for n in names if "coder" in n or "instruct" in n][:3]
    if not pick:
        pick = names[:2]
    print(",".join(pick[:4]))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
