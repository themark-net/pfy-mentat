#!/usr/bin/env bash
# Resumable 16-way ranged download of the community Q3_K_S GGUF (~33.9 GB) + sha256 verify.
# Not the official 78 GB FP8 weights. Lands in gitignored tmp/models.
set -uo pipefail
source "$(dirname "$0")/env.sh"
URL="https://huggingface.co/$KOLIBRI_HF_REPO/resolve/main/Kolibri-1-Q3_K_S.gguf"
SIZE=$KOLIBRI_GGUF_BYTES; N=16
mkdir -p "$KOLIBRI_MODEL_DIR/parts" && cd "$KOLIBRI_MODEL_DIR"
if [ "$(stat -c %s Kolibri-1-Q3_K_S.gguf 2>/dev/null || echo 0)" -ne "$SIZE" ]; then
  CH=$(( (SIZE + N - 1) / N ))
  for i in $(seq 0 $((N-1))); do
    S=$((i*CH)); E=$(( (i+1)*CH - 1 )); [ $E -ge $SIZE ] && E=$((SIZE-1))
    ( until [ "$(stat -c %s parts/p$i 2>/dev/null || echo 0)" -eq $((E-S+1)) ]; do
        have=$(stat -c %s parts/p$i 2>/dev/null || echo 0)
        curl -sL --retry 5 -r $((S+have))-$E "$URL" >> parts/p$i || sleep 2
      done ) &
  done
  wait
  cat $(for i in $(seq 0 $((N-1))); do echo parts/p$i; done) > Kolibri-1-Q3_K_S.gguf && rm -rf parts
fi
echo "$KOLIBRI_GGUF_SHA256  Kolibri-1-Q3_K_S.gguf" | sha256sum -c - || { echo "FAIL: sha256 mismatch"; exit 1; }
echo "DL_OK $KOLIBRI_GGUF"
