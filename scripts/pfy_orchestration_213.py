#!/usr/bin/env python3
"""Deepen attach orchestration beyond thin skill inject -- cite #213.

Selecting orchestration + Attach OpenCode|Hermes|Grok|Codex|Claude must start (or clearly
start) a multi-step agent loop on the FreeToken-first local endpoint -- not
only inject /agent-loops. Prove two local turns, write loop/monitor evidence,
and FAIL+next if the runtime is missing. Never a silent bare session claiming
orchestration. LIVE_HARD_OFF: no cloud embeddings / live catalog writes.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ISSUE = "#213"
TURN_CAP = 8
CARD_FILE = "loop-card.md"
EVIDENCE_FILE = "loop-evidence.json"
PROMPT_FILE = "loop-prompt.md"
MONITOR_FILE = "monitor-note"
NEXT_UP = "Launch env or ./pfy up"
NEXT_SETUP = "./pfy setup"
NEXT_ATTACH = "Attach OpenCode | Hermes | Grok | Codex | Claude"
SIDECARS = ("opencode", "hermes", "grok", "codex", "claude", "claude-code")
FT_BASE = "http://127.0.0.1:1919"

STEP1 = (
    "You are starting a pfy agent loop on the local model. "
    "Write LOOP EXIT CARD with all 8 exits filled for: manage agents on "
    "the FreeToken-first local endpoint. Reply with the card only."
)
STEP2 = (
    "Confirm multi-step loop start. Reply with one LOOP REPORT: "
    "Type: goal; Iterations: 1/%d; Status: STARTED; Exit fired: none."
    % TURN_CAP
)


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read(path):
    path = Path(path)
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def _write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text((text or "").rstrip() + "\n", encoding="utf-8")


def fail(hid, reason, next_step, **extra):
    copy = "FAIL orchestration -- %s \u00b7 %s" % (reason, next_step)
    out = {
        "ok": False,
        "id": hid or "",
        "live": "FAIL",
        "copy": copy,
        "error": reason,
        "next_step": next_step,
        "usable": False,
        "loop_ok": False,
        "using": "orchestration",
        "mode": "orchestration",
        "issue": ISSUE,
    }
    out.update(extra)
    return out


def openai_compat_root(base):
    root = str(base or "").rstrip("/")
    if root.endswith("/v1"):
        root = root[:-3].rstrip("/")
    return root


def inspect_models(base_url):
    if not base_url:
        return []
    base = openai_compat_root(base_url)
    ids, seen = [], set()
    for path in ("/v1/models", "/api/tags"):
        try:
            req = urllib.request.Request(base + path, method="GET")
            with urllib.request.urlopen(req, timeout=2) as r:
                d = json.loads(r.read().decode() or "{}")
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        for m in d.get("data") or []:
            name = (m.get("id") or m.get("name") or "") if isinstance(m, dict) else str(m)
            name = str(name).strip()
            if name and name not in seen:
                seen.add(name)
                ids.append(name)
        for m in d.get("models") or []:
            name = (m.get("name") or m.get("model") or m.get("id") or "") if isinstance(m, dict) else str(m)
            name = str(name).strip()
            if name and name not in seen:
                seen.add(name)
                ids.append(name)
    return ids


def _http_ok(url, timeout=1):
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return 200 <= int(getattr(r, "status", 200) or 200) < 300
    except Exception:
        return False


def probe_freetoken_base(live_openai_base=None, allow_live_probe=True):
    """FreeToken-first live base. Missing runtime is not a slogan attach. Cite #213."""
    det = {}
    base = ""
    if callable(live_openai_base):
        try:
            got = live_openai_base()
        except Exception:
            got = ("", {})
        if isinstance(got, (tuple, list)) and got:
            base = str(got[0] or "")
            det = got[1] if len(got) > 1 and isinstance(got[1], dict) else {}
        elif isinstance(got, str):
            base = got
    engine = str((det or {}).get("engine") or "").strip() or "none"
    status = str((det or {}).get("status") or "").strip().lower()
    if allow_live_probe and (
        _http_ok(FT_BASE + "/v1/models") or _http_ok(FT_BASE + "/health")
    ):
        base = FT_BASE + "/v1"
        engine = "freetoken"
        status = "ready"
        det = dict(det or {})
        det["engine"] = "freetoken"
        det["status"] = "ready"
        det["base_url"] = FT_BASE
    if allow_live_probe and not base:
        for key in ("LOCAL_OPENAI_BASE_URL", "OPENAI_BASE_URL"):
            envb = str(os.environ.get(key) or "").strip()
            if envb and envb != "(none)":
                base = envb
                break
    if base:
        b = str(base).rstrip("/")
        if not b.endswith("/v1"):
            b = b + "/v1"
        base = b
        if allow_live_probe and status != "ready":
            if inspect_models(base):
                status = "ready"
                if engine in ("", "none"):
                    engine = "local"
    return base, det, engine, status


