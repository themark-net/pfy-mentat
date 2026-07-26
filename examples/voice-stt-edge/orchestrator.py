#!/usr/bin/env python3
"""T-0096 — dual-tier voice orchestrator (high ↔ low).

Default route: **high-first** (Grok coordinates, may DELEGATE_LOCAL to OpenCode).

  VOICE_AUTO_AGENT=1|auto|orchestrate  → run orchestrator
  VOICE_ROUTE=high-first|local-first|local-only|high-only
    default: high-first

  VOICE_AUTO_AGENT=opencode → low only (T-0092)
  VOICE_AUTO_AGENT=grok     → high only
  VOICE_AUTO_AGENT=mock     → mock orchestrate (smoke)

Tier history written into last-run.json for phone /api/last-run.
"""
from __future__ import annotations

import json
import os
import re
import sys
import uuid
from pathlib import Path
from typing import Any

# Import runner primitives
import agent_runner as ar

DELEGATE_RE = re.compile(
    r"<<<DELEGATE_LOCAL\s*\n(?P<body>.*?)\n\s*>>>",
    re.DOTALL | re.IGNORECASE,
)
# Softer patterns if model forgets exact fence
DELEGATE_SOFT = re.compile(
    r"(?:DELEGATE_LOCAL|DELEGATE TO LOCAL|ASSIGN_LOCAL)\s*[:\-]?\s*(?P<body>.+?)(?:\n\n|\Z)",
    re.DOTALL | re.IGNORECASE,
)

ESCALATE_SIGNALS = (
    "does not support tools",
    "escalat",
    "need cloud",
    "need grok",
    "cannot complete",
    "failed after",
    "no progress",
)


def route_mode() -> str:
    raw = (os.environ.get("VOICE_ROUTE") or "high-first").strip().lower()
    if raw in ("high-first", "high_first", "hf"):
        return "high-first"
    if raw in ("local-first", "local_first", "lf"):
        return "local-first"
    if raw in ("local-only", "local_only", "local"):
        return "local-only"
    if raw in ("high-only", "high_only", "high", "cloud-only"):
        return "high-only"
    return "high-first"


def coordinator_prompt(user_prompt: str, repo: Path) -> str:
    return f"""# Voice operator — HIGH coordinator (T-0096)

You are the **high-reasoning monitor** for repo `{repo}`.
A voice/STT transcript produced the operator request below.

## Your job

1. Understand the request; restate a short DoD if useful.
2. Prefer **delegating bulk implementation** to a local OpenCode/Ollama worker.
3. Handle yourself when you need cloud tools, design judgment, MCP/GitHub, or security review.
4. You may use tools on this host when available.

## How to delegate to local worker

If a local worker should implement (edits, simple scripts, mechanical fixes), end with exactly:

<<<DELEGATE_LOCAL
<clear implement instructions for the local worker — concrete files/commands>
>>>

If you fully complete the task yourself, **do not** emit DELEGATE_LOCAL.
If the task is trivial (one-liner, pure Q&A), answer yourself without delegating.

## Operator request

{user_prompt}
"""


def review_prompt(user_prompt: str, local_reply: str, repo: Path) -> str:
    return f"""# Voice operator — HIGH review after local worker (T-0096)

Repo: `{repo}`

## Original request
{user_prompt}

## Local worker result
{local_reply[:6000]}

## Your job
Review: accept, request one more local fix (emit DELEGATE_LOCAL again), or finish with a short status for the operator.
If done, do **not** emit DELEGATE_LOCAL.
"""


def extract_delegate(text: str) -> str | None:
    if not text:
        return None
    m = DELEGATE_RE.search(text)
    if m:
        body = m.group("body").strip()
        return body or None
    m = DELEGATE_SOFT.search(text)
    if m:
        body = m.group("body").strip()
        # avoid swallowing entire reply
        if len(body) > 20 and len(body) < 4000:
            return body
    return None


