 "PASS", "copy": "PASS eval", "stdout": str(text).strip()[:400]}

def pull_model(name):
    # #173: FreeToken-first via ./pfy models pull (detect spine); no engine → FAIL+next.
    name = (name or "").strip()
    if not name:
        return {"ok": False, "live": "FAIL", "copy": "FAIL pull", "error": "no name",
                "next_step": "Launch env or ./pfy up"}
    if not PFY.is_file():
        return {"ok": False, "live": "FAIL", "copy": "FAIL pull", "error": "scripts/pfy missing",
                "next_step": "Launch env or ./pfy up"}
    rc, out = _run(["bash", str(PFY), "models", "pull", name], timeout=180.0)
    blob = (out or "")
    low = blob.lower()
    nxt = "Launch env or ./pfy up"
    if rc != 0 or "fail: no local engine" in low or "no local engine to pull" in low:
        err = (blob or "pull failed")[-400:]
        return {
            "ok": False, "live": "FAIL", "copy": "FAIL pull — " + nxt,
            "error": err, "stdout": blob[-800:], "next_step": nxt,
        }
    if "honest skip" in low or "has no pull" in low:
        return {"ok": True, "live": "SKIP", "copy": "SKIP pull", "stdout": blob[-800:]}
    return {"ok": True, "live": "PASS", "copy": "PASS pull", "stdout": blob[-800:]}

def launch_env():
    """Same path as bare ./pfy before the window: inference then env-stage. No harness exec.

    Always record_last_verb so LOOP last/timestamp refresh even when already up.
    Honest skip / already-up paints SKIP (never silent). Cite #159 enrich.
    """
    def _enrich_env(res):
        try:
            import importlib.util
            path = ROOT / "scripts" / "pfy_verify_159.py"
            if not path.is_file():
                out = dict(res or {})
                out["ok"] = False
                out["live"] = "FAIL"
                out["copy"] = "FAIL env · verify module missing"
                out["error"] = str(path)
                return out
            spec = importlib.util.spec_from_file_location("pfy_verify_159", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            enriched = mod.enrich_launch_env(res, live_openai_base, STATE, ROOT)
            emod, eerr = _load_enterable_162()
            if emod is None:
                out = dict(enriched or {})
                steps = list(out.get("next_steps") or [])
                reason = "SKIP enterable session · module missing"
                steps.append({"id": "enterable", "label": reason, "value": reason})
                out["next_steps"] = steps
                out["session_reach"] = "SKIP"
                out["enterable"] = False
                what = str(out.get("what") or "")
                if "enterable" not in what.lower():
                    out["what"] = (what + " · " + reason).strip(" ·")
                return out
            return emod.arm_launch_env_session(enriched, open_enterable_opencode_session)
        except Exception as e:
            out = dict(res or {})
            out["ok"] = False
            out["live"] = "FAIL"
            out["copy"] = "FAIL env · enrich"
            out["error"] = str(e)[:400]
            return out
    if not PFY.is_file():
        record_last_verb("env")
        return _enrich_env({"ok": False, "live": "FAIL", "copy": "FAIL env", "error": "scripts/pfy missing"})
    rc, out = _run(["bash", str(PFY), "env"], timeout=120.0)
    blob = out or ""
    low = blob.lower()
    # Always stamp the click so LOOP last + when move even if tape was already READY.
    record_last_verb("env")
    if rc != 0:
        return _enrich_env({
            "ok": False, "live": "FAIL", "copy": "FAIL env",
            "error": (blob or "env failed")[-400:],
            "stdout": blob[-800:],
        })
    # Honest skip / no local runtime: paint SKIP, not a fake PASS that looks like silence.
    if (
        "honest skip" in low
        or "no local runtime" in low
        or "skip: env-stage" in low
        or "env-stage.sh missing" in low
    ):
        return _enrich_env({"ok": True, "live": "SKIP", "copy": "SKIP env", "stdout": blob[-800:]})
    return _enrich_env({
        "ok": True, "live": "PASS", "copy": "PASS env",
        "error": "",
        "stdout": blob[-800:],
    }