"""Loop paint: catalog modules + live local/cloud hedge (ADR-0017).

The operator window's front door is not a harness picker. It shows:

  * which **modules** (toolsets from ``data/toolsets.json``) are gathered and
    whether they are implementable (best cell across harnesses)
  * whether **local compute** is up and whether **cloud credits** can run
    (hedge for bulk / interactive / hard)

Harness attach is pudding-proof behind Launch session, not a Loop control.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from . import hedge, registry, toolsets

MODULES_FILE = "loop-modules.json"
TASKS = hedge.TASKS
WIZARD_MODE = {
    "orchestration": "orchestration",
    "code-graph": "code-graph",
    "catalog-ask": "catalog",
}


def _state(state: Path | None) -> Path:
    return registry.state_dir(state)


def modules_path(state: Path | None = None) -> Path:
    return _state(state) / MODULES_FILE


def load_selection(state: Path | None = None) -> dict:
    path = modules_path(state)
    empty = {"enabled": [], "task": "interactive"}
    if not path.is_file():
        return empty
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return empty
    if not isinstance(data, dict):
        return empty
    enabled = [str(x) for x in (data.get("enabled") or []) if str(x).strip()]
    task = str(data.get("task") or "interactive").strip().lower()
    if task not in TASKS:
        task = "interactive"
    return {"enabled": enabled, "task": task}


def save_selection(sel: dict, state: Path | None = None) -> Path:
    path = modules_path(state)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"enabled": list(sel.get("enabled") or []), "task": sel.get("task") or "interactive"}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _best_status(impl: dict) -> str:
    """Harness-agnostic: implemented if any cell is, else partial, else stub."""
    cells = [str((c or {}).get("status") or "stub") for c in impl.values()]
    if "implemented" in cells:
        return "implemented"
    if "partial" in cells:
        return "partial"
    return "stub"


def _module_row(t: dict, enabled: set[str]) -> dict:
    tid = str(t.get("id") or "")
    impl = t.get("implementation") or {}
    status = _best_status(impl)
    how = next((str((c or {}).get("how") or "") for c in impl.values() if (c or {}).get("how")), "")
    return {
        "id": tid,
        "title": str(t.get("title") or tid),
        "status": status,
        "how": how,
        "lanes": list(t.get("lanes") or []),
        "catalog_tool": t.get("catalog_tool"),
        "enabled": tid in enabled,
        "stub": status == "stub",
        "wizard_mode": WIZARD_MODE.get(tid),
    }


def toggle(tid: str, on: bool, *, state: Path | None = None, root_dir: Path | None = None) -> dict:
    """Enable/disable a module. Stub modules cannot be enabled."""
    t = registry.toolset(tid, root_dir)
    if t is None:
        return {
            "ok": False, "live": "FAIL", "id": tid,
            "error": "unknown module %r" % tid,
            "next_step": "pick one of: %s" % ", ".join(registry.toolset_ids(root_dir)),
            "copy": "FAIL module -- unknown %s" % tid,
        }
    status = _best_status(t.get("implementation") or {})
    if on and status == "stub":
        stub_how = next((str((c or {}).get("how") or "") for c in (t.get("implementation") or {}).values() if (c or {}).get("status") == "stub"), "no config surface wired")
        return {
            "ok": False, "live": "STUB", "id": tid, "status": status,
            "error": "module %s is stub" % tid,
            "next_step": stub_how,
            "copy": "STUB module %s — not implementable yet" % tid,
        }
    sel = load_selection(state)
    have = [x for x in sel["enabled"] if x != tid]
    if on:
        have.append(tid)
    sel["enabled"] = have
    save_selection(sel, state)
    return {
        "ok": True, "live": "READY", "id": tid, "on": on, "status": status,
        "enabled": have, "task": sel["task"],
        "wizard_mode": WIZARD_MODE.get(tid) if on else None,
        "copy": "READY module %s %s" % (tid, "on" if on else "off"),
    }


def set_task(task: str, *, state: Path | None = None) -> dict:
    task = str(task or "").strip().lower()
    if task not in TASKS:
        return {
            "ok": False, "live": "FAIL", "error": "unknown task %r" % task,
            "next_step": "use %s" % "|".join(TASKS),
            "copy": "FAIL task -- use %s" % "|".join(TASKS),
        }
    sel = load_selection(state)
    sel["task"] = task
    save_selection(sel, state)
    return {"ok": True, "live": "READY", "task": task, "enabled": sel["enabled"], "copy": "READY task %s" % task}


def fields(
    *,
    state: Path | None = None,
    root_dir: Path | None = None,
    local: dict | None = None,
) -> dict:
    """Snapshot fragment for Loop: modules + hedge for the selected task class."""
    sel = load_selection(state)
    enabled = set(sel["enabled"])
    modules = [_module_row(t, enabled) for t in registry.toolset_rows(root_dir)]
    # Reuse one detector pass for all three task classes so the split is comparable.
    local = dict(local) if local is not None else hedge.detect_local(root_dir)
    routes = {task: hedge.decide(task, local=local, state=state, root_dir=root_dir) for task in TASKS}
    chosen = routes[sel["task"]]
    local_ok = str(local.get("status") or "").lower() == "ready"
    gab_key = bool(str(os.environ.get("GAB_API_KEY") or "").strip())
    return {
        "modules": modules,
        "modules_enabled": list(sel["enabled"]),
        "modules_task": sel["task"],
        "hedge": {
            "task": sel["task"],
            "lane": chosen.get("lane"),
            "ok": bool(chosen.get("ok")),
            "live": chosen.get("live") or "FAIL",
            "reason": chosen.get("reason") or chosen.get("copy") or "",
            "next_step": chosen.get("next_step") or "",
            "copy": chosen.get("copy") or "",
            "local_engine": chosen.get("local_engine") or local.get("engine") or "none",
            "local_status": chosen.get("local_status") or local.get("status") or "missing",
            "local_base_url": chosen.get("local_base_url") or local.get("base_url") or "",
            "local_ready": local_ok,
            "budget": chosen.get("budget", 0),
            "spent": chosen.get("spent", 0),
            "remaining": chosen.get("remaining", 0),
            "cost": chosen.get("cost", 1),
            "profile": chosen.get("profile") or "(unset)",
            "gab_key": gab_key,
            "routes": {
                t: {"lane": r.get("lane"), "ok": bool(r.get("ok")), "reason": r.get("reason") or ""}
                for t, r in routes.items()
            },
        },
    }


def apply_enabled(*, hid: str, state: Path | None = None, root_dir: Path | None = None, yes: bool = True) -> list[dict]:
    """Apply each enabled module onto ``hid`` using the hedge-chosen lane. Honest FAIL/STUB kept."""
    sel = load_selection(state)
    local = hedge.detect_local(root_dir)
    out = []
    for tid in sel["enabled"]:
        t = registry.toolset(tid, root_dir)
        if t is None:
            out.append({"toolset": tid, "live": "FAIL", "copy": "unknown module"})
            continue
        lanes = list(t.get("lanes") or ["local"])
        if "cloud" in lanes and "local" not in lanes:
            lane = "cloud"
        else:
            rec = hedge.decide("interactive" if "local" in lanes else "hard", local=local, state=state, root_dir=root_dir)
            lane = rec.get("lane") if rec.get("ok") else (lanes[0] if lanes else "local")
            if lane not in lanes:
                lane = lanes[0]
        p = toolsets.plan(tid, hid, lane, root_dir=root_dir, state=state)
        if p.get("ok") and yes:
            p = toolsets.apply(p, yes=True, state=state, root_dir=root_dir)
        out.append({"toolset": tid, "harness": hid, "lane": lane, "live": p.get("live"), "copy": p.get("copy"), "ok": p.get("ok")})
    return out
