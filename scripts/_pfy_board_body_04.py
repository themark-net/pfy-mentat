tml>"
    )



def frontend_static(path: str):
    """Serve sibling assets from gui/operator/frontend (app-core-*.js, app-ui.js, …)."""
    name = (path or "").lstrip("/")
    if not name or "/" in name or "\\" in name or ".." in name or name.startswith("."):
        return None
    if not name.endswith((".js", ".css", ".map", ".svg", ".png", ".ico", ".woff2")):
        return None
    fp = (FRONTEND_DIR / name).resolve()
    try:
        fp.relative_to(FRONTEND_DIR.resolve())
    except ValueError:
        return None
    if not fp.is_file():
        return None
    ctype = {
        ".js": "application/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".map": "application/json; charset=utf-8",
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".ico": "image/x-icon",
        ".woff2": "font/woff2",
    }.get(fp.suffix.lower(), "application/octet-stream")
    return fp, ctype


def run_stage():
    """Run product env-stage (./pfy stage). Not --lab. Honest skip is PASS."""
    if not PFY.is_file():
        return {"ok": False, "live": "FAIL", "copy": "FAIL env-stage", "error": "scripts/pfy missing"}
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
    return {"ok": True, "live":