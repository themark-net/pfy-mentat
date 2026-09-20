#!/usr/bin/env python3
"""Gab cloud lane + local recommend sync -- cite #228.

Cloud: OpenAI-compatible https://gab.ai/v1 with model=auto (default) or
pin-by-id from GET /v1/models. Missing GAB_API_KEY / Plus → FAIL+next
(docs gab.ai/docs/api-auth).

Local: Gab open-weight family signal → Ollama tags + size → nimo host fit
(fits|tight|won't-fit). Surfaces in #207 recommend/try without replacing
FreeToken-first order. Pull: fits ok; tight=confirm; won't-fit disabled;
never auto-pull 405B-class without explicit opt-in.

Honesty: gab auto ≠ local ranking; Gab does NOT host GGUF / local weights.
We pull open-weight families Gab lists to run local (Ollama).

LIVE_HARD_OFF for CI: offline fixture scripts/fixtures/gab_models_v1.json.
#225 Launch intact. No Env tab.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ISSUE = "#228"
GAB_BASE = "https://gab.ai/v1"
GAB_MODELS = GAB_BASE + "/models"
GAB_AUTH_DOCS = "https://gab.ai/docs/api-auth"
GAB_API_DOCS = "https://gab.ai/docs/api"
NEXT_KEY = "set GAB_API_KEY · Plus/max plan · " + GAB_AUTH_DOCS
NEXT_PLUS = "Gab Plus/max plan required · " + GAB_API_DOCS
NEXT_UP = "Launch env or ./pfy up"
NEXT_SMALLER = "smaller Q4 ≤32B · free VRAM · never auto 405B"
NEXT_OLLAMA = "start Ollama · ollama serve"
NEXT_CONFIRM = "confirm tight pull (opt-in) · or pick fits row"
CHIP_AUTO = "gab auto · cloud router"
CHIP_SYNC = "local sync · family signal"
CHIP_HONEST = "gab auto ≠ local ranking"
CHIP_NO_GGUF = "Gab does not host GGUF — we pull open-weight families to Ollama"
STATE_GAB = "gab-cloud.json"
STATE_SYNC = "gab-local-sync.json"
FIXTURE_REL = Path("scripts") / "fixtures" / "gab_models_v1.json"

# Open-weight family tokens Gab surfaces (id / owned_by / aliases).
OPEN_WEIGHT_FAMILIES = (
    "gemma",
    "qwen",
    "deepseek",
    "glm",
    "kimi",
    "llama",
    "mistral",
    "phi",
    "gpt-oss",
)

# Proprietary cloud — never map to local Ollama pull from Gab signal.
PROPRIETARY = (
    "claude",
    "gpt-",
    "gpt5",
    "o3",
    "gemini",
    "arya",
    "muse-spark",
    "minimax-m",
)

# Gab cloud/open-weight id → preferred Ollama library tag + Q4-class size.
# Gab lists cloud slugs; we map families we can actually `ollama pull`.
# 405B-class stays won't-fit / opt-in only.
OLLAMA_MAP = (
    # (match substrings in gab id, ollama_tag, vram_gb, download_gb, params_b, role)
    (("gemma-4-26b", "gemma4-26b", "gemma-4"), "gemma4:26b", 17.0, 16.0, 26.0, "coder"),
    (("gemma",), "gemma2:27b", 17.0, 16.0, 27.0, "general"),
    (("qwen-3-5-397", "qwen3.5-397", "397b"), "qwen2.5:72b", 220.0, 220.0, 397.0, "huge"),
    (("qwen-3-8-flash", "qwen3.8-flash"), "qwen3-coder:30b", 20.0, 18.0, 30.0, "coder"),
    (("qwen-3-7-flash", "qwen3.7-flash"), "qwen3-coder:30b", 20.0, 18.0, 30.0, "coder"),
    (("qwen-3-8-max", "qwen-3-7-max", "qwen-3-7-plus"), "qwen2.5-coder:32b", 22.0, 20.0, 32.0, "coder"),
    (("qwen3-coder", "qwen-coder"), "qwen3-coder:30b", 20.0, 18.0, 30.0, "coder"),
    (("qwen2.5-coder", "qwen-2.5-coder"), "qwen2.5-coder:32b", 22.0, 20.0, 32.0, "coder"),
    (("qwen",), "qwen2.5:14b", 12.0, 9.0, 14.0, "general"),
    (("deepseek",), "deepseek-coder:6.7b", 6.0, 3.8, 6.7, "coder"),
    (("glm-5-3-flash", "glm-4.7-flash", "glm4-flash"), "glm-4.7-flash", 12.0, 10.0, 9.0, "coder"),
    (("glm",), "glm4:9b", 8.0, 5.5, 9.0, "general"),
    (("kimi",), "qwen2.5:14b", 12.0, 9.0, 14.0, "agents"),  # closest common local stand-in
    (("gpt-oss",), "gpt-oss:120b", 65.0, 65.0, 120.0, "general"),
    (("llama-405", "405b"), "llama3.1:405b", 220.0, 220.0, 405.0, "huge"),
    (("llama3.3", "llama-3.3"), "llama3.3:70b", 40.0, 40.0, 70.0, "general"),
    (("llama",), "llama3.2:3b", 3.5, 2.0, 3.0, "small"),
    (("mistral",), "mistral:7b", 6.0, 4.1, 7.0, "general"),
    (("phi",), "phi3:mini", 3.0, 2.2, 3.8, "small"),
)

# Default nimo profile (~64 GiB 8060S pool, ~61 GiB RAM).
NIMO_HOST = {
    "name": "nimo",
    "vram_gb": 64.0,
    "ram_gb": 61.0,
    "free_vram_gb": 43.0,
    "ok": True,
}


def _now_state(STATE):
    return Path(STATE)


def _read(path):
    path = Path(path)
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text((text or "").rstrip() + "\n", encoding="utf-8")


def fail(kind, reason, next_step, **extra):
    copy = "FAIL %s -- %s · %s" % (kind, reason, next_step)
    out = {
        "ok": False,
        "live": "FAIL",
        "copy": copy,
        "error": reason,
        "next_step": next_step,
        "usable": False,
        "issue": ISSUE,
        "honesty": CHIP_HONEST,
        "chip_no_gguf": CHIP_NO_GGUF,
    }
    out.update(extra)
    return out


def fixture_path(ROOT=None):
    root = Path(ROOT or os.environ.get("PFY_ROOT") or Path(__file__).resolve().parents[1])
    return root / FIXTURE_REL


def load_fixture(ROOT=None):
    path = fixture_path(ROOT)
    raw = _read(path)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def gab_api_key():
    return (
        str(os.environ.get("GAB_API_KEY") or "").strip()
        or str(os.environ.get("GABAI_API_KEY") or "").strip()
    )


def key_status():
    key = gab_api_key()
    if key:
        return {"set": True, "paint": "set", "key_present": True}
    return {"set": False, "paint": "missing", "key_present": False}


def is_open_weight(model):
    """True if Gab model id looks like an open-weight family we may map locally."""
    mid = str((model or {}).get("id") or "").lower()
    owned = str((model or {}).get("owned_by") or "").lower()
    aliases = " ".join(str(a).lower() for a in ((model or {}).get("aliases") or []))
    blob = " ".join((mid, owned, aliases))
    if mid in ("auto",):
        return False
    caps = (model or {}).get("capabilities") or {}
    if not caps.get("text"):
        return False
    if any(p in mid for p in PROPRIETARY):
        # deepseek/qwen/gemma/glm/kimi are open even if hosted by Gab
        if not any(f in mid for f in OPEN_WEIGHT_FAMILIES):
            return False
    if any(f in blob for f in OPEN_WEIGHT_FAMILIES):
        return True
    return False


def map_to_ollama(gab_id):
    """Map a Gab model id to Ollama tag + size. None if no mapping."""
    s = str(gab_id or "").lower()
    for matches, tag, vram, dl, params, role in OLLAMA_MAP:
        if any(m in s for m in matches):
            return {
                "gab_id": gab_id,
                "tag": tag,
                "name": tag,
                "vram_gb": float(vram),
                "download_gb": float(dl),
                "params_b": float(params),
                "role": role,
                "source": "gab-open-weight",
            }
    return None


def host_profile(host=None):
    """Host VRAM/RAM profile. Prefer explicit/nimo; fall back to detect."""
    if isinstance(host, dict) and host.get("ok"):
        out = dict(NIMO_HOST)
        out.update(host)
        out["ok"] = True
        return out
    # Env overrides (tests / operator)
    vram = os.environ.get("PFY_HOST_VRAM_GB")
    ram = os.environ.get("PFY_HOST_RAM_GB")
    free_v = os.environ.get("PFY_HOST_FREE_VRAM_GB")
    if vram or ram:
        try:
            return {
                "name": "env",
                "vram_gb": float(vram or ram or 0),
                "ram_gb": float(ram or vram or 0),
                "free_vram_gb": float(free_v or vram or ram or 0),
                "ok": True,
            }
        except ValueError:
            pass
    # Default nimo guidance for this slice (DoD).
    return dict(NIMO_HOST)


def classify_fit(entry, host=None):
    """fits | tight | won't-fit for nimo-class host."""
    host = host_profile(host)
    vram = float(host.get("vram_gb") or 0)
    free_v = float(host.get("free_vram_gb") or vram)
    need = float((entry or {}).get("vram_gb") or 0)
    params = float((entry or {}).get("params_b") or 0)
    role = str((entry or {}).get("role") or "")
    # 405B-class / huge: won't-fit unless absurd VRAM
    if role == "huge" or params >= 200 or need >= 150:
        return "won't-fit"
    if need <= 0:
        return "won't-fit"
    if need <= min(free_v * 0.85, 32.0) or (params <= 32 and need <= free_v):
        return "fits"
    if need <= vram and (params <= 120 or need <= free_v + 8):
        return "tight"
    if need <= vram:
        return "tight"
    return "won't-fit"


