        for key in ("data", "models"):
            for m in d.get(key) or []:
                name = (m.get("id") or m.get("name") or m.get("model") if isinstance(m, dict) else str(m)) or ""
                name = str(name).strip()
                if name and name not in seen:
                    seen.add(name); ids.append(name)
    return ids

def org_messages():
    for path in ORG_CANDIDATES:
        if not path.is_file():
            continue
        raw = path.read_text(encoding="utf-8", errors="replace").strip()
        if not raw:
            continue
        items = []
        if path.suffix == ".jsonl":
            for line in raw.splitlines():
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        else:
            try:
                loaded = json.loads(raw)
            except json.JSONDecodeError:
                continue
            items = loaded if isinstance(loaded, list) else (loaded.get("messages") or loaded.get("items") or [loaded])
        out = []
        for it in items:
            if not isinstance(it, dict):
                continue
            who = str(it.get("from") or it.get("who") or "")
            whom = str(it.get("to") or it.get("whom") or "")
            if who or whom:
                out.append({"from": who, "to": whom, "pr": it.get("pr") or "", "issue": it.get("issue") or "",
                            "state": str(it.get("state") or it.get("status") or ""),
                            "text": str(it.get("text") or it.get("summary") or "")[:240]})
        return out
    return []

def one_liner(hid, rec):
    if hid in STUB_ALWAYS:
        return GROK_USE
    if hid == "llama-swap":
        return "llama-swap"
    if hid in ("llama.cpp", "llama-server"):
        return "llama-server"
    if hid == "shimmy":
        return "shimmy"
    if hid == "freetoken":
        return "ft serve --model $PFY_FT_MODEL"
    if hid == "ollama":
        return "ollama serve"
    if hid == "grok":
        return "curl -fsSL https://x.ai/cli/install.sh | bash"
    setup = str(rec.get("setup") or "").strip()
    return (setup.splitlines()[0] if setup else f"./pfy start {hid}")

def now_state(active, live, procs, verb):
    ids = {r["id"] for r in procs}
    mapped = "llama.cpp" if active == "llama-server" else active
    if mapped in STUB_ALWAYS or live in ("stub", "detected-stub", "missing"):
        return "blocked"
    if mapped in ids or active in ids:
        return "running"
    v = verb.get("verb") or ""
    return "blocked" if v.startswith("start") or v.startswith("up") else "idle"

def rsf_inference(det):
    st = (det.get("status") or "").strip().lower()
    if st == "ready":
        return "READY"
    if st == "partial":
        return "FAIL"
    return "SKIP"

def rsf_env_stage(verb, usage):
    blob = " ".join(usage).lower()
    v = (verb.get("verb") or "").strip()
    if "fail" in blob or "error" in blob:
        return "FAIL"
    if "honest skip" in blob or "skip: env-stage" in blob:
        return "SKIP"
    if v.startswith(("start", "up", "stage", "gui", "board", "env", "launch-env")):
        return "READY"
    return "SKIP"

def rsf_attach(active, live_active):
    if active in STUB_ALWAYS:
        return "FAIL"
    live = (live_active or "").lower()
    if live == "ready":
        return "READY"
    if live in ("stub", "detected-stub"):
        return "FAIL"
    return "SKIP"

def tape_steps(det, verb, usage, active, live_active):
    return [
        {"id": "inference", "label": "inference", "live": rsf_inference(det)},
        {"id": "env-stage", "label": "env-stage", "live": rsf_env_stage(verb, usage)},
        {"id": "harness-attach", "label": "harness attach", "live": rsf_attach(active, live_active)},
    ]
def snapshot():
    reg = load_registry()
    harnesses = list(reg.get("harnesses") or [])
    default = str(reg.get("default_harness") or "grok")
    det = detector_json()
    status_te