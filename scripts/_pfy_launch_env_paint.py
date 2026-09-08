def launch_env():
    """Same path as bare ./pfy before the window: inference then env-stage. No harness exec.

    Always record_last_verb so LOOP last/timestamp refresh even when already up.
    Honest skip / already-up paints SKIP (never silent).
    """
    if not PFY.is_file():
        record_last_verb("env")
        return {"ok": False, "live": "FAIL", "copy": "FAIL env", "error": "scripts/pfy missing"}
    rc, out = _run(["bash", str(PFY), "env"], timeout=120.0)
    blob = out or ""
    low = blob.lower()
    # Always stamp the click so LOOP last + when move even if tape was already READY.
    record_last_verb("env")
    if rc != 0:
        return {
            "ok": False, "live": "FAIL", "copy": "FAIL env",
            "error": (blob or "env failed")[-400:],
            "stdout": blob[-800:],
        }
    # #191: ready engine is PASS even if an earlier cascade candidate printed honest skip.
    if "status: ready" in low:
        return {
            "ok": True, "live": "PASS", "copy": "PASS env",
            "error": "",
            "stdout": blob[-800:],
        }
    # Stage-only skip (no ready engine line): paint SKIP, not a fake PASS.
    if (
        "skip: env-stage" in low
        or "env-stage.sh missing" in low
    ):
        return {"ok": True, "live": "SKIP", "copy": "SKIP env", "stdout": blob[-800:]}
    return {
        "ok": True, "live": "PASS", "copy": "PASS env",
        "error": "",
        "stdout": blob[-800:],
    }
