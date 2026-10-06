#!/usr/bin/env bash
# Runtime matrix helper: llama.cpp ROCm or Vulkan. Reasoning off for Choice JSON.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
OUT="$ROOT/pipelines/dogfood/local-bench-5"
MODEL_BLOB=${1:?gguf}
LABEL=${2:?label}
BACKEND=${3:?rocm|vulkan}
PORT=${4:-18280}
CTX=${5:-4096}
mkdir -p "$OUT"
case "$BACKEND" in
  rocm|rocm-noreason)
    export HSA_OVERRIDE_GFX_VERSION=${HSA_OVERRIDE_GFX_VERSION:-11.5.1}
    export GGML_BACKEND_PATH=/usr/local/lib/ollama/rocm_v7_2/libggml-hip.so
    export LD_LIBRARY_PATH=/usr/local/lib/ollama/rocm_v7_2:/usr/local/lib/ollama:${LD_LIBRARY_PATH:-}
    export GGML_CUDA_ENABLE_UNIFIED_MEMORY=1 GGML_HIP_UMA=1
    BIN=/usr/local/lib/ollama/llama-server
    ;;
  vulkan)
    export GGML_BACKEND_PATH=/usr/local/lib/ollama/libggml-vulkan.so
    export LD_LIBRARY_PATH=/usr/local/lib/ollama:${LD_LIBRARY_PATH:-}
    BIN=/usr/local/lib/ollama/llama-server
    ;;
  *) echo "bad backend $BACKEND"; exit 2;;
esac
EXTRA=(--no-mmap -ngl 999 -c "$CTX" -np 1 -fa on -rea off --reasoning-budget 0 --no-webui)
LOG=/tmp/rt-${LABEL}-${BACKEND}.log
rm -f "$LOG" /tmp/rt-${LABEL}-${BACKEND}.stop
"$BIN" --model "$MODEL_BLOB" --host 127.0.0.1 --port "$PORT" "${EXTRA[@]}" >"$LOG" 2>&1 &
PID=$!
echo PID=$PID
python3 "$OUT/peak_sampler.py" "$PID" "$OUT/peak-${LABEL}-${BACKEND}.json" /tmp/rt-${LABEL}-${BACKEND}.stop &
SAMP=$!
T0=$(date +%s)
ok=0
for i in $(seq 1 120); do
  curl -sf --max-time 2 http://127.0.0.1:$PORT/health >/dev/null 2>&1 && { ok=1; break; }
  kill -0 $PID 2>/dev/null || { echo DIED; tail -40 "$LOG"; touch /tmp/rt-${LABEL}-${BACKEND}.stop; exit 1; }
  sleep 5
done
[ $ok -eq 1 ] || { echo TIMEOUT; touch /tmp/rt-${LABEL}-${BACKEND}.stop; kill $PID; exit 1; }
LOAD=$(($(date +%s)-T0))
python3 "$OUT/bench_llamacpp.py" --base "http://127.0.0.1:$PORT" --model-name "${LABEL}:${BACKEND}" --gate 0.85 --receipt "$OUT/receipt-${LABEL}-${BACKEND}.json"
touch /tmp/rt-${LABEL}-${BACKEND}.stop
kill $PID 2>/dev/null || true; sleep 2; kill -9 $PID 2>/dev/null || true
wait $SAMP 2>/dev/null || true
python3 - <<PY
import json,re
from pathlib import Path
OUT=Path("$OUT"); label="$LABEL"; be="$BACKEND"; load=$LOAD
rec=json.loads((OUT/f"receipt-{label}-{be}.json").read_text())
peak=json.loads((OUT/f"peak-{label}-{be}.json").read_text()) if (OUT/f"peak-{label}-{be}.json").exists() else {}
rec["peak"]=peak; rec["load_s"]=load; rec["backend"]=be; rec["flags"]="-rea off --reasoning-budget 0 --no-mmap -ngl 999"
t=Path(f"/tmp/rt-{label}-{be}.log").read_text(errors="ignore")
pp=[float(x) for x in re.findall(r"prompt eval time =.*?,\s*([0-9.]+) tokens per second\)", t)]
dec=[float(x) for x in re.findall(r" {4,}eval time =.*?,\s*([0-9.]+) tokens per second\)", t)]
xs=lambda a: ({"n":len(a),"p50":round(sorted(a)[len(a)//2],1)} if a else None)
rec["tok_s"]={"pp":xs(pp),"decode":xs(dec)}
(OUT/f"receipt-{label}-{be}.json").write_text(json.dumps(rec, indent=2))
print(json.dumps({"label":label,"backend":be,"load":load,"acc":(rec.get("decision") or {}).get("accuracy"),"parse_ok":(rec.get("decision") or {}).get("parse_ok"),"peak_rss":peak.get("rss_gib"),"tok":rec["tok_s"]}, indent=2))
PY
