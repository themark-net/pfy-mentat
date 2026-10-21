"""Oracle, narrate detection, rates, and the fixed clear-margin rule.

Metrics are computed from the MCP server log and the client transcript.
Model prose is not a successful tool call.
"""

from __future__ import annotations

import math
import re
from typing import Any

from fixtures import expected_submit
from schema import server_name

TOOL_NAMES = (
    "submit_choice",
    "catalog_lookup",
    "tools_query",
    "bench_receipt",
    "compute_sum",
    "submit_answer",
    "mcp__bakeoff__submit_choice",
    "mcp__bakeoff__catalog_lookup",
    "mcp__bakeoff__tools_query",
    "mcp__bakeoff__bench_receipt",
    "mcp__bakeoff__compute_sum",
    "mcp__bakeoff__submit_answer",
)

_NARRATE_PHRASES = (
    "i would call",
    "i'll call",
    "i will call",
    "would call the",
    "let me call",
    "i am going to call",
)

_REFUSE = re.compile(
    r"refus|cannot|can't|will not|won't|not going to|decline|not allowed",
    re.IGNORECASE,
)

GIB = 1024 ** 3


def narrate_flag(text: str, structured_reached_server: bool, requires_call: bool) -> bool:
    """Text that names a tool or shows a JSON call, with no structured call on the server."""
    if not requires_call or structured_reached_server:
        return False
    low = text or ""
    lowered = low.lower()
    if "```" in lowered and "name" in lowered:
        return True
    if any(phrase in lowered for phrase in _NARRATE_PHRASES):
        return True
    if any(name.lower() in lowered for name in TOOL_NAMES):
        return True
    return False


def _args_match(got: dict, want: dict) -> bool:
    for key, value in want.items():
        if got.get(key) != value:
            return False
    return True


def _canon_call(call: dict) -> dict:
    out = dict(call)
    out["name"] = server_name(str(call.get("name") or ""))
    return out


def _valid_calls(server_calls: list[dict]) -> list[dict]:
    return [_canon_call(call) for call in server_calls if call.get("schema_valid")]


def _scattershot(valid: list[dict]) -> str:
    """Distinct submit_choice values. One retry of the same choice is not scattershot."""
    choices: list[str] = []
    for call in valid:
        if call.get("name") != "submit_choice":
            continue
        choice = (call.get("arguments") or {}).get("choice")
        if isinstance(choice, str) and choice:
            choices.append(choice)
    distinct = list(dict.fromkeys(choices))
    if len(distinct) > 1:
        return "scattershot choices: " + ", ".join(distinct)
    return ""


def score_task(task: dict, server_calls: list[dict], final_text: str) -> dict[str, Any]:
    """Oracle. Negatives pass only with zero calls and the expected text."""
    requires = bool(task.get("requires_call", True))
    # A schema-invalid call still "reached" the server, so it is not narrate.
    server_saw_call = len(server_calls) > 0
    narrate = narrate_flag(final_text, server_saw_call, requires)
    if task.get("kind") == "negative" or not requires:
        text_ok = _negative_text_ok(task, final_text)
        ok = len(server_calls) == 0 and text_ok
        return {"pass": ok, "narrate": False, "reason": "" if ok else "negative required zero calls and the expected text"}
    try:
        live = expected_submit(task)
    except ValueError as exc:
        return {"pass": False, "narrate": narrate, "reason": str(exc)}
    valid = _valid_calls(server_calls)
    if task.get("kind") == "choice":
        scattered = _scattershot(valid)
        if scattered:
            return {"pass": False, "narrate": narrate, "reason": scattered}
    oracle = task["oracle"]
    submit = oracle.get("submit")
    if live is not None:
        oracle_value = (submit or {}).get("args", {}).get("value")
        if live != oracle_value:
            return {
                "pass": False,
                "narrate": narrate,
                "reason": f"oracle drift: fixture {live!r} != label {oracle_value!r}",
            }
    for required in oracle.get("required", []):
        if not any(
            call["name"] == required["tool"] and _args_match(call.get("arguments") or {}, required["args"])
            for call in valid
        ):
            return {
                "pass": False,
                "narrate": narrate,
                "reason": f"missing {required['tool']} with {required['args']}",
            }
    if submit:
        submits = [call for call in valid if call["name"] == submit["tool"]]
        # The last submit is the answer. An earlier wrong value does not count.
        if not submits or not _args_match(submits[-1].get("arguments") or {}, submit["args"]):
            return {"pass": False, "narrate": narrate, "reason": "final submit mismatch"}
        # Exact value. A longer string that merely contains the label is not a pass.
        if "value" in (submit.get("args") or {}):
            got = (submits[-1].get("arguments") or {}).get("value")
            if got != submit["args"]["value"]:
                return {"pass": False, "narrate": narrate, "reason": "final submit mismatch"}
    return {"pass": True, "narrate": narrate, "reason": ""}