def _completion(base, model, messages, timeout=30):
    root = openai_compat_root(base)
    url = root + "/v1/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": 256,
        "temperature": 0,
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer local",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode() or "{}")
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError) as e:
        return "", "loop step failed: %s" % str(e)[:200]
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
    text = str(text).strip()
    if len(text) < 2:
        return "", "loop step empty completion"
    return text, ""


def loop_card_text(hid, base, model):
    hid = hid or "harness"
    return (
        "LOOP EXIT CARD\n"
        "========================================\n"
        "Goal (success criteria):     manage agents on FreeToken-first local "
        "(%s) in the attached %s session\n"
        "1 Goal met:                  LOOP REPORT Status STARTED, then operator "
        "continues in the TUI\n"
        "2 Turn cap:                  %d iterations\n"
        "3 Budget cap:                local-only (LIVE_HARD_OFF, no cloud)\n"
        "4 Wall clock:                30m session\n"
        "5 No-progress:               3 identical state hashes\n"
        "6 Human interrupt:           user stop / Attach another mode\n"
        "7 Error threshold:           3 consecutive same failure\n"
        "8 External event:            n/a\n"
        "Loop type:                   goal\n"
        "Human gate:                  operator Attach / mode change\n"
        "Model:                       %s\n"
        "Endpoint:                    %s\n"
        "Issue:                       %s\n"
        "========================================\n"
        % (base or "(none)", hid, TURN_CAP, model or "(none)", base or "(none)", ISSUE)
    )


def loop_prompt_text(hid, card_path, evidence_path):
    return (
        "PFY_ATTACH_MODE=orchestration (%s). This is not a bare TUI.\n"
        "A multi-step agent loop has STARTED on the FreeToken-first local model.\n"
        "Load /agent-loops. Continue from the exit card at:\n"
        "  %s\n"
        "Last loop evidence:\n"
        "  %s\n"
        "Write exits before iterating. Do not claim orchestration without this card.\n"
        % (ISSUE, card_path, evidence_path)
    )


def _preview(text, n=120):
    s = " ".join(str(text or "").split())
    if len(s) <= n:
        return s
    return s[: n - 1] + "\u2026"


def clear_evidence(STATE):
    STATE = Path(STATE)
    for name in (CARD_FILE, EVIDENCE_FILE, PROMPT_FILE):
        path = STATE / name
        try:
            if path.is_file():
                path.unlink()
        except OSError:
            pass


def _write_evidence(STATE, payload):
    STATE = Path(STATE)
    STATE.mkdir(parents=True, exist_ok=True)
    path = STATE / EVIDENCE_FILE
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def write_monitor_note(STATE, text):
    _write(Path(STATE) / MONITOR_FILE, (text or "").strip()[:240])


def snapshot_fields(STATE):
    STATE = Path(STATE)
    empty = {
        "loop_ok": False,
        "loop_copy": "",
        "loop_when": "",
        "loop_model": "",
        "loop_steps": 0,
        "loop_hid": "",
        "loop_status": "",
        "loop_evidence": "",
        "loop_next": NEXT_ATTACH,
    }
    raw = _read(STATE / EVIDENCE_FILE)
    if not raw:
        return empty
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return empty
    if not isinstance(data, dict):
        return empty
    ok = bool(data.get("ok"))
    copy = str(data.get("copy") or "")
    empty.update({
        "loop_ok": ok,
        "loop_copy": copy,
        "loop_when": str(data.get("when") or ""),
        "loop_model": str(data.get("model") or ""),
        "loop_steps": int(data.get("steps") or 0),
        "loop_hid": str(data.get("hid") or ""),
        "loop_status": str(data.get("status") or ""),
        "loop_evidence": str(STATE / EVIDENCE_FILE),
        "loop_next": "" if ok else str(data.get("next_step") or NEXT_UP),
    })
    return empty


def apply_child_env(env, STATE=None):
    """Inherit loop card/evidence into Attach child. Cite #213."""
    env = env if env is not None else {}
    if STATE is None:
        STATE = os.environ.get("PFY_STATE_DIR") or str(Path.home() / ".pfy-mentat")
    STATE = Path(STATE)
    card = STATE / CARD_FILE
    evidence = STATE / EVIDENCE_FILE
    prompt = STATE / PROMPT_FILE
    if card.is_file():
        env["PFY_LOOP_CARD"] = str(card)
        env["PFY_ATTACH_HANDOFF"] = str(card)
    if evidence.is_file():
        env["PFY_LOOP_EVIDENCE"] = str(evidence)
    if prompt.is_file():
        env["PFY_LOOP_PROMPT"] = str(prompt)
        env["PFY_ATTACH_PROMPT"] = str(prompt)
    note = STATE / MONITOR_FILE
    if note.is_file():
        env["PFY_MONITOR_NOTE"] = str(note)
    return env


