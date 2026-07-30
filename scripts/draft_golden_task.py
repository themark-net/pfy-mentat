#!/usr/bin/env python3
"""Draft a golden-task JSON card (semi-auto). Operator edits before commit."""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "golden-tasks"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True, help="GT-NNNN")
    ap.add_argument("--title", required=True)
    ap.add_argument("--scale", default="docs", choices=["orchestration", "multi_file", "single_code", "docs"])
    ap.add_argument("--human", required=True)
    ap.add_argument("--agent", action="append", default=[], help="agent task bullet (repeatable)")
    ap.add_argument("--artifact", action="append", default=[], help="file path artifact (repeatable)")
    ap.add_argument("--check", action="append", default=[], help="acceptance check string")
    args = ap.parse_args()

    arts = [{"kind": "file", "ref": a, "note": "artifact"} for a in args.artifact]
    checks = args.check or [f"File {a} exists" for a in args.artifact] or ["(edit acceptance_checks)"]
    card = {
        "id": args.id,
        "title": args.title,
        "created": date.today().isoformat(),
        "scale": args.scale,
        "human_request": args.human,
        "agent_tasks": args.agent or ["(edit agent_tasks)"],
        "artifacts": arts,
        "acceptance_checks": checks,
        "source_session": date.today().isoformat(),
        "replay_prompt": args.human,
        "notes": "draft via scripts/draft_golden_task.py — edit before relying on scores",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    slug = args.title.lower().replace(" ", "-")[:40]
    path = OUT / f"{args.id}-{slug}.json"
    path.write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