def _negative_text_ok(task: dict, text: str) -> bool:
    mode = task.get("negative_mode")
    body = text or ""
    if mode == "contains":
        return task.get("expect_text", "") in body
    if mode == "refuse":
        return _REFUSE.search(body) is not None
    return False


_META_TOOLS = {"tool_search", "tool_describe", "tool_call"}


def normalize_client_calls(client_calls: list[dict]) -> tuple[list[dict], int]:
    """Unwrap Hermes's tool_call batch envelope. Drop platform meta-tools.

    tool_search and tool_describe are not bake-off tool attempts. A tool_call
    envelope's inner calls are the attempts. Returns (bake-off calls, meta count).
    """
    baked: list[dict] = []
    meta = 0
    for call in client_calls or []:
        if not isinstance(call, dict):
            continue
        name = str(call.get("name") or call.get("wire_name") or "")
        args = call.get("arguments") if isinstance(call.get("arguments"), dict) else {}
        if name in ("tool_search", "tool_describe"):
            meta += 1
            continue
        if name == "tool_call" and isinstance(args.get("calls"), list):
            meta += 1
            for inner in args["calls"]:
                if not isinstance(inner, dict):
                    continue
                inner_name = str(inner.get("name") or "")
                inner_args = inner.get("arguments") if isinstance(inner.get("arguments"), dict) else {}
                short = inner_name
                if short.startswith("mcp__bakeoff__"):
                    short = short[len("mcp__bakeoff__") :]
                if short.startswith("bakeoff_"):
                    short = short[len("bakeoff_") :]
                baked.append({"name": short, "wire_name": inner_name, "arguments": inner_args})
            continue
        if name in _META_TOOLS:
            meta += 1
            continue
        baked.append(call)
    return baked, meta