def export_env_lines(STATE=None):
    env = apply_child_env({}, STATE)
    return ["export %s=%s" % (k, env[k]) for k in sorted(env) if env[k]]


def prove_loop_start(base, model, complete_fn=None):
    """Two local turns = multi-step start. Returns (ok, steps, err). Cite #213."""
    complete_fn = complete_fn or _completion
    messages = [{"role": "user", "content": STEP1}]
    text1, err = complete_fn(base, model, messages)
    if err or not text1:
        return False, [], err or "loop step 1 failed"
    messages.append({"role": "assistant", "content": text1})
    messages.append({"role": "user", "content": STEP2})
    text2, err = complete_fn(base, model, messages)
    if err or not text2:
        return False, [{"n": 1, "preview": _preview(text1)}], err or "loop step 2 failed"
    return True, [
        {"n": 1, "preview": _preview(text1)},
        {"n": 2, "preview": _preview(text2)},
    ], ""


def start_loop(
    ROOT,
    STATE,
    hid,
    base="",
    inspect_models_fn=None,
    complete_fn=None,
    live_openai_base=None,
    allow_live_probe=True,
):
    """Prove multi-step loop start and write monitor evidence. Cite #213.

    Does not spawn a TUI. Caller must not paint attached on ok:False.
    Missing runtime = FAIL+next -- never silent bare claiming orchestration.
    """
    _ = ROOT
    STATE = Path(STATE)
    hid = str(hid or "").strip()
    if hid and hid not in SIDECARS:
        return fail(hid, "not a sidecar for orchestration", NEXT_ATTACH)
    inspect_models_fn = inspect_models_fn or inspect_models

    if live_openai_base is not None or not base:
        base, _det, engine, status = probe_freetoken_base(
            live_openai_base, allow_live_probe=allow_live_probe
        )
    else:
        b = str(base).rstrip("/")
        if b and not b.endswith("/v1"):
            b = b + "/v1"
        base = b
        engine = "local"
        status = "ready" if base else "missing"

    if not base or status != "ready":
        clear_evidence(STATE)
        return fail(
            hid,
            "orchestration runtime missing -- no local engine",
            NEXT_UP,
            engine=engine,
            detect_status=status or "missing",
            base_url=base or "",
        )

    models = []
    try:
        models = list(inspect_models_fn(openai_compat_root(base)) or [])
    except Exception as e:
        clear_evidence(STATE)
        return fail(hid, "models list failed: %s" % str(e)[:160], NEXT_UP, base_url=base)
    if not models:
        clear_evidence(STATE)
        return fail(hid, "no models on live endpoint", NEXT_UP, base_url=base, engine=engine)
    model = str(models[0]).strip()
    if not model:
        clear_evidence(STATE)
        return fail(hid, "empty model name", NEXT_UP, base_url=base)

    ok, steps, err = prove_loop_start(base, model, complete_fn=complete_fn)
    if not ok:
        clear_evidence(STATE)
        return fail(
            hid,
            err or "loop start failed",
            NEXT_UP,
            base_url=base,
            engine=engine,
            model=model,
        )

    when = _now()
    card = loop_card_text(hid, base, model)
    card_path = STATE / CARD_FILE
    evidence_path = STATE / EVIDENCE_FILE
    prompt_path = STATE / PROMPT_FILE
    _write(card_path, card)
    copy = "started %d/%d \u00b7 %s \u00b7 %s" % (len(steps), TURN_CAP, hid or "harness", model)
    payload = {
        "ok": True,
        "issue": ISSUE,
        "hid": hid,
        "when": when,
        "base": base,
        "engine": engine,
        "model": model,
        "steps": len(steps),
        "turn_cap": TURN_CAP,
        "status": "STARTED",
        "copy": copy,
        "previews": steps,
    }
    _write_evidence(STATE, payload)
    _write(prompt_path, loop_prompt_text(hid, card_path, evidence_path))
    write_monitor_note(STATE, "loop %s" % copy)
    env = apply_child_env({}, STATE)
    return {
        "ok": True,
        "id": hid,
        "live": "READY",
        "copy": copy,
        "using": "orchestration",
        "mode": "orchestration",
        "usable": True,
        "loop_ok": True,
        "loop_copy": copy,
        "loop_when": when,
        "loop_model": model,
        "loop_steps": len(steps),
        "loop_hid": hid,
        "loop_status": "STARTED",
        "loop_evidence": str(evidence_path),
        "base_url": base,
        "engine": engine,
        "model": model,
        "env": env,
        "handoff": str(card_path),
        "issue": ISSUE,
    }


