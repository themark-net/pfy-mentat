#!/usr/bin/env python3
"""GAP-05: lint examples smoke/run-in-cage presence for known integration examples."""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EX = ROOT / "examples"
required = {
    "litellm-ollama": ("smoke_completion.py", "smoke.sh"),
    "codebase-memory-mcp": ("smoke.sh", "run-in-cage.sh"),
    "repowise": ("smoke.sh", "run-in-cage.sh"),
    "write-guard-mcp": ("smoke.sh", "run-in-cage.sh"),
    "opencode-ollama": ("smoke.sh",),
    "voice-stt-edge": ("smoke.sh",),
    "eval-harness": ("run_structural.py",),
}
bad = []
for name, files in required.items():
    d = EX / name
    if not d.is_dir():
        bad.append(f"missing dir {name}")
        continue
    if not any((d / f).exists() for f in files):
        bad.append(f"{name}: need one of {files}")
if bad:
    print("FAIL smoke contract:", bad)
    sys.exit(1)
print(f"PASS smoke contract {len(required)} example dirs")
sys.exit(0)
