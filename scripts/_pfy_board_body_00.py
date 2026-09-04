#!/usr/bin/env python3
"""Local operator board. Independent poller — not a daemon, not a supervisor.

Serves the shared GUI at gui/operator/frontend/index.html.
POST /start spawns OpenCode worker or optional Grok monitor sidecar. local-only never auto-calls cloud.
POST /stage runs ./pfy stage (env-stage).
POST /env runs ./pfy env (inference + env-stage). No harness exec.
POST /models/pull runs ./pfy models pull <name>.
POST /eval runs a live-endpoint chat/completions probe against LOCAL_OPENAI_BASE_URL.
POST /tools toggles skills, MCP, write-guard, extra tools.
POST /space-invaders runs session Space Invaders via Attach OpenCode (#155).
"""
from __future__ import annotations
import json, os, shutil, socket, subprocess, sys, urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PFY = ROOT / "scripts" / "pfy"
DETECT = ROOT / "scripts" / "detect-local-runtime.sh"
REG = ROOT / "data" / "harnesses.json"
STATE = Path(os.environ.get("PFY_STATE_DIR", str(Path.home() / ".pfy-mentat")))
HOST = os.environ.get("PFY_BOARD_HOST", "127.0.0.1")
PORT = int(os.environ.get("PFY_BOARD_PORT", "8765"))
REFRESH_MS = int(os.environ.get("PFY_BOARD_REFRESH_MS", "2000"))
DETECT_ORDER = [
    ("freetoken", "FreeToken", ":1919"),
    ("llama-swap", "llama-swap", ":9292"),
    ("llama.cpp", "llama-server", ":8080"),
    ("ollama", "Ollama", ":11434"),
]
PS_MATCH = {
    "freetoken": ("ft", "freetoken"), "llama-swap": ("llama-swap",),
    "llama.cpp": ("llama-server",), "llama-server": ("llama-server",),
    "ollama": ("ollama",), "shimmy": ("shimmy",), "grok": ("grok",),
    "opencode": ("opencode", "opencode-cli"), "hermes": ("hermes", "hermes-agent"),
    "claude-code": ("claude",), "codex": ("codex",), "gemini": ("gemini", "gemini-cli"),
    "exo": ("exo.sh", "exo"),
}
STUB_ALWAYS = {"continue", "agent-cage"}
NO_SPAWN = {"llama-swap", "llama.cpp", "llama-server", "shimmy"}
SIDECAR_OK = {"grok", "opencode"}
ISSUE_BASE = "https://github.com/themark-net/pfy-mentat/issues/"
GROK_USE = "pfy harness use grok"
FRONTEND = ROOT / "gui" / "operator" / "frontend" / "index.html"
ORG_CANDIDATES = (
    STATE / "org-messages.jsonl", STATE / "org-messages.json",
    ROOT / "data" / "org-messages.jsonl", ROOT / "data" / "org-messages.json",
    ROOT / ".pfy" / "org-messages.jsonl", ROOT / ".pfy" / "org-messages.json",
)
ENGINE_ALIAS = {"ft": "freetoken", "llama-server": "llama.cpp", "freetoken": "freetoken"}
ALLOWED_LIVE = frozenset({"ready", "partial", "stub", "detected-stub", "missing", "skip"})

def honest_live(value):
    v = str(value or "").strip().lower()
    if v in ALLOWED_LIVE:
        return v
    return "missing"

def _run(argv, timeout=20.0):
    try:
        p = subprocess.run(argv, cwd=str(ROOT), capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, str(e)
    return p.returncode, (p.stdout or "") + (("\n" + p.stderr) if p.stderr else "")

def load_registry():
    if not REG.is_file():
        return {"harnesses": [], "default_harness": "grok"}
    return json.loads(REG.read_text(encoding="utf-8"))

def detector_json():
    if not DETECT.is_file():
        return {"engine": "none", "status": "missing", "base_url": ""}
    _rc, out = _run(["bash", str(DETECT), "--json"], timeout=8.0)
    for raw in out.splitlines():
        s = raw.strip()
        if s.startswith("{") and s.endswith("}"):
            try:
                d = json.loads(s)
            except json.JSONDecodeError:
                break
            if isinstance(d, dict):
                return {"engine": d.get("engine") or "none", "status": d.get("status") or "missing", "base_url": d.get("base_url") or ""}
    return {"engine": "none", "status": "missing", "base_url": ""}

def pfy_status_stdout():
    rc, out = _run(["bash", str(PFY), "status"], timeout=25