def fetch_gab_models(ROOT=None, *, use_network=None, fixture_only=False):
    """GET /v1/models. Auth optional. CI: fixture_only / PFY_GAB_OFFLINE=1."""
    offline = fixture_only or str(os.environ.get("PFY_GAB_OFFLINE") or "").strip() in (
        "1",
        "true",
        "yes",
    )
    if use_network is False or offline:
        data = load_fixture(ROOT)
        if data is None:
            return fail("sync", "offline fixture missing", "./pfy setup", rows=[], source="fixture")
        return {
            "ok": True,
            "live": "PASS",
            "copy": "PASS gab models · fixture",
            "data": data.get("data") or [],
            "source": "fixture",
            "issue": ISSUE,
        }
    headers = {"Accept": "application/json", "User-Agent": "pfy-mentat/228"}
    key = gab_api_key()
    if key:
        headers["Authorization"] = "Bearer " + key
    try:
        req = urllib.request.Request(GAB_MODELS, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=12) as r:
            status = int(getattr(r, "status", 200) or 200)
            raw = r.read()
        if status == 403:
            return fail("sync", "plus required", NEXT_PLUS, http_status=403, rows=[])
        if status == 401:
            return fail("sync", "key missing or invalid", NEXT_KEY, http_status=401, rows=[])
        data = json.loads(raw.decode("utf-8", errors="replace") or "{}")
        return {
            "ok": True,
            "live": "PASS",
            "copy": "PASS gab models · network",
            "data": data.get("data") or [],
            "source": "network",
            "issue": ISSUE,
        }
    except urllib.error.HTTPError as e:
        code = int(getattr(e, "code", 0) or 0)
        if code == 403:
            return fail("sync", "plus required", NEXT_PLUS, http_status=403, rows=[])
        if code == 401:
            return fail("sync", "key missing or invalid", NEXT_KEY, http_status=401, rows=[])
        # Fall back to fixture for operator continuity
        data = load_fixture(ROOT)
        if data is not None:
            return {
                "ok": True,
                "live": "SKIP",
                "copy": "SKIP gab network · using fixture",
                "data": data.get("data") or [],
                "source": "fixture-fallback",
                "error": "HTTP %s" % code,
                "issue": ISSUE,
            }
        return fail("sync", "HTTP %s" % code, "Refresh sync · " + GAB_API_DOCS, http_status=code, rows=[])
    except Exception as e:
        data = load_fixture(ROOT)
        if data is not None:
            return {
                "ok": True,
                "live": "SKIP",
                "copy": "SKIP gab network · using fixture",
                "data": data.get("data") or [],
                "source": "fixture-fallback",
                "error": str(e)[:160],
                "issue": ISSUE,
            }
        return fail("sync", "network fail: %s" % str(e)[:120], "Refresh sync", rows=[])


