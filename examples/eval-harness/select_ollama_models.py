#!/usr/bin/env python3
"""Pick Ollama coding models that *fit* this machine (not only already-pulled).

- Discovers what is already on Ollama (tags API, proxy-bypassed)
- Estimates RAM from on-disk size or catalog defaults
- May recommend pulls for better gates *if* they fit disk+RAM
- Prefers a strong **already-pulled** coder when good enough

Usage:
  python3 select_ollama_models.py
  python3 select_ollama_models.py --exports
  python3 select_ollama_models.py --json
  python3 select_ollama_models.py --pull-gate

Env:
  OLLAMA_HOST / OPENAI_BASE_URL  default http://127.0.0.1:11434
  EVAL_RAM_BUDGET_GB             default available*0.55
  EVAL_DISK_BUDGET_GB            default free*0.4 (min 5)
  EVAL_ALLOW_PULL=0              only already-present fitters
  EVAL_MIN_GATE_QUALITY=4        prefer pull only if best pulled quality < this
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# Curated tags we may pull if they fit and beat local inventory.
MODEL_CATALOG: list[dict[str, Any]] = [
    {"name": "deepseek-coder:latest", "role": "smoke", "download_gb": 0.8, "ram_gb": 2.0, "quality": 1},
    {"name": "deepseek-coder:6.7b-instruct", "role": "matrix", "download_gb": 3.8, "ram_gb": 7.0, "quality": 3},
    {"name": "qwen2.5-coder:7b-instruct", "role": "matrix", "download_gb": 4.7, "ram_gb": 8.0, "quality": 4},
    {"name": "qwen2.5:14b", "role": "gate", "download_gb": 9.0, "ram_gb": 14.0, "quality": 5},
    {"name": "qwen2.5-coder:14b-instruct", "role": "gate", "download_gb": 9.0, "ram_gb": 14.0, "quality": 6},
    {"name": "codestral:22b", "role": "matrix", "download_gb": 12.5, "ram_gb": 20.0, "quality": 7},
]

# Name patterns → coding suitability (higher = better eval gate). Prefer *coder* names.
NAME_QUALITY: list[tuple[re.Pattern[str], int]] = [
    (re.compile(r"codestral|devstral|qwen3-coder|coder-next|starcoder2?:?(1[4-9]|2[0-9])", re.I), 7),
    (re.compile(r"qwen2\.5-coder:1[4-9]|deepseek-coder:(6|7|33)|codellama:1[3-9]|coder:1[4-9]", re.I), 6),
    (re.compile(r"qwen2\.5-coder|qwen2\.5:1[4-9]|deepseek-coder|codellama|starcoder", re.I), 5),
    (re.compile(r"(^|/)(coder|code)|instruct.*code|code.*instruct", re.I), 4),
    # General chat — usable matrix fillers only if nothing better
    (re.compile(r"qwen|llama3|mistral|gemma|granite|phi", re.I), 2),
    (re.compile(r"deepseek-coder:latest|tiny|1b|0\.5b|cloud", re.I), 1),
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
    if not p.is_file():
        return total, avail
    data: dict[str, str] = {}
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
    return shutil.disk_usage(path).free / (1024**3)


def ollama_base() -> str:
    base = (
        os.environ.get("OLLAMA_HOST")
        or os.environ.get("OPENAI_BASE_URL")
        or "http://127.0.0.1:11434"
    )
    base = base.rstrip("/")
    if base.endswith("/v1"):
        base = base[: -len("/v1")]
    return base


def _urlopen(url: str, timeout: float = 10):
    """Open URL bypassing HTTP(S)_PROXY (cage mitm returns 403 to urllib)."""
    # Prefer no proxy for loopback / docker host / private nets
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req = urllib.request.Request(url, headers={"User-Agent": "pfy-eval-select/1.0"})
    return opener.open(req, timeout=timeout)


def list_pulled(base: str) -> list[dict[str, Any]]:
    url = f"{base}/api/tags"
    try:
        with _urlopen(url) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
        print(f"warn: cannot list Ollama tags at {url}: {e}", file=sys.stderr)
        return []
    out = []
    for m in data.get("models") or []:
        name = m.get("name")
        if not name:
            continue
        size_b = float(m.get("size") or 0)
        size_gb = size_b / (1024**3) if size_b else 0.0
        out.append({"name": name, "size_gb": size_gb, "raw": m})
    return out


def quality_for_name(name: str) -> int:
    for pat, q in NAME_QUALITY:
        if pat.search(name):
            return q
    return 2


def ram_for_size_gb(size_gb: float) -> float:
    # Runtime headroom ~1.4–1.6× weights for Ollama GGUF
    if size_gb <= 0:
        return 4.0
    return max(2.0, size_gb * 1.5)


def budget() -> HostBudget:
    total, avail = meminfo()
    ram_budget = float(os.environ.get("EVAL_RAM_BUDGET_GB") or max(2.0, avail * 0.55))
    disk_free = disk_free_gb(os.environ.get("EVAL_DISK_PATH", "/"))
    disk_budget = float(os.environ.get("EVAL_DISK_BUDGET_GB") or max(5.0, disk_free * 0.4))
    return HostBudget(total, avail, ram_budget, disk_free, disk_budget)


def fits(ram_gb: float, download_gb: float, b: HostBudget, *, need_download: bool) -> bool:
    if ram_gb > b.ram_budget_gb:
        return False
    if need_download and download_gb > b.disk_budget_gb:
        return False
    return True


def catalog_entry(name: str) -> dict[str, Any] | None:
    for m in MODEL_CATALOG:
        if m["name"] == name:
            return m
    return None


def build_candidates(pulled: list[dict[str, Any]], b: HostBudget, allow_pull: bool) -> list[dict[str, Any]]:
    cands: list[dict[str, Any]] = []
    pulled_names = {p["name"] for p in pulled}

    for p in pulled:
        name = p["name"]
        cat = catalog_entry(name)
        size_gb = p["size_gb"] or (cat["download_gb"] if cat else 4.0)
        ram_gb = cat["ram_gb"] if cat else ram_for_size_gb(size_gb)
        q = cat["quality"] if cat else quality_for_name(name)
        role = cat["role"] if cat else ("smoke" if q <= 1 else "matrix")
        if not fits(ram_gb, 0.0, b, need_download=False):
            continue
        cands.append(
            {
                "name": name,
                "role": role,
                "download_gb": size_gb,
                "ram_gb": ram_gb,
                "quality": q,
                "pulled": True,
                "need_download": False,
            }
        )

    if allow_pull:
        for m in MODEL_CATALOG:
            if m["name"] in pulled_names:
                continue
            if not fits(m["ram_gb"], m["download_gb"], b, need_download=True):
                continue
            cands.append({**m, "pulled": False, "need_download": True})

    return cands


def select(pulled: list[dict[str, Any]], b: HostBudget, allow_pull: bool) -> dict[str, Any]:
    min_gate_q = int(os.environ.get("EVAL_MIN_GATE_QUALITY", "4"))
    cands = build_candidates(pulled, b, allow_pull)
    if not cands:
        return {
            "gate": None,
            "models": [],
            "reason": "no model fits RAM/disk (pulled or catalog)",
            "budget": asdict(b),
            "pulled_count": len(pulled),
            "pulled_names": [p["name"] for p in pulled[:30]],
        }

    def sort_key(x: dict[str, Any]) -> tuple:
        # Prefer coding-ish names, then quality, then already pulled
        coding = 1 if re.search(r"coder|codestral|devstral|starcoder|codellama", x["name"], re.I) else 0
        return (coding, x["quality"], x["pulled"], -x["ram_gb"])

    cands.sort(key=sort_key, reverse=True)

    pulled_fit = [c for c in cands if c["pulled"]]
    coding_pulled = [c for c in pulled_fit if re.search(r"coder|codestral|devstral|starcoder|codellama", c["name"], re.I)]
    best_pulled = max(coding_pulled or pulled_fit, key=lambda c: c["quality"]) if pulled_fit else None
    best_any = cands[0]

    # Prefer already-pulled coder if quality is enough; pull only for clear upgrade
    if best_pulled and best_pulled["quality"] >= min_gate_q:
        if (not best_any["pulled"]) and best_any["quality"] >= best_pulled["quality"] + 2:
            gate = best_any
        else:
            gate = best_pulled
    else:
        gate = best_any

    matrix = [gate["name"]]
    # Prefer coding models in matrix; allow general models as last resort
    ordered = sorted(cands, key=sort_key, reverse=True)
    for c in ordered:
        if c["name"] in matrix:
            continue
        if c.get("role") == "smoke" or c["quality"] <= 1:
            continue
        if c["quality"] < 3 and any(x["quality"] >= 3 and x["name"] not in matrix for x in cands):
            continue
        matrix.append(c["name"])
        if len(matrix) >= 3:
            break

    smoke = next((c["name"] for c in cands if c.get("role") == "smoke"), "deepseek-coder:latest")
    if not any(c["name"] == smoke for c in cands):
        # any tiny pulled
        tiny = [c for c in pulled_fit if c["quality"] <= 2]
        smoke = tiny[0]["name"] if tiny else smoke

    return {
        "gate": gate["name"],
        "models": matrix,
        "matrix": matrix,
        "gate_meta": gate,
        "fitters": cands,
        "budget": asdict(b),
        "pulled_count": len(pulled),
        "pulled_names": [p["name"] for p in pulled],
        "ollama_base": ollama_base(),
        "allow_pull": allow_pull,
        "smoke": smoke,
        "min_gate_quality": min_gate_q,
    }


def pull_model(name: str) -> int:
    print(f"==> ollama pull {name}", flush=True)
    if not shutil.which("ollama"):
        print("error: ollama CLI not on PATH — pull on host: ollama pull " + name, file=sys.stderr)
        return 1
    return subprocess.call(["ollama", "pull", name])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exports", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--pull-gate", action="store_true")
    ap.add_argument("--no-pull", action="store_true")
    args = ap.parse_args()

    allow_pull = not args.no_pull and os.environ.get("EVAL_ALLOW_PULL", "1") != "0"
    b = budget()
    base = ollama_base()
    pulled = list_pulled(base)
    sel = select(pulled, b, allow_pull=allow_pull)

    if args.json:
        # trim raw
        print(json.dumps({k: v for k, v in sel.items() if k != "fitters" or True}, indent=2, default=str)[:20000])
        return 0 if sel.get("gate") else 2

    print("=== Ollama model fit selection ===")
    print(
        f"  RAM total={b.mem_total_gb:.1f}Gi available={b.mem_available_gb:.1f}Gi "
        f"budget={b.ram_budget_gb:.1f}Gi"
    )
    print(f"  disk free={b.disk_free_gb:.0f}Gi budget={b.disk_budget_gb:.0f}Gi")
    print(f"  ollama={base} pulled={sel.get('pulled_count', 0)} allow_pull={allow_pull}")
    if pulled:
        sample = ", ".join(p["name"] for p in pulled[:6])
        print(f"  inventory sample: {sample}{'…' if len(pulled) > 6 else ''}")

    if not sel.get("gate"):
        print(f"  FAIL: {sel.get('reason')}")
        return 2

    gm = sel["gate_meta"]
    print(
        f"  GATE: {sel['gate']}  (quality={gm['quality']} ram~{gm['ram_gb']:.1f}G "
        f"dl~{gm['download_gb']:.1f}G pulled={gm['pulled']})"
    )
    print(f"  MATRIX: {', '.join(sel['models'])}")
    print(f"  SMOKE: {sel.get('smoke')}")
    need = [c["name"] for c in sel.get("fitters", []) if c.get("need_download") and c["name"] in sel["models"]]
    if need:
        print(f"  TO PULL: {', '.join(need)}")
    elif not gm["pulled"]:
        print(f"  TO PULL: {sel['gate']}")
    else:
        print("  TO PULL: (none — using inventory)")

    if args.pull_gate and not gm["pulled"]:
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
        print(f"LITELLM_SMOKE_MODEL={sel.get('smoke', 'deepseek-coder:latest')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
