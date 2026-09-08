#!/usr/bin/env python3
"""Attach OpenCode developer-usable prove helpers -- cite #193."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path


def openai_compat_root(base):
    """Strip trailing /v1 so probes are not /v1/v1/models. Same class as #187."""
    root = str(base or "").rstrip("/")
    if root.endswith("/v1"):
        root = root[:-3].rstrip("/")
    return root


def prove_developer_usable(base, inspect_models):
    """List models + one smoke prompt against live base. Cite #193.

    Returns (ok, model_name, error). Fail => Attach must not paint attached.
    Normalize like #187 print_live_models: strip trailing /v1 before
    probing /v1/models and /v1/chat/completions (live_openai_base often
    returns .../v1; inspect_models appends /v1/models).
    """
    root = openai_compat_root(base)
    models = []
    try:
        models = list(inspect_models(root) or [])
    except Exception as e:
        return False, "", "models list failed: %s" % str(e)[:200]
    if not models:
        return False, "", "no models on live endpoint"
    name = str(models[0]).strip()
    if not name:
        return False, "", "empty model name"
    url = root + "/v1/chat/completions"
    payload = json.dumps({
        "model": name,
        "messages": [{"role": "user", "content": "Reply with exactly: PFY_ATTACH_SMOKE_OK"}],
        "max_tokens": 32,
        "temperature": 0,
    }).encode("utf-8")
    try:
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer local",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode() or "{}")
    except Exception as e:
        return False, name, "smoke failed: %s" % str(e)[:200]
    text = ""
    try:
        choice = (data.get("choices") or [{}])[0]
        if not isinstance(choice, dict):
            choice = {}
        msg = choice.get("message") or {}
        if isinstance(msg, dict):
            text = msg.get("content") or ""
        if not text:
            text = choice.get("text") or ""
    except Exception:
        text = ""
    if len(str(text).strip()) < 2:
        return False, name, "smoke empty completion"
    return True, name, ""


def fail_not_usable(clear_session_reach, STATE, hid, reason, next_step, engine, status, base="", model=""):
    clear_session_reach(STATE)
    attach_base_path = Path(STATE) / "opencode-attach-base"
    try:
        if attach_base_path.is_file():
            attach_base_path.unlink()
    except OSError:
        pass
    copy = "FAIL attach -- %s \u00b7 %s" % (reason, next_step)
    return {
        "ok": False,
        "id": hid,
        "live": "FAIL",
        "copy": copy,
        "error": reason,
        "session_reach": "FAIL",
        "next_step": next_step,
        "next_steps": [{"id": "next", "label": next_step, "value": next_step}],
        "engine": engine,
        "detect_status": status or "missing",
        "base_url": base,
        "model": model,
        "usable": False,
    }


SESSION_REACH_USABLE = "terminal \u00b7 OpenCode \u00b7 models \u00b7 smoke"