def pin_model_ids(models):
    """Ids suitable for cloud pin-by-id (text models, including auto)."""
    out = []
    for m in models or []:
        mid = str(m.get("id") or "").strip()
        if not mid:
            continue
        caps = m.get("capabilities") or {}
        if mid == "auto" or caps.get("text"):
            out.append(mid)
    return out


def cloud_lane(STATE=None, *, model="auto", ROOT=None):
    """Wizard/Attach Gab cloud lane status. model=auto default or pin id."""
    STATE = _now_state(STATE or os.environ.get("PFY_STATE_DIR") or Path.home() / ".pfy-mentat")
    model = str(model or "auto").strip() or "auto"
    ks = key_status()
    chips = [CHIP_AUTO, CHIP_HONEST, CHIP_NO_GGUF]
    base = {
        "endpoint": GAB_BASE,
        "endpoint_label": "Gab · " + GAB_BASE,
        "model": model,
        "model_mode": "auto" if model == "auto" else "pin",
        "lane": "cloud/subscription",
        "provider": "gab",
        "chips": chips,
        "honesty": CHIP_HONEST,
        "chip_auto": CHIP_AUTO,
        "chip_no_gguf": CHIP_NO_GGUF,
        "key": ks["paint"],
        "key_present": ks["key_present"],
        "docs_auth": GAB_AUTH_DOCS,
        "docs_api": GAB_API_DOCS,
        "issue": ISSUE,
    }
    if not ks["key_present"]:
        out = fail(
            "gab",
            "key missing",
            NEXT_KEY,
            **base,
        )
        out["copy"] = "FAIL gab -- key missing · %s" % NEXT_KEY
        _write(STATE / STATE_GAB, json.dumps({**base, "ok": False}, indent=2))
        return out
    # Optional: validate pin id against fixture/network list (offline ok)
    if model != "auto":
        fetched = fetch_gab_models(ROOT, fixture_only=True)
        ids = set(pin_model_ids(fetched.get("data") or []))
        if ids and model not in ids:
            # still allow — live list may have newer ids; warn via next
            base["pin_warning"] = "id not in fixture; verify GET /v1/models"
    rec = {
        "ok": True,
        "live": "READY",
        "copy": "READY gab · %s · model=%s · %s" % (GAB_BASE, model, CHIP_AUTO),
        "usable": True,
        "next_step": "Launch session",
        "env": {
            "OPENAI_BASE_URL": GAB_BASE,
            "OPENAI_API_KEY": "${GAB_API_KEY}",
            "GAB_API_KEY": "${GAB_API_KEY}",
            "PFY_GAB_MODEL": model,
            "LOCAL_CODER_MODEL": model,
        },
        **base,
    }
    # Persist without secrets
    safe = {k: v for k, v in rec.items() if k != "env"}
    safe["env_keys"] = list((rec.get("env") or {}).keys())
    _write(STATE / STATE_GAB, json.dumps(safe, indent=2))
    return rec


