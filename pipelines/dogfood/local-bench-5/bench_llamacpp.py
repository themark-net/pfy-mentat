#!/usr/bin/env python3
"""Run #230 Choice cases against llama-server (OpenAI-compatible). Stdlib only."""
from __future__ import annotations
import argparse, json, time, urllib.request
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[3]
BENCH = ROOT / "examples" / "local-bench" / "bench.py"
CASES = ROOT / "data" / "decision-gates" / "laya-trial.cases.v0.json"

def load_bench():
    spec = importlib.util.spec_from_file_location("lb", BENCH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def http_json(url, body, timeout=120):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:18080")
    ap.add_argument("--model-name", required=True)
    ap.add_argument("--gate", type=float, default=0.85)
    ap.add_argument("--receipt", required=True)
    ap.add_argument("--max-cases", type=int, default=None)
    args = ap.parse_args()
    bench = load_bench()
    cases = json.loads(CASES.read_text())["cases"]
    if args.max_cases:
        cases = cases[:args.max_cases]

    # health
    t0 = time.time()
    while time.time() - t0 < 1800:
        try:
            urllib.request.urlopen(args.base + "/health", timeout=5)
            break
        except Exception:
            time.sleep(2)
    else:
        raise SystemExit("server never healthy")

    load_wall = round(time.time() - t0, 2)
    rows = []
    # warmup timing
    warm = http_json(args.base + "/v1/chat/completions", {
        "model": "local",
        "messages": [{"role":"user","content":"Reply with the single word: pong"}],
        "max_tokens": 8,
        "temperature": 0,
    }, timeout=600)
    # speed prompt
    filler = ("padding " * 80)
    t1 = time.perf_counter()
    speed = http_json(args.base + "/v1/chat/completions", {
        "model": "local",
        "messages": [{"role":"user","content": "Read padding then reply BENCH_OK only.\n\n"+filler}],
        "max_tokens": 16,
        "temperature": 0,
    }, timeout=600)
    speed_wall = round(time.perf_counter() - t1, 4)
    usage = speed.get("usage") or {}
    # llama.cpp often returns timings in incomplete; best-effort
    pp_tok = usage.get("prompt_tokens")
    out_tok = usage.get("completion_tokens")

    for i, case in enumerate(cases):
        prompt = bench.decision_prompt(case)
        keys = list((case.get("criteria") or {}).keys())
        t_c = time.perf_counter()
        try:
            gen = http_json(args.base + "/v1/chat/completions", {
                "model": "local",
                "messages": [{"role":"user","content": prompt}],
                "max_tokens": 96,
                "temperature": 0,
            }, timeout=180)
            text = (((gen.get("choices") or [{}])[0].get("message") or {}).get("content")) or ""
            parsed = bench.parse_choice_json(text, keys)
            row = bench.score_case(case, parsed, args.gate, round(time.perf_counter()-t_c,4))
        except Exception as e:
            parsed = {"parse_ok": False, "choice": None, "confidence": 0.0, "error": str(e), "raw": ""}
            row = bench.score_case(case, parsed, args.gate, round(time.perf_counter()-t_c,4), error=str(e))
        rows.append(row)
        print(f"  {args.model_name} {i+1}/{len(cases)} {row['id']} choice={row.get('choice')} label={row.get('label')} esc={row.get('escalate')}", flush=True)

    decision = bench.summarize_rows(rows, args.gate)
    # mem snapshot
    mem = {}
    for ln in open("/proc/meminfo"):
        if ":" in ln:
            k,v = ln.split(":",1)
            parts=v.split()
            if parts and parts[0].isdigit():
                mem[k]=int(parts[0])
    from pathlib import Path as P
    gtt=None
    for p in P("/sys/class/drm").glob("card*/device/mem_info_gtt_used"):
        gtt=round(int(p.read_text())/1024**3,3)
    rec = {
        "name": args.model_name,
        "backend": "llama-server-rocm-nommap",
        "flags": "--no-mmap -ngl 999 -c 4096 -np 1 -fa on GGML_HIP_UMA=1",
        "verdict": "RAN",
        "load_wait_s": load_wall,
        "speed_wall_s": speed_wall,
        "usage_speed": usage,
        "decision": decision,
        "mem_available_gb": round(mem.get("MemAvailable",0)/1024/1024,3),
        "swap_used_gb": round((mem.get("SwapTotal",0)-mem.get("SwapFree",0))/1024/1024,3),
        "gtt_used_gib": gtt,
        "n_cases": len(rows),
    }
    Path(args.receipt).write_text(json.dumps(rec, indent=2))
    print(json.dumps({"verdict":"RAN","accuracy":decision.get("accuracy"),"escalate_rate":decision.get("escalate_rate"),
                      "wrong_but_confident":decision.get("wrong_but_confident"),"parse_ok":decision.get("parse_ok"),
                      "receipt":args.receipt}))

if __name__ == "__main__":
    main()
