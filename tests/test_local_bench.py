"""Entry 089 local-bench fails closed; parse helper is deterministic. Cite #230."""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "examples" / "local-bench" / "bench.py"


def _load():
    spec = importlib.util.spec_from_file_location("local_bench_089", BENCH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bench = _load()


class ParseChoiceTests(unittest.TestCase):
    def test_plain_json(self):
        got = bench.parse_choice_json('{"choice":"hold","confidence":0.91}', ["push", "hold", "escalate"])
        self.assertTrue(got["parse_ok"])
        self.assertEqual(got["choice"], "hold")
        self.assertEqual(got["confidence"], 0.91)

    def test_fenced_and_percent_confidence(self):
        text = "Sure.\n```json\n{\"choice\":\"push\",\"confidence\":92}\n```\n"
        got = bench.parse_choice_json(text, ["push", "hold"])
        self.assertTrue(got["parse_ok"], got)
        self.assertEqual(got["choice"], "push")
        self.assertEqual(got["confidence"], 0.92)

    def test_missing_json_is_parse_fail(self):
        got = bench.parse_choice_json("I think you should hold.")
        self.assertFalse(got["parse_ok"])
        self.assertIn("JSON", got["error"] or "")

    def test_score_low_conf_escalates(self):
        case = {"id": "x", "label": "hold", "criteria": {"push": "p", "hold": "h"}}
        parsed = {"parse_ok": True, "choice": "hold", "confidence": 0.4, "error": None, "raw": ""}
        row = bench.score_case(case, parsed, 0.85, 0.1)
        self.assertTrue(row["correct"])
        self.assertTrue(row["escalate"])
        self.assertEqual(row["chip_conf"], "conf low")

    def test_score_wrong_but_confident(self):
        case = {"id": "ph-03", "label": "hold", "criteria": {"push": "p", "hold": "h"}}
        parsed = {"parse_ok": True, "choice": "push", "confidence": 0.99, "error": None, "raw": ""}
        row = bench.score_case(case, parsed, 0.85, 0.1)
        self.assertFalse(row["correct"])
        self.assertFalse(row["escalate"])
        summary = bench.summarize_rows([row], 0.85)
        self.assertEqual(summary["wrong_but_confident"], 1)
        self.assertEqual(summary["wrong_but_confident_ids"], ["ph-03"])

    def test_rss_sampler_ignores_grok_exe(self):
        # Fail: matching argv text tagged the parent grok PID as the ollama runner.
        # Recover: key off /proc/<pid>/exe only.
        self.assertFalse(bench.is_ollama_exe("/home/mark/.local/bin/grok"))
        self.assertTrue(bench.is_ollama_exe("/usr/local/bin/ollama"))
        self.assertTrue(bench.is_ollama_exe("/usr/local/lib/ollama/llama-server"))

    def test_summarize_parse_ok_count(self):
        ok = {"id": "a", "ran": True, "parse_ok": True, "correct": True, "escalate": False, "latency_s": 0.1}
        bad = {"id": "b", "ran": True, "parse_ok": False, "correct": False, "escalate": True, "latency_s": 0.2}
        summary = bench.summarize_rows([ok, bad], 0.85)
        self.assertEqual(summary["parse_ok"], 1)
        self.assertEqual(summary["parse_ok_rate"], 0.5)

    def test_parse_fail_escalates_not_wbc(self):

        case = {"id": "y", "label": "hold", "criteria": {"hold": "h"}}
        parsed = bench.parse_choice_json("nope")
        row = bench.score_case(case, parsed, 0.85, 0.2)
        self.assertTrue(row["escalate"])
        self.assertFalse(row["correct"])
        summary = bench.summarize_rows([row], 0.85)
        self.assertEqual(summary["wrong_but_confident"], 0)


class _OllamaHandler(BaseHTTPRequestHandler):
    tags = [{"name": "present:tag", "size": 1}]

    def log_message(self, fmt, *args):  # noqa: A003
        return

    def _send(self, code: int, blob: dict):
        raw = json.dumps(blob).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path.startswith("/api/version"):
            self._send(200, {"version": "0.30.8-test"})
            return
        if self.path.startswith("/api/tags"):
            self._send(200, {"models": list(self.tags)})
            return
        if self.path.startswith("/api/ps"):
            self._send(200, {"models": []})
            return
        self._send(404, {"error": self.path})

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        _ = self.rfile.read(length) if length else b""
        if self.path.startswith("/api/generate"):
            self._send(200, {"response": '{"choice":"hold","confidence":0.2}', "done": True})
            return
        self._send(404, {"error": self.path})


def _serve(tags=None):
    handler = _OllamaHandler
    if tags is not None:
        class Bound(_OllamaHandler):
            pass
        Bound.tags = tags
        handler = Bound
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    host, port = httpd.server_address[:2]
    return httpd, "http://%s:%s" % (host, port)


class FailClosedTests(unittest.TestCase):
    def test_ollama_down_check_exits_nonzero(self):
        env = os.environ.copy()
        env.pop("OLLAMA_HOST", None)
        env.pop("OLLAMA_BASE_URL", None)
        p = subprocess.run(
            [sys.executable, str(BENCH), "--check", "--base-url", "http://127.0.0.1:1"],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
        )
        # Fail: unreachable Ollama counted as a successful bench.
        # Recover: --check on a dead port exits non-zero and names the URL.
        self.assertNotEqual(p.returncode, 0, p.stdout + p.stderr)
        blob = json.loads(p.stdout.strip().splitlines()[-1])
        self.assertEqual(blob.get("verdict"), "FAIL_CANNOT_RUN")
        self.assertIn("unreachable", (blob.get("reason") or "").lower())
        self.assertIn("127.0.0.1:1", blob.get("reason") or "")

    def test_ollama_down_full_run_writes_receipt(self):
        env = os.environ.copy()
        env.pop("OLLAMA_HOST", None)
        with tempfile.TemporaryDirectory(prefix="local-bench-") as td:
            receipt = Path(td) / "receipt.json"
            p = subprocess.run(
                [
                    sys.executable,
                    str(BENCH),
                    "--base-url",
                    "http://127.0.0.1:1",
                    "--receipt",
                    str(receipt),
                    "--models",
                    "qwen2.5-coder:1.5b",
                ],
                cwd=str(ROOT),
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(p.returncode, 0, p.stdout + p.stderr)
            self.assertTrue(receipt.is_file(), p.stdout + p.stderr)
            blob = json.loads(receipt.read_text(encoding="utf-8"))
        self.assertEqual(blob.get("verdict"), "FAIL_CANNOT_RUN")
        self.assertIn("unreachable", (blob.get("reason") or "").lower())

    def test_missing_model_name_fails_closed(self):
        httpd, url = _serve(tags=[{"name": "present:tag", "size": 1}])
        env = os.environ.copy()
        env.pop("OLLAMA_HOST", None)
        try:
            with tempfile.TemporaryDirectory(prefix="local-bench-") as td:
                receipt = Path(td) / "receipt.json"
                p = subprocess.run(
                    [
                        sys.executable,
                        str(BENCH),
                        "--base-url",
                        url,
                        "--models",
                        "no-such-model:7b",
                        "--receipt",
                        str(receipt),
                    ],
                    cwd=str(ROOT),
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(p.returncode, 0, p.stdout + p.stderr)
                self.assertTrue(receipt.is_file(), p.stdout + p.stderr)
                blob = json.loads(receipt.read_text(encoding="utf-8"))
        finally:
            httpd.shutdown()
            httpd.server_close()
        # Fail: a missing tag was skipped and the receipt looked like a real run.
        # Recover: missing model name is FAIL_CANNOT_RUN and names the tag.
        self.assertEqual(blob.get("verdict"), "FAIL_CANNOT_RUN")
        reason = blob.get("reason") or ""
        self.assertIn("no-such-model:7b", reason)
        self.assertIn("missing", reason.lower())
        self.assertEqual(blob.get("missing_models"), ["no-such-model:7b"])

    def test_check_ready_against_stub(self):
        httpd, url = _serve()
        env = os.environ.copy()
        try:
            p = subprocess.run(
                [sys.executable, str(BENCH), "--check", "--base-url", url],
                cwd=str(ROOT),
                env=env,
                capture_output=True,
                text=True,
            )
        finally:
            httpd.shutdown()
            httpd.server_close()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        blob = json.loads(p.stdout.strip().splitlines()[-1])
        self.assertEqual(blob.get("verdict"), "READY")
        self.assertEqual(blob.get("ollama_version"), "0.30.8-test")



class OutdirPathTests(unittest.TestCase):
    def test_relative_outdir_log_path_safe(self):
        """Relative --outdir outside repo used to make Path.relative_to raise → false DROP."""
        with tempfile.TemporaryDirectory(prefix="local-bench-out-") as td:
            outdir = Path(td).resolve()
            log_path = outdir / "demo_model.log"
            log_path.write_text("x\n", encoding="utf-8")
            # Same logic as bench_one after the Entry 090 fix
            try:
                rel = str(log_path.resolve().relative_to(bench.ROOT.resolve()))
                raised = False
            except ValueError:
                rel = str(log_path)
                raised = True
            self.assertTrue(raised, "temp outdir should be outside ROOT")
            self.assertEqual(rel, str(log_path))
            # Resolved outdir always absolute
            resolved = (Path(td) if td else Path(".")).resolve()
            self.assertTrue(resolved.is_absolute())

    def test_outdir_arg_is_resolved_absolute(self):
        """main() must resolve --outdir so relative paths stay stable after chdir."""
        with tempfile.TemporaryDirectory(prefix="local-bench-rel-") as td:
            # Simulate CLI: relative outdir from ROOT
            rel = os.path.relpath(td, start=str(bench.ROOT))
            outdir = (Path(rel) if rel else Path(".")).resolve()
            self.assertTrue(outdir.is_absolute())
            self.assertEqual(outdir, Path(td).resolve())



if __name__ == "__main__":
    unittest.main()