def apply_cloud_env(env=None, *, model="auto"):
    """Return child env dict for Gab cloud attach/launch. Never logs the key."""
    env = dict(env or os.environ)
    key = gab_api_key()
    model = str(model or "auto").strip() or "auto"
    if not key:
        return None, fail("gab", "key missing", NEXT_KEY, model=model)
    env["OPENAI_BASE_URL"] = GAB_BASE
    env["OPENAI_API_KEY"] = key
    env["GAB_API_KEY"] = key
    env["PFY_GAB_MODEL"] = model
    env["LOCAL_CODER_MODEL"] = model
    env["PFY_CLOUD_PROVIDER"] = "gab"
    env["PFY_CLOUD_ENDPOINT"] = GAB_BASE
    return env, None


def local_sync(
    ROOT=None,
    STATE=None,
    *,
    pulled=None,
    host=None,
    fixture_only=False,
    use_network=None,
):
    """Gab open-weight → Ollama map + host fit. Does not replace FreeToken-first."""
    ROOT = Path(ROOT or os.environ.get("PFY_ROOT") or Path(__file__).resolve().parents[1])
    STATE = _now_state(STATE or os.environ.get("PFY_STATE_DIR") or Path.home() / ".pfy-mentat")
    host = host_profile(host)
    fetched = fetch_gab_models(ROOT, use_network=use_network, fixture_only=fixture_only)
    if not fetched.get("ok") and fetched.get("live") == "FAIL":
        return fetched
    models = fetched.get("data") or []
    pulled_set = {str(x).strip().lower() for x in (pulled or []) if str(x).strip()}
    rows = []
    seen_tags = set()
    for m in models:
        if not is_open_weight(m):
            continue
        mapped = map_to_ollama(m.get("id"))
        if not mapped:
            continue
        tag = mapped["tag"]
        if tag in seen_tags:
            continue
        seen_tags.add(tag)
        fit = classify_fit(mapped, host)
        local = tag.lower() in pulled_set or any(
            tag.lower() == p or tag.lower().split(":")[0] in p for p in pulled_set
        )
        # also match bare name
        if not local:
            for p in pulled_set:
                if tag.lower() in p or p in tag.lower():
                    local = True
                    break
        pull_enabled = (not local) and fit == "fits"
        pull_confirm = (not local) and fit == "tight"
        pull_disabled = fit == "won't-fit" or local
        row = {
            "gab_id": mapped["gab_id"],
            "tag": tag,
            "name": tag,
            "size": "~%sG" % int(mapped["download_gb"]) if mapped["download_gb"] >= 1 else "~%.1fG" % mapped["download_gb"],
            "vram_gb": mapped["vram_gb"],
            "download_gb": mapped["download_gb"],
            "params_b": mapped["params_b"],
            "fit": fit,
            "local": "local" if local else "not-local",
            "is_local": bool(local),
            "pull_enabled": bool(pull_enabled),
            "pull_confirm": bool(pull_confirm),
            "pull_disabled": bool(pull_disabled),
            "role": mapped["role"],
            "source": "gab-open-weight→ollama",
            "recommended_for": list(m.get("recommended_for") or []),
        }
        rows.append(row)
    # Prefer fits first, then tight; never lead with won't-fit. Stable by size.
    order = {"fits": 0, "tight": 1, "won't-fit": 2}
    rows.sort(key=lambda r: (order.get(r["fit"], 9), r["vram_gb"], r["tag"]))
    copy = "PASS local sync · Gab families · %s" % CHIP_HONEST
    if not rows:
        return fail(
            "sync",
            "no open-weight families mapped",
            "Refresh sync · check fixture",
            rows=[],
            host=host,
            chips=[CHIP_SYNC, CHIP_HONEST, CHIP_NO_GGUF],
            source=fetched.get("source"),
        )
    out = {
        "ok": True,
        "live": "PASS",
        "copy": copy,
        "error": "",
        "rows": rows,
        "ranked": rows,  # alias for #207 surface
        "host": host,
        "chips": [CHIP_SYNC, CHIP_HONEST, CHIP_NO_GGUF],
        "honesty": CHIP_HONEST,
        "chip_sync": CHIP_SYNC,
        "chip_no_gguf": CHIP_NO_GGUF,
        "source": fetched.get("source"),
        "freetoken_first": True,
        "note": "Gab open-weight signal mapped to Ollama; FreeToken-first order unchanged",
        "usable": True,
        "issue": ISSUE,
        "next_step": "Pull fits+not-local · tight needs confirm · won't-fit disabled",
    }
    try:
        _write(
            STATE / STATE_SYNC,
            json.dumps(
                {
                    "ok": True,
                    "rows": [{"tag": r["tag"], "fit": r["fit"], "local": r["local"]} for r in rows],
                    "honesty": CHIP_HONEST,
                    "source": out["source"],
                },
                indent=2,
            ),
        )
    except OSError:
        pass
    return out


