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
    # Honest skip / no local runtime: paint SKIP, not a fake PASS that looks like silence.
    if (
        "honest skip" in low
        or "no local runtime" in low
        or "skip: env-stage" in low
        or "env-stage.sh missing" in low
    ):
        return {"ok": True, "live": "SKIP", "copy": "SKIP env", "stdout": blob[-800:]}
    return {
        "ok": True, "live": "PASS", "copy": "PASS env",
        "error": "",
        "stdout": blob[-800:],
    }
