#!/usr/bin/env python3
"""Read-only MCP stdio server for the Hermes bake-off.

Logs every tools/call with arguments and schema validity. Schema-invalid
calls return isError and are not successes. No network. No writes outside
the log file.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

from fixtures import bench_receipt, catalog_lookup, compute_sum, tools_query
from mcp_framing import read_message, write_message
from schema import mcp_tools, server_name, validate_args


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _log(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")
        handle.flush()


def _dispatch(name: str, args: dict) -> dict:
    if name == "catalog_lookup":
        return catalog_lookup(args["entry_number"])
    if name == "tools_query":
        return tools_query(args["name"], args["field"])
    if name == "bench_receipt":
        return bench_receipt(args["model"], args["metric"], args["receipt"])
    if name == "compute_sum":
        return compute_sum(args["a"], args["b"])
    if name == "submit_choice":
        return {"accepted": True, "case_id": args["case_id"], "choice": args["choice"]}
    if name == "submit_answer":
        return {"accepted": True, "task_id": args["task_id"], "value": args["value"]}
    return {"error": "unknown tool"}


def _handle(message: dict, log_path: Path, task_id: str) -> dict | None:
    method = message.get("method")
    msg_id = message.get("id")
    if method and method.startswith("notifications/"):
        return None
    if method == "initialize":
        params = message.get("params") or {}
        version = params.get("protocolVersion") or "2024-11-05"
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": version,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "pfy-hermes-bakeoff", "version": "0.1.0"},
                "instructions": "Fixture-backed read-only tools. submit_* records the answer.",
            },
        }
    if method in ("ping",):
        return {"jsonrpc": "2.0", "id": msg_id, "result": {}}
    if method in ("resources/list", "prompts/list"):
        key = "resources" if method.startswith("resources") else "prompts"
        return {"jsonrpc": "2.0", "id": msg_id, "result": {key: []}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": mcp_tools()}}
    if method == "tools/call":
        params = message.get("params") or {}
        raw_name = str(params.get("name") or "")
        name = server_name(raw_name)
        args = params.get("arguments")
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {"_unparsed": args}
        ok, error = validate_args(name, args)
        row = {
            "ts": _now(),
            "task_id": task_id,
            "method": "tools/call",
            "name": name,
            "wire_name": raw_name,
            "arguments": args if isinstance(args, dict) else {"_raw": str(args)},
            "schema_valid": ok,
            "error": error,
        }
        if not ok:
            _log(log_path, row)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": "FAIL schema: " + error}],
                    "isError": True,
                },
            }
        try:
            payload = _dispatch(name, args)
        except Exception as exc:  # noqa: BLE001 — log and return, do not kill the server
            row["schema_valid"] = False
            row["error"] = type(exc).__name__
            _log(log_path, row)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": "FAIL dispatch: " + type(exc).__name__}],
                    "isError": True,
                },
            }
        row["result_found"] = bool(payload.get("found", True)) if isinstance(payload, dict) else True
        _log(log_path, row)
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(payload, sort_keys=True)}],
                "isError": False,
            },
        }
    if msg_id is None:
        return None
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"method not found: {method}"},
    }


def serve(log_path: Path, task_id: str) -> int:
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer
    while True:
        try:
            message = read_message(stdin)
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write("mcp_server read error: " + type(exc).__name__ + "\n")
            sys.stderr.write(traceback.format_exc())
            return 1
        if message is None:
            return 0
        reply = _handle(message, log_path, task_id)
        if reply is not None:
            write_message(stdout, reply)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bake-off MCP stdio server")
    parser.add_argument("--log", required=True)
    parser.add_argument("--task-id", default="")
    args = parser.parse_args(argv)
    return serve(Path(args.log), args.task_id)


if __name__ == "__main__":
    raise SystemExit(main())
