#!/usr/bin/env python3
"""Local usage parse for operator GUI — cite #165. Reuses #161 `./pfy usage` output."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


SKIP = "SKIP"
FAIL_NO_ENGINE = "FAIL: no local engine up"
NEXT_STEP = "Launch env or ./pfy up"


def _empty(ok: bool = False, **extra: Any) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "ok": ok,
        "engine": "",
        "endpoint": "",
        "models": [],
        "tok_path": SKIP,
        "vram": SKIP,
        "fail": "" if ok else FAIL_NO_ENGINE,
        "next_step": "" if ok else NEXT_STEP,
        "lines": [],
    }
    out.update(extra)
    return out


def parse_usage_text(text: str) -> Dict[str, Any]:
    """Parse `bash scripts/pfy usage` (or status usage block) into a dict.

    Keys: engine, endpoint, models, tok_path, vram, ok, next_step, fail, lines.
    Unknown tok_path/vram stay honest SKIP — never invent.
    """
    lines = [ln.rstrip() for ln in (text or "").splitlines()]
    # Drop leading "usage:" banner if present
    body = list(lines)
    if body and body[0].strip().lower() == "usage:":
        body = body[1:]

    engine = ""
    endpoint = ""
    models: List[str] = []
    tok_path = SKIP
    vram_parts: List[str] = []
    fail = ""
    next_step = ""
    in_models = False
    in_vram = False

    for raw in body:
        s = raw.strip()
        if not s:
            in_models = False
            continue
        low = s.lower()
        if low.startswith("fail:"):
            fail = s if s.upper().startswith("FAIL") else ("FAIL: " + s.split(":", 1)[-1].strip())
            if "no local engine" in low and "FAIL:" not in fail:
                fail = FAIL_NO_ENGINE
            in_models = in_vram = False
            continue
        if low.startswith("next:"):
            nxt = s.split(":", 1)[1].strip()
            # Prefer operator-accessible wording from DoD
            if "./pfy up" in nxt or "launch" in nxt.lower():
                next_step = NEXT_STEP if "launch" not in nxt.lower() else nxt
                if "launch" not in next_step.lower():
                    next_step = NEXT_STEP
            else:
                next_step = nxt or NEXT_STEP
            in_models = in_vram = False
            continue
        if low.startswith("engine:"):
            engine = s.split(":", 1)[1].strip()
            in_models = in_vram = False
            continue
        if low.startswith("endpoint:"):
            endpoint = s.split(":", 1)[1].strip()
            if endpoint in ("(none)", "none"):
                endpoint = ""
            in_models = in_vram = False
            continue
        if low.startswith("tok_path:"):
            tok_path = s.split(":", 1)[1].strip() or SKIP
            in_models = in_vram = False
            continue
        if low == "vram:" or low.startswith("vram:"):
            rest = s.split(":", 1)[1].strip() if ":" in s else ""
            if rest:
                vram_parts = [rest]
                in_vram = False
            else:
                vram_parts = []
                in_vram = True
            in_models = False
            continue
        if low.startswith("models:"):
            in_models = True
            in_vram = False
            continue
        if in_vram:
            if s.startswith("gpu") or "/" in s or s[0].isdigit():
                vram_parts.append(s)
                continue
            in_vram = False
        if in_models:
            if s.startswith("(") and "none" in low:
                continue
            if ":" in s and not s.startswith("http") and s.split(":", 1)[0].isalpha():
                # next top-level key
                in_models = False
            else:
                models.append(s)
                continue

    vram = SKIP
    if vram_parts:
        joined = "; ".join(vram_parts)
        if joined.upper() == SKIP or not joined.strip():
            vram = SKIP
        else:
            vram = joined

    ok = bool(engine) and engine.lower() not in ("none",) and not fail
    if not ok:
        fail = fail or FAIL_NO_ENGINE
        next_step = next_step or NEXT_STEP
    else:
        fail = ""
        next_step = ""
        if not tok_path:
            tok_path = SKIP
        if not vram:
            vram = SKIP

    return {
        "ok": ok,
        "engine": engine if ok else (engine or ""),
        "endpoint": endpoint if ok else endpoint,
        "models": models if ok else models,
        "tok_path": tok_path if tok_path else SKIP,
        "vram": vram if vram else SKIP,
        "fail": fail,
        "next_step": next_step,
        "lines": [ln for ln in lines if ln.strip()],
    }


def run_pfy_usage(root: Path, runner: Callable[..., Tuple[int, str]], timeout: float = 25.0) -> Tuple[int, str]:
    """Run `bash scripts/pfy usage` (ROOT-relative)."""
    pfy = Path(root) / "scripts" / "pfy"
    if not pfy.is_file():
        return 127, ""
    rc, out = runner(["bash", str(pfy), "usage"], timeout=timeout)
    return rc, out or ""


def collect_usage(root: Path, runner: Callable[..., Tuple[int, str]], timeout: float = 25.0) -> Dict[str, Any]:
    """Run usage CLI and parse — primary board entry for #165."""
    rc, out = run_pfy_usage(root, runner, timeout=timeout)
    if not (out or "").strip():
        info = _empty(ok=False, error=f"pfy usage empty, exit {rc}")
        info["lines"] = []
        return info
    info = parse_usage_text(out)
    info["rc"] = rc
    return info


def enrich_status_runtime(runtime: Optional[dict], usage: Optional[dict]) -> Dict[str, Any]:
    """Merge usage fields into status_runtime without inventing values."""
    sr = dict(runtime or {})
    u = usage or {}
    if u.get("engine"):
        sr["engine"] = u["engine"]
    if u.get("endpoint"):
        sr["endpoint"] = u["endpoint"]
        sr["base_url"] = u["endpoint"]
    sr["tok_path"] = u.get("tok_path") or SKIP
    sr["vram"] = u.get("vram") or SKIP
    if u.get("ok") is False:
        sr["usage_ok"] = False
        if u.get("fail"):
            sr["usage_fail"] = u["fail"]
        if u.get("next_step"):
            sr["usage_next"] = u["next_step"]
    else:
        sr["usage_ok"] = True
    return sr
