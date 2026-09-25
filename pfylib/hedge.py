"""Hedge policy: spend local compute first, cloud credits only when local can't (ADR-0017).

Inputs
  task    ``bulk`` | ``hard`` | ``interactive``
  local   ``{"engine","base_url","status"}`` from ``scripts/detect-local-runtime.sh``
          (``status == "ready"`` is the only value that counts as available)
  budget  ``PFY_CLOUD_BUDGET`` -- integer **credits** the operator allows for cloud
          lanes in this ledger period. Unit is operator-defined; by default one
          cloud decision costs ``PFY_CLOUD_TASK_COST`` credits (default 1).
          Unset/0 means: no cloud spend unless nothing else can run -- and then
          it still FAILs, because 0 remaining is 0.
  ledger  ``$PFY_STATE_DIR/hedge-ledger.json`` -- append-only spend entries.
  profile ``DEPLOY_PROFILE=local-only`` forbids cloud outright (ADR-0006/0011).

Rules (deterministic, offline)
  1. ``hard``  -> cloud if budget remains, else local if ready, else FAIL.
  2. others    -> local if ready, else cloud if budget remains, else FAIL.
  3. FAIL always carries a next step; the policy never fakes a lane.
"""
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from . import registry

TASKS = ("bulk", "hard", "interactive")
LANES = ("local", "cloud")
LEDGER_FILE = "hedge-ledger.json"
DEFAULT_TASK_COST = 1


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _int_env(key: str, default: int) -> int:
    raw = str(os.environ.get(key) or "").strip()
    if not raw:
        return default
    try:
        return max(0, int(raw))
    except ValueError:
        return default


def budget_from_env() -> int:
    return _int_env("PFY_CLOUD_BUDGET", 0)


def task_cost() -> int:
    return max(1, _int_env("PFY_CLOUD_TASK_COST", DEFAULT_TASK_COST))


def profile() -> str:
    return str(os.environ.get("DEPLOY_PROFILE") or "").strip().lower()


# ---------------------------------------------------------------- detect ---