def should_escalate_local(result: dict) -> bool:
    if not result.get("ok"):
        return True
    blob = (result.get("reply") or "") + " " + (result.get("error") or "")
    low = blob.lower()
    return any(s in low for s in ESCALATE_SIGNALS)


def _tier(
    name: str,
    result: dict,
    *,
    role: str,
) -> dict[str, Any]:
    return {
        "tier": name,
        "role": role,
        "mode": result.get("mode"),
        "status": result.get("status"),
        "ok": result.get("ok"),
        "exit_code": result.get("exit_code"),
        "duration_s": result.get("duration_s"),
        "reply_preview": (result.get("reply_preview") or result.get("reply") or "")[:400],
        "error": result.get("error"),
    }


def run_high(
    prompt: str,
    repo: Path,
    out: Path,
    run_id: str,
    max_turns: int,
    timeout_s: int,
    *,
    mock: bool,
) -> dict:
    if mock:
        # Deterministic: always delegate a small task for smoke
        reply = (
            "Plan: local worker should implement a tiny script.\n\n"
            "<<<DELEGATE_LOCAL\n"
            "Write a one-line bash comment file /tmp/pfy-orchestrate-ok.txt saying ORCH_LOCAL_OK\n"
            "or just reply with ORCH_LOCAL_OK if you cannot write files.\n"
            ">>>\n"
        )
        (out / "last-reply.txt").write_text(reply, encoding="utf-8")
        return {
            "status": "done",
            "ok": True,
            "run_id": run_id,
            "mode": "mock-high",
            "exit_code": 0,
            "reply": reply,
            "reply_preview": reply[:500],
            "duration_s": 0.05,
        }
    return ar.run_grok(
        prompt, repo, out, max_turns=max_turns, timeout_s=timeout_s, run_id=run_id
    )


def run_low(
    prompt: str,
    repo: Path,
    out: Path,
    run_id: str,
    timeout_s: int,
    *,
    mock: bool,
) -> dict:
    if mock:
        reply = "ORCH_LOCAL_OK\nVOICE_RUNNER_MOCK_OK\n"
        (out / "last-reply.txt").write_text(reply, encoding="utf-8")
        return {
            "status": "done",
            "ok": True,
            "run_id": run_id,
            "mode": "mock-low",
            "exit_code": 0,
            "reply": reply,
            "reply_preview": reply[:500],
            "duration_s": 0.05,
        }
    return ar.run_opencode(prompt, repo, out, run_id, timeout_s)