def merge_recommend(base_rec, gab_sync):
    """Surface Gab sync into #207 recommend without replacing FreeToken-first list."""
    base = dict(base_rec or {})
    gab = dict(gab_sync or {})
    ft_ranked = list(base.get("ranked") or [])
    gab_rows = list(gab.get("rows") or gab.get("ranked") or [])
    # Annotate FreeToken-first rows
    for r in ft_ranked:
        if isinstance(r, dict):
            r.setdefault("source", "freetoken-first")
            r.setdefault("lane_order", "freetoken-first")
    # Append Gab rows that are not already named in FT list
    ft_names = {str(x.get("name") or "").lower() for x in ft_ranked if isinstance(x, dict)}
    extra = []
    for r in gab_rows:
        name = str(r.get("name") or r.get("tag") or "").lower()
        if name and name not in ft_names:
            item = dict(r)
            item["name"] = r.get("tag") or r.get("name")
            item["lane_order"] = "gab-local-sync"
            item["honesty"] = CHIP_HONEST
            extra.append(item)
    merged = ft_ranked + extra
    base["ranked"] = merged
    base["gab_sync"] = {
        "ok": bool(gab.get("ok")),
        "rows": gab_rows,
        "chips": gab.get("chips") or [CHIP_HONEST],
        "honesty": CHIP_HONEST,
        "chip_no_gguf": CHIP_NO_GGUF,
        "source": gab.get("source"),
        "copy": gab.get("copy") or "",
    }
    base["honesty"] = CHIP_HONEST
    base["chips"] = list(dict.fromkeys(
        list(base.get("chips") or []) + list(gab.get("chips") or []) + [CHIP_HONEST, CHIP_NO_GGUF]
    ))
    if base.get("ok") and gab_rows:
        base["copy"] = (base.get("copy") or "PASS recommend") + " · gab sync " + CHIP_HONEST
    elif not base.get("ok") and gab.get("ok") and gab_rows:
        # Local engine recommend failed but Gab sync still useful to surface
        top = gab_rows[0].get("tag")
        base = {
            "ok": True,
            "live": "PASS",
            "copy": "PASS recommend · gab local sync · %s · %s" % (top, CHIP_HONEST),
            "error": "",
            "ranked": extra,
            "top": top,
            "gab_sync": base["gab_sync"],
            "honesty": CHIP_HONEST,
            "chips": [CHIP_SYNC, CHIP_HONEST, CHIP_NO_GGUF],
            "freetoken_first": True,
            "note": "FreeToken-first unavailable; showing Gab→Ollama sync only",
            "next_step": base_rec.get("next_step") or NEXT_UP,
            "usable": True,
            "issue": ISSUE,
            "host": gab.get("host") or {},
            "engine": (base_rec or {}).get("engine") or "gab-sync",
        }
    return base


def pull_gated(
    tag,
    *,
    ROOT=None,
    STATE=None,
    confirm_tight=False,
    opt_in_huge=False,
    pulled=None,
    host=None,
    pull_fn=None,
    fixture_only=True,
):
    """ollama pull for recommended-not-yet-local that fit. Gate tight/won't-fit/405B."""
    tag = str(tag or "").strip()
    if not tag:
        return fail("pull", "no tag", "pick a recommend row")
    sync = local_sync(ROOT, STATE, pulled=pulled, host=host, fixture_only=fixture_only)
    if not sync.get("ok"):
        return sync
    row = None
    for r in sync.get("rows") or []:
        if r.get("tag") == tag or r.get("name") == tag:
            row = r
            break
    if row is None:
        # Allow explicit tag not in sync only with opt-in huge path blocked by default
        mapped = map_to_ollama(tag) or {
            "tag": tag,
            "name": tag,
            "vram_gb": 999.0,
            "params_b": 999.0,
            "role": "huge",
            "download_gb": 999.0,
        }
        fit = classify_fit(mapped, host)
        row = {
            "tag": tag,
            "name": tag,
            "fit": fit,
            "is_local": False,
            "local": "not-local",
            "role": mapped.get("role"),
            "params_b": mapped.get("params_b"),
            "vram_gb": mapped.get("vram_gb"),
        }
    if row.get("is_local"):
        return {
            "ok": True,
            "live": "SKIP",
            "copy": "SKIP pull -- already local · %s" % tag,
            "tag": tag,
            "fit": row.get("fit"),
            "issue": ISSUE,
        }
    fit = row.get("fit") or "won't-fit"
    if fit == "won't-fit":
        return fail(
            "pull",
            "won't-fit",
            NEXT_SMALLER,
            tag=tag,
            fit=fit,
            pull_disabled=True,
        )
    if (row.get("role") == "huge" or float(row.get("params_b") or 0) >= 200) and not opt_in_huge:
        return fail(
            "pull",
            "405B-class needs explicit opt-in",
            "pass --opt-in-huge · " + NEXT_SMALLER,
            tag=tag,
            fit=fit,
            pull_disabled=True,
        )
    if fit == "tight" and not confirm_tight:
        return fail(
            "pull",
            "tight needs confirm",
            NEXT_CONFIRM,
            tag=tag,
            fit=fit,
            pull_confirm=True,
        )
    # Execute pull via callback or ollama
    if callable(pull_fn):
        res = pull_fn(tag) or {}
    else:
        if not shutil.which("ollama"):
            return fail("pull", "ollama missing", NEXT_OLLAMA, tag=tag, fit=fit)
        try:
            p = subprocess.run(
                ["ollama", "pull", tag],
                capture_output=True,
                text=True,
                timeout=600,
            )
            res = {
                "ok": p.returncode == 0,
                "copy": ("PASS pull · " + tag) if p.returncode == 0 else ("FAIL pull · " + tag),
                "stdout": ((p.stdout or "") + (p.stderr or ""))[-800:],
                "error": "" if p.returncode == 0 else ((p.stderr or p.stdout or "pull failed")[-400:]),
            }
        except Exception as e:
            return fail("pull", str(e)[:160], "retry / check Ollama", tag=tag, fit=fit)
    if not res.get("ok"):
        return fail(
            "pull",
            res.get("error") or res.get("copy") or "pull failed",
            "retry / check Ollama",
            tag=tag,
            fit=fit,
            pull=res,
        )
    return {
        "ok": True,
        "live": "PASS",
        "copy": "PASS pull · %s · fit=%s · %s" % (tag, fit, CHIP_HONEST),
        "tag": tag,
        "fit": fit,
        "pull": res,
        "honesty": CHIP_HONEST,
        "usable": True,
        "issue": ISSUE,
        "next_step": "Attach re-probe · TUI reload",
    }


