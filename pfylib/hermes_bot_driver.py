#!/usr/bin/env python3
"""One Hermes turn for `pfy bot`. Library driver, isolated HERMES_HOME.

The parent kills this process on timeout. This file does not run the
upstream installer and refuses a home under ~/.hermes.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


# One-shot bot turns are chat only. Approvals are off, so tools stay off too.
ENABLED_TOOLSETS: tuple[str, ...] = ()


def _refuse_home(raw: str) -> Path:
    resolved = Path(raw).expanduser().resolve()
    forbidden = (Path.home() / ".hermes").resolve()
    if resolved == forbidden or forbidden in resolved.parents:
        raise SystemExit(f"FAIL: HERMES_HOME resolves under ~/.hermes ({resolved})")
    return resolved


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _config(home: Path, model: str, base_url: str, reasoning: str) -> None:
    effort = "none" if reasoning == "off" else "high"
    text = f"""model:
  default: {json.dumps(model)}
  provider: custom
  base_url: {json.dumps(base_url)}
  api_key: "no-key"
agent:
  max_turns: 6
  reasoning_effort: {json.dumps(effort)}
tools:
  tool_search:
    enabled: off
approvals:
  mode: off
"""
    home.mkdir(parents=True, exist_ok=True)
    (home / "config.yaml").write_text(text, encoding="utf-8")


def _fail(out: Path, message: str) -> int:
    _write(out, {"ok": False, "final_text": "", "tool_calls": [], "error": message})
    print("FAIL:", message, file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--reasoning", choices=("off", "on"), required=True)
    parser.add_argument("--home", required=True)
    parser.add_argument("--checkout", required=True)
    args = parser.parse_args(argv)
    out = Path(args.out)
    try:
        home = _refuse_home(args.home)
    except SystemExit as exc:
        _write(out, {"ok": False, "final_text": "", "tool_calls": [], "error": str(exc)})
        print(exc, file=sys.stderr)
        return 2
    checkout = Path(args.checkout).resolve()
    if not checkout.exists():
        return _fail(out, "Hermes checkout missing")
    os.environ["HERMES_HOME"] = str(home)
    _config(home, args.model, args.base_url, args.reasoning)
    # This pin loads plugins from the checkout cwd, same as the bake-off arm.
    os.chdir(checkout)
    sys.path.insert(0, str(checkout))
    try:
        from run_agent import AIAgent
    except Exception as exc:  # noqa: BLE001 -- missing pin is a closed failure
        return _fail(out, "Hermes import failed: " + type(exc).__name__)
    try:
        agent = AIAgent(
            model=args.model,
            provider="custom",
            base_url=args.base_url,
            api_key="no-key",
            quiet_mode=True,
            skip_memory=True,
            skip_context_files=True,
            max_iterations=6,
            # Approvals are off in config.yaml, so no tool may run unapproved:
            # an empty list enables no toolsets (no terminal, file, web, browser).
            enabled_toolsets=list(ENABLED_TOOLSETS),
            reasoning_config={"enabled": args.reasoning == "on", "effort": "none" if args.reasoning == "off" else "high"},
            request_overrides={"temperature": 0, "seed": 1},
        )
        result = agent.run_conversation(user_message=args.prompt)
    except Exception as exc:  # noqa: BLE001
        return _fail(out, "Hermes run failed: " + type(exc).__name__)
    text = ""
    calls: list[dict] = []
    if isinstance(result, dict):
        raw = result.get("final_response") or ""
        text = raw if isinstance(raw, str) else str(raw)
        for message in result.get("messages") or []:
            if not isinstance(message, dict):
                continue
            for call in message.get("tool_calls") or []:
                if not isinstance(call, dict):
                    calls.append({"name": "", "arguments": call})
                    continue
                function = call.get("function") or call
                name = function.get("name") if isinstance(function, dict) else ""
                arguments = function.get("arguments") if isinstance(function, dict) else None
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        arguments = arguments
                calls.append({"name": str(name or ""), "arguments": arguments})
    _write(out, {"ok": True, "final_text": text, "tool_calls": calls, "error": None})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
