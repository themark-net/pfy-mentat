#!/usr/bin/env python3
"""Score one atg-compile case. Stdin JSON, one JSON object on stdout.

Runs under the atg-framework interpreter (pydantic is not installed on the
pfy system Python). One structured completion per case: a malformed DAG is
an invalid case, not a hidden retry that consumes the next reply.
"""
from __future__ import annotations

import json
import sys
import time

from pydantic import ValidationError

from atg.graph import GraphError
from atg.llm import LLMError, OpenAICompatClient, _parse_model
from atg.planner import CompileError
from atg.run import run_task
from atg.tools import ToolRegistry
from atg.types import TaskNode


def add(a: int, b: int) -> dict:
    return {"value": int(a) + int(b)}


def mul(a: int, b: int) -> dict:
    return {"value": int(a) * int(b)}


def sub(a: int, b: int) -> dict:
    return {"value": int(a) - int(b)}


def concat(a: str, b: str) -> dict:
    return {"text": str(a) + str(b)}


def upper(text: str) -> dict:
    return {"text": str(text).upper()}


def lookup(key: str) -> dict:
    table = {"blue": 3, "red": 1, "green": 2}
    if key not in table:
        raise KeyError(key)
    return {"value": table[key]}


def strlen(text: str) -> dict:
    return {"value": len(str(text))}


_INT2 = {
    "type": "object",
    "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
    "required": ["a", "b"],
}
_TOOLS = {
    "add": (add, "Add integers a and b. Returns value.", _INT2),
    "mul": (mul, "Multiply integers a and b. Returns value.", _INT2),
    "sub": (sub, "Subtract b from a. Returns value.", _INT2),
    "concat": (
        concat,
        "Concatenate strings a and b. Returns text.",
        {
            "type": "object",
            "properties": {"a": {"type": "string"}, "b": {"type": "string"}},
            "required": ["a", "b"],
        },
    ),
    "upper": (
        upper,
        "Uppercase text. Returns text.",
        {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
    ),
    "lookup": (
        lookup,
        "Look up key in a fixed table (blue=3, red=1, green=2). Returns value.",
        {
            "type": "object",
            "properties": {"key": {"type": "string"}},
            "required": ["key"],
        },
    ),
    "strlen": (
        strlen,
        "Length of text. Returns value.",
        {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
    ),
}


class OneShot(OpenAICompatClient):
    """Same request shape as OpenAICompatClient, without the schema retry."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.calls = 0

    def complete_structured(self, messages, schema):
        self.calls += 1
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": schema.__name__,
                "schema": schema.model_json_schema(),
            },
        }
        content = self._content(messages, response_format=response_format)
        try:
            return _parse_model(content, schema)
        except (ValidationError, json.JSONDecodeError) as exc:
            raise LLMError("%s returned invalid structured output" % self.model) from exc


def build_registry(names: list[str]) -> ToolRegistry:
    registry = ToolRegistry()
    for name in names:
        fn, description, parameters = _TOOLS[name]
        registry.register(fn, name=name, description=description, parameters=parameters, refine=False)
    return registry


def _emit(case_id: str, valid: bool, sink_ok: bool, repairs: int, sink, error, wall_s: float, calls: int) -> None:
    json.dump(
        {
            "id": case_id,
            "valid_dag": valid,
            "sink_correct": sink_ok,
            "repairs": repairs,
            "sink": sink,
            "error": error,
            "wall_s": round(wall_s, 4),
            "llm_calls": calls,
        },
        sys.stdout,
    )
    sys.stdout.write("\n")


def score(req: dict) -> None:
    started = time.perf_counter()
    case = req["case"]
    case_id = str(case.get("id") or "")
    client = OneShot(
        req.get("model") or "fake",
        base_url=req["base_url"],
        timeout_s=float(req.get("timeout_s") or 30),
    )
    try:
        registry = build_registry(list(case.get("tools") or []))
        root = TaskNode(
            id=str(case.get("root_id") or "job"),
            name=str(case["task"]),
            declared_outputs=list(case.get("declared_outputs") or ["value"]),
            inputs=dict(case.get("inputs") or {}),
        )
        result = run_task(
            root,
            registry,
            client,
            max_repairs=int(req.get("max_repairs") or 2),
            judge=False,
        )
    except (LLMError, CompileError, ValidationError, GraphError, KeyError) as exc:
        _emit(case_id, False, False, 0, None, str(exc), time.perf_counter() - started, client.calls)
        return
    sinks = [nid for nid in result.graph.node_ids() if not result.graph.successors(nid)]
    got = None
    if len(sinks) == 1:
        got = dict(result.graph.get(sinks[0]).outputs or {})
    valid = bool(result.thought.ok)
    sink_ok = valid and got == case.get("expected_sink")
    err = None if valid else "; ".join(result.thought.errors)
    _emit(
        case_id,
        valid,
        sink_ok,
        int(result.metrics.repairs),
        got,
        err,
        time.perf_counter() - started,
        client.calls,
    )


def main() -> int:
    score(json.load(sys.stdin))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        raise SystemExit(1)
