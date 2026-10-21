#!/usr/bin/env python3
"""Drive the upstream core loop on the Choice bank. Host-side only.

Gold, the id map, scores, the log and the receipt stay under host-only.
OpenCode runs go through sbun. ``propose_workers`` and ``rollout_workers``
are 1. Finals are the parallel-mode labels ``agg1``..``aggk``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import cases  # noqa: E402
import common  # noqa: E402
import pfy_adapter  # noqa: E402

# Exactly one worker. Two at k=1 overlaps bun calls; the sandbox lock then
# rejects the second, and the trace shows the overlap.
PROPOSE_WORKERS = 1
ROLLOUT_WORKERS = 1
# Parallel mode. Sequential mode names the same tree c1, which this driver
# does not read.
FINAL_LABEL = "agg1"

HOST_ONLY: Path
RUNS: Path


def log(msg: str) -> None:
    line = msg.rstrip() + "\n"
    path = HOST_ONLY / "drive.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line)
    sys.stdout.write(line)
    sys.stdout.flush()


def atomic_write(path: Path, text: str) -> None:
    """Write ``path`` via a temp file created inside host-only, then replace."""
    path = Path(path)
    root = HOST_ONLY.resolve()
    dest = path.resolve() if path.parent.exists() else (path.parent.resolve() / path.name)
    if dest != root and root not in dest.parents:
        raise SystemExit(f"refusing host write outside host-only: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(root), prefix=".host-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def canonical(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def git_sha(repo: Path) -> str:
    # A missing checkout is recorded as "missing", not fatal, until preflight runs.
    proc = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return "missing"
    return proc.stdout.strip()


def rollout_base_labels(k: int) -> list[str]:
    """Exactly k base labels. A second base at k=1 makes R=5 (want 4)."""
    return [f"base{i}" for i in range(1, k + 1)]


def train_ids_for(task_ids: list[str], heldout_ids: list[str]) -> list[str]:
    """Train batch from the split only. Held-out ids never join it."""
    del heldout_ids
    return list(task_ids)


_CUE = re.compile(r"^cue:\s*(.+)$", re.M)
_LESSON = re.compile(r"^lesson:\s*(.+)$", re.M)
_SECRET = re.compile(
    r"(TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIALS?|_API_KEY|_PAT)$", re.IGNORECASE
)


def clean_env(base: dict[str, str]) -> dict[str, str]:
    """Drop Vertex and paid-key names before they reach a child."""
    out: dict[str, str] = {}
    for key, value in base.items():
        upper = key.upper()
        if upper.startswith("GOOGLE_") or "VERTEX" in upper:
            continue
        if _SECRET.search(key):
            continue
        out[key] = value
    return out


def parse_notes(notes: str) -> tuple[str, str]:
    cue_m = _CUE.search(notes or "")
    lesson_m = _LESSON.search(notes or "")
    cue = cue_m.group(1).strip() if cue_m else "read the case state"
    lesson = lesson_m.group(1).strip() if lesson_m else "keep the harness that held up on this batch"
    return cue, lesson


def _models_url(endpoint: str) -> str:
    """One /v1/models URL. A caller that already passed /v1 is not doubled."""
    base = endpoint.strip().rstrip("/")
    if base.endswith("/v1"):
        base = base[: -len("/v1")]
    return base + "/v1/models"


def endpoint_up(endpoint: str, model: str) -> bool:
    url = _models_url(endpoint)
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            body = resp.read().decode("utf-8", "replace")
    except Exception:
        return False
    suffix = model.split("/")[-1]
    if model in body or suffix in body:
        return True
    # llama-server --model <blob> lists the blob digest, not the OpenCode name.
    sha = os.environ.get("HARNESS2_GGUF_SHA", "").strip().lower()
    if len(sha) == 64 and all(c in "0123456789abcdef" for c in sha):
        return sha in body.lower()
    return False


def bind_relay_port(endpoint: str) -> int:
    """Publish the endpoint port as the one source sbun and the config share."""
    port = urlparse(endpoint).port
    if port is None or not (1 <= int(port) <= 65535):
        print("BLOCKED: relay port unknown (set HARNESS2_RELAY_PORT)", file=sys.stderr)
        raise SystemExit(2)
    os.environ["HARNESS2_RELAY_PORT"] = str(int(port))
    common.write_opencode_config(int(port))
    return int(port)


def ensure_endpoint(endpoint: str, model: str) -> None:
    """One recheck stands in for a single relay restart. Then exit 2."""
    if endpoint_up(endpoint, model):
        return
    time.sleep(0.2)
    if endpoint_up(endpoint, model):
        log("endpoint: rechecked")
        return
    print("endpoint down", file=sys.stderr)
    raise SystemExit(2)


def boot() -> None:
    h2 = common.harness_root()
    os.environ.setdefault("HARNESS2_W", str(common.worktree()))
    sys.path.insert(0, str(h2))
    import harness2.config as h2config

    sbun = HERE / "sbun"
    h2config.BUN = sbun.resolve()
    h2config.OPENCODE_DIR = h2 / "dependencies" / "opencode"
    if not isinstance(h2config.BUN, Path):
        raise SystemExit("config.BUN must be a Path")
    from harness2.substrate.opencode import OpencodeSubstrate

    OpencodeSubstrate().preflight()


def load_dotenv_model() -> str:
    path = common.harness_root() / ".env"
    if not path.is_file():
        print("missing HARNESS2_SOLVER_MODEL", file=sys.stderr)
        raise SystemExit(2)
    parsed = common.parse_dotenv(path.read_text(encoding="utf-8"))
    err = common.check_dotenv(parsed)
    if err:
        print(err, file=sys.stderr)
        raise SystemExit(2)
    return parsed["HARNESS2_SOLVER_MODEL"]


def score_run(run_dir: Path, gold_rows: list[dict], mapping: dict[str, str], gate: float) -> dict:
    attached = []
    for case in gold_rows:
        row = dict(case)
        row["opaque"] = mapping[case["id"]]
        attached.append(row)
    from pfy_adapter import read_answers

    return cases.score_batch(attached, read_answers(run_dir), gate=gate)


def write_pins(audit: Path, payload: dict) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    path = audit / "PINS.json"
    if path.is_file() and path.read_text(encoding="utf-8") != text:
        stamp = time.strftime("%Y%m%dT%H%M%S")
        stale = audit.parent / f"_audit.stale-{stamp}"
        shutil.move(str(audit), str(stale))
        log("audit: cleared, pins changed")
    audit.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_proposer(model: str, audit: Path, timeout: int):
    from harness2.core.proposer import Proposer
    from harness2.core.spec import ChannelSpec

    class LocalProposer(Proposer):
        reused: int = 0

        def env(self) -> dict[str, str]:
            return clean_env(super().env())

        def call(self, mission, context_dir, label, **kwargs):
            # Stub runs have no transport to retry. Live runs keep upstream's
            # max_attempts (recursion passes TRANSPORT_ATTEMPTS).
            if os.environ.get("HARNESS2_STUB_MODE"):
                kwargs["max_attempts"] = 1
            reply = super().call(mission, context_dir, label, **kwargs)
            if reply.cached:
                self.reused += 1
                key = reply.audit.name if reply.audit else "reply"
                log(f"audit: reuse {label}.{key}")
            return reply

    prop = LocalProposer(
        ChannelSpec("opencode", model, effort="high", steps=40, timeout=timeout),
        audit_dir=audit,
        attempts=2,
    )
    prop.reused = 0
    return prop


def adopts(agg_score: dict, base_score: dict) -> bool:
    """agg1 replaces H_t unless it regresses. A tie on both counts adopts."""
    return (
        agg_score["n_correct"] >= base_score["n_correct"]
        and agg_score["parse_ok"] >= base_score["parse_ok"]
    )


def run_task(adapter, prop, task_id, gold_rows, mapping, gate, H, lib_dir, k, work, index):
    from harness2.core.recursion import run_parallel
    from harness2.core.spec import RunView
    from harness2.core import tree as harness_tree

    work.mkdir(parents=True, exist_ok=True)
    surface = adapter.substrate.surface()
    hdir = work / "chain-base"
    harness_tree.write_tree(surface, H, hdir, stubs=False)
    base_sha = adapter.tree_sha(H)
    views = []
    for label in rollout_base_labels(k):
        rid = f"{task_id}__{label}"
        rd = adapter.execute(task_id, hdir, rid)
        views.append(
            RunView(
                label=label,
                run_id=rid,
                run_dir=rd,
                ok=rd.is_dir(),
                delivered=adapter.delivered(rd),
            )
        )
    result = run_parallel(
        task_id,
        k,
        views,
        adapter=adapter,
        prop=prop,
        work_dir=work,
        run_id_of=lambda label, tid=task_id: f"{tid}__{label}",
        base_tree=dict(H),
        library_dir=lib_dir,
        propose_workers=PROPOSE_WORKERS,
        rollout_workers=ROLLOUT_WORKERS,
    )
    agg_tree = result.trees[FINAL_LABEL]
    agg_view = result.rollouts[FINAL_LABEL]
    base_view = result.rollouts["base1"]
    base_score = score_run(base_view.run_dir, gold_rows, mapping, gate)
    agg_score = score_run(agg_view.run_dir, gold_rows, mapping, gate)
    if adopts(agg_score, base_score):
        new_h = dict(agg_tree)
        kept = False
    else:
        log("kept H_t: agg1 regressed")
        new_h = dict(H)
        kept = True
    notes = ""
    for stage in result.stages:
        if stage.label == FINAL_LABEL:
            notes = stage.notes or ""
    cue, lesson = parse_notes(notes)
    evidence = (
        f"train batch {index}: base1 {base_score['n_correct']}/{base_score['n']}, "
        f"agg1 {agg_score['n_correct']}/{agg_score['n']}"
    )
    return {
        "H": new_h,
        "kept": kept,
        "notes": notes,
        "cue": cue,
        "lesson": lesson,
        "evidence": evidence,
        "base_sha": base_sha,
        "agg_sha": adapter.tree_sha(agg_tree),
        "base_score": base_score,
        "agg_score": agg_score,
        "base_labels": [view.label for view in views],
        "run_id": agg_view.run_id,
    }


def score_heldout(adapter, H, gold_rows, mapping, gate, step: str) -> dict:
    from harness2.core import tree as harness_tree

    root = Path(os.environ["HARNESS2_HELDOUT_ROOT"])
    (root / step / "tmp").mkdir(parents=True, exist_ok=True)
    os.environ["HARNESS2_EXEC_HELDOUT"] = step
    try:
        surface = adapter.substrate.surface()
        hdir = root / step / "harness"
        harness_tree.write_tree(surface, H, hdir, stubs=False)
        rd = adapter.execute("heldout", hdir, f"heldout__{step}")
        scored = score_run(rd, gold_rows, mapping, gate)
        dest_root = HOST_ONLY / "heldout" / step
        dest_root.mkdir(parents=True, exist_ok=True)
        dest = dest_root / rd.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.move(str(rd), str(dest))
        scored["run_dir"] = str(dest)
        return scored
    finally:
        os.environ.pop("HARNESS2_EXEC_HELDOUT", None)


def publish(receipt: dict) -> None:
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    atomic_write(HOST_ONLY / "receipt.json", text)
    if os.environ.get("HARNESS2_PUBLISH_RECEIPT", "1") != "1":
        return
    dest = common.worktree() / "pipelines" / "dogfood" / "harness2-local" / "receipt.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    global HOST_ONLY, RUNS
    parser = argparse.ArgumentParser(description="Drive harness2 on the Choice bank")
    parser.add_argument("--k", type=int, default=1)
    parser.add_argument("--cases", type=Path, default=cases.CASES_PATH)
    parser.add_argument("--split", type=Path, default=cases.SPLIT_PATH)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--max-tasks", type=int, default=0)
    parser.add_argument("--only", choices=("all", "heldout"), default="all")
    parser.add_argument("--no-heldout", action="store_true")
    parser.add_argument("--editor-timeout", type=int, default=900)
    parser.add_argument("--heldout-step", default="c")
    args = parser.parse_args(argv)
    if args.k < 1:
        print("k must be positive", file=sys.stderr)
        return 2

    wt = common.worktree()
    os.environ.setdefault("HARNESS2_W", str(wt))
    HOST_ONLY = Path(os.environ.get("HARNESS2_HOST_ONLY", wt / "tmp" / "host-only")).resolve()
    RUNS = Path(os.environ.get("HARNESS2_RUNS_DIR", wt / "tmp" / "harness2-runs")).resolve()
    held_root = wt / "tmp" / "heldout-runs"
    os.environ["HARNESS2_HELDOUT_ROOT"] = str(held_root)
    os.environ["HARNESS2_RUNS_DIR"] = str(RUNS)
    HOST_ONLY.mkdir(parents=True, exist_ok=True)
    (RUNS / "tmp").mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(RUNS / "tmp")

    model = load_dotenv_model()
    bind_relay_port(args.endpoint)
    boot()
    ensure_endpoint(args.endpoint, model)

    bank = cases.load_bank(args.cases)
    gate = float(bank.get("conf_gate") or 0.85)
    by_id = {case["id"]: case for case in bank["cases"]}
    mapping = cases.id_map(list(by_id))
    split = json.loads(args.split.read_text(encoding="utf-8"))
    train = [(f"train-{i}", list(ids)) for i, ids in enumerate(split["train_tasks"], 1)]
    if args.max_tasks:
        train = train[: args.max_tasks]
    heldout_ids = list(split["heldout"])
    for _name, ids in train:
        for rid in ids:
            if rid not in by_id:
                print(f"unknown case {rid}", file=sys.stderr)
                return 2
    for rid in heldout_ids:
        if rid not in by_id:
            print(f"unknown case {rid}", file=sys.stderr)
            return 2

    batches: dict[str, list[dict]] = {}
    gold_of: dict[str, list[dict]] = {}
    for name, ids in train:
        use = train_ids_for(ids, heldout_ids)
        gold_of[name] = [by_id[rid] for rid in use]
        batches[name] = [cases.strip_case(by_id[rid], mapping[rid]) for rid in use]
    batches["heldout"] = [cases.strip_case(by_id[rid], mapping[rid]) for rid in heldout_ids]
    gold_held = [by_id[rid] for rid in heldout_ids]

    stripped_all = cases.strip_cases(bank["cases"], mapping)
    pins = {
        "harness2": git_sha(common.harness_root()),
        "opencode": git_sha(common.harness_root() / "dependencies" / "opencode"),
        "gguf": os.environ.get("HARNESS2_GGUF_SHA", "not-loaded"),
        "ctx": int(os.environ.get("HARNESS2_CTX", "32768")),
        "temperature": 0,
        "seed": 230,
        "split_sha256": hashlib.sha256(args.split.read_bytes()).hexdigest(),
        "id_map_sha256": sha256_text(canonical(mapping)),
        "stripped_sha256": sha256_text(cases.canonical_order(stripped_all)),
        "install_mode": pfy_adapter.INSTALL_MODE,
    }
    audit = RUNS / "_audit"
    write_pins(audit, pins)
    atomic_write(HOST_ONLY / "id-map.json", canonical(mapping))
    atomic_write(
        HOST_ONLY / "gold-labels.json",
        canonical({case["id"]: case["label"] for case in bank["cases"]}),
    )

    adapter = pfy_adapter.PfyAdapter(
        batches=batches,
        train_ids=[name for name, _ids in train],
        runs=RUNS,
        model=model,
        editor_timeout=args.editor_timeout,
    )
    from harness2.core import tree as harness_tree

    H = harness_tree.read_tree(adapter.substrate.surface(), adapter.base_harness())
    receipt: dict = {
        "status": "draft",
        "install_mode": pfy_adapter.INSTALL_MODE,
        "propose_workers": PROPOSE_WORKERS,
        "rollout_workers": ROLLOUT_WORKERS,
        "k": args.k,
        "final_label": FINAL_LABEL,
        "bun": str((HERE / "sbun").resolve()),
        "reused_replies": 0,
        "negative_finding": None,
        "heldout_harness": None,
        "tasks": [],
    }

    if args.only == "heldout":
        ensure_endpoint(args.endpoint, model)
        held = score_heldout(adapter, H, gold_held, mapping, gate, args.heldout_step)
        held.pop("run_dir", None)
        atomic_write(HOST_ONLY / "heldout-score.json", canonical(held))
        receipt["heldout_harness"] = "base"
        receipt["heldout_score"] = held
        receipt["final_tree_sha256"] = adapter.tree_sha(H)
        log(
            f"heldout {args.heldout_step}: {held['n_correct']}/{held['n']} "
            f"wrong_but_confident={held['wrong_but_confident']}"
        )
        publish(receipt)
        return 0

    from harness2.core import library as library_store

    prop = make_proposer(model, audit, args.editor_timeout)
    lib = library_store.Library(
        root=RUNS / "library" / "agg",
        domain="pfy-decisions",
        surface=adapter.substrate.surface(),
    )
    lib_dir = None
    adopted = False
    for index, (name, _ids) in enumerate(train, 1):
        ensure_endpoint(args.endpoint, model)
        outcome = run_task(
            adapter,
            prop,
            name,
            gold_of[name],
            mapping,
            gate,
            H,
            lib_dir,
            args.k,
            RUNS / "work" / name,
            index,
        )
        H = outcome["H"]
        if not outcome["kept"]:
            adopted = True
        lib.add(
            name,
            H,
            why=outcome["notes"] or outcome["lesson"],
            label=FINAL_LABEL,
            run_id=outcome["run_id"],
            experience={
                "cue": outcome["cue"],
                "lesson": outcome["lesson"],
                "evidence": outcome["evidence"],
            },
        )
        lib_dir = lib.context_dir()
        atomic_write(
            HOST_ONLY / "train-scores.json",
            canonical({"task": name, "base": outcome["base_score"], "agg": outcome["agg_score"]}),
        )
        receipt["tasks"].append(
            {
                "task_id": name,
                "base_labels": outcome["base_labels"],
                "final_label": FINAL_LABEL,
                "base_tree_sha256": outcome["base_sha"],
                "agg_tree_sha256": outcome["agg_sha"],
                "kept_base": outcome["kept"],
                "library_dir": str(lib_dir or ""),
                "base_score": outcome["base_score"],
                "agg_score": outcome["agg_score"],
            }
        )
        log(
            f"task {name}: base1 {outcome['base_score']['n_correct']}/{outcome['base_score']['n']} "
            f"agg1 {outcome['agg_score']['n_correct']}/{outcome['agg_score']['n']} "
            f"kept_base={outcome['kept']}"
        )

    receipt["reused_replies"] = int(getattr(prop, "reused", 0))
    receipt["final_tree_sha256"] = adapter.tree_sha(H)
    if (not adopted) or args.no_heldout:
        if not adopted:
            log("negative finding: chain kept the base")
            receipt["negative_finding"] = "chain-kept-base"
        receipt["heldout_harness"] = None
    else:
        ensure_endpoint(args.endpoint, model)
        held = score_heldout(adapter, H, gold_held, mapping, gate, args.heldout_step)
        held.pop("run_dir", None)
        atomic_write(HOST_ONLY / "heldout-score.json", canonical(held))
        receipt["heldout_harness"] = "chain-final"
        receipt["heldout_tree_sha256"] = adapter.tree_sha(H)
        receipt["heldout_score"] = held
    publish(receipt)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        raise SystemExit(1)
