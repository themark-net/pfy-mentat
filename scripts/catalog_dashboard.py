#!/usr/bin/env python3
"""GAP-04: generate static scoring dashboard from tools.json."""
from __future__ import annotations
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "pipelines" / "catalog" / "dashboard.latest.md"


def main() -> int:
    data = json.loads((ROOT / "data/tools.json").read_text())
    tools = data["tools"]
    by_tier: dict[str, list] = defaultdict(list)
    for t in tools:
        by_tier[t.get("tier", "?")].append(t)
    stages = Counter(t.get("integration_stage", "?") for t in tools)
    lines = [
        "# Catalog scoring dashboard",
        "",
        f"Generated: {date.today().isoformat()} · tools.json v{data.get('version')} · n={len(tools)}",
        "",
        "## Tier counts",
        "",
        "| Tier | Count |",
        "|------|------:|",
    ]
    for tier in sorted(by_tier.keys()):
        lines.append(f"| {tier} | {len(by_tier[tier])} |")
    lines += ["", "## Integration stages", "", "| Stage | Count |", "|-------|------:|"]
    for st, n in sorted(stages.items()):
        lines.append(f"| {st} | {n} |")
    lines += [
        "",
        "## S-tier (must-act / core)",
        "",
        "| Name | Overall | Stage | Category |",
        "|------|--------:|-------|----------|",
    ]
    for t in sorted(by_tier.get("S", []), key=lambda x: -x.get("scores", {}).get("overall", 0)):
        sc = t.get("scores", {}).get("overall", "")
        lines.append(
            f"| {t['name']} | {sc} | {t.get('integration_stage', '')} | {t.get('primary_category', '')} |"
        )
    lines += [
        "",
        "## All tools (compact)",
        "",
        "| Name | Tier | Stage | Overall |",
        "|------|------|-------|--------:|",
    ]
    for t in sorted(tools, key=lambda x: (x.get("tier", "Z"), -x.get("scores", {}).get("overall", 0))):
        lines.append(
            f"| {t['name']} | {t.get('tier')} | {t.get('integration_stage')} | {t.get('scores', {}).get('overall', '')} |"
        )
    lines.append("")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
