#!/usr/bin/env python3
"""Direct OpenAI-compatible tool loop. Same MCP server, same wire names as Hermes.

This is the fallback when `opencode run` cannot be driven headless against Ollama.
It is the loop pfy harnesses ride on: POST /v1/chat/completions with tools=.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from mcp_framing import read_message, write_message
from schema import WIRE_PREFIX, openai_tools, server_name

HERE = Path(__file__).resolve().parent


def _post(base_url: str, body: dict, timeout: float) -> dict:
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=data,
        headers={"Content-Type": "application/json", "Authorization": "Bearer no-key"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


class McpSession:
    def __init__(self, log_path: Path, task_id: str):
        python = os.environ.get("BAKEOFF_PYTHON") or sys.executable
        self.proc = subprocess.Popen(
            [python, str(HERE / "mcp_server.py"), "--log", str(log_path), "--task-id", task_id],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self._next = 0
        self._request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "pfy-bakeoff-baseline", "version": "0.1.0"},
        })
        self._notify("notifications/initialized", {})

    def close(self) -> None:
        if self.proc.poll() is None:
            self.proc.kill()
        self.proc.wait(timeout=5)

    def _notify(self, method: str, params: dict) -> None:
        write_message(self.proc.stdin, {"jsonrpc": "2.0", "method": method, "params": params})

    def _request(self, method: str, params: dict) -> dict:
        self._next += 1
        msg_id = self._next
        write_message(
            self.proc.stdin,
            {"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params},
        )
        while True:
            message = read_message(self.proc.stdout)
            if message is None:
                raise RuntimeError("MCP server closed")
            if message.get("id") == msg_id:
                return message

    def call(self, wire_name: str, arguments: dict) -> str:
        message = self._request("tools/call", {"name": server_name(wire_name), "arguments": arguments})
        result = message.get("result") or {}
        content = result.get("content") or []
        texts = [part.get("text", "") for part in content if isinstance(part, dict)]
        return "\n".join(texts) or json.dumps(result)


def _parse_args(raw) -> dict:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {"_raw": raw}
        return parsed if isinstance(parsed, dict) else {"_raw": raw}
    return {}


def run_task(task: dict, system: str, base_url: str, model: str, num_ctx: int, log_path: Path) -> dict:
    session = McpSession(log_path, task["id"])
    client_calls = []
    assistant_chunks = []
    error = None
    try:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": task["prompt"]},
        ]
        for _round in range(6):
            body = {
                "model": model,
                "temperature": 0,
                "seed": 1,
                "messages": messages,
                "tools": openai_tools(),
                "tool_choice": "auto",
                "think": False,
                "options": {"num_ctx": num_ctx, "temperature": 0, "seed": 1},
            }
            try:
                payload = _post(base_url, body, timeout=160)
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", "replace")[:500]
                if "seed" in detail.lower() and "seed" in body:
                    body.pop("seed", None)
                    body["options"].pop("seed", None)
                    payload = _post(base_url, body, timeout=160)
                else:
                    raise
            choice = (payload.get("choices") or [{}])[0]
            message = choice.get("message") or {}
            content = message.get("content") or ""
            if isinstance(content, str) and content.strip():
                assistant_chunks.append(content)
            tool_calls = message.get("tool_calls") or []
            messages.append(message)
            if not tool_calls:
                break
            for index, call in enumerate(tool_calls):
                function = call.get("function") or {}
                wire = function.get("name") or ""
                args = _parse_args(function.get("arguments"))
                client_calls.append({"name": server_name(wire), "wire_name": wire, "arguments": args})
                if not wire.startswith(WIRE_PREFIX) and wire not in (
                    "submit_choice",
                    "catalog_lookup",
                    "tools_query",
                    "bench_receipt",
                    "compute_sum",
                    "submit_answer",
                ):
                    text = "FAIL unknown tool"
                else:
                    text = session.call(wire, args)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.get("id") or f"call_{index}",
                        "content": text,
                    }
                )
    except Exception as exc:  # noqa: BLE001
        error = type(exc).__name__ + ": " + str(exc)[:300]
    finally:
        session.close()
    final = assistant_chunks[-1] if assistant_chunks else ""
    return {
        "ok": error is None,
        "final_text": final,
        "assistant_text": "\n".join(assistant_chunks),
        "client_calls": client_calls,
        "error": error,
        "driver": "direct-openai-tool-loop",
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
    bundle = json.loads(Path(args.task_file).read_text(encoding="utf-8"))
    task = next(item for item in bundle["tasks"] if item["id"] == args.task_id)
    result = run_task(task, args.system, args.base_url, args.model, args.num_ctx, Path(args.log))
    Path(args.out).write_text(json.dumps(result), encoding="utf-8")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
