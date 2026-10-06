#!/usr/bin/env python3
"""Append one JSON edge-probe event. Stdlib only."""
from __future__ import annotations
import json, os, time, subprocess
from pathlib import Path
from datetime import datetime, timezone

OUT = Path(__file__).resolve().parent / "edge-events.jsonl"

def mem():
    d = {}
    for ln in open("/proc/meminfo"):
        if ":" in ln:
            k, v = ln.split(":", 1)
            parts = v.split()
            if parts and parts[0].isdigit():
                d[k] = int(parts[0])  # kB
    return {
        "mem_total_gb": round(d.get("MemTotal", 0) / 1024 / 1024, 3),
        "mem_available_gb": round(d.get("MemAvailable", 0) / 1024 / 1024, 3),
        "mem_free_gb": round(d.get("MemFree", 0) / 1024 / 1024, 3),
        "swap_total_gb": round(d.get("SwapTotal", 0) / 1024 / 1024, 3),
        "swap_free_gb": round(d.get("SwapFree", 0) / 1024 / 1024, 3),
        "swap_used_gb": round((d.get("SwapTotal", 0) - d.get("SwapFree", 0)) / 1024 / 1024, 3),
    }

def gtt():
    from pathlib import Path
    out = {}
    for p in Path("/sys/class/drm").glob("card*/device/mem_info_gtt_used"):
        out["gtt_used_gib"] = round(int(p.read_text()) / 1024**3, 3)
    for p in Path("/sys/class/drm").glob("card*/device/mem_info_gtt_total"):
        out["gtt_total_gib"] = round(int(p.read_text()) / 1024**3, 3)
    for p in Path("/sys/class/drm").glob("card*/device/mem_info_vram_used"):
        out["vram_used_gib"] = round(int(p.read_text()) / 1024**3, 3)
    return out

def heavy_procs(limit=12):
    rows = []
    try:
        out = subprocess.check_output(
            ["ps", "-eo", "pid,user,rss,etime,comm,args", "--sort=-rss"],
            text=True, timeout=10,
        )
        for ln in out.splitlines()[1:limit+1]:
            rows.append(ln.strip()[:240])
    except Exception as e:
        rows.append("err:"+str(e))
    return rows

def ollama_ps():
    try:
        import urllib.request
        return json.load(urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=5))
    except Exception as e:
        return {"error": str(e)}


def runner_rss():
    """Peak-ish snapshot of llama-server RSS via harness (works cross-user)."""
    import importlib.util
    root = Path(__file__).resolve().parents[3]
    bench_py = root / "examples" / "local-bench" / "bench.py"
    spec = importlib.util.spec_from_file_location("local_bench_edge", bench_py)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    rows = mod.ollama_runner_stats()
    out = []
    for r in rows:
        rss = r.get("rss_kb") or 0
        out.append({
            "pid": r.get("pid"),
            "name": r.get("name"),
            "is_runner": r.get("is_runner"),
            "rss_kb": rss,
            "rss_gib": round(rss / 1024 / 1024, 3) if rss else 0,
            "exe": (r.get("exe") or "")[:120],
        })
    return out

def emit(event: dict):
    event = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "host": "nimo",
        **event,
        "mem": mem(),
        "gpu": gtt(),
        "ollama_ps": ollama_ps(),
        "heavy_procs_top": heavy_procs(),
        "runner_rss": runner_rss(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    print(json.dumps({"logged": event.get("phase"), "mem_available_gb": event["mem"]["mem_available_gb"]}, ensure_ascii=False))

if __name__ == "__main__":
    import sys
    phase = sys.argv[1] if len(sys.argv) > 1 else "snapshot"
    model = sys.argv[2] if len(sys.argv) > 2 else None
    extra = {}
    if len(sys.argv) > 3:
        extra = json.loads(sys.argv[3])
    emit({"phase": phase, "model": model, **extra})