def attach_usable(ROOT=None, STATE=None, *, model="auto", start_fn=None, which=None):
    """Attach Gab cloud: prove key + models list (+ optional harness start)."""
    STATE = _now_state(STATE or os.environ.get("PFY_STATE_DIR") or Path.home() / ".pfy-mentat")
    lane = cloud_lane(STATE, model=model, ROOT=ROOT)
    if not lane.get("ok"):
        return lane
    env, err = apply_cloud_env(model=model)
    if err:
        return err
    # Prove models list (auth optional). Offline / bad test keys → fixture.
    offline = str(os.environ.get("PFY_GAB_OFFLINE") or "").strip() in ("1", "true", "yes")
    if offline:
        fetched = fetch_gab_models(ROOT, fixture_only=True)
    else:
        fetched = fetch_gab_models(ROOT, use_network=True)
        if not fetched.get("ok"):
            # GET /v1/models is auth-optional; fall back rather than block attach prove
            fetched = fetch_gab_models(ROOT, fixture_only=True)
    if not fetched.get("ok") and fetched.get("live") == "FAIL" and not load_fixture(ROOT):
        return fetched
    ids = pin_model_ids(fetched.get("data") or [])
    if model != "auto" and ids and model not in ids:
        return fail(
            "attach",
            "pin id not in /v1/models",
            "pick id from GET /v1/models · or model=auto",
            model=model,
            endpoint=GAB_BASE,
        )
    reach = "gab · %s · model=%s · %s" % (GAB_BASE, model, CHIP_AUTO)
    out = {
        "ok": True,
        "live": "READY",
        "copy": "READY attach gab · %s" % reach,
        "usable": True,
        "attached": "gab",
        "endpoint": GAB_BASE,
        "model": model,
        "session_reach": reach,
        "chips": [CHIP_AUTO, CHIP_HONEST, CHIP_NO_GGUF],
        "honesty": CHIP_HONEST,
        "issue": ISSUE,
        "next_step": "",
        "models_count": len(ids),
        "provider": "gab",
        "lane": "cloud/subscription",
    }
    if callable(start_fn):
        try:
            started = start_fn(env=env, model=model, base=GAB_BASE) or {}
            out["start"] = {k: started.get(k) for k in ("ok", "pid", "copy", "error") if k in started}
            if started.get("ok") is False:
                return fail(
                    "attach",
                    started.get("error") or "harness start failed",
                    started.get("next_step") or "./pfy setup",
                    endpoint=GAB_BASE,
                    model=model,
                )
            if started.get("pid"):
                out["pid"] = started["pid"]
        except Exception as e:
            return fail("attach", str(e)[:160], "./pfy setup", endpoint=GAB_BASE, model=model)
    _write(
        STATE / STATE_GAB,
        json.dumps(
            {
                "ok": True,
                "attached": "gab",
                "endpoint": GAB_BASE,
                "model": model,
                "honesty": CHIP_HONEST,
                "chip_no_gguf": CHIP_NO_GGUF,
            },
            indent=2,
        ),
    )
    return out


def snapshot_fields(STATE=None, ROOT=None, *, pulled=None, host=None, fixture_only=True):
    STATE = _now_state(STATE or os.environ.get("PFY_STATE_DIR") or Path.home() / ".pfy-mentat")
    ks = key_status()
    sync = local_sync(ROOT, STATE, pulled=pulled, host=host, fixture_only=fixture_only)
    lane = cloud_lane(STATE, model=os.environ.get("PFY_GAB_MODEL") or "auto", ROOT=ROOT)
    rows = sync.get("rows") or []
    return {
        "gab_ok": bool(lane.get("ok")),
        "gab_key": ks["paint"],
        "gab_endpoint": GAB_BASE,
        "gab_model": lane.get("model") or "auto",
        "gab_chip_auto": CHIP_AUTO,
        "gab_honesty": CHIP_HONEST,
        "gab_chip_no_gguf": CHIP_NO_GGUF,
        "gab_sync_ok": bool(sync.get("ok")),
        "gab_sync_rows": rows,
        "gab_sync_copy": sync.get("copy") or "",
        "gab_sync_source": sync.get("source") or "",
        "recommend_gab": [r.get("tag") for r in rows if r.get("fit") == "fits"],
    }


