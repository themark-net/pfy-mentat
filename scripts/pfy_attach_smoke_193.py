#!/usr/bin/env python3
"""Attach OpenCode usability smoke — cite #193.

Proves FreeToken-first live base can list models and answer one chat
completion. No model / probe fail => FAIL + next (never fake PASS).
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Callable, Dict, List, Optional

NEXT_STEP = "Launch env or ./pfy up"
SMOKE_PROMPT = "Reply with exactly: PFY_ATTACH_OK"


def _normalize_base(base_url: str) -> str:
    b = (base_url or "").strip().rstrip("/")
    if not b or b in ("(none)", "none"):
        return ""
    if not b.endswith("/v1"):
        b = b + "/v1"
    return b


def _default_inspect_models(base_url: str) -> List[str]:
    base = _normalize_base(base_url)
    if not base:
        return []
    root = base[:-3] if base.endswith("/v1") else base
    ids: List[str] = []
    seen = set()
    for path in ("/v1/models", "/api/tags"):
        try:
            req = urllib.request.Request(root.rstrip("/") + path, method="GET")
            with urllib.request.urlopen(req, timeout=2) as r:
                d = json.loads(r.read().decode() or "{}")
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        for key in ("data", "models"):
            rows = d.get(key)
            if not isinstance(rows, list):
                continue
            for m in rows:
                name = ""
                if isinstance(m, dict):
                    name = str(m.get("id") or m.get("name") or "").strip()
                elif isinstance(m, str):
                    name = m.strip()
                if name and name not in seen:
                    seen.add(name)
                    ids.append(name)
        if ids:
            break
    return ids


def attach_smoke(
    base_url: str,
    inspect_models: Optional[Callable[[str], List[str]]] = None,
    timeout: float = 30.0,
    model: str = "",
) -> Dict[str, Any]:
    """POST one /v1/chat/completions against FreeToken-first live base. Cite #193.

    Returns: ok, smoke (PASS|FAIL), models, model, error, next_step, copy.
    """
    base = _normalize_base(base_url)
    next_step = NEXT_STEP
    empty: Dict[str, Any] = {
        "ok": False,
        "smoke": "FAIL",
        "models": [],
        "model": "",
        "error": "",
        "next_step": next_step,
        "copy": "smoke: FAIL",
    }
    if not base:
        empty["error"] = "no live local endpoint"
        empty["copy"] = "smoke: FAIL · no live local endpoint · " + next_step
        return empty

    inspector = inspect_models or _default_inspect_models
    try:
        models = list(inspector(base) or [])
    except Exception as e:
        empty["error"] = "models probe: " + str(e)[:200]
        empty["copy"] = "smoke: FAIL · models probe · " + next_step
        return empty

    name = (model or "").strip()
    if not name and models:
        name = str(models[0]).strip()
    if not name:
        name = (
            os.environ.get("LOCAL_CODER_MODEL")
            or os.environ.get("PFY_FT_MODEL")
            or os.environ.get("PFY_OLLAMA_MODEL")
            or os.environ.get("PFY_LLAMA_MODEL")
            or ""
        ).strip()
    if not name:
        return {
            "ok": False,
            "smoke": "FAIL",
            "models": models,
            "model": "",
            "error": "no model on live endpoint",
            "next_step": next_step,
            "copy": "models: 0 · smoke: FAIL · no model · " + next_step,
        }

    url = base.rstrip("/") + "/chat/completions"
    payload = json.dumps(
        {
            "model": name,
            "messages": [{"role": "user", "content": SMOKE_PROMPT}],
            "max_tokens": 32,
            "temperature": 0,
        }
    ).encode("utf-8")
    try:
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json", "Authorization": "Bearer local"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=float(timeout)) as r:
            data = json.loads(r.read().decode() or "{}")
    except Exception as e:
        return {
            "ok": False,
            "smoke": "FAIL",
            "models": models,
            "model": name,
            "error": str(e)[:400],
            "next_step": next_step,
            "copy": "models: %s · smoke: FAIL · %s · %s"
            % (len(models), str(e)[:120], next_step),
        }

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
        return {
            "ok": False,
            "smoke": "FAIL",
            "models": models,
            "model": name,
            "error": "empty completion",
            "next_step": next_step,
            "copy": "models: %s · smoke: FAIL · empty completion · %s"
            % (len(models), next_step),
        }

    mlabel = ",".join(str(x) for x in models[:3]) if models else name
    if len(models) > 3:
        mlabel += ",…"
    return {
        "ok": True,
        "smoke": "PASS",
        "models": models,
        "model": name,
        "error": "",
        "next_step": "",
        "copy": "models: %s (%s) · smoke: PASS" % (len(models), mlabel or name),
        "completion": str(text).strip()[:80],
    }


def enrich_attach_result(
    result: Dict[str, Any],
    base_url: str = "",
    inspect_models: Optional[Callable[[str], List[str]]] = None,
    model: str = "",
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """Merge smoke/models into an Attach success (or reuse) result. Cite #193."""
    out = dict(result or {})
    base = base_url or str(out.get("base_url") or "")
    smoke = attach_smoke(base, inspect_models=inspect_models, timeout=timeout, model=model or str(out.get("model") or ""))
    out["smoke"] = smoke.get("smoke") or "FAIL"
    out["models"] = list(smoke.get("models") or [])
    if smoke.get("model") and not out.get("model"):
        out["model"] = smoke["model"]
    out["smoke_error"] = smoke.get("error") or ""
    copy = str(out.get("copy") or "").rstrip()
    bit = str(smoke.get("copy") or ("smoke: " + out["smoke"]))
    if "smoke:" not in copy.lower():
        out["copy"] = (copy + " · " + bit).strip(" ·")
    next_steps = list(out.get("next_steps") or [])
    if not smoke.get("ok"):
        nxt = smoke.get("next_step") or NEXT_STEP
        out["next_step"] = out.get("next_step") or nxt
        label = "smoke FAIL · ./pfy models && ./pfy smoke"
        if not any((s or {}).get("id") == "smoke" for s in next_steps):
            next_steps.append({"id": "smoke", "label": label, "value": "./pfy smoke"})
        out["next_steps"] = next_steps
    else:
        if not any((s or {}).get("id") == "smoke" for s in next_steps):
            next_steps.insert(0, {"id": "smoke", "label": "smoke PASS", "value": "PASS"})
        if out.get("models") and not any((s or {}).get("id") == "models" for s in next_steps):
            next_steps.insert(0, {
                "id": "models",
                "label": "models %s" % len(out["models"]),
                "value": "./pfy models",
            })
        out["next_steps"] = next_steps
    return out