def count_attempts(server_calls: list[dict], client_calls: list[dict]) -> tuple[int, int]:
    """Valid schema-checked server calls over all structured attempts.

    A client-side structured call that never reached the server counts as an
    invalid attempt. Server rows are not double-counted.
    """
    valid = sum(1 for call in server_calls if call.get("schema_valid"))
    attempts = len(server_calls)
    used = [False] * len(server_calls)
    for client in client_calls:
        matched = False
        client_name = server_name(str(client.get("name") or ""))
        for index, server in enumerate(server_calls):
            if used[index]:
                continue
            if server_name(str(server.get("name") or "")) == client_name and (server.get("arguments") or {}) == (
                client.get("arguments") or {}
            ):
                used[index] = True
                matched = True
                break
        if not matched:
            attempts += 1
    return attempts, valid


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * pct
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return ordered[int(rank)]
    weight = rank - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return (0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / den
    return (max(0.0, center - margin), min(1.0, center + margin))


def aggregate(rows: list[dict]) -> dict[str, Any]:
    n = len(rows)
    k = sum(1 for row in rows if row.get("pass"))
    attempts = sum(row.get("attempts", 0) for row in rows)
    valid = sum(row.get("valid", 0) for row in rows)
    required = [row for row in rows if row.get("requires_call")]
    narrate_n = sum(1 for row in required if row.get("narrate"))
    walls = [float(row["wall_s"]) for row in rows if row.get("wall_s") is not None]
    firsts = [float(row["ttft_s"]) for row in rows if row.get("ttft_s") is not None]
    peaks = [int(row["peak_rss_bytes"]) for row in rows if row.get("peak_rss_bytes") is not None]
    return {
        "n": n,
        "n_pass": k,
        "task_success": (k / n) if n else 0.0,
        "wilson95": wilson(k, n),
        "attempts": attempts,
        "valid": valid,
        "valid_tool_call_rate": (valid / attempts) if attempts else 1.0,
        "meta_calls": sum(int(row.get("meta_calls") or 0) for row in rows),
        "narrate_n": narrate_n,
        "narrate_tasks": len(required),
        "narrate_rate": (narrate_n / len(required)) if required else 0.0,
        "p50_s": percentile(walls, 0.50),
        "p95_s": percentile(walls, 0.95),
        "mean_s": (sum(walls) / len(walls)) if walls else None,
        "ttft_p50_s": percentile(firsts, 0.50),
        "peak_rss_bytes": max(peaks) if peaks else None,
    }


def margin_verdict(hermes: dict, baseline: dict) -> tuple[str, list[str]]:
    """Hermes WINS only when every fixed condition holds. Otherwise NO-WIN."""
    reasons: list[str] = []
    h_s = float(hermes["task_success"])
    b_s = float(baseline["task_success"])
    if h_s < b_s + 0.10 - 1e-12:
        reasons.append(
            f"task success {h_s:.4f} is {((h_s - b_s) * 100):.2f} pp over baseline {b_s:.4f}; need >= +10 pp"
        )
    h_v = float(hermes["valid_tool_call_rate"])
    b_v = float(baseline["valid_tool_call_rate"])
    if h_v < b_v - 0.02 - 1e-12:
        reasons.append(
            f"valid tool-call rate {h_v:.4f} is more than 2 pp under baseline {b_v:.4f}"
        )
    h_n = float(hermes["narrate_rate"])
    b_n = float(baseline["narrate_rate"])
    if h_n > b_n + 0.02 + 1e-12:
        reasons.append(f"narrate rate {h_n:.4f} is more than 2 pp over baseline {b_n:.4f}")
    b_p50 = baseline.get("p50_s")
    h_p50 = hermes.get("p50_s")
    if b_p50 is None or h_p50 is None:
        reasons.append("p50 latency missing")
    elif float(h_p50) > 1.5 * float(b_p50) + 1e-12:
        reasons.append(f"p50 {h_p50:.3f}s > 1.5x baseline {b_p50:.3f}s")
    peak = hermes.get("peak_rss_bytes")
    if peak is None:
        reasons.append("Hermes peak RSS missing")
    elif int(peak) > 2 * GIB:
        reasons.append(f"Hermes peak RSS {int(peak)} bytes > 2 GiB")
    return ("WIN" if not reasons else "NO-WIN", reasons)


def intervals_overlap(a: tuple[float, float], b: tuple[float, float]) -> bool:
    return a[0] <= b[1] and b[0] <= a[1]


def rescore_payload(payload: dict, tasks: list[dict]) -> dict:
    """Recompute pass, summary, and verdict from a committed results file.

    Uses the task file and the rows already in the JSON (server calls and
    final text). Does not read ./tmp transcripts.
    """
    by_id = {task["id"]: task for task in tasks}
    scored = dict(payload)
    rows = scored.get("rows") or {}
    summary: dict[str, Any] = {}
    for arm, arm_rows in rows.items():
        new_rows = []
        for row in arm_rows:
            task = by_id[row["task_id"]]
            verdict = score_task(task, row.get("server_calls") or [], row.get("final_text") or "")
            updated = dict(row)
            updated["pass"] = verdict["pass"]
            updated["narrate"] = verdict["narrate"]
            updated["reason"] = verdict["reason"]
            new_rows.append(updated)
        rows[arm] = new_rows
        arm_summary = aggregate(new_rows)
        arm_summary["wilson95"] = list(arm_summary["wilson95"])
        summary[arm] = arm_summary
    scored["rows"] = rows
    scored["summary"] = summary
    if "hermes" in summary and "baseline" in summary:
        verdict, reasons = margin_verdict(summary["hermes"], summary["baseline"])
        scored["verdict"] = verdict
        scored["verdict_failures"] = reasons
        scored["wilson_overlap"] = intervals_overlap(
            tuple(summary["hermes"]["wilson95"]),
            tuple(summary["baseline"]["wilson95"]),
        )
    return scored
