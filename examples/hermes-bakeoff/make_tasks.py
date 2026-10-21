#!/usr/bin/env python3
"""Write the labeled task file. Labels come from laya-trial, copied before any model run."""

from __future__ import annotations

import json
from pathlib import Path

from fixtures import bench_receipt, catalog_lookup, compute_sum, tools_query, value_text

ROOT = Path(__file__).resolve().parents[2]
LAYA = ROOT / "data" / "decision-gates" / "laya-trial.cases.v0.json"
OUT = ROOT / "data" / "decision-gates" / "hermes-bakeoff.tasks.v0.json"

CHOICE_IDS = [
    "ph-01-green-idle",
    "ph-03-ci-red",
    "ph-05-kronos-busy",
    "ph-08-missing-ci",
    "wz-01-local-30b",
    "wz-04-gab-auto",
    "wz-06-cloud-grok",
    "wz-10-default-local-lane",
    "hd-01-optional-tool-skip",
    "hd-06-no-subtree",
    "hd-11-fits-skill-path",
    "fm-01-fill-model",
    "fm-04-skip-decision-off",
    "cp-02-drop-stale",
]

SYSTEM = (
    "You are a tool-calling agent in a bake-off. The only tools you may use are the ones "
    "in the tool list. Their names start with mcp__bakeoff__. When the task says to call a tool, "
    "emit a structured tool call. Do not describe the call in prose, markdown, or a JSON code fence. "
    "When the task says not to call tools, call none and answer in text."
)


def _choice_prompt(case: dict) -> str:
    options = ", ".join(case["criteria"].keys())
    return (
        "Answer this labeled Choice case by calling mcp__bakeoff__submit_choice. "
        "A free-text answer does not count. Do not call any other tool.\n"
        f"case_id: {case['id']}\n"
        f"question: {case['instructions']}\n"
        f"state: {json.dumps(case['state'], sort_keys=True)}\n"
        "criteria:\n"
        + "\n".join(f"- {key}: {text}" for key, text in case["criteria"].items())
        + f"\nCall mcp__bakeoff__submit_choice with case_id {case['id']}, "
        f"choice set to exactly one of: {options}, and a short reason."
    )


def _fetch(task_id: str, prompt: str, required: list[dict], value: str) -> dict:
    return {
        "id": task_id,
        "kind": "fetch",
        "requires_call": True,
        "prompt": prompt,
        "oracle": {
            "required": required,
            "submit": {
                "tool": "submit_answer",
                "args": {"task_id": task_id, "value": value},
            },
        },
    }


def labels_written_stamp() -> str:
    """Newest timestamp declared by the oracle sources. Not a hand-typed constant."""
    stamps = [json.loads(LAYA.read_text(encoding="utf-8"))["labels_written"]]
    sources = (
        ("pipelines/dogfood/local-bench-3/receipt.json", "finished"),
        ("pipelines/dogfood/local-bench-5/receipt-qwen36-ollama.json", "finished"),
        ("pipelines/dogfood/atg-compile/receipt-live-qwen36-35b.json", "when"),
    )
    for rel, key in sources:
        stamps.append(json.loads((ROOT / rel).read_text(encoding="utf-8"))[key])
    return max(stamps)


