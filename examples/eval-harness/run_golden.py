#!/usr/bin/env python3
"""Golden-task lane (OQ-0008 / #31): validate cards, write pipelines/eval/golden.latest.md.

No LLM required for deterministic acceptance_checks.
Optional future: --replay with EVAL_MODEL (not implemented here).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATE = Path(__file__).resolve().parent / "validate_golden_tasks.py"
GT_DIR = ROOT / "data" / "golden-tasks"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--write-md",
        type=Path,
        default=ROOT / "pipelines" / "eval" / "golden.latest.md",
    )
    ap.add_argument("--strict-artifacts", action="store_true")
    args = ap.parse_args()

    cmd = [sys.executable, str(VALIDATE)]
    if args.strict_artifacts:
        cmd.append("--strict-artifacts")
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    out = (p.stdout or "") + (p.stderr or "")
    print(out, end="" if out.endswith("\n") else "\n")

    cards = sorted(GT_DIR.glob("GT-*.json"))
    lines = [
        f"# Golden-task eval — {datetime.now(timezone.utc).isoformat()}",
        "",
        f"**validate_golden_tasks.py:** {'PASS' if p.returncode == 0 else 'FAIL'} (exit {p.returncode})",
        "",
        "| Card | Scale | Title |",
        "|------|-------|-------|",
    ]
    for c in cards:
        try:
            data = json.loads(c.read_text(encoding="utf-8"))
            lines.append(
                f"| `{data.get('id', c.stem)}` | {data.get('scale', '?')} | {data.get('title', c.name)[:60]} |"
            )
        except Exception as e:  # noqa: BLE001
            lines.append(f"| `{c.name}` | ? | parse error: {e} |")
    lines.append("")
    lines.append("Deterministic lane only — no LLM replay yet. See docs/ops/local-model-storage-and-eval.md.")
    lines.append("")

    args.write_md.parent.mkdir(parents=True, exist_ok=True)
    args.write_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {args.write_md}", flush=True)
    return p.returncode


if __name__ == "__main__":
    raise SystemExit(main())
