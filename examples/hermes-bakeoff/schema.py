"""Tool JSON schemas and a small validator. The subset is what these tools use."""

from __future__ import annotations

from typing import Any

WIRE_PREFIX = "mcp__bakeoff__"

TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "submit_choice": {
        "description": "Record the Choice label for one labeled case. This is the only accepted answer for choice tasks.",
        "properties": {
            "case_id": {"type": "string", "minLength": 1},
            "choice": {"type": "string", "minLength": 1},
            "reason": {"type": "string", "minLength": 1},
        },
        "required": ["case_id", "choice", "reason"],
    },
    "catalog_lookup": {
        "description": "Look up one sources/entries file by its catalog number. Returns slug and filename.",
        "properties": {"entry_number": {"type": "integer"}},
        "required": ["entry_number"],
    },
    "tools_query": {
        "description": "Read one field of one data/tools.json row. field is tier, integration_stage, or overall.",
        "properties": {
            "name": {"type": "string", "minLength": 1},
            "field": {"type": "string", "enum": ["tier", "integration_stage", "overall"]},
        },
        "required": ["name", "field"],
    },
    "bench_receipt": {
        "description": "Read one metric for one model from a committed local-bench or atg receipt.",
        "properties": {
            "model": {"type": "string", "minLength": 1},
            "metric": {
                "type": "string",
                "enum": ["n_correct", "accuracy", "eval_tok_s", "n_valid", "n_sink_correct"],
            },
            "receipt": {
                "type": "string",
                "enum": ["local-bench-3", "local-bench-5-ollama", "atg-compile"],
            },
        },
        "required": ["model", "metric", "receipt"],
    },
    "compute_sum": {
        "description": "Add two numbers and return value. Use this instead of mental arithmetic when the task says so.",
        "properties": {
            "a": {"type": "number"},
            "b": {"type": "number"},
        },
        "required": ["a", "b"],
    },
    "submit_answer": {
        "description": "Submit the final answer string for a fetch or chain task.",
        "properties": {
            "task_id": {"type": "string", "minLength": 1},
            "value": {"type": "string", "minLength": 1},
        },
        "required": ["task_id", "value"],
    },
}


def input_schema(name: str) -> dict[str, Any]:
    spec = TOOL_SCHEMAS[name]
    return {
        "type": "object",
        "properties": spec["properties"],
        "required": spec["required"],
        "additionalProperties": False,
    }


def mcp_tools() -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "description": spec["description"],
            "inputSchema": input_schema(name),
        }
        for name, spec in TOOL_SCHEMAS.items()
    ]


def openai_tools() -> list[dict[str, Any]]:
    """Same surface Hermes shows the model: mcp__bakeoff__<tool>."""
    return [
        {
            "type": "function",
            "function": {
                "name": WIRE_PREFIX + name,
                "description": spec["description"],
                "parameters": input_schema(name),
            },
        }
        for name, spec in TOOL_SCHEMAS.items()
    ]


def server_name(wire_or_server: str) -> str:
    """Short tool name. Hermes uses mcp__bakeoff__X. opencode uses bakeoff_X."""
    name = wire_or_server or ""
    if name.startswith(WIRE_PREFIX):
        name = name[len(WIRE_PREFIX) :]
    if name.startswith("bakeoff_"):
        name = name[len("bakeoff_") :]
    return name


def validate_args(name: str, args: Any) -> tuple[bool, str]:
    """Return (ok, error). name is the server tool name, not the wire prefix."""
    if name not in TOOL_SCHEMAS:
        return False, f"unknown tool {name}"
    if isinstance(args, str):
        return False, "arguments must be an object, not a string"
    if not isinstance(args, dict):
        return False, "arguments must be an object"
    spec = TOOL_SCHEMAS[name]
    allowed = set(spec["properties"])
    extra = set(args) - allowed
    if extra:
        return False, "unexpected fields: " + ", ".join(sorted(extra))
    missing = [key for key in spec["required"] if key not in args]
    if missing:
        return False, "missing fields: " + ", ".join(missing)
    for key, rule in spec["properties"].items():
        if key not in args:
            continue
        value = args[key]
        kind = rule["type"]
        if kind == "string":
            if not isinstance(value, str):
                return False, f"{key} must be a string"
            if rule.get("minLength") and len(value.strip()) < rule["minLength"]:
                return False, f"{key} is empty"
            if "enum" in rule and value not in rule["enum"]:
                return False, f"{key} not in enum"
        elif kind == "integer":
            if isinstance(value, bool) or not isinstance(value, int):
                return False, f"{key} must be an integer"
        elif kind == "number":
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return False, f"{key} must be a number"
    return True, ""
