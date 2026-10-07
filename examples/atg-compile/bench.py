#!/usr/bin/env python3
"""atg-compile bench. One model, one endpoint, call atg-framework by path.

Metrics: valid-DAG rate, sink-correct rate, repairs, wall time.
Exit 2 when the pinned atg checkout or the OpenAI-compatible endpoint is
missing. That path writes no receipt. It does not start a model server.

    python3 examples/atg-compile/bench.py --base-url http://127.0.0.1:9
    python3 examples/atg-compile/bench.py --base-url http://127.0.0.1:PORT --limit 2
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pfylib.hedge import health_llamacpp_nommap  # noqa: E402

PINNED_SHA = "3c686b6cf712d3f8095e0df10f0789692814214f"
PINNED_BRANCH = "build/atg-finish"
DEFAULT_ATG_REPO = os.environ.get("ATG_REPO") or "/tmp/atg-finish"
CASES_REL = Path("data/decision-gates/atg-compile.cases.v0.json")
RECEIPT_REL = Path("pipelines/dogfood/atg-compile/receipt.json")
DRIVER_REL = Path("examples/atg-compile/atg_case_driver.py")
DEFAULT_MODEL = "qwen3.6:35b"

EXIT_OK = 0
EXIT_CANNOT_RUN = 2


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cannot_run(reason: str, next_step: str) -> int:
    rec = {
        "verdict": "FAIL_CANNOT_RUN",
        "exit_code": EXIT_CANNOT_RUN,
        "reason": reason,
        "next_step": next_step,
        "claims_pass": False,
        "feature_go": False,
        "catalog_hold": "70-75",
        "integration_stage": "I1",
    }
    print(json.dumps(rec))
    print("next step: %s" % next_step)
    return EXIT_CANNOT_RUN


def atg_head(repo: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return (proc.stdout or "").strip()


def atg_dirty(repo: Path) -> bool:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return bool((proc.stdout or "").strip())


def atg_python(repo: Path) -> Path | None:
    cand = repo / ".venv" / "bin" / "python"
    if cand.is_file() and os.access(cand, os.X_OK):
        return cand
    return None


def load_cases(path: Path, limit: int) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    cases = list(data.get("cases") or [])
    if limit > 0:
        cases = cases[:limit]
    return cases


def peak_sampler_cls():
    path = ROOT / "examples" / "local-bench" / "bench.py"
    spec = importlib.util.spec_from_file_location("pfy_local_bench_089", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.PeakSampler


def score_case(py: Path, repo: Path, driver: Path, case: dict, base: str, model: str, timeout: float, run_id: str) -> dict:
    payload = json.dumps({"base_url": base, "model": model, "timeout_s": timeout, "case": case, "max_repairs": 2})
    env = os.environ.copy()
    env.pop("ATG_JUDGE", None)
    src = str(repo / "src")
    env["PYTHONPATH"] = src if not env.get("PYTHONPATH") else src + os.pathsep + env["PYTHONPATH"]
    env["ATG_BASE_URL"] = base
    env["ATG_MODEL"] = model
    try:
        argv = [str(py), str(driver)]
        if run_id:
            argv.append(run_id)
        proc = subprocess.run(
            argv,
            input=payload,
            capture_output=True,
            text=True,
            timeout=timeout + 5,
            env=env,
            cwd=str(repo),
        )
    except subprocess.TimeoutExpired:
        return {
            "id": case.get("id"),
            "valid_dag": False,
            "sink_correct": False,
            "repairs": 0,
            "error": "atg driver timed out",
            "llm_calls": 0,
        }
    if proc.returncode != 0 or not (proc.stdout or "").strip():
        return {
            "id": case.get("id"),
            "valid_dag": False,
            "sink_correct": False,
            "repairs": 0,
            "error": (proc.stderr or proc.stdout or "driver failed")[-500:],
            "llm_calls": 0,
        }
    line = [ln for ln in proc.stdout.splitlines() if ln.strip().startswith("{")][-1]
    try:
        rec = json.loads(line)
    except json.JSONDecodeError:
        rec = {"id": case.get("id"), "valid_dag": False, "sink_correct": False, "repairs": 0, "error": "driver JSON unreadable"}
    return rec


def run(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cases", default=str(ROOT / CASES_REL))
    ap.add_argument("--base-url", default=os.environ.get("ATG_BASE_URL") or "")
    ap.add_argument("--model", default=os.environ.get("ATG_MODEL") or DEFAULT_MODEL)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--receipt", default=str(ROOT / RECEIPT_REL))
    ap.add_argument("--atg-repo", default=DEFAULT_ATG_REPO)
    ap.add_argument("--health-timeout", type=float, default=2.0)
    ap.add_argument("--case-timeout", type=float, default=60.0)
    ap.add_argument("--run-id", default="", help="marker forwarded to the atg driver argv")
    args = ap.parse_args(argv)

    models = [part.strip() for part in str(args.model).split(",") if part.strip()]
    if len(models) != 1:
        return cannot_run(
            "atg-compile runs one model at a time (got %d)" % len(models),
            "pass a single --model. Default is %s on Ollama. qwen3-coder-next is a separate llamacpp-nommap run."
            % DEFAULT_MODEL,
        )
    model = models[0]
    repo = Path(args.atg_repo).expanduser()
    if not repo.is_dir():
        return cannot_run(
            "atg checkout missing: %s" % repo,
            "set ATG_REPO to the %s checkout pinned at %s (this host: /tmp/atg-finish). Do not use ~/DEVELOP/atg-framework."
            % (PINNED_BRANCH, PINNED_SHA),
        )
    head = atg_head(repo)
    if head != PINNED_SHA:
        return cannot_run(
            "atg HEAD %s != pinned %s" % (head or "(unreadable)", PINNED_SHA),
            "check out %s at %s and pass --atg-repo. Do not score ~/DEVELOP/atg-framework."
            % (PINNED_BRANCH, PINNED_SHA),
        )
    py = atg_python(repo)
    if py is None:
        return cannot_run(
            "atg interpreter missing under %s" % (repo / ".venv"),
            "in that checkout run uv sync --extra dev, then rerun this bench. Do not start a model to do it.",
        )
    driver = ROOT / DRIVER_REL
    if not driver.is_file():
        return cannot_run("atg case driver missing: %s" % driver, "restore %s" % DRIVER_REL)
    cases_path = Path(args.cases)
    if not cases_path.is_file():
        return cannot_run("case set missing: %s" % cases_path, "restore %s" % CASES_REL)
    base = str(args.base_url or "").strip().rstrip("/")
    if not base:
        return cannot_run(
            "no OpenAI-compatible endpoint",
            "pass --base-url (Ollama http://127.0.0.1:11434, or the llamacpp-nommap port). Do not start a second model while one is loaded.",
        )
    health = health_llamacpp_nommap(base, timeout=args.health_timeout)
    if not health.get("ok"):
        return cannot_run(
            health.get("reason") or "endpoint down",
            health.get("next_step") or "start the endpoint and retry. /v1/models must answer.",
        )
    try:
        cases = load_cases(cases_path, args.limit)
    except (OSError, json.JSONDecodeError) as exc:
        return cannot_run("case set unreadable: %s" % exc, "fix %s" % cases_path)
    if not cases:
        return cannot_run("case set is empty", "restore cases in %s" % cases_path)

    sampler = peak_sampler_cls()(interval=0.25).start()
    started = time.perf_counter()
    rows = []
    try:
        for case in cases:
            rows.append(score_case(py, repo, driver, case, base, model, args.case_timeout, args.run_id))
    finally:
        peak = sampler.finish()
    wall = round(time.perf_counter() - started, 4)
    n = len(rows)
    n_valid = sum(1 for row in rows if row.get("valid_dag"))
    n_invalid = n - n_valid
    n_sink = sum(1 for row in rows if row.get("sink_correct"))
    repairs = sum(int(row.get("repairs") or 0) for row in rows)
    receipt = {
        "verdict": "SCORED",
        "claims_pass": False,
        "feature_go": False,
        "catalog_hold": "70-75",
        "integration_stage": "I1",
        "when": now(),
        "model": model,
        "one_model_at_a_time": True,
        "base_url": base,
        "atg_repo": str(repo),
        "atg_sha": head,
        "atg_branch": PINNED_BRANCH,
        "atg_dirty": atg_dirty(repo),
        "n_cases": n,
        "n_valid": n_valid,
        "n_invalid": n_invalid,
        "valid_dag_rate": round(n_valid / n, 4) if n else 0,
        "n_sink_correct": n_sink,
        "sink_correct_rate": round(n_sink / n, 4) if n else 0,
        "repairs": repairs,
        "wall_s": wall,
        "peak": peak,
        "cases": rows,
        "credit": "Zhang et al. (2026), arXiv:2607.01942. Independent reimplementation. Not a paper-benchmark claim.",
    }
    out = Path(args.receipt)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ("verdict", "n_valid", "n_invalid", "n_sink_correct", "repairs", "wall_s", "atg_sha")}))
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(run())
