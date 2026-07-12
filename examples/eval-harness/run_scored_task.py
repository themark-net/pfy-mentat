#!/usr/bin/env python3
"""Tier-1 scored coding task via LiteLLM → local OpenAI-compatible endpoint.

Exit: 0 pass, 1 fail, 2 skip (missing model/prereq).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
from pathlib import Path


def _normalize_ascii_punct(s: str) -> str:
    """Map common smart punctuation that breaks Python syntax (small models)."""
    table = str.maketrans(
        {
            "\u2013": "-",  # en dash
            "\u2014": "-",  # em dash
            "\u2212": "-",  # minus
            "\u2018": "'",
            "\u2019": "'",
            "\u201c": '"',
            "\u201d": '"',
            "\u00a0": " ",
        }
    )
    return s.translate(table)


def extract_python(text: str) -> str:
    """Pull executable Python from model output (fences, def blocks, or raw)."""
    text = _normalize_ascii_punct(text.strip())
    m = re.search(r"```(?:python)?\s*([\s\S]*?)```", text, re.I)
    if m:
        text = m.group(1).strip()
        text = _normalize_ascii_punct(text)

    # Prefer a contiguous def … body (stop at next top-level prose/heading)
    def_m = re.search(
        r"(^|\n)(def\s+\w+\s*\([^)]*\)\s*(?:->\s*[^:]+)?\s*:[\s\S]*)",
        text,
    )
    if def_m:
        body = def_m.group(2)
        lines: list[str] = []
        for i, line in enumerate(body.splitlines()):
            if i == 0:
                lines.append(line)
                continue
            # Stop when model resumes prose after the function
            if line.strip() and not line[0].isspace() and not line.startswith(
                ("def ", "class ", "@", "import ", "from ", "#")
            ):
                break
            lines.append(line)
        text = "\n".join(lines).rstrip()

    return text


def load_tests(path: Path):
    spec = importlib.util.spec_from_file_location("task_tests", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load tests: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "run_tests"):
        raise RuntimeError("test_task.py must define run_tests(ns) -> list[str]")
    return mod.run_tests


def resolve_model() -> str:
    return (
        os.environ.get("EVAL_MODEL")
        or os.environ.get("LITELLM_SMOKE_MODEL")
        or "qwen2.5:14b"
    )


def score_task(
    task: str,
    tasks_root: Path,
    *,
    model_name: str | None = None,
    base: str | None = None,
    api_key: str | None = None,
    max_tokens: int = 512,
) -> dict:
    """Run one task; return result dict with pass/failures (never raises for score fails)."""
    task_dir = tasks_root / task
    prompt_path = task_dir / "prompt.txt"
    tests_path = task_dir / "test_task.py"
    if not prompt_path.is_file() or not tests_path.is_file():
        return {
            "task": task,
            "model": model_name or resolve_model(),
            "pass": False,
            "failures": [f"task incomplete: {task_dir}"],
            "error": "incomplete_task",
            "skip": False,
        }

    base = (base or os.environ.get("OPENAI_BASE_URL", "http://host.docker.internal:11435/v1")).rstrip(
        "/"
    )
    model_name = model_name or resolve_model()
    api_key = api_key or os.environ.get("OLLAMA_API_KEY", "ollama")
    litellm_model = f"openai/{model_name}"

    try:
        from litellm import completion
    except ImportError:
        return {
            "task": task,
            "model": litellm_model,
            "pass": False,
            "failures": ["litellm not installed"],
            "error": "import",
            "skip": False,
        }

    prompt = prompt_path.read_text(encoding="utf-8")
    try:
        resp = completion(
            model=litellm_model,
            api_base=base,
            api_key=api_key,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0,
        )
    except Exception as e:  # noqa: BLE001
        return {
            "task": task,
            "model": litellm_model,
            "pass": False,
            "failures": [f"completion failed: {e}"],
            "error": "completion",
            "skip": False,
        }

    raw = (resp.choices[0].message.content or "").strip()
    code = extract_python(raw)
    if not code:
        return {
            "task": task,
            "model": litellm_model,
            "pass": False,
            "failures": ["empty model code"],
            "error": "empty",
            "code_preview": "",
            "raw_chars": len(raw),
            "skip": False,
        }

    ns: dict = {}
    try:
        exec(compile(code, "<candidate>", "exec"), ns, ns)  # noqa: S102
    except Exception as e:  # noqa: BLE001
        return {
            "task": task,
            "model": litellm_model,
            "pass": False,
            "failures": [f"compile/exec: {type(e).__name__}: {e}"],
            "error": "exec",
            "code_preview": code[:500],
            "raw_chars": len(raw),
            "skip": False,
        }

    run_tests = load_tests(tests_path)
    fails = run_tests(ns)
    return {
        "task": task,
        "model": litellm_model,
        "pass": len(fails) == 0,
        "failures": fails,
        "code_preview": code[:500],
        "raw_chars": len(raw),
        "code_chars": len(code),
        "skip": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--task",
        default="001-is-palindrome",
        help="Task directory name under tasks/",
    )
    ap.add_argument(
        "--tasks-root",
        type=Path,
        default=Path(__file__).resolve().parent / "tasks",
    )
    args = ap.parse_args()

    model_name = resolve_model()
    base = os.environ.get("OPENAI_BASE_URL", "http://host.docker.internal:11435/v1").rstrip("/")
    print(f"eval tier1: task={args.task} base={base} model=openai/{model_name}", flush=True)

    result = score_task(args.task, args.tasks_root, model_name=model_name, base=base)
    print(
        f"eval: model_output_chars={result.get('raw_chars', '?')} "
        f"code_chars={result.get('code_chars', '?')}",
        flush=True,
    )
    print(
        json.dumps(
            {k: result[k] for k in ("task", "model", "pass", "failures") if k in result},
            indent=2,
        ),
        flush=True,
    )

    if result.get("error") == "exec":
        print(f"SCORE: FAIL ({result['failures'][0]})", flush=True)
        print("--- code ---", flush=True)
        print((result.get("code_preview") or "")[:2000], flush=True)
        return 1

    if not result.get("pass"):
        print("SCORE: FAIL", flush=True)
        for f in result.get("failures") or []:
            print(f"  - {f}", flush=True)
        return 1

    print("SCORE: PASS", flush=True)
    out = os.environ.get("EVAL_RESULT_JSON")
    if out:
        Path(out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
