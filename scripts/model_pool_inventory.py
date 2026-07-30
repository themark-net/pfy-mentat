#!/usr/bin/env python3
"""GAP-16: soft model pool inventory (250GB policy). Never hard-fails unless --strict."""
from __future__ import annotations
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAX = 250.0
OUT = ROOT / "pipelines" / "eval" / "model-pool.latest.md"


def du_gb(path: Path) -> float:
    if not path.exists():
        return 0.0
    try:
        p = subprocess.run(["du", "-sb", str(path)], capture_output=True, text=True, check=False)
        if p.returncode != 0:
            return 0.0
        return int(p.stdout.split()[0]) / (1024**3)
    except Exception:
        return 0.0


def ollama_list() -> list[str]:
    try:
        p = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        if p.returncode != 0:
            return []
        return [ln for ln in p.stdout.splitlines()[1:] if ln.strip()]
    except Exception:
        return []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-gb", type=float, default=float(os.environ.get("MODEL_POOL_MAX_GB", DEFAULT_MAX)))
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    roots = [
        Path(os.environ.get("OLLAMA_MODELS", str(Path.home() / ".ollama" / "models"))),
        Path(os.environ.get("PFY_MODEL_POOL", str(Path.home() / "pfy-models"))),
    ]
    rows = []
    total = 0.0
    for r in roots:
        g = du_gb(r)
        total += g
        rows.append((str(r), g, r.exists()))
    models = ollama_list()
    lines = [
        "# Model pool inventory",
        "",
        f"max_gb: {args.max_gb}",
        f"total_gb_approx: {total:.2f}",
        f"status: {'OVER' if total > args.max_gb else 'ok'}",
        "",
        "| Path | GB | exists |",
        "|------|---:|--------|",
    ]
    for path, g, ex in rows:
        lines.append(f"| `{path}` | {g:.2f} | {ex} |")
    lines += ["", f"ollama list lines: {len(models)}", ""]
    for m in models[:40]:
        lines.append(f"- {m}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT} total_gb={total:.2f} max={args.max_gb}")
    if args.strict and total > args.max_gb:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
