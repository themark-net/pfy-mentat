#!/usr/bin/env python3
"""Local operator board. Independent poller — not a daemon, not a supervisor.

Serves the shared GUI at gui/operator/frontend/index.html.
POST /start spawns OpenCode worker or optional Grok monitor sidecar. local-only never auto-calls cloud.
POST /stage runs ./pfy stage (env-stage).
POST /env runs ./pfy env (inference + env-stage). No harness exec.
POST /models/pull runs ./pfy models pull <name>.
POST /eval runs a live-endpoint chat/completions probe against LOCAL_OPENAI_BASE_URL.
POST /tools toggles skills, MCP, write-guard, extra tools.
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
