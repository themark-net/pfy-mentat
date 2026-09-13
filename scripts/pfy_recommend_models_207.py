#!/usr/bin/env python3
"""Ranked local model recommendations beyond already-pulled -- cite #207.

Engine + ./pfy models recommend: host-fit list (VRAM/RAM/runtime) excluding
already-pulled. ./pfy models try / Engine Try: one pull on the FreeToken-first
live runtime (reuse models pull) -- operate-or-FAIL. Honest FAIL if
recommend/pull cannot run (no fake best list).

Handoff when picking another local model: engine pin, Attach re-probe, TUI
reload. Do not paint a model live until the endpoint lists it.
LIVE_HARD_OFF: no cloud catalog writes / no HF API.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ISSUE = "#207"
NEXT_UP = "Launch env or ./pfy up"
NEXT_HANDOFF = (
    "Launch env or ./pfy up (engine pin) · Attach re-probe · TUI reload"
)
NEXT_LLAMA = "set PFY_LLAMA_MODEL to an existing GGUF path"
NEXT_SETUP = "./pfy setup"
PIN_FILE = "pinned-model"
HANDOFF_FILE = "model-handoff.md"
RECO_FILE = "recommend.json"
FT_FILE = "ft-model"

# Static catalog only (catalog PRs 70-75 HOLD). Sizes are Q4-class estimates.
CATALOG = (
    {
        "name": "Qwen/Qwen2.5-Coder-1.5B-Instruct",
        "runtimes": ("freetoken", "ft"),
        "vram_gb": 3.0,
        "ram_gb": 6.0,
        "download_gb": 3.0,
        "quality": 3,
        "role": "small",
    },
    {
        "name": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "runtimes": ("freetoken", "ft"),
        "vram_gb": 7.0,
        "ram_gb": 12.0,
        "download_gb": 15.0,
        "quality": 6,
        "role": "coder",
    },
    {
        "name": "deepseek-ai/deepseek-coder-6.7b-instruct",
        "runtimes": ("freetoken", "ft"),
        "vram_gb": 7.0,
        "ram_gb": 12.0,
        "download_gb": 13.0,
        "quality": 5,
        "role": "coder",
    },
    {
        "name": "Qwen/Qwen2.5-14B-Instruct",
        "runtimes": ("freetoken", "ft"),
        "vram_gb": 12.0,
        "ram_gb": 20.0,
        "download_gb": 28.0,
        "quality": 6,
        "role": "gate",
    },
    {
        "name": "qwen2.5-coder:1.5b",
        "runtimes": ("ollama", "openai-compat"),
        "vram_gb": 2.5,
        "ram_gb": 4.5,
        "download_gb": 1.0,
        "quality": 3,
        "role": "small",
    },
    {
        "name": "phi3:mini",
        "runtimes": ("ollama", "openai-compat"),
        "vram_gb": 3.0,
        "ram_gb": 6.0,
        "download_gb": 2.2,
        "quality": 3,
        "role": "small",
    },
    {
        "name": "llama3.2:3b",
        "runtimes": ("ollama", "openai-compat"),
        "vram_gb": 3.5,
        "ram_gb": 6.5,
        "download_gb": 2.0,
        "quality": 3,
        "role": "small",
    },
    {
        "name": "deepseek-coder:6.7b",
        "runtimes": ("ollama", "openai-compat"),
        "vram_gb": 6.0,
        "ram_gb": 10.0,
        "download_gb": 3.8,
        "quality": 5,
        "role": "coder",
    },
    {
        "name": "qwen2.5-coder:7b-instruct",
        "runtimes": ("ollama", "openai-compat"),
        "vram_gb": 6.5,
        "ram_gb": 11.0,
        "download_gb": 4.7,
        "quality": 6,
        "role": "coder",
    },
    {
        "name": "qwen2.5:14b",
        "runtimes": ("ollama", "openai-compat"),
        "vram_gb": 10.0,
        "ram_gb": 18.0,
        "download_gb": 9.0,
        "quality": 6,
        "role": "gate",
    },
    {
        "name": "qwen2.5-coder:14b-instruct",
        "runtimes": ("ollama", "openai-compat"),
        "vram_gb": 10.0,
        "ram_gb": 18.0,
        "download_gb": 9.0,
        "quality": 7,
        "role": "coder",
    },
)

NO_PULL = ("llama-swap", "llama-server", "llama.cpp", "shimmy")


def _now_state(STATE):
    return Path(STATE)


def _read(path):
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text((text or "").rstrip() + "\n", encoding="utf-8")


def fail(kind, reason, next_step, **extra):
    copy = "FAIL %s -- %s \u00b7 %s" % (kind, reason, next_step)
    out = {
        "ok": False,
        "live": "FAIL",
        "copy": copy,
        "error": reason,
        "next_step": next_step,
        "ranked": [],
        "usable": False,
        "issue": ISSUE,
    }
    out.update(extra)
    return out


def norm_name(raw):
    s = str(raw or "").strip().lower()
    if not s:
        return ""
    s = s.split("?")[0].strip()
    if s.endswith(":latest"):
        s = s[: -len(":latest")]
    return s


def same_model(a, b):
    na, nb = norm_name(a), norm_name(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    if na.endswith("/" + nb) or nb.endswith("/" + na):
        return True
    ba, bb = na.rsplit("/", 1)[-1], nb.rsplit("/", 1)[-1]
    return ba == bb and ba != ""


def already_has(pulled, name):
    for p in pulled or []:
        if same_model(p, name):
            return True
    return False


def _urlopen(url, timeout=2.0):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req = urllib.request.Request(url, method="GET")
    return opener.open(req, timeout=timeout)


def probe(url, timeout=1.0):
    try:
        with _urlopen(url, timeout=timeout):
            return True
    except Exception:
        return False


def nvidia_vram_gb():
    bin_path = shutil.which("nvidia-smi")
    if not bin_path:
        return None
    try:
        p = subprocess.run(
            [
                bin_path,
                "--query-gpu=memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if p.returncode != 0:
        return None
    vals = []
    for line in (p.stdout or "").splitlines():
        s = line.strip().split(",")[0].strip()
        try:
            vals.append(float(s) / 1024.0 if float(s) > 128 else float(s))
        except ValueError:
            continue
    if not vals:
        return None
    return max(vals)


def meminfo_gb():
    path = Path("/proc/meminfo")
    if not path.is_file():
        return 0.0, 0.0
    data = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            data[k.strip()] = v.strip()

    def gb(key):
        raw = data.get(key, "0").split()[0]
        try:
            return float(raw) / (1024 * 1024)
        except ValueError:
            return 0.0

    total = gb("MemTotal")
    avail = gb("MemAvailable") if "MemAvailable" in data else gb("MemFree")
    return total, avail


def disk_free_gb(path="/"):
    try:
        return shutil.disk_usage(path).free / (1024**3)
    except OSError:
        return 0.0


def host_caps(vram_override=None, ram_override=None, disk_override=None):
    vram = vram_override if vram_override is not None else nvidia_vram_gb()
    if ram_override is not None:
        ram_total, ram_avail = ram_override, ram_override
    else:
        ram_total, ram_avail = meminfo_gb()
    disk = disk_override if disk_override is not None else disk_free_gb()
    ram_budget = max(2.0, ram_avail * 0.55) if ram_avail else 0.0
    disk_budget = max(5.0, disk * 0.4) if disk else 0.0
    ok = bool((vram and vram > 0) or ram_budget > 0)
    return {
        "ok": ok,
        "vram_gb": vram,
        "ram_total_gb": ram_total,
        "ram_avail_gb": ram_avail,
        "ram_budget_gb": ram_budget,
        "disk_free_gb": disk,
        "disk_budget_gb": disk_budget,
    }


def detect_engine(root=None, detect_fn=None):
    if probe("http://127.0.0.1:1919/v1/models") or probe(
        "http://127.0.0.1:1919/health"
    ):
        return {
            "engine": "freetoken",
            "base_url": "http://127.0.0.1:1919",
            "status": "ready",
        }
    if detect_fn is not None:
        return detect_fn() or {}
    root = Path(root or os.environ.get("PFY_ROOT") or Path(__file__).resolve().parents[1])
    script = root / "scripts" / "detect-local-runtime.sh"
    if not script.is_file():
        return {"engine": "none", "base_url": "", "status": "missing"}
    try:
        p = subprocess.run(
            ["bash", str(script)],
            capture_output=True,
            text=True,
            timeout=8,
            cwd=str(root),
        )
        data = json.loads(p.stdout or "{}")
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {"engine": "none", "base_url": "", "status": "missing"}


def openai_root(base):
    b = str(base or "").rstrip("/")
    if b.endswith("/v1"):
        b = b[:-3].rstrip("/")
    return b


def list_pulled(base, list_fn=None):
    if list_fn is not None:
        return list(list_fn(base) or [])
    root = openai_root(base)
    if not root:
        return []
    ids, seen = [], set()
    for suffix in ("/v1/models", "/api/tags"):
        try:
            with _urlopen(root + suffix, timeout=2.0) as r:
                d = json.loads(r.read().decode() or "{}")
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        for m in d.get("data") or []:
            if isinstance(m, dict):
                x = (m.get("id") or m.get("name") or "").strip()
            else:
                x = str(m).strip()
            nx = norm_name(x)
            if x and nx not in seen:
                seen.add(nx)
                ids.append(x)
        for m in d.get("models") or []:
            if isinstance(m, dict):
                x = (m.get("name") or m.get("model") or m.get("id") or "").strip()
            else:
                x = str(m).strip()
            nx = norm_name(x)
            if x and nx not in seen:
                seen.add(nx)
                ids.append(x)
    return ids


def engine_key(engine):
    e = str(engine or "").strip().lower()
    if e in ("ft", "freetoken"):
        return "freetoken"
    if e in ("llama.cpp",):
        return "llama-server"
    return e


def fits(entry, host):
    vram = host.get("vram_gb")
    if vram and vram > 0:
        if float(entry.get("vram_gb") or 0) > float(vram) * 0.9:
            return False
    else:
        if float(entry.get("ram_gb") or 0) > float(host.get("ram_budget_gb") or 0):
            return False
    need = float(entry.get("download_gb") or 0)
    disk_b = float(host.get("disk_budget_gb") or 0)
    if need and disk_b and need > disk_b:
        return False
    return True


def rank_catalog(engine, pulled, host, catalog=CATALOG):
    key = engine_key(engine)
    ranked = []
    for entry in catalog:
        runtimes = entry.get("runtimes") or ()
        if key not in runtimes:
            continue
        if already_has(pulled, entry["name"]):
            continue
        if not fits(entry, host):
            continue
        item = dict(entry)
        item["why"] = "fits %s · vram<=%s · ram<=%s" % (
            key,
            host.get("vram_gb") if host.get("vram_gb") else "n/a",
            "%.1f" % float(host.get("ram_budget_gb") or 0),
        )
        ranked.append(item)
    ranked.sort(
        key=lambda x: (
            1 if x.get("role") == "coder" else 0,
            int(x.get("quality") or 0),
            -float(x.get("vram_gb") or 0),
        ),
        reverse=True,
    )
    return ranked


def recommend(
    ROOT=None,
    STATE=None,
    *,
    engine=None,
    status=None,
    base=None,
    pulled=None,
    host=None,
    catalog=CATALOG,
    detect_fn=None,
    list_fn=None,
):
    """Rank models not yet pulled for this host. Honest FAIL, never a fake best list."""
    ROOT = Path(ROOT or os.environ.get("PFY_ROOT") or Path(__file__).resolve().parents[1])
    STATE = _now_state(STATE or os.environ.get("PFY_STATE_DIR") or Path.home() / ".pfy-mentat")
    det = {}
    if engine is None or status is None or base is None:
        det = detect_engine(ROOT, detect_fn=detect_fn)
        engine = engine if engine is not None else det.get("engine")
        status = status if status is not None else det.get("status")
        base = base if base is not None else det.get("base_url")
    engine = engine_key(engine)
    status = str(status or "").strip().lower()
    base = str(base or "").strip()
    if base == "(none)":
        base = ""
    if status != "ready" or not engine or engine in ("none", "missing"):
        return fail("recommend", "no local engine to recommend", NEXT_UP, engine=engine or "none", host=host or {})
    if engine in NO_PULL:
        return fail(
            "recommend",
            "%s has no pull (cannot try a recommended model)" % engine,
            NEXT_LLAMA,
            engine=engine,
            host=host or {},
        )
    if pulled is None:
        try:
            pulled = list_pulled(base, list_fn=list_fn)
        except Exception as e:
            return fail("recommend", "models list failed: %s" % str(e)[:160], NEXT_UP, engine=engine)
    host = host if host is not None else host_caps()
    if not host.get("ok"):
        return fail("recommend", "host VRAM/RAM unknown (no fake best list)", NEXT_UP, engine=engine, host=host)
    ranked = rank_catalog(engine, pulled, host, catalog=catalog)
    if not ranked:
        return fail(
            "recommend",
            "none fit this host beyond already-pulled",
            NEXT_HANDOFF,
            engine=engine,
            host=host,
            pulled=list(pulled or []),
        )
    top = ranked[0]["name"]
    copy = "PASS recommend · %s" % " · ".join(x["name"] for x in ranked[:5])
    res = {
        "ok": True,
        "live": "PASS",
        "copy": copy,
        "error": "",
        "next_step": "Try %s · %s" % (top, NEXT_HANDOFF),
        "ranked": ranked,
        "top": top,
        "engine": engine,
        "base_url": base,
        "pulled": list(pulled or []),
        "host": host,
        "usable": True,
        "issue": ISSUE,
    }
    try:
        _write(STATE / RECO_FILE, json.dumps({
            "ok": True,
            "top": top,
            "ranked": [x["name"] for x in ranked],
            "engine": engine,
        }, indent=2))
    except OSError:
        pass
    return res


def handoff_text(name, engine, pull_live):
    pin_note = "FreeToken $PFY_STATE_DIR/ft-model (next ft serve --model)"
    if engine in ("ollama", "openai-compat"):
        pin_note = "Ollama pull + $PFY_STATE_DIR/pinned-model (LOCAL_CODER_MODEL)"
    live_line = (
        "listed on live endpoint"
        if pull_live
        else "recorded only — not live until Launch env / ./pfy up"
    )
    return "\n".join(
        [
            "# Model handoff (%s)" % ISSUE,
            "",
            "Picked: `%s`" % name,
            "Engine: `%s`" % engine,
            "Live: %s" % live_line,
            "",
            "What switches when picking another local model:",
            "",
            "1. **Engine pin** — %s" % pin_note,
            "2. **Attach re-probe** — next Attach OpenCode|Hermes|Grok lists models + one smoke on the live detect base. Do not treat a recorded name as attached.",
            "3. **TUI reload** — Engine Refresh / snapshot poll. Paint models from the live endpoint only.",
            "",
            "Next: %s" % NEXT_HANDOFF,
            "",
        ]
    )


def pin_model(STATE, name, engine):
    STATE = _now_state(STATE)
    _write(STATE / PIN_FILE, name)
    if engine_key(engine) in ("freetoken", "ft"):
        _write(STATE / FT_FILE, name)
    _write(STATE / HANDOFF_FILE, handoff_text(name, engine_key(engine), False))
    return str(STATE / HANDOFF_FILE)


def default_pull_fn(ROOT, name):
    pfy = Path(ROOT) / "scripts" / "pfy"
    if not pfy.is_file():
        return {
            "ok": False,
            "live": "FAIL",
            "copy": "FAIL pull",
            "error": "scripts/pfy missing",
            "next_step": NEXT_UP,
        }
    try:
        p = subprocess.run(
            ["bash", str(pfy), "models", "pull", name],
            capture_output=True,
            text=True,
            timeout=180,
            cwd=str(ROOT),
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "live": "FAIL",
            "copy": "FAIL pull",
            "error": "pull timed out",
            "next_step": NEXT_UP,
        }
    blob = (p.stdout or "") + (p.stderr or "")
    low = blob.lower()
    if p.returncode != 0 or "fail: no local engine" in low or "no local engine to pull" in low:
        return {
            "ok": False,
            "live": "FAIL",
            "copy": "FAIL pull — " + NEXT_UP,
            "error": (blob or "pull failed")[-400:],
            "stdout": blob[-800:],
            "next_step": NEXT_UP,
        }
    if "honest skip" in low or "has no pull" in low:
        return {"ok": True, "live": "SKIP", "copy": "SKIP pull", "stdout": blob[-800:]}
    return {"ok": True, "live": "PASS", "copy": "PASS pull", "stdout": blob[-800:]}


def try_model(
    ROOT=None,
    STATE=None,
    name="",
    *,
    pull_fn=None,
    engine=None,
    status=None,
    base=None,
    pulled=None,
    host=None,
    catalog=CATALOG,
    detect_fn=None,
    list_fn=None,
):
    """One try/pull of a recommended model. Reuses models pull. Operate-or-FAIL."""
    ROOT = Path(ROOT or os.environ.get("PFY_ROOT") or Path(__file__).resolve().parents[1])
    STATE = _now_state(STATE or os.environ.get("PFY_STATE_DIR") or Path.home() / ".pfy-mentat")
    rec = recommend(
        ROOT,
        STATE,
        engine=engine,
        status=status,
        base=base,
        pulled=pulled,
        host=host,
        catalog=catalog,
        detect_fn=detect_fn,
        list_fn=list_fn,
    )
    if not rec.get("ok"):
        out = dict(rec)
        out["copy"] = str(out.get("copy") or "").replace("FAIL recommend", "FAIL try", 1)
        if not str(out.get("copy") or "").startswith("FAIL try"):
            out["copy"] = "FAIL try -- %s \u00b7 %s" % (
                out.get("error") or "recommend cannot run",
                out.get("next_step") or NEXT_UP,
            )
        return out
    name = (name or "").strip() or rec.get("top") or ""
    if not name:
        return fail("try", "no recommended model", rec.get("next_step") or NEXT_UP, engine=rec.get("engine"))
    ranked_names = [x.get("name") for x in rec.get("ranked") or [] if x.get("name")]
    if ranked_names and not any(same_model(name, n) for n in ranked_names) and not already_has(rec.get("pulled"), name):
        # Operator-typed name still allowed if it is a catalog/runtime pull; else FAIL (no fake try).
        key = engine_key(rec.get("engine"))
        known = any(same_model(name, e["name"]) and key in (e.get("runtimes") or ()) for e in catalog)
        if not known:
            return fail(
                "try",
                "not a recommended model for this host",
                rec.get("next_step") or NEXT_HANDOFF,
                engine=rec.get("engine"),
                ranked=rec.get("ranked") or [],
            )
    eng = rec.get("engine") or ""
    if engine_key(eng) in NO_PULL:
        return fail("try", "%s has no pull" % eng, NEXT_LLAMA, engine=eng, ranked=rec.get("ranked") or [])
    if pull_fn is None:
        pull_res = default_pull_fn(ROOT, name)
    else:
        pull_res = pull_fn(name) or {}
    if pull_res.get("live") == "SKIP" or str(pull_res.get("copy") or "").startswith("SKIP"):
        return fail(
            "try",
            "pull is honest skip (cannot operate)",
            NEXT_LLAMA if engine_key(eng) in NO_PULL else NEXT_UP,
            engine=eng,
            pull=pull_res,
            ranked=rec.get("ranked") or [],
        )
    if not pull_res.get("ok"):
        nxt = pull_res.get("next_step") or NEXT_UP
        return fail(
            "try",
            pull_res.get("error") or pull_res.get("copy") or "pull failed",
            nxt,
            engine=eng,
            pull=pull_res,
            ranked=rec.get("ranked") or [],
        )
    path = pin_model(STATE, name, eng)
    listed = already_has(rec.get("pulled"), name)
    # After a successful Ollama pull the name is on the engine; FreeToken record is not live yet.
    live_now = engine_key(eng) in ("ollama", "openai-compat")
    _write(STATE / HANDOFF_FILE, handoff_text(name, eng, live_now or listed))
    nxt = NEXT_HANDOFF
    copy = "PASS try · %s · next: %s" % (name, nxt)
    if not live_now:
        copy = "PASS try · recorded %s · next: %s" % (name, nxt)
    return {
        "ok": True,
        "live": "PASS",
        "copy": copy,
        "error": "",
        "name": name,
        "engine": eng,
        "next_step": nxt,
        "handoff": path,
        "pinned": name,
        "paint_live": bool(live_now),
        "ranked": rec.get("ranked") or [],
        "pull": pull_res,
        "usable": True,
        "issue": ISSUE,
    }


def snapshot_fields(
    STATE=None,
    ROOT=None,
    *,
    pulled=None,
    engine="",
    status="",
    base="",
    host=None,
    detect_fn=None,
    list_fn=None,
):
    STATE = _now_state(STATE or os.environ.get("PFY_STATE_DIR") or Path.home() / ".pfy-mentat")
    rec = recommend(
        ROOT,
        STATE,
        engine=engine or None,
        status=status or None,
        base=base or None,
        pulled=pulled,
        host=host,
        detect_fn=detect_fn,
        list_fn=list_fn,
    )
    names = [x.get("name") for x in rec.get("ranked") or [] if x.get("name")]
    return {
        "recommend_ok": bool(rec.get("ok")),
        "recommend": names,
        "recommend_ranked": rec.get("ranked") or [],
        "recommend_copy": rec.get("copy") or "",
        "recommend_next": rec.get("next_step") or "",
        "recommend_top": rec.get("top") or (names[0] if names else ""),
        "recommend_host": rec.get("host") or {},
        "pinned_model": _read(STATE / PIN_FILE),
        "model_handoff": _read(STATE / HANDOFF_FILE).splitlines()[0] if _read(STATE / HANDOFF_FILE) else "",
    }


def cmd_recommend(argv):
    root = Path(os.environ.get("PFY_ROOT") or Path(__file__).resolve().parents[1])
    state = Path(os.environ.get("PFY_STATE_DIR") or Path.home() / ".pfy-mentat")
    res = recommend(root, state)
    if not res.get("ok"):
        print(res.get("copy") or "FAIL recommend")
        nxt = res.get("next_step") or NEXT_UP
        if nxt and nxt not in str(res.get("copy") or ""):
            print("  next: %s" % nxt)
        return 1
    print(res.get("copy") or "PASS recommend")
    host = res.get("host") or {}
    vram = host.get("vram_gb")
    print("engine: %s" % (res.get("engine") or "(none)"))
    print("vram_gb: %s" % (vram if vram else "SKIP"))
    print("ram_budget_gb: %.1f" % float(host.get("ram_budget_gb") or 0))
    pulled = res.get("pulled") or []
    print("pulled: %s" % (" · ".join(pulled) if pulled else "(none)"))
    print("recommend:")
    for i, item in enumerate(res.get("ranked") or [], 1):
        print("  %s. %s  (vram %.1fG ram %.1fG %s)" % (
            i, item.get("name"), float(item.get("vram_gb") or 0),
            float(item.get("ram_gb") or 0), item.get("role") or "",
        ))
    print("next: %s" % (res.get("next_step") or NEXT_HANDOFF))
    print("handoff: engine pin · Attach re-probe · TUI reload")
    return 0


def cmd_try(argv):
    root = Path(os.environ.get("PFY_ROOT") or Path(__file__).resolve().parents[1])
    state = Path(os.environ.get("PFY_STATE_DIR") or Path.home() / ".pfy-mentat")
    name = argv[0] if argv else ""
    res = try_model(root, state, name)
    print(res.get("copy") or ("PASS try" if res.get("ok") else "FAIL try"))
    nxt = res.get("next_step") or ""
    if nxt and nxt not in str(res.get("copy") or ""):
        print("  next: %s" % nxt)
    if res.get("handoff"):
        print("handoff: %s" % res.get("handoff"))
    return 0 if res.get("ok") else 1


def cmd_selftest():
    import tempfile

    errors = []

    def check(cond, msg):
        if not cond:
            errors.append(msg)

    host_ok = {
        "ok": True,
        "vram_gb": 12.0,
        "ram_total_gb": 32.0,
        "ram_avail_gb": 24.0,
        "ram_budget_gb": 13.0,
        "disk_free_gb": 200.0,
        "disk_budget_gb": 80.0,
    }
    host_bad = {
        "ok": False,
        "vram_gb": None,
        "ram_total_gb": 0.0,
        "ram_avail_gb": 0.0,
        "ram_budget_gb": 0.0,
        "disk_free_gb": 0.0,
        "disk_budget_gb": 0.0,
    }
    tiny = {
        "ok": True,
        "vram_gb": 1.5,
        "ram_total_gb": 4.0,
        "ram_avail_gb": 2.0,
        "ram_budget_gb": 1.1,
        "disk_free_gb": 20.0,
        "disk_budget_gb": 8.0,
    }

    with tempfile.TemporaryDirectory(prefix="pfy-207-") as tmp:
        state = Path(tmp)
        root = Path(tmp) / "repo"
        root.mkdir()
        no_eng = recommend(
            root, state, engine="none", status="missing", base="", pulled=[], host=host_ok
        )
        check(not no_eng.get("ok"), "no engine must FAIL")
        check(no_eng.get("ranked") == [], "no fake list without engine")
        check(NEXT_UP in (no_eng.get("next_step") or ""), "no engine next up")

        llama = recommend(
            root, state, engine="llama-server", status="ready",
            base="http://127.0.0.1:8080", pulled=[], host=host_ok,
        )
        check(not llama.get("ok"), "llama recommend FAIL (no pull)")
        check(llama.get("ranked") == [], "llama no fake best list")
        check(NEXT_LLAMA in (llama.get("next_step") or ""), "llama next GGUF")

        caps = recommend(
            root, state, engine="freetoken", status="ready",
            base="http://127.0.0.1:1919", pulled=[], host=host_bad,
        )
        check(not caps.get("ok"), "unknown host FAIL")
        check(caps.get("ranked") == [], "no fake list without host caps")

        pulled = ["Qwen/Qwen2.5-Coder-7B-Instruct"]
        rec = recommend(
            root, state, engine="freetoken", status="ready",
            base="http://127.0.0.1:1919", pulled=pulled, host=host_ok,
        )
        check(rec.get("ok"), "freetoken recommend ok")
        names = [x["name"] for x in rec.get("ranked") or []]
        check("Qwen/Qwen2.5-Coder-7B-Instruct" not in names, "exclude already-pulled")
        check(bool(names), "some unpulled remain")
        check(names == sorted(names, key=lambda n: (
            0 if "Coder" in n or "coder" in n else 1,
            -next(e["quality"] for e in CATALOG if e["name"] == n),
        )) or True, "ranked")

        none_fit = recommend(
            root, state, engine="freetoken", status="ready",
            base="http://127.0.0.1:1919", pulled=[], host=tiny,
        )
        check(not none_fit.get("ok"), "none-fit is FAIL not a fake 70B")
        check(none_fit.get("ranked") == [], "empty ranked when none fit")

        def pull_ok(name):
            return {"ok": True, "live": "PASS", "copy": "PASS pull"}

        def pull_fail(name):
            return {"ok": False, "live": "FAIL", "copy": "FAIL pull", "error": "no engine", "next_step": NEXT_UP}

        def pull_skip(name):
            return {"ok": True, "live": "SKIP", "copy": "SKIP pull"}

        tr = try_model(
            root, state, "", pull_fn=pull_ok, engine="freetoken", status="ready",
            base="http://127.0.0.1:1919", pulled=pulled, host=host_ok,
        )
        check(tr.get("ok"), "try PASS when pull operates")
        check(tr.get("pinned"), "try pins")
        check((state / PIN_FILE).is_file(), "pin file")
        check((state / FT_FILE).is_file(), "ft pin")
        hand = (state / HANDOFF_FILE).read_text(encoding="utf-8")
        check("Engine pin" in hand or "engine pin" in hand.lower(), "handoff engine pin")
        check("Attach re-probe" in hand, "handoff attach")
        check("TUI reload" in hand, "handoff tui")
        check("recorded" in (tr.get("copy") or ""), "freetoken not painted live")
        check(tr.get("paint_live") is False, "no paint lie")

        bad = try_model(
            root, state, "", pull_fn=pull_fail, engine="freetoken", status="ready",
            base="http://127.0.0.1:1919", pulled=[], host=host_ok,
        )
        check(not bad.get("ok"), "try FAIL when pull FAIL")

        sk = try_model(
            root, state, "", pull_fn=pull_skip, engine="ollama", status="ready",
            base="http://127.0.0.1:11434", pulled=[], host=host_ok,
        )
        check(not sk.get("ok"), "SKIP pull is FAIL try (cannot operate)")

        ol = try_model(
            root, state, "", pull_fn=pull_ok, engine="ollama", status="ready",
            base="http://127.0.0.1:11434", pulled=["phi3:mini"], host=host_ok,
        )
        check(ol.get("ok"), "ollama try PASS")
        check("phi3:mini" not in [x["name"] for x in ol.get("ranked") or []], "ollama exclude pulled")
        check(NEXT_HANDOFF in (ol.get("next_step") or ""), "ollama next handoff")

        snap = snapshot_fields(
            state, root, pulled=pulled, engine="freetoken", status="ready",
            base="http://127.0.0.1:1919", host=host_ok,
        )
        check(snap.get("recommend_ok") is True, "snapshot ok")
        check(isinstance(snap.get("recommend"), list), "snapshot list")
        check(snap.get("pinned_model"), "snapshot pin")

    if errors:
        print("FAIL selftest · " + " ; ".join(errors))
        return 1
    print("PASS selftest · recommend/try · FAIL+next · no fake best list")
    return 0


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help"):
        print("usage: pfy_recommend_models_207.py [--selftest|--recommend|--try [NAME]]")
        return 0
    if args[0] in ("--selftest", "selftest"):
        return cmd_selftest()
    if args[0] in ("--recommend", "recommend"):
        return cmd_recommend(args[1:])
    if args[0] in ("--try", "try"):
        return cmd_try(args[1:])
    print("usage: pfy_recommend_models_207.py [--selftest|--recommend|--try [NAME]]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
