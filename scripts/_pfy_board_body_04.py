"ok": False, "live": "FAIL", "copy": "FAIL env-stage", "error": "scripts/pfy missing"}
    rc, out = _run(["bash", str(PFY), "stage"], timeout=90.0)
    ok = rc == 0
    live = "PASS" if ok else "FAIL"
    copy = "PASS env-stage" if ok else "FAIL env-stage"
    return {
        "ok": ok, "live": live, "copy": copy,
        "error": "" if ok else ((out or "env-stage failed")[-400:]),
        "stdout": (out or "")[-800:],
    }

def test_model():
    # Live-endpoint eval: OpenAI-compat chat/completions on detector base_url.
    # Same completion path as examples/opencode-ollama/smoke.sh, against LOCAL_OPENAI_BASE_URL.
    # Not eval-integration-change. PASS only if the endpoint returns a completion.
    det = detector_json()
    st = str(det.get("status") or "").strip().lower()
    eng = str(det.get("engine") or "none").strip().lower()
    base = str(det.get("base_url") or os.environ.get("LOCAL_OPENAI_BASE_URL") or "").strip()
    if base == "(none)":
        base = ""
    live = st == "ready" and eng not in ("", "none") and bool(base)
    if not live:
        return {"ok": True, "live": "SKIP", "copy": "SKIP eval", "error": ""}
    models = inspect_models(base)
    name = ""
    if models:
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
        return {"ok": False, "live": "FAIL", "copy": "FAIL eval", "error": "no model on live endpoint"}
    root = base.rstrip("/")
    if root.endswith("/v1"):
        url = root + "/chat/completions"
    else:
        url = root + "/v1/chat/completions"
    payload = json.dumps({
        "model": name,
        "messages": [{"role": "user", "content": "Reply with exactly: PFY_EVAL_OK"}],
        "max_tokens": 32,
        "temperature": 0,
    }).encode("utf-8")
    try:
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode() or "{}")
    except Exception as e:
        return {"ok": False, "live": "FAIL", "copy": "FAIL eval", "error": str(e)[:400]}
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
        return {"ok": False, "live": "FAIL", "copy": "FAIL eval", "error": "empty completion"}
    return {"ok": True, "live": "PASS", "copy": "PASS eval", "stdout": str(text).strip()[:400]}

def pull_model(name):
    # Live-engine pull: FreeToken records; Ollama pulls; llama skip honest.
    name = (name or "").strip()
    if not name:
        return {"ok": False, "live": "FAIL", "copy": "FAIL pull", "error": "no name"}
    if not PFY.is_file():
        return {"ok": False, "live": "FAIL", "copy": "FAIL pull", "error": "scripts/pfy missing"}
    rc, out = _run(["bash", str(PFY), "models", "pull", name], timeout=180.0)
    blob = (out or "")
    low = blob.lower()
    if rc != 0:
        return {
            "ok": False, "live": "FAIL", "copy": "FAIL pull",
            "error": (blob or "pull failed")[-400:],
            "stdout": blob[-800:],
        }
    if "honest skip" in low or "has no pull" in low or "no local engine" in low:
        return {"ok": True, "live": "SKIP", "copy": "SKIP pull", "stdout": blob[-800:]}
    return {"ok": True, "live": "PASS", "copy": "PASS pull", "stdout": blob[-800:]}

def launch_env():
    """Same path as bare ./pfy before the window: inference then e