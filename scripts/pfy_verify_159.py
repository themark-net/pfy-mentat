#!/usr/bin/env python3
"""Verify surfaces for Space Invaders + Launch env — cite #159.

Open game / Open folder / TASK preview+copy and Launch-env what + next step.
Session proof stays Attach OpenCode + on-disk artifact (not a board-hosted game).
"""
from __future__ import annotations

import shutil
import subprocess
import webbrowser
from pathlib import Path

SI_REL = Path("workspace") / "space-invaders"
INDEX = "index.html"
TASK = "TASK.md"


def paths(root) -> dict:
    root = Path(root)
    folder = (root / SI_REL).resolve()
    abs_path = folder / INDEX
    task_path = folder / TASK
    rel = str(SI_REL / INDEX).replace("\\", "/")
    exists = abs_path.is_file()
    task_text = ""
    if task_path.is_file():
        try:
            task_text = task_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            task_text = ""
    return {
        "rel": rel,
        "abs_path": str(abs_path),
        "folder": str(folder),
        "task_path": str(task_path),
        "task_text": task_text,
        "exists": exists,
        "note": "Session proof: Attach OpenCode + disk artifact — not a board-hosted game",
    }


def _open_uri(uri: str) -> tuple[bool, str]:
    try:
        if webbrowser.open(uri):
            return True, ""
    except Exception as e:
        last = str(e)
    else:
        last = "webbrowser.open returned False"
    xdg = shutil.which("xdg-open")
    if xdg:
        try:
            proc = subprocess.run([xdg, uri], capture_output=True, text=True, timeout=15, check=False)
            if proc.returncode == 0:
                return True, ""
            last = ((proc.stderr or proc.stdout or "") or "xdg-open failed")[-400:]
        except Exception as e:
            last = str(e)[:400]
    return False, last or "no opener"


def open_game(root) -> dict:
    info = paths(root)
    if not info["exists"]:
        return {"ok": False, "live": "FAIL", "copy": "FAIL Open game · artifact missing", "error": "missing " + info["rel"], **{k: info[k] for k in ("rel", "abs_path", "folder", "task_path", "task_text", "exists", "note")}}
    uri = Path(info["abs_path"]).resolve().as_uri()
    ok, err = _open_uri(uri)
    if not ok:
        return {"ok": False, "live": "FAIL", "copy": "FAIL Open game", "error": err[:400], "uri": uri, **{k: info[k] for k in ("rel", "abs_path", "folder", "task_path", "task_text", "exists", "note")}}
    return {"ok": True, "live": "PASS", "copy": "PASS Open game · " + info["rel"], "error": "", "uri": uri, **{k: info[k] for k in ("rel", "abs_path", "folder", "task_path", "task_text", "exists", "note")}}


def open_folder(root) -> dict:
    info = paths(root)
    folder = Path(info["folder"])
    if not folder.is_dir():
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return {"ok": False, "live": "FAIL", "copy": "FAIL Open folder", "error": str(e)[:400], **{k: info[k] for k in ("rel", "abs_path", "folder", "task_path", "task_text", "exists", "note")}}
    target = str(folder)
    xdg = shutil.which("xdg-open")
    err = "xdg-open missing"
    if xdg:
        try:
            proc = subprocess.run([xdg, target], capture_output=True, text=True, timeout=15, check=False)
            if proc.returncode == 0:
                return {"ok": True, "live": "PASS", "copy": "PASS Open folder · " + info["folder"], "error": "", **{k: info[k] for k in ("rel", "abs_path", "folder", "task_path", "task_text", "exists", "note")}}
            err = ((proc.stderr or proc.stdout or "") or "xdg-open failed")[-400:]
        except Exception as e:
            err = str(e)[:400]
    try:
        uri = folder.resolve().as_uri()
        ok, werr = _open_uri(uri)
        if ok:
            return {"ok": True, "live": "PASS", "copy": "PASS Open folder · " + info["folder"], "error": "", "uri": uri, **{k: info[k] for k in ("rel", "abs_path", "folder", "task_path", "task_text", "exists", "note")}}
        err = werr or err
    except Exception as e:
        err = str(e)[:400]
    return {"ok": False, "live": "FAIL", "copy": "FAIL Open folder", "error": (err or "open failed")[:400], **{k: info[k] for k in ("rel", "abs_path", "folder", "task_path", "task_text", "exists", "note")}}


