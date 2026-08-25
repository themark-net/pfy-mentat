#!/usr/bin/env python3
"""Local operator board. Independent poller — not a daemon, not a supervisor."""
from __future__ import annotations
import json, os, socket, subprocess, sys, urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
PFY = ROOT / "scripts" / "pfy"
DETECT = ROOT / "scripts" / "detect-local-runtime.sh"
REG = ROOT / "data" / "harnesses.json"
STATE = Path(os.environ.get("PFY_STATE_DIR", str(Path.home() / ".pfy-mentat")))
HOST = os.environ.get("PFY_BOARD_HOST", "127.0.0.1")
PORT = int(os.environ.get("PFY_BOARD_PORT", "3847"))
REFRESH_MS = int(os.environ.get("PFY_BOARD_REFRESH_MS", "4000"))
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
ISSUE_BASE = "https://github.com/themark-net/pfy-mentat/issues/"
GROK_USE = "pfy harness use grok"
ORG_CANDIDATES = (
    STATE / "org-messages.jsonl", STATE / "org-messages.json",
    ROOT / "data" / "org-messages.jsonl", ROOT / "data" / "org-messages.json",
    ROOT / ".pfy" / "org-messages.jsonl", ROOT / ".pfy" / "org-messages.json",
)

def _run(argv: list[str], timeout: float = 20.0) -> tuple[int, str]:
    try:
        p = subprocess.run(argv, cwd=str(ROOT), capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, str(e)
    return p.returncode, (p.stdout or "") + (("\n" + p.stderr) if p.stderr else "")

def load_registry() -> dict[str, Any]:
    if not REG.is_file():
        return {"harnesses": [], "default_harness": "grok"}
    return json.loads(REG.read_text(encoding="utf-8"))

def detector_json() -> dict[str, Any]:
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

def pfy_status_stdout() -> str:
    rc, out = _run(["bash", str(PFY), "status"], timeout=25.0)
    return out if out.strip() else f"(pfy status empty, exit {rc})"

def parse_status(text: str) -> dict[str, Any]:
    active, usage, chips = "", [], []
    runtime = {"engine": "", "status": "", "base_url": ""}
    in_usage = in_table = False
    for line in text.splitlines():
        if line.startswith("active harness:"):
            active = line.split(":", 1)[1].strip(); in_usage = False; continue
        if line.startswith("local runtime:"):
            for part in line.split(":", 1)[1].split():
                if "=" in part:
                    k, v = part.split("=", 1); runtime[k] = v
            in_usage = False; continue
        if line.startswith("usage:"):
            in_usage = True; in_table = False; continue
        stripped = line.strip()
        if stripped.startswith("ID") and "STATUS" in line:
            in_table = True; in_usage = False; continue
        if in_table:
            if stripped.startswith("----") or stripped.startswith("next:") or stripped.startswith("override:"):
                if stripped.startswith("next:") or stripped.startswith("override:"):
                    in_table = False
                continue
            if not stripped:
                in_table = False; continue
            parts = stripped.split(None, 3)
            if len(parts) >= 3:
                chips.append({"id": parts[0], "live": parts[1], "role": parts[2], "name": parts[3] if len(parts) > 3 else ""})
            continue
        if in_usage:
            if not stripped:
                in_usage = False; continue
            usage.append(line.rstrip())
    return {"active": active, "runtime": runtime, "usage": usage, "chips": chips}

def process_table() -> list[dict[str, str]]:
    rc, out = _run(["ps", "-eo", "pid,args"], timeout=5.0)
    if rc != 0:
        rc, out = _run(["ps", "ax", "-o", "pid,args"], timeout=5.0)
    rows = []
    for line in out.splitlines()[1:]:
        s = line.strip()
        if not s:
            continue
        pid, _, args = s.partition(" ")
        low = args.lower()
        if "pfy-board.py" in low:
            continue
        hit = ""
        for hid, needles in PS_MATCH.items():
            for n in needles:
                tok = n.lower()
                if tok in low.split() or f"/{tok}" in low or low.endswith(tok):
                    hit = hid; break
            if hit:
                break
        if hit:
            rows.append({"pid": pid, "id": hit, "args": args.strip()[:180]})
    return rows

def last_verb() -> dict[str, str]:
    p = STATE / "last-verb"
    if not p.is_file():
        return {"verb": "(none)", "when": ""}
    verb, when = "(none)", ""
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("verb:"):
            verb = line.split(":", 1)[1].strip() or "(none)"
        elif line.startswith("when:"):
            when = line.split(":", 1)[1].strip()
    return {"verb": verb, "when": when}

def active_harness(default: str) -> str:
    p = STATE / "active-harness"
    if p.is_file():
        v = p.read_text(encoding="utf-8", errors="replace").strip()
        if v:
            return v
    return default

def deploy_profile() -> str:
    envp = ROOT / ".env"
    if envp.is_file():
        for line in envp.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.strip().startswith("DEPLOY_PROFILE="):
                return line.split("=", 1)[1].strip().strip("'\"")
    return os.environ.get("DEPLOY_PROFILE", "")

def inspect_models(base_url: str) -> list[str]:
    if not base_url:
        return []
    base = base_url.rstrip("/")
    ids, seen = [], set()
    for path in ("/v1/models", "/api/tags"):
        try:
            req = urllib.request.Request(base + path, method="GET")
            with urllib.request.urlopen(req, timeout=2) as r:
                d = json.loads(r.read().decode() or "{}")
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        for key in ("data", "models"):
            for m in d.get(key) or []:
                name = (m.get("id") or m.get("name") or m.get("model") if isinstance(m, dict) else str(m)) or ""
                name = str(name).strip()
                if name and name not in seen:
                    seen.add(name); ids.append(name)
    return ids

def org_messages() -> list[dict[str, Any]]:
    for path in ORG_CANDIDATES:
        if not path.is_file():
            continue
        raw = path.read_text(encoding="utf-8", errors="replace").strip()
        if not raw:
            continue
        items: list[Any] = []
        if path.suffix == ".jsonl":
            for line in raw.splitlines():
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        else:
            try:
                loaded = json.loads(raw)
            except json.JSONDecodeError:
                continue
            items = loaded if isinstance(loaded, list) else (loaded.get("messages") or loaded.get("items") or [loaded])
        out = []
        for it in items:
            if not isinstance(it, dict):
                continue
            who = str(it.get("from") or it.get("who") or "")
            whom = str(it.get("to") or it.get("whom") or "")
            if who or whom:
                out.append({"from": who, "to": whom, "pr": it.get("pr") or "", "issue": it.get("issue") or "",
                            "state": str(it.get("state") or it.get("status") or ""),
                            "text": str(it.get("text") or it.get("summary") or "")[:240]})
        return out
    return []

def one_liner(hid: str, rec: dict[str, Any]) -> str:
    if hid in STUB_ALWAYS:
        return GROK_USE
    if hid == "llama-swap":
        return "llama-swap"
    if hid in ("llama.cpp", "llama-server"):
        return "llama-server"
    if hid == "shimmy":
        return "shimmy"
    if hid == "freetoken":
        return "ft serve --model $PFY_FT_MODEL"
    if hid == "ollama":
        return "ollama serve"
    if hid == "grok":
        return "curl -fsSL https://x.ai/cli/install.sh | bash"
    setup = str(rec.get("setup") or "").strip()
    return (setup.splitlines()[0] if setup else f"./pfy start {hid}")

def now_state(active: str, live: str, procs: list[dict[str, str]], verb: dict[str, str]) -> str:
    ids = {r["id"] for r in procs}
    mapped = "llama.cpp" if active == "llama-server" else active
    if mapped in STUB_ALWAYS or live in ("stub", "detected-stub", "missing"):
        return "blocked"
    if mapped in ids or active in ids:
        return "running"
    v = verb.get("verb") or ""
    return "blocked" if v.startswith("start") or v.startswith("up") else "idle"
