#!/usr/bin/env python3
"""T-0093: Select a tools-capable Ollama model (or document tool-split).

OpenCode agent mode fails with:
  "registry.ollama.ai/… does not support tools"
when the tag has no tool template. deepseek-coder:6.7b is a common offender.

This script:
  1. Lists pulled Ollama tags
  2. Probes each candidate with a tiny tools chat request
  3. Picks LOCAL_TOOLS_MODEL (tools OK) vs LOCAL_CODER_MODEL (completion OK)
  4. Prints exports + writes examples/opencode-ollama/.generated/tools-model.env

Usage:
  python3 examples/eval-harness/select_tools_model.py
  python3 examples/eval-harness/select_tools_model.py --exports
  python3 examples/eval-harness/select_tools_model.py --json
  python3 examples/eval-harness/select_tools_model.py --probe-only MODEL

Env:
  OLLAMA_HOST / OPENAI_BASE_URL
  LOCAL_CODER_MODEL          preferred completion model (default deepseek-coder:6.7b)
  LOCAL_TOOLS_MODEL          force/prefer this if tools-capable when present
  EVAL_ALLOW_PULL=0          do not suggest pulls (default 0 for safety)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "examples" / "opencode-ollama" / ".generated"

# Prefer these when already pulled (known tool-friendly families on Ollama).
TOOLS_PREFERENCE: list[str] = [
    "qwen2.5-coder:7b-instruct",
    "qwen2.5-coder:7b",
    "qwen2.5-coder:14b-instruct",
    "qwen2.5-coder:14b",
    "qwen2.5:7b-instruct",
    "qwen2.5:14b-instruct",
    "llama3.1:8b-instruct",
    "llama3.1:8b",
    "llama3.2:3b-instruct",
    "llama3.2:3b",
    "mistral-nemo:12b",
    "mistral-small:latest",
    "command-r:35b",
    "phi4:latest",
]

# Pull suggestions if none tools-capable (operator must opt in).
PULL_SUGGEST: list[dict[str, Any]] = [
    {"name": "qwen2.5-coder:7b-instruct", "ram_gb": 8, "download_gb": 4.7, "note": "good default tools+coder"},
    {"name": "llama3.1:8b-instruct", "ram_gb": 8, "download_gb": 4.9, "note": "strong tool calling"},
    {"name": "qwen2.5:7b-instruct", "ram_gb": 8, "download_gb": 4.7, "note": "general tools"},
]


def ollama_root() -> str:
    base = (
        os.environ.get("OLLAMA_HOST")
        or os.environ.get("OPENAI_BASE_URL")
        or "http://127.0.0.1:11434"
    )
    base = base.rstrip("/")
    if base.endswith("/v1"):
        base = base[: -len("/v1")]
    return base


def openai_base() -> str:
    return ollama_root() + "/v1"


def _urlopen(url: str, data: bytes | None = None, timeout: float = 60, headers: dict | None = None):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    h = {"User-Agent": "pfy-select-tools/1.0", "Content-Type": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h, method="POST" if data else "GET")
    return opener.open(req, timeout=timeout)


def list_pulled() -> list[str]:
    url = f"{ollama_root()}/api/tags"
    try:
        with _urlopen(url, timeout=8) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"error: cannot reach Ollama at {url}: {e}", file=sys.stderr)
        return []
    names = []
    for m in data.get("models") or []:
        n = m.get("name")
        if n:
            names.append(n)
    return names


def name_match(want: str, names: list[str]) -> str | None:
    if want in names:
        return want
    # allow tag prefix / suffix flexibility
    for n in names:
        if n == want or n.startswith(want + "-") or want in n:
            return n
    base = want.split(":")[0]
    for n in names:
        if n.startswith(base + ":"):
            return n
    return None


def probe_tools(model: str, timeout: float = 90) -> dict[str, Any]:
    """Return {ok, reason, raw_snippet} after a minimal tools chat call."""
    url = openai_base() + "/chat/completions"
    body = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "Use the tool get_answer to answer. Call the tool with value 42.",
            }
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_answer",
                    "description": "Return a canned answer",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "value": {"type": "integer", "description": "input value"},
                        },
                        "required": ["value"],
                    },
                },
            }
        ],
        "tool_choice": "auto",
        "max_tokens": 64,
        "temperature": 0,
        "stream": False,
    }
    raw = b""
    try:
        with _urlopen(
            url,
            data=json.dumps(body).encode(),
            timeout=timeout,
            headers={"Authorization": "Bearer ollama"},
        ) as resp:
            raw = resp.read()
            data = json.loads(raw.decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        low = err_body.lower()
        if "does not support tools" in low or "support tools" in low:
            return {"ok": False, "reason": "no_tools", "detail": err_body[:300], "model": model}
        return {"ok": False, "reason": "http_error", "detail": f"{e.code} {err_body[:300]}", "model": model}
    except Exception as e:
        return {"ok": False, "reason": "network", "detail": str(e)[:300], "model": model}

    # Success if API accepted tools (even if model replies in plain text)
    if "error" in data:
        err = str(data["error"]).lower()
        if "does not support tools" in err or "support tools" in err:
            return {"ok": False, "reason": "no_tools", "detail": str(data["error"])[:300], "model": model}
        return {"ok": False, "reason": "api_error", "detail": str(data["error"])[:300], "model": model}

    msg = (data.get("choices") or [{}])[0].get("message") or {}
    has_calls = bool(msg.get("tool_calls"))
    content = (msg.get("content") or "")[:120]
    return {
        "ok": True,
        "reason": "tools_api_ok",
        "tool_calls": has_calls,
        "content_preview": content,
        "model": model,
        "detail": "API accepted tools schema"
        + ("; model emitted tool_calls" if has_calls else "; model may answer in text"),
    }


def score_tools_candidate(name: str) -> int:
    low = name.lower()
    if re.search(r"qwen2\.5-coder.*(7|14)|llama3\.1:8b|mistral-nemo", low):
        return 5
    if re.search(r"qwen2\.5|llama3\.[12]|mistral|command-r|phi4", low):
        return 4
    if re.search(r"instruct|chat", low):
        return 3
    if re.search(r"deepseek-coder|starcoder", low):
        return 1  # usually no tools
    return 2


def select(names: list[str], probes: dict[str, dict[str, Any]]) -> dict[str, Any]:
    coder = os.environ.get("LOCAL_CODER_MODEL", "deepseek-coder:6.7b")
    coder_resolved = name_match(coder, names) or coder

    forced = os.environ.get("LOCAL_TOOLS_MODEL", "").strip()
    if forced:
        fr = name_match(forced, names)
        if fr and probes.get(fr, {}).get("ok"):
            return {
                "LOCAL_CODER_MODEL": coder_resolved,
                "LOCAL_TOOLS_MODEL": fr,
                "tools_mode": "local_tools",
                "reason": f"LOCAL_TOOLS_MODEL forced and tools-ok: {fr}",
            }
        if fr and not probes.get(fr, {}).get("ok"):
            return {
                "LOCAL_CODER_MODEL": coder_resolved,
                "LOCAL_TOOLS_MODEL": "",
                "tools_mode": "split",
                "reason": f"LOCAL_TOOLS_MODEL={forced} present but tools probe failed",
            }

    tools_ok = [n for n, p in probes.items() if p.get("ok")]
    # Prefer preference list order, then score
    ordered: list[str] = []
    for pref in TOOLS_PREFERENCE:
        m = name_match(pref, tools_ok)
        if m and m not in ordered:
            ordered.append(m)
    for n in sorted(tools_ok, key=score_tools_candidate, reverse=True):
        if n not in ordered:
            ordered.append(n)

    if ordered:
        tools = ordered[0]
        return {
            "LOCAL_CODER_MODEL": coder_resolved if name_match(coder_resolved, names) else tools,
            "LOCAL_TOOLS_MODEL": tools,
            "tools_mode": "local_tools",
            "reason": f"tools-capable pulled model: {tools}",
            "alternatives": ordered[:5],
        }

    # No tools model — explicit split
    allow_pull = os.environ.get("EVAL_ALLOW_PULL", "0").strip() not in ("0", "false", "no")
    return {
        "LOCAL_CODER_MODEL": coder_resolved,
        "LOCAL_TOOLS_MODEL": "",
        "tools_mode": "split",
        "reason": (
            "no tools-capable model among pulled tags; "
            "use completion-only local worker + escalate tools to Grok "
            "or: ollama pull qwen2.5-coder:7b-instruct"
        ),
        "suggest_pull": [p["name"] for p in PULL_SUGGEST] if allow_pull else [
            p["name"] for p in PULL_SUGGEST
        ],
        "suggest_note": "EVAL_ALLOW_PULL=1 to auto-pull in future; for now pull manually",
    }


def write_env(sel: dict[str, Any]) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "tools-model.env"
    tools = sel.get("LOCAL_TOOLS_MODEL") or ""
    coder = sel.get("LOCAL_CODER_MODEL") or "deepseek-coder:6.7b"
    mode = sel.get("tools_mode") or "split"
    lines = [
        "# Generated by select_tools_model.py (T-0093) — do not commit secrets",
        f"export LOCAL_CODER_MODEL={coder}",
        f"export LOCAL_TOOLS_MODEL={tools}",
        f"export TOOLS_MODE={mode}",
        "# Prefer tools model for OpenCode agent when set:",
        f"export OPENCODE_AGENT_MODEL={tools or coder}",
        f"# reason: {sel.get('reason', '')}",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="T-0093 select tools-capable Ollama model")
    ap.add_argument("--exports", action="store_true", help="print shell exports only")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--probe-only", metavar="MODEL", help="probe one model and exit")
    ap.add_argument("--timeout", type=float, default=90)
    ap.add_argument("--write-env", action="store_true", default=True)
    ap.add_argument("--no-write-env", action="store_true")
    args = ap.parse_args(argv)

    if args.probe_only:
        r = probe_tools(args.probe_only, timeout=args.timeout)
        print(json.dumps(r, indent=2))
        return 0 if r.get("ok") else 2

    print(f"== select_tools_model (T-0093) ==", file=sys.stderr)
    print(f"  ollama={ollama_root()}", file=sys.stderr)
    names = list_pulled()
    if not names:
        print("error: no Ollama models (is ollama up?)", file=sys.stderr)
        if args.json:
            print(json.dumps({"error": "ollama_unreachable", "tools_mode": "split"}))
        return 1
    print(f"  pulled={len(names)}", file=sys.stderr)

    # Probe: preference list hits first, then other instruct/chat names (cap to keep fast)
    to_probe: list[str] = []
    for pref in TOOLS_PREFERENCE:
        m = name_match(pref, names)
        if m and m not in to_probe:
            to_probe.append(m)
    # Always probe current coder
    coder = os.environ.get("LOCAL_CODER_MODEL", "deepseek-coder:6.7b")
    cm = name_match(coder, names)
    if cm and cm not in to_probe:
        to_probe.append(cm)
    # Add a few more high-score names
    for n in sorted(names, key=score_tools_candidate, reverse=True):
        if n not in to_probe and score_tools_candidate(n) >= 3:
            to_probe.append(n)
        if len(to_probe) >= 8:
            break

    probes: dict[str, dict[str, Any]] = {}
    for n in to_probe:
        print(f"  probe tools: {n} …", file=sys.stderr)
        probes[n] = probe_tools(n, timeout=args.timeout)
        st = "OK" if probes[n].get("ok") else probes[n].get("reason", "fail")
        print(f"    → {st}", file=sys.stderr)

    sel = select(names, probes)
    sel["probes"] = {k: {kk: vv for kk, vv in v.items() if kk != "raw"} for k, v in probes.items()}
    sel["pulled_count"] = len(names)

    if not args.no_write_env and args.write_env:
        path = write_env(sel)
        print(f"  wrote {path}", file=sys.stderr)

    if args.exports:
        print(f"export LOCAL_CODER_MODEL={sel.get('LOCAL_CODER_MODEL', '')}")
        print(f"export LOCAL_TOOLS_MODEL={sel.get('LOCAL_TOOLS_MODEL', '')}")
        print(f"export TOOLS_MODE={sel.get('tools_mode', 'split')}")
        tools = sel.get("LOCAL_TOOLS_MODEL") or sel.get("LOCAL_CODER_MODEL") or ""
        print(f"export OPENCODE_AGENT_MODEL={tools}")
        return 0

    if args.json:
        print(json.dumps(sel, indent=2))
        return 0

    print("")
    print(f"tools_mode:     {sel.get('tools_mode')}")
    print(f"LOCAL_CODER_MODEL: {sel.get('LOCAL_CODER_MODEL')}")
    print(f"LOCAL_TOOLS_MODEL: {sel.get('LOCAL_TOOLS_MODEL') or '(none — tool-split)'}")
    print(f"reason:         {sel.get('reason')}")
    if sel.get("suggest_pull"):
        print("suggest pull:   " + ", ".join(sel["suggest_pull"][:3]))
    print("")
    print("Use:")
    print("  set -a; . examples/opencode-ollama/.generated/tools-model.env; set +a")
    print("  make worker-stage   # or opencode with OPENCODE_AGENT_MODEL")
    if sel.get("tools_mode") == "split":
        print("  Tool-split: local completion worker + Grok/monitor for tool-heavy steps")
        print("  See docs/ops/local-tools-split.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
