#!/usr/bin/env python3
"""Pick Ollama coding models that *fit* this machine (not only already-pulled).

Estimates download size + runtime RAM; ranks candidates for eval gate + matrix.

Usage:
  python3 select_ollama_models.py              # human report
  python3 select_ollama_models.py --exports    # EVAL_MODEL=... EVAL_MODELS=...
  python3 select_ollama_models.py --json
  python3 select_ollama_models.py --pull-gate  # ollama pull gate if missing

Env:
  OLLAMA_HOST / OPENAI_BASE_URL  — tags endpoint (default http://127.0.0.1:11434)
  EVAL_RAM_BUDGET_GB             — override usable RAM for models (default: available*0.55)
  EVAL_DISK_BUDGET_GB            — override free disk for pulls (default: free*0.4, min 5)
  EVAL_ALLOW_PULL=0              — never suggest pull (only already-present fitters)
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

# Curated coding-oriented Ollama tags. Sizes are approximate GGUF download / peak RAM.
# Prefer smaller coders when RAM is tight; escalate when headroom exists.
MODEL_CATALOG: list[dict] = [
    {
        "name": "deepseek-coder:latest",
        "role": "smoke",
        "download_gb": 0.8,
        "ram_gb": 2.0,
        "quality": 1,
        "notes": "tiny connectivity / weak for suite gate",
    },
    {
        "name": "deepseek-coder:6.7b-instruct",
        "role": "matrix",
        "download_gb": 3.8,
        "ram_gb": 7.0,
        "quality": 3,
        "notes": "solid small coder",
    },
    {
        "name": "qwen2.5-coder:7b-instruct",
        "role": "matrix",
        "download_gb": 4.7,
        "ram_gb": 8.0,
        "quality": 4,
        "notes": "good 7B coder",
    },
    {
        "name": "qwen2.5:14b",
        "role": "gate",
        "download_gb": 9.0,
        "ram_gb": 14.0,
        "quality": 5,
        "notes": "default historical EVAL_MODEL gate",
    },
    {
        "name": "qwen2.5-coder:14b-instruct",
        "role": "gate",
        "download_gb": 9.0,
        "ram_gb": 14.0,
        "quality": 6,
        "notes": "strong coder 14B",
    },
    {
        "name": "codestral:22b",
        "role": "matrix",
        "download_gb": 12.5,
        "ram_gb": 20.0,
        "quality": 7,
        "notes": "large; needs ~20GB RAM headroom",
    },
]


@dataclass
class HostBudget:
    mem_total_gb: float
    mem_available_gb: float
    ram_budget_gb: float
    disk_free_gb: float
    disk_budget_gb: float


def meminfo() -> tuple[float, float]:
    total = avail = 0.0
    p = Path("/proc/meminfo")
    if p.is_file():
        data = {}
        for line in p.read_text().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                data[k.strip()] = v.strip()
        def kb(key: str) -> float:
            raw = data.get(key, "0").split()[0]
            return float(raw) / (1024 * 1024)

        total = kb("MemTotal")
        avail = kb("MemAvailable") if "MemAvailable" in data else kb("MemFree")
    return total, avail


def disk_free_gb(path: str = "/") -> float:
    u = shutil.disk_usage(path)
    return u.free / (1024**3)


def ollama_base() -> str:
    base = os.environ.get("OLLAMA_HOST") or os.environ.get("OPENAI_BASE_URL") or "http://127.0.0.1:11434"
    base = base.rstrip("/")
    if base.endswith("/v1"):
        base = base[: -len("/v1")]
    return base


def pulled_names(base: str) -> set[str] | None:
    url = f"{base}/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=8) as resp:  # noqa: S310
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return None
    return {m.get("name") for m in (data.get("models") or []) if m.get("name")}


def budget() -> HostBudget:
    total, avail = meminfo()
    ram_budget = float(os.environ.get("EVAL_RAM_BUDGET_GB") or max(2.0, avail * 0.55))
    disk_free = disk_free_gb(os.environ.get("EVAL_DISK_PATH", "/"))
    disk_budget = float(os.environ.get("EVAL_DISK_BUDGET_GB") or max(5.0, disk_free * 0.4))
    return HostBudget(total, avail, ram_budget, disk_free, disk_budget)


def fits(m: dict, b: HostBudget, *, need_download: bool) -> bool:
    if m["ram_gb"] > b.ram_budget_gb:
        return False
    if need_download and m["download_gb"] > b.disk_budget_gb:
        return False
    return True


def select(pulled: set[str] | None, b: HostBudget, allow_pull: bool) -> dict:
    present = pulled or set()
    candidates = []
    for m in MODEL_CATALOG:
        is_pulled = m["name"] in present
        need_dl = not is_pulled
        if need_dl and not allow_pull:
            continue
        if not fits(m, b, need_download=need_dl):
            continue
        candidates.append({**m, "pulled": is_pulled, "need_download": need_dl})

    # Prefer higher quality among fitters; for gate prefer role=gate or highest quality
    candidates.sort(key=lambda x: (x["quality"], x["pulled"]), reverse=True)
    if not candidates:
        return {
            "gate": None,
            "models": [],
            "matrix": [],
            "reason": "no catalog model fits RAM/disk budget",
            "budget": asdict(b),
            "pulled_count": len(present),
        }

    # Gate: best quality that fits; prefer already pulled if quality within 1 of best
    best = candidates[0]
    pulled_near = [c for c in candidates if c["pulled"] and c["quality"] >= best["quality"] - 1]
    gate = max(pulled_near, key=lambda c: c["quality"]) if pulled_near else best

    # Matrix: gate + up to 2 smaller coders (skip smoke-only unless nothing else)
    matrix = [gate["name"]]
    for c in sorted(candidates, key=lambda x: x["quality"]):
        if c["name"] in matrix:
            continue
        if c.get("role") == "smoke" and any(
            x.get("role") != "smoke" and x["name"] not in matrix for x in candidates
        ):
            continue
        if c["quality"] < gate["quality"]:
            matrix.append(c["name"])
        if len(matrix) >= 3:
            break

    return {
        "gate": gate["name"],
        "models": matrix,
        "matrix": matrix,
        "gate_meta": gate,
        "fitters": candidates,
        "budget": asdict(b),
        "pulled_count": len(present),
        "ollama_base": ollama_base(),
        "allow_pull": allow_pull,
    }


def pull_model(name: str) -> int:
    print(f"==> ollama pull {name}", flush=True)
    return subprocess.call(["ollama", "pull", name])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exports", action="store_true", help="print EVAL_MODEL=… shell lines")
    ap.add_argument("--json", action="store_true", help="JSON report")
    ap.add_argument("--pull-gate", action="store_true", help="ollama pull gate model if missing")
    ap.add_argument(
        "--no-pull",
        action="store_true",
        help="only consider already-pulled models that fit",
    )
    args = ap.parse_args()
    allow_pull = not args.no_pull and os.environ.get("EVAL_ALLOW_PULL", "1") != "0"
    b = budget()
    base = ollama_base()
    pulled = pulled_names(base)
    sel = select(pulled, b, allow_pull=allow_pull)

    if args.json:
        print(json.dumps(sel, indent=2, default=str))
        return 0 if sel.get("gate") else 2

    print("=== Ollama model fit selection ===")
    print(
        f"  RAM total={b.mem_total_gb:.1f}Gi available={b.mem_available_gb:.1f}Gi "
        f"budget={b.ram_budget_gb:.1f}Gi"
    )
    print(f"  disk free={b.disk_free_gb:.0f}Gi budget={b.disk_budget_gb:.0f}Gi")
    print(f"  ollama={base} pulled={sel.get('pulled_count', '?')} allow_pull={allow_pull}")
    if not sel.get("gate"):
        print(f"  FAIL: {sel.get('reason')}")
        return 2
    print(f"  GATE: {sel['gate']}  (quality={sel['gate_meta']['quality']} "
          f"ram~{sel['gate_meta']['ram_gb']}G dl~{sel['gate_meta']['download_gb']}G "
          f"pulled={sel['gate_meta']['pulled']})")
    print(f"  MATRIX: {', '.join(sel['models'])}")
    need = [c["name"] for c in sel.get("fitters", []) if c.get("need_download") and c["name"] in sel["models"]]
    if need:
        print(f"  TO PULL: {', '.join(need)}")

    if args.pull_gate and not sel["gate_meta"]["pulled"]:
        if not allow_pull:
            print("error: --pull-gate but pulls disabled", file=sys.stderr)
            return 1
        rc = pull_model(sel["gate"])
        if rc != 0:
            return rc

    if args.exports:
        print(f"EVAL_MODEL={sel['gate']}")
        print(f"EVAL_GATE_MODEL={sel['gate']}")
        print(f"EVAL_MODELS={','.join(sel['models'])}")
        print(f"LITELLM_SMOKE_MODEL={next((c['name'] for c in MODEL_CATALOG if c['role']=='smoke'), 'deepseek-coder:latest')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
