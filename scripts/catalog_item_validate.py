#!/usr/bin/env python3
"""Validate catalog item v2 fields on data/toolsets.json (stdlib only; no jsonschema).

Rows that declare ``kind``, plus code-graph, core-skills, and rea, must have
the v2 required keys. Also runs pfylib.registry.validate.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pfylib import registry  # noqa: E402

REQUIRED = ("id", "title", "kind", "provides", "install", "presets", "secrets")
KINDS = frozenset({"skill", "mcp", "external", "env", "bundle"})
STRATEGIES = frozenset({"native", "delegate"})
MUST = ("code-graph", "core-skills", "rea")


def _check_item(item: dict, problems: list[str]) -> None:
    tid = item.get("id")
    label = tid if isinstance(tid, str) and tid else "?"
    for key in REQUIRED:
        if key not in item:
            problems.append("%s: missing %s" % (label, key))
    if "kind" in item and item.get("kind") not in KINDS:
        problems.append("%s: illegal kind %r" % (label, item.get("kind")))
    install = item.get("install")
    strategy = install.get("strategy") if isinstance(install, dict) else None
    if "install" in item and strategy not in STRATEGIES:
        problems.append("%s: install.strategy must be native|delegate (got %r)" % (label, strategy))
    secrets = item.get("secrets")
    presets = item.get("presets")
    if "secrets" in item and not isinstance(secrets, list):
        problems.append("%s: secrets must be a list" % label)
    if "presets" in item and not isinstance(presets, list):
        problems.append("%s: presets must be a list" % label)
    if isinstance(presets, list) and presets and secrets != []:
        problems.append("%s: non-empty presets requires secrets == []" % label)


def main() -> int:
    path = ROOT / "data" / "toolsets.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print("FAIL catalog-item-v2: %s" % exc)
        return 1
    rows = data.get("toolsets") if isinstance(data, dict) else None
    problems: list[str] = []
    if not isinstance(rows, list):
        problems.append("toolsets.json: toolsets[] missing")
        rows = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            problems.append("toolsets.json: non-object row")
            continue
        tid = row.get("id")
        if isinstance(tid, str):
            seen.add(tid)
        if (isinstance(tid, str) and tid in MUST) or "kind" in row:
            _check_item(row, problems)
    for iid in MUST:
        if iid not in seen:
            problems.append("missing required item %s" % iid)
    for problem in registry.validate(root_dir=ROOT):
        problems.append("registry: %s" % problem)
    if problems:
        for problem in problems:
            print("FAIL %s" % problem)
        return 1
    print("PASS catalog-item-v2")
    return 0


if __name__ == "__main__":
    sys.exit(main())
