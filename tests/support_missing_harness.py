"""Run the missing-binary arm of exec_harness from scripts/pfy.

PATH contains python3 only, so the harness binary, curl, and npm are absent.
Inference ensure is not called. The function body is the one in scripts/pfy.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PFY = ROOT / "scripts" / "pfy"


def _extract(text: str, name: str) -> str:
    marker = name + "() {"
    start = text.index(marker)
    depth = 0
    for index in range(start, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    raise RuntimeError("unbalanced " + name)


def run_missing_harness(harness_id: str) -> subprocess.CompletedProcess[str]:
    text = PFY.read_text(encoding="utf-8")
    body = "\n".join(
        [
            _extract(text, "have"),
            _extract(text, "json_field"),
            _extract(text, "rt_get"),
            "detect_status() { echo missing; }",
            "print_fs_nav() { echo filesystem: direct; }",
            "apply_opencontext_env() { :; }",
            "apply_attach_mode_env() { return 0; }",
            'local_runtime() { echo \'{"engine":"none","status":"missing","base_url":""}\'; }',
            _extract(text, "exec_harness"),
            "exec_harness " + harness_id,
        ]
    )
    python = shutil.which("python3")
    if not python:
        raise RuntimeError("python3 is not on PATH")
    scratch = ROOT / "tmp"
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="missing-harness-", dir=scratch) as td:
        bindir = Path(td) / "bin"
        bindir.mkdir()
        os.symlink(python, bindir / "python3")
        script = "\n".join(
            [
                "set -u",
                "ROOT=" + str(ROOT),
                'REG="$ROOT/data/harnesses.json"',
                body,
            ]
        )
        return subprocess.run(
            ["/bin/bash", "-c", script],
            cwd=td,
            capture_output=True,
            text=True,
            env={"PATH": str(bindir), "HOME": td, "PFY_STATE_DIR": td},
            timeout=30,
        )
