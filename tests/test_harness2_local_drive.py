#!/usr/bin/env python3
"""Behavior of drive.py: the upstream loop, the chain, and the host boundary.

A stub bun and a stub /v1/models server stand in for OpenCode and the model.
Every OpenCode launch still goes through sbun and the real sandbox.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DRIVE = REPO / "examples" / "harness2-local" / "drive.py"
STUB = REPO / "tmp" / "harness2" / "h2-stub-bun"
# Rollout labels only. Upstream's surface table says "c1 persona", which is not a rollout.
C1_LABEL = re.compile(r'(?:__c1\b|"final_label"\s*:\s*"c1"|"base_labels"\s*:\s*\[[^\]]*"c1")')
SESSION_LABEL = re.compile(r"^(?:base|inv|dom|agg)\d+(?:\.a\d+)?$")
CORRECT_KEY = re.compile(r'"correct"\s*:')


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cases = _load("h2cases_drive", REPO / "examples" / "harness2-local" / "cases.py")
leaks = _load("h2leaks_drive", REPO / "examples" / "harness2-local" / "leaks.py")

STUB_SRC = r'''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path

def flag(name):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return ""

ws = Path(flag("--dir") or ".")
title = flag("--title")
mode = os.environ.get("HARNESS2_STUB_MODE", "label")
right = os.environ.get("HARNESS2_STUB_RIGHT", "push")
wrong = os.environ.get("HARNESS2_STUB_WRONG", "hold")
try:
    conf = float(os.environ.get("HARNESS2_STUB_CONF", "0.99"))
except ValueError:
    conf = 0.99

def finish_editor():
    harness = ws / "context" / "harness"
    sp = harness / "systemprompt.md"
    if sp.is_file():
        text = sp.read_text(encoding="utf-8")
        line = "\nRule: read every criteria key before choosing.\n"
        if line.strip() not in text:
            sp.write_text(text + line, encoding="utf-8")
    out = ws / "output"
    out.mkdir(parents=True, exist_ok=True)
    (out / "answer.md").write_text(
        "<notes>\ncue: read the case state\n"
        "lesson: keep the harness that held up on this batch\n</notes>\n",
        encoding="utf-8",
    )

if (ws / "MISSION.md").is_file() or (ws / "context" / "harness").is_dir():
    finish_editor()
    raise SystemExit(0)

rows = []
src = ws / "cases.json"
if src.is_file():
    rows = json.loads(src.read_text(encoding="utf-8"))
answers = []
for row in rows:
    keys = list(row.get("criteria") or {})
    if mode == "wrong":
        choice = wrong
    elif mode == "first":
        choice = keys[0] if keys else right
    elif mode == "regress":
        choice = right if title == "base1" else wrong
    elif mode == "improve":
        choice = wrong if title == "base1" else right
    else:
        choice = right
    if keys and choice not in keys:
        choice = keys[0]
    answers.append({
        "case": row.get("id"),
        "choice": choice,
        "confidence": conf,
        "why": "matched a criteria key",
    })
out = ws / "output"
out.mkdir(parents=True, exist_ok=True)
(out / "answer.json").write_text(json.dumps({"answers": answers}), encoding="utf-8")
'''


class Handler(BaseHTTPRequestHandler):
    model = "llamacpp/qwen3.6-35b"

    def do_GET(self) -> None:  # noqa: N802
        body = json.dumps({"object": "list", "data": [{"id": self.model}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        return


def _serve() -> tuple[ThreadingHTTPServer, int]:
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, port


def _synth(n_tasks: int, per: int, n_held: int) -> tuple[dict, dict]:
    cases_out = []
    ids = []
    n = n_tasks * per + n_held
    for i in range(1, n + 1):
        rid = f"syn-{i:02d}"
        ids.append(rid)
        cases_out.append({
            "id": rid,
            "label": "push",
            "instructions": "Pick one allowed action.",
            "state": {"note": "nested only"},
            "criteria": {"push": "ship it", "hold": "wait"},
            "note": f"verbatim note for {rid} is twenty characters or more",
        })
    bank = {"conf_gate": 0.85, "cases": cases_out}
    order = ids[:]
    train = [order[i * per:(i + 1) * per] for i in range(n_tasks)]
    held = order[n_tasks * per:]
    split = {"seed": 230, "train_tasks": train, "heldout": held}
    return bank, split


def _sensitive(name: str) -> bool:
    if "score" in name:
        return True
    if name == "drive.log":
        return True
    if name.startswith("id-map") or name.startswith("gold"):
        return True
    if name.startswith("receipt") and name.endswith(".json"):
        return True
    return False


def _under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _bad_name(name: str) -> bool:
    low = name.lower()
    if "score" in low:
        return True
    if low.startswith("heldout"):
        return True
    if low.startswith("receipt") and low.endswith(".json"):
        return True
    if low == "drive.log" or low.startswith("id-map") or low.startswith("gold"):
        return True
    return False


def _trace_overlap(text: str) -> int:
    live = 0
    worst = 0
    for line in text.splitlines():
        kind = line.split(" ", 1)[0] if line else ""
        if kind == "start":
            live += 1
            worst = max(worst, live)
        elif kind == "end":
            live = max(0, live - 1)
    return worst


def _files(root: Path):
    if not root.is_dir():
        return
    for path in root.rglob("*"):
        if path.is_file() and not path.is_symlink():
            yield path


class DriveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch = REPO / "tmp" / "h2drv" / self._testMethodName
        if self.scratch.exists():
            subprocess.run(["chmod", "-R", "u+rwX", "--", str(self.scratch)], check=False)
            shutil.rmtree(self.scratch)
        self.runs = self.scratch / "runs"
        self.host = self.scratch / "host-only"
        self.runs.mkdir(parents=True)
        self.host.mkdir()
        (self.runs / "tmp").mkdir()
        STUB.parent.mkdir(parents=True, exist_ok=True)
        STUB.write_text(STUB_SRC, encoding="utf-8")
        STUB.chmod(0o755)
        self.httpd, self.port = _serve()
        self.started = time.time()

    def tearDown(self) -> None:
        self.httpd.shutdown()
        STUB.unlink(missing_ok=True)
        held = REPO / "tmp" / "heldout-runs"
        if held.is_dir():
            for step in held.iterdir():
                if step.name.startswith("t3"):
                    subprocess.run(["chmod", "-R", "u+rwX", "--", str(step)], check=False)
                    shutil.rmtree(step, ignore_errors=True)
        if self.scratch.exists():
            subprocess.run(["chmod", "-R", "u+rwX", "--", str(self.scratch)], check=False)
            shutil.rmtree(self.scratch, ignore_errors=True)

    def _write_bank(self, bank: dict, split: dict) -> tuple[Path, Path]:
        cases_path = self.scratch / "cases.json"
        split_path = self.scratch / "split.json"
        cases_path.write_text(json.dumps(bank), encoding="utf-8")
        split_path.write_text(json.dumps(split), encoding="utf-8")
        return cases_path, split_path

    def _run(self, mode: str, bank: dict, split: dict, extra: list[str], timeout: float):
        cases_path, split_path = self._write_bank(bank, split)
        trace = self.scratch / "bun.trace"
        hook_log = self.scratch / "writes.jsonl"
        wrapper = self.scratch / "run_drive.py"
        argv = [
            str(DRIVE),
            "--k", "1",
            "--cases", str(cases_path),
            "--split", str(split_path),
            "--endpoint", f"http://127.0.0.1:{self.port}",
            "--editor-timeout", "180",
            *extra,
        ]
        wrapper.write_text(textwrap.dedent(f"""\
            import os, sys
            from pathlib import Path
            log_path = Path({str(hook_log)!r})
            host = Path({str(self.host)!r})
            def _under(path, root):
                try:
                    Path(path).resolve().relative_to(root.resolve())
                    return True
                except ValueError:
                    return False
            def _sensitive(name):
                return (
                    "score" in name or name == "drive.log"
                    or name.startswith("id-map") or name.startswith("gold")
                    or (name.startswith("receipt") and name.endswith(".json"))
                )
            def hook(event, args):
                if getattr(hook, "busy", False):
                    return
                hook.busy = True
                try:
                    row = None
                    if event == "open" and args:
                        path, mode = args[0], args[1] if len(args) > 1 else ""
                        flags = args[2] if len(args) > 2 else 0
                        if not isinstance(path, (str, bytes, os.PathLike)):
                            return
                        text = path.decode() if isinstance(path, bytes) else str(path)
                        writing = False
                        if isinstance(mode, str) and any(ch in mode for ch in "wa+"):
                            writing = True
                        elif mode in (None, "") and isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT):
                            writing = True
                        if writing:
                            dest = Path(text)
                            if not dest.is_absolute():
                                dest = Path.cwd() / dest
                            bad = _sensitive(dest.name) and not _under(dest, host)
                            row = {{"op": "open", "path": str(dest), "bad": bad}}
                    elif event == "os.rename" and len(args) >= 2:
                        src, dst = Path(str(args[0])), Path(str(args[1]))
                        if not src.is_absolute():
                            src = Path.cwd() / src
                        if not dst.is_absolute():
                            dst = Path.cwd() / dst
                        bad = False
                        if _sensitive(dst.name) and not _under(dst, host):
                            bad = True
                        if _sensitive(dst.name) and not _under(src, host):
                            bad = True
                        if _sensitive(src.name) and not _under(src, host):
                            bad = True
                        row = {{"op": "rename", "src": str(src), "dst": str(dst), "bad": bad}}
                    if row is not None:
                        with log_path.open("a", encoding="utf-8") as fh:
                            fh.write(__import__("json").dumps(row) + "\\n")
                finally:
                    hook.busy = False
            sys.addaudithook(hook)
            import runpy
            sys.argv = {argv!r}
            runpy.run_path({str(DRIVE)!r}, run_name="__main__")
        """), encoding="utf-8")
        env = os.environ.copy()
        env.update({
            "HARNESS2_RUNS_DIR": str(self.runs),
            "HARNESS2_HOST_ONLY": str(self.host),
            "HARNESS2_PUBLISH_RECEIPT": "0",
            "HARNESS2_REAL_BUN": str(STUB),
            "HARNESS2_BUN_TRACE": str(trace),
            "HARNESS2_STUB_MODE": mode,
            "HARNESS2_EXEC_TIMEOUT": "90",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONUNBUFFERED": "1",
        })
        env.pop("HARNESS2_HELDOUT", None)
        env.pop("HARNESS2_EXEC_HELDOUT", None)
        proc = subprocess.run(
            [sys.executable, str(wrapper)],
            cwd=str(REPO),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc, trace, hook_log

    def _receipt(self) -> dict:
        return json.loads((self.host / "receipt.json").read_text(encoding="utf-8"))

    def _assert_trace(self, trace: Path, expect: int) -> None:
        text = trace.read_text(encoding="utf-8") if trace.is_file() else ""
        starts = sum(1 for line in text.splitlines() if line.startswith("start "))
        self.assertEqual(_trace_overlap(text), 1 if starts else 0, text)
        self.assertLessEqual(_trace_overlap(text), 1, text)
        self.assertEqual(starts, expect, text[-500:])

    def _assert_host_boundary(self, hook_log: Path) -> None:
        self.assertTrue((self.host / "drive.log").is_file())
        self.assertTrue((self.host / "receipt.json").is_file())
        self.assertTrue((self.host / "id-map.json").is_file())
        self.assertTrue((self.host / "gold-labels.json").is_file())
        rows = []
        if hook_log.is_file():
            for line in hook_log.read_text(encoding="utf-8").splitlines():
                rows.append(json.loads(line))
        bad = [row for row in rows if row.get("bad")]
        self.assertEqual(bad, [], bad[:5])
        roots = [self.runs]
        state = REPO / "tmp" / "state"
        if state.is_dir():
            roots.append(state)
        for root in roots:
            for path in _files(root):
                if root.name == "state":
                    rel = path.relative_to(root)
                    if rel.parts and rel.parts[0] in {"uv-cache", "uv-python", "uv-bin", "uv-tools", "npm-cache", "bun-cache", "bun", "xdg-cache", "xdg-config", "xdg-data", "xdg-state"}:
                        continue
                    if path.stat().st_mtime < self.started - 1:
                        continue
                self.assertFalse(_bad_name(path.name), path)
                if path.stat().st_size > 1_000_000:
                    continue
                if path.suffix in {".json", ".md", ".txt", ".log", ".jsonl", ".stderr"} or path.suffix == "":
                    text = path.read_text(encoding="utf-8", errors="replace")
                    self.assertIsNone(CORRECT_KEY.search(text), path)

    def _assert_leak(self, bank: dict, split: dict) -> None:
        ids = [case["id"] for case in bank["cases"]]
        labels = sorted({case["label"] for case in bank["cases"]})
        notes = [case.get("note") or "" for case in bank["cases"]]
        mapping = cases.id_map(ids)
        raw = (self.scratch / "cases.json").read_text(encoding="utf-8")
        canon_map = cases.canonical(mapping)
        held_real = set(split["heldout"])
        held_opaque = {mapping[rid] for rid in held_real}
        for path in _files(self.runs):
            if path.stat().st_size > 1_000_000:
                continue
            if path.suffix not in {".json", ".md", ".txt", ".log", ".jsonl", ".stderr", ""} and path.name != "cases.json":
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            self.assertNotIn(raw, text, path)
            self.assertNotIn(canon_map, text, path)
            self.assertEqual(leaks.real_id_hits(text, ids), [], path)
            self.assertEqual(leaks.short_id_hits(text), [], path)
            self.assertEqual(leaks.note_hits(text, notes), [], path)
            scanned = leaks.answer_pair_text(text) if path.name == "answer.json" else text
            self.assertEqual(leaks.pair_hits(scanned, ids, labels), [], path)
            obj = None
            if path.suffix == ".json":
                try:
                    obj = json.loads(text)
                except json.JSONDecodeError:
                    obj = None
            self._assert_label_keys(obj, path)
            if path.name in {"MISSION.md", "task.md", "cases.json"} or path.name.endswith(".mission.md"):
                for token in held_real:
                    self.assertNotIn(token, text, path)
                for token in held_opaque:
                    self.assertIsNone(
                        re.search(rf"(?<![\w]){re.escape(token)}(?![\w])", text),
                        f"{token} in {path}",
                    )

    def _assert_label_keys(self, obj, path: Path) -> None:
        # Audit meta uses "label" for the session name (agg1.a1), not the gold label.
        if path.name.endswith(".meta.json") and isinstance(obj, dict) and "label" in obj:
            self.assertRegex(str(obj["label"]), SESSION_LABEL, path)
            obj = {k: v for k, v in obj.items() if k != "label"}
        if isinstance(obj, list) and obj and all(isinstance(row, dict) and "criteria" in row for row in obj):
            for row in obj:
                self.assertFalse(set(row) & {"label", "note"}, path)
            return
        if isinstance(obj, dict):
            for key, value in obj.items():
                self.assertNotIn(key, {"label", "note"}, path)
                self._assert_label_keys(value, path)
        elif isinstance(obj, list):
            for value in obj:
                self._assert_label_keys(value, path)

    def test_endpoint_down_writes_no_receipt(self) -> None:
        self.httpd.shutdown()
        bank, split = _synth(1, 1, 1)
        proc, _trace, _hook = self._run("label", bank, split, ["--no-heldout", "--max-tasks", "1"], 60)
        self.assertEqual(proc.returncode, 2, proc.stderr[-800:])
        self.assertIn("endpoint down", proc.stderr)
        self.assertFalse((self.host / "receipt.json").exists())
        self.assertNotIn("PASS", proc.stdout)

    def test_heldout_wrong_choice_scores_zero(self) -> None:
        bank, split = _synth(1, 1, 16)
        proc, trace, hook = self._run(
            "wrong", bank, split, ["--only", "heldout", "--heldout-step", "t3w"], 180,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr[-1500:] + "\n" + proc.stdout[-800:])
        self._assert_trace(trace, 1)
        receipt = self._receipt()
        self.assertEqual(receipt["status"], "draft")
        self.assertEqual(receipt["heldout_harness"], "base")
        score = receipt["heldout_score"]
        self.assertEqual(score["n"], 16)
        self.assertEqual(score["n_correct"], 0)
        self.assertEqual(score["wrong_but_confident"], 16)
        self.assertEqual(score["parse_ok"], 1.0)
        self._assert_host_boundary(hook)
        self.assertTrue(str(receipt["bun"]).endswith("/sbun"))

    def test_improve_chain_adopts_and_scores_heldout(self) -> None:
        bank, split = _synth(2, 2, 16)
        proc, trace, hook = self._run(
            "improve", bank, split, ["--heldout-step", "t3i"], 600,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr[-2000:] + "\n" + proc.stdout[-1500:])
        self._assert_trace(trace, 15)
        receipt = self._receipt()
        self.assertEqual(receipt["status"], "draft")
        self.assertEqual(receipt["final_label"], "agg1")
        self.assertEqual(receipt["k"], 1)
        self.assertEqual(len(receipt["tasks"]), 2)
        blob = json.dumps(receipt)
        self.assertIsNone(C1_LABEL.search(blob), blob)
        for task in receipt["tasks"]:
            self.assertEqual(task["base_labels"], ["base1"])
            self.assertEqual(task["final_label"], "agg1")
        first, second = receipt["tasks"]
        self.assertNotEqual(first["agg_tree_sha256"], first["base_tree_sha256"])
        self.assertEqual(second["base_tree_sha256"], first["agg_tree_sha256"])
        self.assertFalse(second["kept_base"])
        self.assertEqual(first["base_score"]["n_correct"], 0)
        self.assertEqual(first["agg_score"]["n_correct"], 2)
        snap = list((self.runs / "work" / "train-2").rglob("EXPERIENCE.md"))
        in_context = [p for p in snap if "context" in p.parts and "library" in p.parts]
        self.assertTrue(in_context, [str(p) for p in snap])
        lib = in_context[0].parents[2]
        self.assertEqual(len(list(lib.rglob("EXPERIENCE.md"))), 1)
        self.assertEqual(receipt["heldout_harness"], "chain-final")
        self.assertEqual(receipt["heldout_tree_sha256"], receipt["final_tree_sha256"])
        self.assertEqual(receipt["heldout_score"]["n_correct"], 16)
        self.assertEqual(receipt["heldout_score"]["n"], 16)
        self.assertIn("task train-1:", (self.host / "drive.log").read_text(encoding="utf-8"))
        names = [p.name for p in (self.runs / "executions").iterdir()]
        self.assertEqual(sum(name.endswith("__base1") for name in names), 2)
        self.assertFalse(any(name.endswith("__base2") or name.endswith("__c1") for name in names))
        for path in (self.runs / "executions").iterdir():
            self.assertNotIn("__c1", path.name, path.name)
        self._assert_host_boundary(hook)
        self._assert_leak(bank, split)
        self.assertTrue((self.host / "heldout-score.json").is_file())
        self.assertTrue((self.host / "train-scores.json").is_file())

    def test_regress_keeps_the_base(self) -> None:
        bank, split = _synth(2, 2, 16)
        proc, trace, _hook = self._run(
            "regress", bank, split, ["--heldout-step", "t3r"], 600,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr[-2000:] + "\n" + proc.stdout[-1500:])
        self._assert_trace(trace, 14)
        receipt = self._receipt()
        self.assertTrue(all(task["kept_base"] for task in receipt["tasks"]))
        self.assertEqual(receipt["tasks"][1]["base_tree_sha256"], receipt["tasks"][0]["base_tree_sha256"])
        self.assertEqual(receipt["negative_finding"], "chain-kept-base")
        self.assertIsNone(receipt["heldout_harness"])
        self.assertFalse((self.host / "heldout-score.json").exists())
        log = (self.host / "drive.log").read_text(encoding="utf-8")
        self.assertIn("kept H_t: agg1 regressed", log)
        self.assertEqual(receipt["tasks"][0]["base_score"]["n_correct"], 2)
        self.assertEqual(receipt["tasks"][0]["agg_score"]["n_correct"], 0)

    def test_real_bank_hides_labels_and_heldout(self) -> None:
        bank = cases.load_bank()
        split = json.loads(cases.SPLIT_PATH.read_text(encoding="utf-8"))
        proc, trace, hook = self._run(
            "first", bank, split, ["--max-tasks", "1", "--no-heldout"], 400,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr[-2000:] + "\n" + proc.stdout[-1500:])
        self._assert_trace(trace, 7)
        receipt = self._receipt()
        self.assertEqual(receipt["tasks"][0]["base_labels"], ["base1"])
        self.assertEqual(receipt["final_label"], "agg1")
        self.assertIsNone(C1_LABEL.search(json.dumps(receipt)))
        pins = json.loads((self.runs / "_audit" / "PINS.json").read_text(encoding="utf-8"))
        stripped = cases.strip_cases(bank["cases"], cases.id_map(cases.case_ids(bank)))
        digest = __import__("hashlib").sha256(cases.canonical_order(stripped).encode()).hexdigest()
        self.assertEqual(pins["stripped_sha256"], digest)
        self.assertEqual(
            digest,
            "ab0ee29bbe75b46d33248729f9c4dd61376ec357275c8debf6efdb4d296e1b7e",
        )
        self.assertEqual(pins["install_mode"], "workspace_config")
        self._assert_host_boundary(hook)
        self._assert_leak(bank, split)


if __name__ == "__main__":
    unittest.main()