def orchestrate(
    *,
    repo: Path,
    out: Path,
    user_prompt: str,
    route: str | None = None,
    max_turns: int = 8,
    timeout_s: int = 600,
    mock: bool = False,
    review: bool | None = None,
) -> dict:
    """Run dual-tier flow. Returns last-run payload with tier_history."""
    out = ar.ensure_out(out)
    run_id = uuid.uuid4().hex[:12]
    route = route or route_mode()
    if review is None:
        review = os.environ.get("VOICE_ORCH_REVIEW", "0").strip().lower() in (
            "1",
            "true",
            "yes",
        )

    tiers: list[dict] = []
    started = ar.utc_now()
    ar.write_run(
        out,
        {
            "status": "running",
            "ok": False,
            "run_id": run_id,
            "mode": "orchestrate",
            "route": route,
            "mock": mock,
            "started": started,
            "message": f"orchestrating ({route})…",
            "tier_history": [],
        },
    )
    print(f"==> orchestrate route={route} mock={mock} run_id={run_id}", file=sys.stderr)

    final_reply = ""
    ok = False

    try:
        if route == "local-only":
            low = run_low(user_prompt, repo, out, run_id + "L", timeout_s, mock=mock)
            tiers.append(_tier("low", low, role="implement"))
            final_reply = low.get("reply") or ""
            ok = bool(low.get("ok"))

        elif route == "high-only":
            high_p = coordinator_prompt(user_prompt, repo)
            high = run_high(
                high_p, repo, out, run_id + "H", max_turns, timeout_s, mock=mock
            )
            tiers.append(_tier("high", high, role="coordinate"))
            final_reply = high.get("reply") or ""
            ok = bool(high.get("ok"))

        elif route == "local-first":
            low = run_low(user_prompt, repo, out, run_id + "L0", timeout_s, mock=mock)
            tiers.append(_tier("low", low, role="implement"))
            final_reply = low.get("reply") or ""
            ok = bool(low.get("ok"))
            if should_escalate_local(low) or (mock and os.environ.get("VOICE_ORCH_FORCE_ESCALATE") == "1"):
                print("==> local-first escalate → high", file=sys.stderr)
                esc_prompt = (
                    coordinator_prompt(user_prompt, repo)
                    + "\n\n## Local worker failed or requested escalate\n\n"
                    + (low.get("reply") or low.get("error") or "")[:4000]
                )
                high = run_high(
                    esc_prompt, repo, out, run_id + "H", max_turns, timeout_s, mock=mock
                )
                tiers.append(_tier("high", high, role="escalate"))
                # may re-delegate
                deleg = extract_delegate(high.get("reply") or "")
                if deleg:
                    print("==> high re-delegates to local", file=sys.stderr)
                    low2 = run_low(deleg, repo, out, run_id + "L1", timeout_s, mock=mock)
                    tiers.append(_tier("low", low2, role="implement-after-escalate"))
                    final_reply = (
                        (high.get("reply") or "")
                        + "\n\n--- local ---\n"
                        + (low2.get("reply") or "")
                    )
                    ok = bool(high.get("ok") and low2.get("ok"))
                else:
                    final_reply = high.get("reply") or final_reply
                    ok = bool(high.get("ok"))

        else:  # high-first (default)
            high_p = coordinator_prompt(user_prompt, repo)
            high = run_high(
                high_p, repo, out, run_id + "H0", max_turns, timeout_s, mock=mock
            )
            tiers.append(_tier("high", high, role="coordinate"))
            high_reply = high.get("reply") or ""
            final_reply = high_reply
            ok = bool(high.get("ok"))
            deleg = extract_delegate(high_reply)
            if deleg and high.get("ok"):
                print("==> high-first DELEGATE_LOCAL → low", file=sys.stderr)
                low = run_low(deleg, repo, out, run_id + "L0", timeout_s, mock=mock)
                tiers.append(_tier("low", low, role="implement"))
                final_reply = high_reply + "\n\n--- local worker ---\n" + (low.get("reply") or "")
                ok = bool(high.get("ok") and low.get("ok"))
                if review and low.get("ok"):
                    print("==> high review pass", file=sys.stderr)
                    rev = run_high(
                        review_prompt(user_prompt, low.get("reply") or "", repo),
                        repo,
                        out,
                        run_id + "H1",
                        max_turns,
                        timeout_s,
                        mock=mock,
                    )
                    tiers.append(_tier("high", rev, role="review"))
                    final_reply += "\n\n--- high review ---\n" + (rev.get("reply") or "")
                    ok = ok and bool(rev.get("ok"))
                    # one more delegate if review asks
                    d2 = extract_delegate(rev.get("reply") or "")
                    if d2:
                        low2 = run_low(d2, repo, out, run_id + "L1", timeout_s, mock=mock)
                        tiers.append(_tier("low", low2, role="implement-after-review"))
                        final_reply += "\n\n--- local (pass 2) ---\n" + (low2.get("reply") or "")
                        ok = ok and bool(low2.get("ok"))
            elif not high.get("ok"):
                # high failed — optional local attempt
                if os.environ.get("VOICE_ORCH_FALLBACK_LOCAL", "1") not in ("0", "false"):
                    print("==> high failed; fallback local", file=sys.stderr)
                    low = run_low(user_prompt, repo, out, run_id + "Lfb", timeout_s, mock=mock)
                    tiers.append(_tier("low", low, role="fallback"))
                    final_reply = (high.get("error") or "") + "\n" + (low.get("reply") or "")
                    ok = bool(low.get("ok"))

        (out / "last-reply.txt").write_text(final_reply + ("\n" if final_reply else ""), encoding="utf-8")
        payload = {
            "status": "done" if ok else "error",
            "ok": ok,
            "run_id": run_id,
            "mode": "orchestrate",
            "route": route,
            "mock": mock,
            "started": started,
            "finished": ar.utc_now(),
            "tier_history": tiers,
            "tiers": [t["tier"] + ":" + t["role"] for t in tiers],
            "reply": final_reply[-8000:] if len(final_reply) > 8000 else final_reply,
            "reply_preview": final_reply[:500] + ("…" if len(final_reply) > 500 else ""),
            "message": f"orchestrate {route}: {len(tiers)} tier(s)",
            "exit_code": 0 if ok else 1,
        }
        ar.write_run(out, payload)
        print(
            f"==> orchestrate done ok={ok} tiers={[t['tier']+':'+t['role'] for t in tiers]}",
            file=sys.stderr,
        )
        print(f"==> REPLY: {payload['reply_preview']!r}", file=sys.stderr)
        return payload
    except Exception as e:
        payload = {
            "status": "error",
            "ok": False,
            "run_id": run_id,
            "mode": "orchestrate",
            "route": route,
            "tier_history": tiers,
            "error": str(e),
            "message": str(e),
            "finished": ar.utc_now(),
        }
        ar.write_run(out, payload)
        raise


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="T-0096 dual-tier voice orchestrator")
    p.add_argument("--repo", type=Path, default=ar.ROOT)
    p.add_argument("--out-dir", type=Path, default=ar.DEFAULT_OUT)
    p.add_argument("--prompt-file", type=Path)
    p.add_argument("--transcript", "--text", dest="transcript")
    p.add_argument(
        "--route",
        default=None,
        help="high-first|local-first|local-only|high-only (default VOICE_ROUTE or high-first)",
    )
    p.add_argument("--mock", action="store_true", help="mock high+low (no cloud)")
    p.add_argument("--review", action="store_true", help="high reviews after local")
    p.add_argument("--max-turns", type=int, default=int(os.environ.get("VOICE_AGENT_MAX_TURNS", "8")))
    p.add_argument("--timeout", type=int, default=int(os.environ.get("VOICE_AGENT_TIMEOUT", "600")))
    p.add_argument("--status", action="store_true")
    args = p.parse_args(argv)

    out = ar.ensure_out(args.out_dir)
    if args.status:
        print(json.dumps(ar.read_run(out), indent=2))
        return 0

    prompt = ""
    if args.prompt_file and args.prompt_file.is_file():
        prompt = args.prompt_file.read_text(encoding="utf-8")
    elif args.transcript:
        prompt = args.transcript
    else:
        for cand in (out / "agent-prompt.md", out / "last-transcript.txt"):
            if cand.is_file():
                prompt = cand.read_text(encoding="utf-8")
                break
    if not prompt.strip():
        print("error: need --prompt-file, --transcript, or last STT artifacts", file=sys.stderr)
        return 2

    mock = args.mock or os.environ.get("VOICE_ORCH_MOCK", "").strip() in ("1", "true", "yes")
    result = orchestrate(
        repo=args.repo.resolve(),
        out=out,
        user_prompt=prompt,
        route=args.route or route_mode(),
        max_turns=args.max_turns,
        timeout_s=args.timeout,
        mock=mock,
        review=args.review or None,
    )
    print(
        json.dumps(
            {
                k: result.get(k)
                for k in (
                    "status",
                    "ok",
                    "run_id",
                    "mode",
                    "route",
                    "tiers",
                    "reply_preview",
                    "error",
                )
            },
            indent=2,
        )
    )
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
