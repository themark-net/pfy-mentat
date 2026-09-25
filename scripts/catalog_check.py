#!/usr/bin/env python3
"""ADR-0015: tools.json is a slim machine subset of TOOLS.md.
ADR-0017: catalog <-> implementation link between tools.json and data/toolsets.json.

Exit 0 if
  1. every JSON tool name appears in TOOLS.md (does not require row counts to match);
  2. data/toolsets.json is well-formed against data/harnesses.json (pfylib.registry.validate);
  3. every tools.json `implementation` object names an existing toolset whose
     `catalog_tool` is this row's name, with a stage in I0-I4;
  4. every toolset with a non-null `catalog_tool` has exactly that reverse link.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pfylib import registry  # noqa: E402

STAGES = ("I0", "I1", "I2", "I3", "I4")


def main() -> int:
    tools = json.loads((ROOT / "data/tools.json").read_text())
    md = (ROOT / "TOOLS.md").read_text(encoding="utf-8", errors="replace")
    rows = tools.get("tools") or []
    problems: list[str] = []

    missing = [t["name"] for t in rows if t.get("name") and t["name"] not in md]
    if missing:
        problems.append("JSON tools missing from TOOLS.md: %s" % missing)

    problems += ["toolsets: %s" % p for p in registry.validate(root_dir=ROOT)]

    toolsets = {t.get("id"): t for t in registry.toolset_rows(ROOT)}
    linked: dict[str, str] = {}
    for t in rows:
        impl = t.get("implementation")
        if impl is None:
            continue
        name = t.get("name", "?")
        if not isinstance(impl, dict):
            problems.append("%s: implementation must be an object {toolset, stage}" % name)
            continue
        tid = impl.get("toolset")
        if tid not in toolsets:
            problems.append("%s: implementation.toolset %r not in data/toolsets.json" % (name, tid))
        elif toolsets[tid].get("catalog_tool") != name:
            problems.append(
                "%s: implementation.toolset %r has catalog_tool %r (must equal this row name)"
                % (name, tid, toolsets[tid].get("catalog_tool"))
            )
        else:
            linked[tid] = name
        if impl.get("stage") not in STAGES:
            problems.append("%s: implementation.stage %r not in %s" % (name, impl.get("stage"), list(STAGES)))

    for tid, t in toolsets.items():
        ct = t.get("catalog_tool")
        if ct is None:
            continue
        if ct not in md:
            problems.append("toolset %s: catalog_tool %r not found in TOOLS.md" % (tid, ct))
        if linked.get(tid) != ct:
            problems.append(
                "toolset %s: catalog_tool %r has no tools.json row with implementation.toolset == %r" % (tid, ct, tid)
            )

    if problems:
        print("FAIL catalog-check:")
        for p in problems:
            print("  - %s" % p)
        return 1
    n_linked = len(linked)
    n_null = sum(1 for t in toolsets.values() if t.get("catalog_tool") is None)
    print(
        "PASS catalog-check slim-subset ok n_json=%d (not a 1:1 dump of TOOLS.md) · toolsets=%d linked=%d catalog_tool=null:%d"
        % (len(rows), len(toolsets), n_linked, n_null)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