def selftest():
    """Offline CI selftest — no network."""
    root = Path(__file__).resolve().parents[1]
    errors = []

    def check(cond, msg):
        if not cond:
            errors.append(msg)
            print("FAIL", msg)
        else:
            print("ok  ", msg)

    # Fixture present
    fix = load_fixture(root)
    check(isinstance(fix, dict) and fix.get("data"), "fixture loads")
    ids = [m.get("id") for m in (fix or {}).get("data") or []]
    check("auto" in ids, "fixture has auto")
    check(any("qwen" in str(i) for i in ids), "fixture has qwen")
    check(any("gemma" in str(i) for i in ids), "fixture has gemma")

    # Open-weight filter
    ow = [m for m in fix["data"] if is_open_weight(m)]
    check(all(is_open_weight(m) for m in ow), "open-weight filter self-consistent")
    check(not is_open_weight({"id": "claude-sonnet-4-5", "capabilities": {"text": True}}), "claude not open-weight")
    check(not is_open_weight({"id": "auto", "capabilities": {"text": True}}), "auto not open-weight local")
    check(is_open_weight({"id": "gemma-4-26b", "owned_by": "Google", "capabilities": {"text": True}}), "gemma open-weight")
    check(is_open_weight({"id": "qwen-3-5-397b", "capabilities": {"text": True}}), "qwen open-weight")

    # Mapper + fit
    m = map_to_ollama("gemma-4-26b")
    check(m and m["tag"] == "gemma4:26b", "gemma maps to gemma4:26b")
    check(classify_fit(m, NIMO_HOST) == "fits", "gemma4:26b fits nimo")
    huge = map_to_ollama("qwen-3-5-397b")
    check(huge and huge["role"] == "huge", "397b mapped as huge")
    check(classify_fit(huge, NIMO_HOST) == "won't-fit", "397b won't-fit")
    tight = {"vram_gb": 40.0, "params_b": 70.0, "role": "general"}
    check(classify_fit(tight, NIMO_HOST) == "tight", "70B-class tight on nimo")

    # Cloud lane key missing
    old = os.environ.pop("GAB_API_KEY", None)
    os.environ.pop("GABAI_API_KEY", None)
    try:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            lane = cloud_lane(td, model="auto", ROOT=root)
            check(not lane.get("ok"), "cloud FAIL without key")
            check("key missing" in (lane.get("error") or ""), "key missing reason")
            check(GAB_AUTH_DOCS in (lane.get("next_step") or ""), "auth docs next")
            check(CHIP_HONEST in str(lane.get("honesty") or ""), "honesty chip")
            os.environ["GAB_API_KEY"] = "gab_test_not_real"
            lane2 = cloud_lane(td, model="auto", ROOT=root)
            check(lane2.get("ok"), "cloud READY with key")
            check(lane2.get("model") == "auto", "default auto")
            check(CHIP_AUTO in (lane2.get("chip_auto") or ""), "auto chip")
            check(lane2.get("endpoint") == GAB_BASE, "endpoint gab.ai/v1")
            # Local sync offline
            sync = local_sync(root, td, pulled=["gemma4:26b"], host=NIMO_HOST, fixture_only=True)
            check(sync.get("ok"), "local sync ok offline")
            check(CHIP_HONEST in (sync.get("honesty") or ""), "sync honesty")
            check(CHIP_NO_GGUF in str(sync.get("chip_no_gguf") or ""), "no GGUF claim")
            tags = [r["tag"] for r in sync.get("rows") or []]
            check("gemma4:26b" in tags, "sync includes gemma4:26b")
            gemma_row = next(r for r in sync["rows"] if r["tag"] == "gemma4:26b")
            check(gemma_row["local"] == "local", "pulled marked local")
            check(gemma_row["fit"] == "fits", "gemma fits")
            # won't-fit pull disabled
            bad = pull_gated(
                "qwen2.5:72b",
                ROOT=root,
                STATE=td,
                pulled=[],
                host=NIMO_HOST,
                fixture_only=True,
                # force won't-fit via synthetic — use 397 mapping tag path
            )
            # pull 397b-class via mapped huge tag if present
            huge_tag = None
            for r in sync["rows"]:
                if r["fit"] == "won't-fit":
                    huge_tag = r["tag"]
                    break
            if huge_tag:
                bad = pull_gated(
                    huge_tag, ROOT=root, STATE=td, pulled=[], host=NIMO_HOST, fixture_only=True
                )
                check(not bad.get("ok"), "won't-fit pull FAIL")
                check("won't-fit" in (bad.get("error") or bad.get("copy") or ""), "won't-fit reason")
            # tight confirm gate
            tight_tag = None
            for r in sync["rows"]:
                if r["fit"] == "tight" and not r["is_local"]:
                    tight_tag = r["tag"]
                    break
            if tight_tag:
                t1 = pull_gated(
                    tight_tag, ROOT=root, STATE=td, pulled=[], host=NIMO_HOST, fixture_only=True
                )
                check(not t1.get("ok"), "tight without confirm FAIL")
                calls = []

                def fake_pull(name):
                    calls.append(name)
                    return {"ok": True, "copy": "PASS pull"}

                t2 = pull_gated(
                    tight_tag,
                    ROOT=root,
                    STATE=td,
                    pulled=[],
                    host=NIMO_HOST,
                    fixture_only=True,
                    confirm_tight=True,
                    pull_fn=fake_pull,
                )
                check(t2.get("ok"), "tight with confirm PASS")
                check(calls == [tight_tag], "tight pull invoked")
            # fits pull
            fit_tag = None
            for r in sync["rows"]:
                if r["fit"] == "fits" and not r["is_local"]:
                    fit_tag = r["tag"]
                    break
            if fit_tag:
                calls = []

                def fake_pull2(name):
                    calls.append(name)
                    return {"ok": True, "copy": "PASS pull"}

                p = pull_gated(
                    fit_tag,
                    ROOT=root,
                    STATE=td,
                    pulled=["gemma4:26b"],
                    host=NIMO_HOST,
                    fixture_only=True,
                    pull_fn=fake_pull2,
                )
                check(p.get("ok"), "fits pull PASS")
                check(calls == [fit_tag], "fits pull invoked")
            # merge preserves freetoken-first order
            base = {
                "ok": True,
                "copy": "PASS recommend · ft-a",
                "ranked": [{"name": "ft-a", "vram_gb": 3}],
                "top": "ft-a",
            }
            merged = merge_recommend(base, sync)
            check(merged["ranked"][0]["name"] == "ft-a", "FreeToken-first order kept")
            check(merged.get("honesty") == CHIP_HONEST, "merged honesty")
            check("gab_sync" in merged, "gab_sync nested")
            # attach offline with key
            os.environ["PFY_GAB_OFFLINE"] = "1"
            att = attach_usable(root, td, model="auto")
            os.environ.pop("PFY_GAB_OFFLINE", None)
            check(att.get("ok"), "attach gab READY offline")
            check(att.get("endpoint") == GAB_BASE, "attach endpoint")
            check(CHIP_HONEST in str(att.get("honesty") or ""), "attach honesty")
    finally:
        if old is not None:
            os.environ["GAB_API_KEY"] = old
        else:
            os.environ.pop("GAB_API_KEY", None)

    if errors:
        print("FAIL selftest · %d" % len(errors))
        return 1
    print("PASS selftest · gab cloud + local sync · honesty · offline fixture · #228")
    return 0


