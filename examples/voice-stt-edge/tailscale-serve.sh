#!/usr/bin/env bash
# Front voice-remote with Tailscale HTTPS (port 443) so Brave can use the mic.
# Python stays plain HTTP on :8787 — never open https://…:8787
set -euo pipefail

PORT="${VOICE_REMOTE_PORT:-8787}"
BG="${VOICE_SERVE_BG:-1}"

if ! command -v tailscale >/dev/null 2>&1; then
  echo "error: tailscale CLI not found" >&2
  exit 2
fi

if ! tailscale status >/dev/null 2>&1; then
  echo "error: tailscale not connected (tailscale up)" >&2
  exit 2
fi

echo "== check backend HTTP on 127.0.0.1:${PORT} =="
if ! curl -sS -m 2 "http://127.0.0.1:${PORT}/ping" | grep -q pong; then
  echo "error: voice-remote not answering on http://127.0.0.1:${PORT}/ping" >&2
  echo "  start first:  VOICE_REMOTE_HOST=127.0.0.1 make voice-remote" >&2
  echo "  (use 127.0.0.1 when Serve is the only phone front door)" >&2
  exit 1
fi
echo "  backend: pong"

echo "== tailscale serve https:// → http://127.0.0.1:${PORT} =="
# Reset prior serve config for a clean map (optional; comment out to keep other serves)
if [[ "${VOICE_SERVE_RESET:-0}" == "1" ]]; then
  tailscale serve reset || true
fi

ARGS=(serve --https=443 "http://127.0.0.1:${PORT}")
if [[ "$BG" == "1" ]]; then
  ARGS=(serve --bg --https=443 "http://127.0.0.1:${PORT}")
fi
tailscale "${ARGS[@]}"

echo ""
echo "== status =="
tailscale serve status || true

# Best-effort MagicDNS / DNS name
DNS="$(tailscale status --json 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("Self",{}).get("DNSName","") or "")' 2>/dev/null || true)"
DNS="${DNS%.}"  # strip trailing dot

echo ""
echo "== phone: use ONE of these (HTTPS, NO :${PORT}) =="
if [[ -n "$DNS" ]]; then
  echo "  https://${DNS}/"
  echo "  https://${DNS}/ping"
fi
TS_IP="$(tailscale ip -4 2>/dev/null | head -1 || true)"
# MagicDNS preferred; IP with https may work via Serve on 443
if [[ -n "$TS_IP" ]]; then
  echo "  (or https via Serve on 443 — prefer MagicDNS name above)"
fi
echo ""
echo "== do NOT open =="
echo "  https://anything:${PORT}/     ← SSL protocol error (TLS to Python)"
echo "  http://100.x:${PORT}/         ← page may load, then Brave upgrades to HTTPS and breaks"
echo ""
echo "Brave: Settings → Privacy → disable 'Always use secure connections' if it still upgrades."
echo "After STT on host: examples/voice-stt-edge/.generated/handoff.sh"