def task_payload(root) -> dict:
    info = paths(root)
    text = info.get("task_text") or ""
    if not text and not Path(info["task_path"]).is_file():
        return {"ok": False, "live": "FAIL", "copy": "FAIL Copy TASK · missing", "error": "TASK.md missing", "task_text": "", **{k: info[k] for k in ("rel", "abs_path", "folder", "task_path", "exists", "note")}}
    return {"ok": True, "live": "PASS", "copy": "PASS Copy TASK", "error": "", "task_text": text, "value": text, **{k: info[k] for k in ("rel", "abs_path", "folder", "task_path", "exists", "note")}}


def copy_payload(value: str, label: str = "copied") -> dict:
    value = value if value is not None else ""
    if not str(value).strip():
        return {"ok": False, "live": "FAIL", "copy": "FAIL " + label, "error": "empty", "value": ""}
    return {"ok": True, "live": "PASS", "copy": "PASS " + label, "error": "", "value": str(value)}


def _stage_live_from_state(STATE: Path) -> str:
    try:
        p = Path(STATE) / "last-verb.json"
        if p.is_file():
            import json
            data = json.loads(p.read_text(encoding="utf-8", errors="replace") or "{}")
            if str(data.get("verb") or "") in ("env", "launch-env", "stage"):
                return "READY"
    except Exception:
        pass
    return ""


def enrich_launch_env(res, live_openai_base, STATE, ROOT) -> dict:
    res = dict(res or {})
    base = ""
    eng = ""
    det = {}
    try:
        b, det = live_openai_base()
        base = (b or "").strip()
        if not isinstance(det, dict):
            det = {}
        eng = str(det.get("engine") or "").strip()
    except Exception as e:
        res.setdefault("enrich_error", str(e)[:200])
        det = {}
    if base == "(none)":
        base = ""
    stage = ""
    st = str(det.get("status") or "").strip().lower()
    if st == "ready":
        stage = "READY"
    elif st:
        stage = st.upper()
    if not stage:
        stage = _stage_live_from_state(Path(STATE)) or str(res.get("live") or "")
    log = ""
    for name in ("env.log", "launch-env.log", "sidecar-env.log"):
        cand = Path(STATE) / name
        if cand.is_file():
            log = str(cand)
            break
    parts = []
    if base:
        parts.append("engine " + base)
    elif eng and eng.lower() not in ("", "none"):
        parts.append("engine " + eng)
    else:
        parts.append("engine (none)")
    if stage:
        parts.append("stage " + stage)
    if log:
        parts.append("log " + log)
    live = str(res.get("live") or "")
    if live == "SKIP" and not any("skip" in p.lower() for p in parts):
        why = (res.get("error") or "").strip()
        if not why:
            why = "honest skip / no local runtime"
            low = (res.get("stdout") or "").lower()
            if "honest skip" in low:
                why = "honest skip"
            elif "no local runtime" in low:
                why = "no local runtime"
        parts.append(why)
    what = " · ".join(parts)
    next_steps = []
    if base:
        next_steps.append({"id": "endpoint", "label": "Copy endpoint", "value": base})
    next_steps.append({"id": "status", "label": "Copy ./pfy status", "value": "./pfy status"})
    if log:
        next_steps.append({"id": "log", "label": "Copy log path", "value": log})
    res["base_url"] = base
    res["engine"] = eng or str(det.get("engine") or "")
    res["what"] = what
    res["stage"] = stage
    res["log"] = log
    res["next_steps"] = next_steps
    if res.get("ok") and live == "PASS":
        res["copy"] = "PASS env · " + what
    elif res.get("ok") and live == "SKIP":
        res["copy"] = "SKIP env · " + what
    return res


def artifact_get(root) -> dict:
    info = paths(root)
    return {"ok": True if info["exists"] else False, "live": "PASS" if info["exists"] else "FAIL", "copy": ("PASS artifact · " + info["rel"]) if info["exists"] else "FAIL artifact missing", "error": "" if info["exists"] else "missing index.html", **info}