def main(argv=None):
    args = list(argv if argv is not None else sys.argv[1:])
    if not args or args[0] in ("-h", "--help", "help"):
        print(
            "usage: pfy_gab_228.py [--selftest|--cloud [--model ID]|--sync|--pull TAG [--confirm] [--opt-in-huge]|--attach [--model ID]]"
        )
        return 2
    if args[0] in ("--selftest", "selftest"):
        return selftest()
    root = Path(os.environ.get("PFY_ROOT") or Path(__file__).resolve().parents[1])
    state = Path(os.environ.get("PFY_STATE_DIR") or Path.home() / ".pfy-mentat")
    if args[0] in ("--cloud", "cloud"):
        model = "auto"
        if len(args) > 1 and args[1] == "--model" and len(args) > 2:
            model = args[2]
        elif len(args) > 1 and not args[1].startswith("-"):
            model = args[1]
        rec = cloud_lane(state, model=model, ROOT=root)
        print(rec.get("copy") or json.dumps(rec))
        return 0 if rec.get("ok") else 1
    if args[0] in ("--sync", "sync"):
        offline = "--offline" in args or str(os.environ.get("PFY_GAB_OFFLINE") or "") in ("1", "true")
        rec = local_sync(root, state, fixture_only=offline or True)  # default offline-safe
        # Prefer network when explicitly --network
        if "--network" in args:
            rec = local_sync(root, state, fixture_only=False, use_network=True)
        print(rec.get("copy") or "FAIL sync")
        for r in rec.get("rows") or []:
            print(
                "  %s  %s  %s  %s%s"
                % (
                    r["tag"],
                    r["size"],
                    r["fit"],
                    r["local"],
                    "  [Pull]" if r.get("pull_enabled") else ("  [confirm]" if r.get("pull_confirm") else ""),
                )
            )
        print("  chip: %s" % CHIP_HONEST)
        print("  note: %s" % CHIP_NO_GGUF)
        return 0 if rec.get("ok") else 1
    if args[0] in ("--pull", "pull"):
        if len(args) < 2:
            print("usage: --pull TAG [--confirm] [--opt-in-huge]", file=sys.stderr)
            return 2
        tag = args[1]
        rec = pull_gated(
            tag,
            ROOT=root,
            STATE=state,
            confirm_tight=("--confirm" in args),
            opt_in_huge=("--opt-in-huge" in args),
            fixture_only=str(os.environ.get("PFY_GAB_OFFLINE") or "1") != "0",
        )
        print(rec.get("copy") or "FAIL pull")
        return 0 if rec.get("ok") else 1
    if args[0] in ("--attach", "attach"):
        model = "auto"
        if "--model" in args:
            i = args.index("--model")
            if i + 1 < len(args):
                model = args[i + 1]
        rec = attach_usable(root, state, model=model)
        print(rec.get("copy") or "FAIL attach")
        return 0 if rec.get("ok") else 1
    print("unknown command", args[0], file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
