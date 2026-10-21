#!/usr/bin/env python3
"""One Hermes task via AIAgent.run_conversation. Refuses a real ~/.hermes home.

Run with the venv interpreter from the pinned checkout. PYTHON path to the
checkout is added after the isolation guard, so this file's imports win.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from pathlib import Path

from guard import assert_hermes_home
from schema import server_name

HERE = Path(__file__).resolve().parent


def _redact(text: str) -> str:
    out = []
    for token in text.split():
        low = token.lower()
        if "sk-" in low or "api_key" in low or "token=" in low or low.startswith("bearer"):
            out.append("<redacted>")
        else:
            out.append(token)
    return " ".join(out)[:800]


def _write_config(home: Path, model: str, base_url: str, num_ctx: int, log_path: Path, task_id: str) -> None:
    python = os.environ.get("BAKEOFF_PYTHON") or sys.executable
    server = str(HERE / "mcp_server.py")
    # YAML by hand so we do not depend on a yaml package before Hermes imports.
    text = f"""model:
  default: {json.dumps(model)}
  provider: custom
  base_url: {json.dumps(base_url)}
  api_key: "no-key"
  context_length: {int(num_ctx)}
  ollama_num_ctx: {int(num_ctx)}
agent:
  max_turns: 6
  reasoning_effort: "none"
approvals:
  mode: off
mcp_servers:
  bakeoff:
    command: {json.dumps(python)}
    args: [{json.dumps(server)}, "--log", {json.dumps(str(log_path))}, "--task-id", {json.dumps(task_id)}]
    enabled: true
"""
    (home / "config.yaml").write_text(text, encoding="utf-8")


def _extract(messages) -> tuple[str, str, list[dict]]:
    chunks = []
    calls = []
    if not isinstance(messages, list):
        return "", "", []
    for message in messages:
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            chunks.append(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    text = part.get("text") or part.get("content") or ""
                    if isinstance(text, str) and text.strip():
                        chunks.append(text)
        for call in message.get("tool_calls") or []:
            if not isinstance(call, dict):
                continue
            function = call.get("function") or call
            name = function.get("name") or ""
            raw = function.get("arguments") if isinstance(function, dict) else {}
            if isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except json.JSONDecodeError:
                    raw = {"_raw": raw}
            if not isinstance(raw, dict):
                raw = {"_raw": str(raw)}
            calls.append({"name": server_name(name), "wire_name": name, "arguments": raw})
    final = chunks[-1] if chunks else ""
    return final, "\n".join(chunks), calls


def run_task(task: dict, system: str, model: str, base_url: str, num_ctx: int, log_path: Path) -> dict:
    home = assert_hermes_home()
    home.mkdir(parents=True, exist_ok=True)
    _write_config(home, model, base_url, num_ctx, log_path, task["id"])
    checkout = os.environ.get("HERMES_CHECKOUT")
    if not checkout:
        return {"ok": False, "final_text": "", "assistant_text": "", "client_calls": [], "error": "FAIL: HERMES_CHECKOUT unset", "driver": "AIAgent.run_conversation"}
    sys.path.insert(0, checkout)
    os.chdir(checkout)
    from tools.mcp_tool_discovery import register_mcp_servers
    from run_agent import AIAgent

    python = os.environ.get("BAKEOFF_PYTHON") or sys.executable
    server = str(HERE / "mcp_server.py")
    names = register_mcp_servers(
        {
            "bakeoff": {
                "command": python,
                "args": [server, "--log", str(log_path), "--task-id", task["id"]],
                "enabled": True,
            }
        }
    )
    if not names:
        return {
            "ok": False,
            "final_text": "",
            "assistant_text": "",
            "client_calls": [],
            "error": "FAIL: MCP tools did not register",
            "driver": "AIAgent.run_conversation",
        }
    agent = AIAgent(
        model=model,
        provider="custom",
        base_url=base_url,
        api_key="no-key",
        quiet_mode=True,
        skip_memory=True,
        skip_context_files=True,
        enabled_toolsets=["bakeoff"],
        max_iterations=6,
        reasoning_config={"enabled": False, "effort": "none"},
        request_overrides={"temperature": 0, "seed": 1},
    )
    result = agent.run_conversation(user_message=task["prompt"], system_message=system)
    final_response = ""
    messages = []
    if isinstance(result, dict):
        final_response = result.get("final_response") or ""
        messages = result.get("messages") or []
    final, assistant, calls = _extract(messages)
    if not final and isinstance(final_response, str):
        final = final_response
        assistant = (assistant + "\n" + final_response).strip()
    note = ""
    if isinstance(final_response, str) and "needs at least" in final_response:
        note = final_response[:500]
    return {
        "ok": True,
        "final_text": final if isinstance(final, str) else str(final),
        "assistant_text": assistant if isinstance(assistant, str) else str(assistant),
        "client_calls": calls,
        "error": note or None,
        "driver": "AIAgent.run_conversation",
        "mcp_tools": list(names)[:40],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-file", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--system", required=True)
    parser.add_argument("--log", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--num-ctx", type=int, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    # Resolve before run_task chdirs into the Hermes checkout. A relative --out
    # would otherwise land inside the checkout and the scorer would see no result.
    args.task_file = str(Path(args.task_file).resolve())
    args.log = str(Path(args.log).resolve())
    args.out = str(Path(args.out).resolve())
    Path(args.log).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    try:
        bundle = json.loads(Path(args.task_file).read_text(encoding="utf-8"))
        task = next(item for item in bundle["tasks"] if item["id"] == args.task_id)
        result = run_task(task, args.system, args.model, args.base_url, args.num_ctx, Path(args.log))
        code = 0 if result.get("ok") else 1
    except SystemExit as exc:
        result = {
            "ok": False,
            "final_text": "",
            "assistant_text": "",
            "client_calls": [],
            "error": _redact(str(exc)),
            "driver": "AIAgent.run_conversation",
        }
        code = int(exc.code) if isinstance(exc.code, int) else 2
    except Exception as exc:  # noqa: BLE001
        result = {
            "ok": False,
            "final_text": "",
            "assistant_text": "",
            "client_calls": [],
            "error": _redact(type(exc).__name__ + ": " + str(exc)),
            "driver": "AIAgent.run_conversation",
            "trace_tail": _redact(traceback.format_exc()[-500:]),
        }
        code = 1
    if result.get("error"):
        print(result["error"], file=sys.stderr)
    Path(args.out).write_text(json.dumps(result), encoding="utf-8")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
