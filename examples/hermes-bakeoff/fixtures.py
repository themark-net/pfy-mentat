"""Read-only ground truth for bake-off tools. Paths stay inside the repo."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def catalog_lookup(entry_number: int, root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    matches = sorted((root / "sources" / "entries").glob(f"{int(entry_number)}-*.md"))
    if len(matches) != 1:
        return {
            "found": False,
            "entry_number": int(entry_number),
            "error": f"{len(matches)} files",
        }
    slug = matches[0].stem.split("-", 1)[1]
    return {
        "found": True,
        "entry_number": int(entry_number),
        "slug": slug,
        "filename": matches[0].name,
    }


def tools_query(name: str, field: str, root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    tools = json.loads((root / "data" / "tools.json").read_text(encoding="utf-8"))["tools"]
    row = next((item for item in tools if item.get("name") == name), None)
    if row is None:
        return {"found": False, "name": name, "field": field}
    if field == "tier":
        value = row.get("tier")
    elif field == "integration_stage":
        value = row.get("integration_stage")
    elif field == "overall":
        value = (row.get("scores") or {}).get("overall")
    else:
        return {"found": False, "name": name, "field": field, "error": "unknown field"}
    return {"found": value is not None, "name": name, "field": field, "value": value}


_RECEIPTS = {
    "local-bench-3": "pipelines/dogfood/local-bench-3/receipt.json",
    "local-bench-5-ollama": "pipelines/dogfood/local-bench-5/receipt-qwen36-ollama.json",
    "atg-compile": "pipelines/dogfood/atg-compile/receipt-live-qwen36-35b.json",
}


def _find_named_run(obj: Any, model: str) -> dict[str, Any] | None:
    """First object whose name matches and whose decision.n_correct is filled."""
    if isinstance(obj, dict):
        decision = obj.get("decision")
        if (
            obj.get("name") == model
            and isinstance(decision, dict)
            and decision.get("n_correct") is not None
        ):
            return obj
        for value in obj.values():
            hit = _find_named_run(value, model)
            if hit is not None:
                return hit
    elif isinstance(obj, list):
        for value in obj:
            hit = _find_named_run(value, model)
            if hit is not None:
                return hit
    return None


def bench_receipt(model: str, metric: str, receipt: str, root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    rel = _RECEIPTS.get(receipt)
    if rel is None:
        return {"found": False, "error": "unknown receipt"}
    data = json.loads((root / rel).read_text(encoding="utf-8"))
    if receipt == "atg-compile":
        if data.get("model") != model:
            return {"found": False, "error": "model mismatch", "model": data.get("model")}
        if metric not in ("n_valid", "n_sink_correct"):
            return {"found": False, "error": "metric not on this receipt"}
        return {"found": True, "model": model, "metric": metric, "receipt": receipt, "value": data[metric]}
    run = _find_named_run(data, model)
    if run is None:
        return {"found": False, "error": "model run not in receipt"}
    if metric == "n_correct":
        value = run["decision"]["n_correct"]
    elif metric == "accuracy":
        value = run["decision"]["accuracy"]
    elif metric == "eval_tok_s":
        value = run["speed"]["eval_tok_s"]
    else:
        return {"found": False, "error": "metric not on this receipt"}
    return {"found": True, "model": model, "metric": metric, "receipt": receipt, "value": value}


def compute_sum(a: float, b: float) -> dict[str, Any]:
    total = a + b
    if total == int(total):
        total = int(total)
    return {"value": total}


def value_text(value: Any) -> str:
    """Canonical submit_answer string for a tool value."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        text = format(value, "g")
        return text
    return str(value)