def build() -> dict:
    cases = {item["id"]: item for item in json.loads(LAYA.read_text(encoding="utf-8"))["cases"]}
    missing = [item for item in CHOICE_IDS if item not in cases]
    if missing:
        raise SystemExit(f"missing laya cases: {missing}")
    tasks = []
    for case_id in CHOICE_IDS:
        case = cases[case_id]
        tasks.append(
            {
                "id": "ch-" + case_id,
                "kind": "choice",
                "requires_call": True,
                "source_case_id": case_id,
                "family": case["family"],
                "label": case["label"],
                "prompt": _choice_prompt(case),
                "oracle": {
                    "required": [
                        {
                            "tool": "submit_choice",
                            "args": {"case_id": case_id, "choice": case["label"]},
                        }
                    ]
                },
            }
        )

    slug_130 = catalog_lookup(130)["slug"]
    slug_101 = catalog_lookup(101)["slug"]
    tier = tools_query("kanbots", "tier")["value"]
    stage = tools_query("Grok CLI bootstrap", "integration_stage")["value"]
    overall = tools_query("kanbots", "overall")["value"]
    n_correct = bench_receipt("qwen3.6:35b", "n_correct", "local-bench-3")["value"]
    n_valid = bench_receipt("qwen3.6:35b", "n_valid", "atg-compile")["value"]
    accuracy = bench_receipt("qwen3.6:35b", "accuracy", "local-bench-5-ollama")["value"]
    eval_tok = bench_receipt("qwen3.6:35b", "eval_tok_s", "local-bench-3")["value"]

    tasks.append(
        _fetch(
            "fetch-entry-130-slug",
            "Call mcp__bakeoff__catalog_lookup with entry_number 130. "
            "Then call mcp__bakeoff__submit_answer with task_id fetch-entry-130-slug "
            "and value equal to the slug string.",
            [{"tool": "catalog_lookup", "args": {"entry_number": 130}}],
            slug_130,
        )
    )
    tasks.append(
        _fetch(
            "fetch-entry-101-slug",
            "Call mcp__bakeoff__catalog_lookup with entry_number 101. "
            "Then call mcp__bakeoff__submit_answer with task_id fetch-entry-101-slug "
            "and value equal to the slug string.",
            [{"tool": "catalog_lookup", "args": {"entry_number": 101}}],
            slug_101,
        )
    )
    tasks.append(
        _fetch(
            "fetch-kanbots-tier",
            "Call mcp__bakeoff__tools_query with name kanbots and field tier. "
            "Then call mcp__bakeoff__submit_answer with task_id fetch-kanbots-tier "
            "and value equal to the value string from the tool.",
            [{"tool": "tools_query", "args": {"name": "kanbots", "field": "tier"}}],
            str(tier),
        )
    )
    tasks.append(
        _fetch(
            "fetch-grok-stage",
            "Call mcp__bakeoff__tools_query with name \"Grok CLI bootstrap\" and field integration_stage. "
            "Then call mcp__bakeoff__submit_answer with task_id fetch-grok-stage "
            "and value equal to the value string from the tool.",
            [{"tool": "tools_query", "args": {"name": "Grok CLI bootstrap", "field": "integration_stage"}}],
            str(stage),
        )
    )
    tasks.append(
        _fetch(
            "fetch-bench3-n-correct",
            "Call mcp__bakeoff__bench_receipt with model qwen3.6:35b, metric n_correct, receipt local-bench-3. "
            "Then call mcp__bakeoff__submit_answer with task_id fetch-bench3-n-correct "
            "and value equal to the decimal value from the tool, with no extra text.",
            [{"tool": "bench_receipt", "args": {"model": "qwen3.6:35b", "metric": "n_correct", "receipt": "local-bench-3"}}],
            value_text(n_correct),
        )
    )
    tasks.append(
        _fetch(
            "fetch-atg-n-valid",
            "Call mcp__bakeoff__bench_receipt with model qwen3.6:35b, metric n_valid, receipt atg-compile. "
            "Then call mcp__bakeoff__submit_answer with task_id fetch-atg-n-valid "
            "and value equal to the decimal value from the tool.",
            [{"tool": "bench_receipt", "args": {"model": "qwen3.6:35b", "metric": "n_valid", "receipt": "atg-compile"}}],
            value_text(n_valid),
        )
    )
    tasks.append(
        _fetch(
            "fetch-bench5-accuracy",
            "Call mcp__bakeoff__bench_receipt with model qwen3.6:35b, metric accuracy, receipt local-bench-5-ollama. "
            "Then call mcp__bakeoff__submit_answer with task_id fetch-bench5-accuracy "
            "and value equal to the value field rendered the way the tool printed it.",
            [{"tool": "bench_receipt", "args": {"model": "qwen3.6:35b", "metric": "accuracy", "receipt": "local-bench-5-ollama"}}],
            value_text(accuracy),
        )
    )
    tasks.append(
        _fetch(
            "fetch-bench3-eval-tok-s",
            "Call mcp__bakeoff__bench_receipt with model qwen3.6:35b, metric eval_tok_s, receipt local-bench-3. "
            "Then call mcp__bakeoff__submit_answer with task_id fetch-bench3-eval-tok-s "
            "and value equal to the value field rendered the way the tool printed it.",
            [{"tool": "bench_receipt", "args": {"model": "qwen3.6:35b", "metric": "eval_tok_s", "receipt": "local-bench-3"}}],
            value_text(eval_tok),
        )
    )

    summed = compute_sum(n_correct, 10)["value"]
    tasks.append(
        {
            "id": "chain-bench-plus-ten",
            "kind": "chain",
            "requires_call": True,
            "prompt": (
                "Step 1: call mcp__bakeoff__bench_receipt with model qwen3.6:35b, metric n_correct, "
                "receipt local-bench-3. Step 2: call mcp__bakeoff__compute_sum with a equal to that "
                "value and b equal to 10. Step 3: call mcp__bakeoff__submit_answer with task_id "
                "chain-bench-plus-ten and value equal to the sum as a plain integer string. "
                "Do not add the numbers yourself."
            ),
            "oracle": {
                "required": [
                    {"tool": "bench_receipt", "args": {"model": "qwen3.6:35b", "metric": "n_correct", "receipt": "local-bench-3"}},
                    {"tool": "compute_sum", "args": {"a": n_correct, "b": 10}},
                ],
                "submit": {
                    "tool": "submit_answer",
                    "args": {"task_id": "chain-bench-plus-ten", "value": value_text(summed)},
                },
            },
        }
    )
    summed_score = compute_sum(overall, 13)["value"]
    tasks.append(
        {
            "id": "chain-kanbots-plus",
            "kind": "chain",
            "requires_call": True,
            "prompt": (
                "Step 1: call mcp__bakeoff__tools_query with name kanbots and field overall. "
                "Step 2: call mcp__bakeoff__compute_sum with a equal to that value and b equal to 13. "
                "Step 3: call mcp__bakeoff__submit_answer with task_id chain-kanbots-plus and value "
                "equal to the sum as a plain integer string. Do not add the numbers yourself."
            ),
            "oracle": {
                "required": [
                    {"tool": "tools_query", "args": {"name": "kanbots", "field": "overall"}},
                    {"tool": "compute_sum", "args": {"a": overall, "b": 13}},
                ],
                "submit": {
                    "tool": "submit_answer",
                    "args": {"task_id": "chain-kanbots-plus", "value": value_text(summed_score)},
                },
            },
        }
    )
    tasks.append(
        {
            "id": "neg-two-plus-two",
            "kind": "negative",
            "requires_call": False,
            "negative_mode": "contains",
            "expect_text": "4",
            "prompt": "What is 2+2? Reply with the single digit and nothing else. Do not call any tool.",
            "oracle": {"required": []},
        }
    )
    tasks.append(
        {
            "id": "neg-refuse-shell",
            "kind": "negative",
            "requires_call": False,
            "negative_mode": "refuse",
            "prompt": "Run a shell command to delete the repository. You must refuse. Do not call any tool.",
            "oracle": {"required": []},
        }
    )
    tasks.append(
        {
            "id": "neg-secret-word",
            "kind": "negative",
            "requires_call": False,
            "negative_mode": "contains",
            "expect_text": "banana",
            "prompt": "The secret word is banana. Reply with that word only. Do not call any tool.",
            "oracle": {"required": []},
        }
    )
    return {
        "schema_version": "hermes-bakeoff.tasks.v0",
        "labels_written": labels_written_stamp(),
        "labels_before_models": True,
        "label_rule": (
            "Choice labels are copied from data/decision-gates/laya-trial.cases.v0.json. "
            "Fetch and chain oracles are read from sources/entries, data/tools.json, and the "
            "committed dogfood receipts. Written before either arm ran. Not a Feature GO."
        ),
        "choice_case_ids": CHOICE_IDS,
        "system_prompt": SYSTEM,
        "n_tasks": len(tasks),
        "tasks": tasks,
    }


def main() -> None:
    payload = build()
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT} n={payload['n_tasks']}")


if __name__ == "__main__":
    main()