def cmd_start(hid, root=None, state=None):
    root = Path(root or os.environ.get("PFY_ROOT") or Path(__file__).resolve().parents[1])
    state = Path(state or os.environ.get("PFY_STATE_DIR") or str(Path.home() / ".pfy-mentat"))
    res = start_loop(root, state, hid)
    if not res.get("ok"):
        print(res.get("copy") or "FAIL orchestration")
        nxt = res.get("next_step") or NEXT_UP
        if nxt and nxt not in str(res.get("copy") or ""):
            print("  next: %s" % nxt)
        return 1
    print("PASS orchestration \u00b7 %s" % res.get("copy"))
    for line in export_env_lines(state):
        print(line)
    return 0


def cmd_selftest():
    import tempfile

    errors = []

    def check(cond, msg):
        if not cond:
            errors.append(msg)

    with tempfile.TemporaryDirectory(prefix="pfy-213-") as tmp:
        state = Path(tmp)
        root = Path(__file__).resolve().parents[1]

        missing = start_loop(
            root,
            state,
            "grok",
            live_openai_base=lambda: ("", {"engine": "none", "status": "missing"}),
            inspect_models_fn=lambda b: [],
            complete_fn=lambda *a, **k: ("", "nope"),
            allow_live_probe=False,
        )
        check(not missing.get("ok"), "missing runtime must FAIL")
        check(NEXT_UP in (missing.get("next_step") or ""), "missing next up")
        check("runtime missing" in (missing.get("error") or ""), "missing copy")
        check(not (state / EVIDENCE_FILE).is_file(), "no evidence on FAIL")

        canned = [
            "LOOP EXIT CARD\n1 Goal met: STARTED\n2 Turn cap: 8",
            "LOOP REPORT Type: goal Iterations: 1/8 Status: STARTED",
        ]

        def fake_complete(base, model, messages, timeout=30):
            n = sum(1 for m in messages if m.get("role") == "user")
            if n <= 0 or n > len(canned):
                return "", "bad step"
            return canned[n - 1], ""

        res = start_loop(
            root,
            state,
            "opencode",
            base="http://127.0.0.1:1919/v1",
            live_openai_base=lambda: (
                "http://127.0.0.1:1919/v1",
                {"engine": "freetoken", "status": "ready", "base_url": "http://127.0.0.1:1919"},
            ),
            inspect_models_fn=lambda b: ["local-test"],
            complete_fn=fake_complete,
            allow_live_probe=False,
        )
        check(res.get("ok") is True, "canned loop start")
        check(res.get("loop_ok") is True, "loop_ok")
        check(res.get("loop_steps") == 2, "two steps")
        check("started 2/8" in (res.get("copy") or ""), "started copy")
        check((state / CARD_FILE).is_file(), "card file")
        check((state / EVIDENCE_FILE).is_file(), "evidence file")
        check("STARTED" in (state / EVIDENCE_FILE).read_text(encoding="utf-8"), "evidence STARTED")
        check("loop started 2/8" in _read(state / MONITOR_FILE), "monitor note")
        snap = snapshot_fields(state)
        check(snap.get("loop_ok") is True, "snapshot ok")
        check("started 2/8" in (snap.get("loop_copy") or ""), "snapshot copy")
        env = apply_child_env({}, state)
        check("PFY_LOOP_CARD" in env, "child card")
        check("PFY_LOOP_EVIDENCE" in env, "child evidence")

        def boom(*a, **k):
            return "", "loop step failed: refused"

        bad = start_loop(
            root,
            state,
            "hermes",
            live_openai_base=lambda: (
                "http://127.0.0.1:1919/v1",
                {"engine": "freetoken", "status": "ready"},
            ),
            inspect_models_fn=lambda b: ["x"],
            complete_fn=boom,
            allow_live_probe=False,
        )
        check(not bad.get("ok"), "prove fail")
        check(not (state / EVIDENCE_FILE).is_file(), "clear evidence on prove fail")

    if errors:
        print("FAIL selftest \u00b7 " + " ; ".join(errors))
        return 1
    print("PASS selftest \u00b7 orchestration loop start + FAIL+next \u00b7 %s" % ISSUE)
    return 0


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help"):
        print("usage: pfy_orchestration_213.py [--selftest|--start HID|--export-env]")
        return 0
    if args[0] in ("--selftest", "selftest"):
        return cmd_selftest()
    if args[0] in ("--export-env", "export-env"):
        for line in export_env_lines():
            print(line)
        return 0
    if args[0] in ("--start", "start"):
        hid = args[1] if len(args) > 1 else ""
        return cmd_start(hid)
    print("usage: pfy_orchestration_213.py [--selftest|--start HID|--export-env]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