def detect_local(root_dir: Path | None = None, *, timeout: float = 6.0) -> dict:
    """Run scripts/detect-local-runtime.sh; any failure is an honest ``missing``."""
    script = registry.root(root_dir) / "scripts" / "detect-local-runtime.sh"
    missing = {"engine": "none", "base_url": "", "status": "missing"}
    if not script.is_file():
        return dict(missing, error="detector missing")
    try:
        p = subprocess.run(["bash", str(script)], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as e:
        return dict(missing, error=str(e)[:120])
    try:
        data = json.loads((p.stdout or "").strip().splitlines()[-1])
    except (ValueError, IndexError):
        return dict(missing, error="detector output not JSON")
    if not isinstance(data, dict):
        return missing
    return {
        "engine": str(data.get("engine") or "none"),
        "base_url": str(data.get("base_url") or ""),
        "status": str(data.get("status") or "missing"),
    }


# ---------------------------------------------------------------- ledger ---

def ledger_path(state: Path | None = None) -> Path:
    return registry.state_dir(state) / LEDGER_FILE


def load_ledger(state: Path | None = None) -> dict:
    path = ledger_path(state)
    empty = {"version": 1, "entries": [], "spent": 0}
    if not path.is_file():
        return empty
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(empty, error="ledger unreadable; treating as empty")
    if not isinstance(data, dict):
        return empty
    entries = [e for e in (data.get("entries") or []) if isinstance(e, dict)]
    spent = sum(int(e.get("amount") or 0) for e in entries if e.get("lane") == "cloud")
    return {"version": 1, "entries": entries, "spent": spent}


def save_ledger(ledger: dict, state: Path | None = None) -> Path:
    path = ledger_path(state)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "updated": _now(),
        "spent": int(ledger.get("spent") or 0),
        "entries": list(ledger.get("entries") or []),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def record(amount: int, *, lane: str = "cloud", task: str = "", note: str = "", state: Path | None = None, budget: int | None = None) -> dict:
    """Append a spend entry; returns remaining budget. Local entries cost 0 credits."""
    if lane not in LANES:
        return {"ok": False, "live": "FAIL", "error": "unknown lane %r" % lane, "next_step": "lane must be local|cloud"}
    amount = max(0, int(amount)) if lane == "cloud" else 0
    ledger = load_ledger(state)
    ledger["entries"].append({"when": _now(), "lane": lane, "task": task, "amount": amount, "note": note})
    ledger["spent"] = int(ledger.get("spent") or 0) + amount
    save_ledger(ledger, state)
    budget = budget_from_env() if budget is None else int(budget)
    remaining = max(0, budget - ledger["spent"])
    return {
        "ok": True,
        "live": "READY",
        "lane": lane,
        "amount": amount,
        "spent": ledger["spent"],
        "budget": budget,
        "remaining": remaining,
        "ledger": str(ledger_path(state)),
        "copy": "READY hedge record · %s %d · spent %d / budget %d · remaining %d" % (lane, amount, ledger["spent"], budget, remaining),
    }


def reset_ledger(state: Path | None = None) -> Path:
    return save_ledger({"entries": [], "spent": 0}, state)


# ---------------------------------------------------------------- decide ---

def decide(
    task: str,
    *,
    local: dict | None = None,
    budget: int | None = None,
    state: Path | None = None,
    cost: int | None = None,
    deploy_profile: str | None = None,
    root_dir: Path | None = None,
) -> dict:
    """Pick ``local`` or ``cloud`` for one task, or FAIL with a next step."""
    task = str(task or "").strip().lower()
    if task not in TASKS:
        return {
            "ok": False,
            "live": "FAIL",
            "lane": None,
            "task": task,
            "reason": "unknown task class %r" % task,
            "next_step": "use --task %s" % "|".join(TASKS),
            "copy": "FAIL hedge -- unknown task class %r · use %s" % (task, "|".join(TASKS)),
        }
    local = dict(local) if local is not None else detect_local(root_dir)
    local_ok = str(local.get("status") or "").lower() == "ready"
    budget = budget_from_env() if budget is None else max(0, int(budget))
    cost = task_cost() if cost is None else max(1, int(cost))
    prof = profile() if deploy_profile is None else str(deploy_profile).lower()
    ledger = load_ledger(state)
    spent = int(ledger.get("spent") or 0)
    remaining = max(0, budget - spent)
    cloud_ok = remaining >= cost and prof != "local-only"

    base = {
        "task": task,
        "local_engine": local.get("engine") or "none",
        "local_status": local.get("status") or "missing",
        "local_base_url": local.get("base_url") or "",
        "budget": budget,
        "spent": spent,
        "remaining": remaining,
        "cost": cost,
        "profile": prof or "(unset)",
        "ledger": str(ledger_path(state)),
    }

    def ready(lane: str, reason: str) -> dict:
        return dict(
            base,
            ok=True,
            live="READY",
            lane=lane,
            reason=reason,
            next_step="",
            copy="READY hedge · lane=%s · %s · remaining %d/%d" % (lane, reason, remaining, budget),
        )

    def fail(reason: str, next_step: str) -> dict:
        return dict(
            base,
            ok=False,
            live="FAIL",
            lane=None,
            reason=reason,
            next_step=next_step,
            copy="FAIL hedge -- %s · %s" % (reason, next_step),
        )

    local_word = "local ready (%s)" % base["local_engine"] if local_ok else "local %s" % base["local_status"]
    if task == "hard":
        if cloud_ok:
            return ready("cloud", "hard task; cloud within budget; %s as hedge" % local_word)
        if local_ok:
            why = "profile local-only" if prof == "local-only" else "no cloud budget (remaining %d < cost %d)" % (remaining, cost)
            return ready("local", "hard task but %s; hedging on %s" % (why, local_word))
        return fail(
            "hard task; %s; cloud unavailable (%s)" % (local_word, "profile local-only" if prof == "local-only" else "remaining %d < cost %d" % (remaining, cost)),
            "./pfy up (start local runtime) or set PFY_CLOUD_BUDGET",
        )
    if local_ok:
        return ready("local", "%s task; %s" % (task, local_word))
    if cloud_ok:
        return ready("cloud", "%s task; local %s; spending cloud credits" % (task, base["local_status"]))
    return fail(
        "%s task; local %s; cloud unavailable (%s)" % (task, base["local_status"], "profile local-only" if prof == "local-only" else "remaining %d < cost %d" % (remaining, cost)),
        "./pfy up (start local runtime) or set PFY_CLOUD_BUDGET",
    )


def decide_and_record(task: str, **kw) -> dict:
    """decide(); if the lane is cloud, debit one task cost into the ledger."""
    state = kw.get("state")
    rec = decide(task, **kw)
    if rec.get("ok") and rec.get("lane") == "cloud":
        r = record(int(rec.get("cost") or 1), lane="cloud", task=task, note="decide_and_record", state=state, budget=rec.get("budget"))
        rec["recorded"] = r.get("amount")
        rec["spent"] = r.get("spent")
        rec["remaining"] = r.get("remaining")
    return rec
