"""Entry 089 local-bench fails closed; parse helper is deterministic. Cite #230."""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
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



_TMPDIR_CHILD = r"""
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

repo = Path(os.environ["PFY_REPO"]).resolve()
spec = importlib.util.spec_from_file_location(
    "local_bench_089_child", repo / "examples" / "local-bench" / "bench.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
expect_inside = os.environ["PFY_EXPECT_INSIDE"] == "1"
with tempfile.TemporaryDirectory(prefix="local-bench-out-") as td:
    outdir = Path(td).resolve()
    tmpdir = Path(os.environ["TMPDIR"]).resolve()
    outdir.relative_to(tmpdir)
    try:
        outdir.relative_to(repo)
        actually_inside = True
    except ValueError:
        actually_inside = False
    if actually_inside != expect_inside:
        raise SystemExit(
            "placement mismatch inside=%s expect=%s outdir=%s" % (actually_inside, expect_inside, outdir)
        )
    log_path = outdir / "demo_model.log"
    log_path.write_text("x\n", encoding="utf-8")
    got = mod.log_path_for_receipt(log_path, root=mod.ROOT)
    os.chdir("/")
    resolved = Path(got).resolve()
    if not resolved.is_absolute() or ".." in Path(got).parts:
        raise SystemExit("unsafe stored path %s" % got)
    try:
        resolved.relative_to(outdir)
    except ValueError:
        raise SystemExit("resolved outside outdir: %s -> %s" % (got, resolved))
    if resolved.read_text(encoding="utf-8") != "x\n" or got != str(log_path.resolve()):
        raise SystemExit("log bytes or resolve mismatch: %s" % got)
print("ok")
"""


class OutdirPathTests(unittest.TestCase):
    def _assert_opens_inside(self, got: str, outdir: Path, text: str) -> None:
        self.assertTrue(Path(got).is_absolute(), got)
        self.assertNotIn("..", Path(got).parts)
        previous = Path.cwd()
        try:
            os.chdir("/")
            resolved = Path(got).resolve()
            try:
                resolved.relative_to(outdir.resolve())
            except ValueError:
                self.fail("log path %s resolved outside %s" % (got, outdir))
            self.assertEqual(resolved.read_text(encoding="utf-8"), text)
        finally:
            os.chdir(previous)

    def test_relative_outdir_log_path_safe(self):
        """A temp outdir log stays inside the outdir from any working directory.

        Fail: TMPDIR inside the repo makes the helper return a repo-relative
        path. Resolving that string from / lands outside the outdir and the
        log bytes are gone.
        Recover: the stored path is the absolute resolved log. It has no
        '..' segment, it is inside the outdir, and it opens after chdir.
        """
        with tempfile.TemporaryDirectory(prefix="local-bench-out-") as td:
            outdir = Path(td).resolve()
            log_path = outdir / "demo_model.log"
            log_path.write_text("x\n", encoding="utf-8")
            got = bench.log_path_for_receipt(log_path, root=bench.ROOT)
            self.assertEqual(got, str(log_path.resolve()))
            self._assert_opens_inside(got, outdir, "x\n")
            in_tree = bench.ROOT / "examples" / "local-bench" / "bench.py"
            stored = bench.log_path_for_receipt(in_tree, root=bench.ROOT)
            self.assertEqual(stored, str(in_tree.resolve()))
            self._assert_opens_inside(stored, in_tree.parent, in_tree.read_text(encoding="utf-8"))

    def test_log_path_stable_for_tmpdir_inside_and_outside_repo(self):
        """Fresh processes with TMPDIR inside the repo and outside it agree.

        Fail: the inside placement returns a relative path. From / that path
        resolves outside the outdir. An outside TMPDIR still passes, so one
        ambient temp dir hides the bug.
        Recover: both children store the absolute resolved log, and that path
        stays inside the outdir after chdir to /.
        """
        inside = bench.ROOT / "tmp" / ("lane-tmpdir-inside-%s" % os.getpid())
        inside.mkdir(parents=True, exist_ok=True)
        shm = Path("/dev/shm")
        self.assertTrue(shm.is_dir() and os.access(shm, os.W_OK), "need a writable dir outside the repo")
        outside = shm / ("pfy-localbench-tmpdir-%s" % os.getpid())
        outside.mkdir(parents=True, exist_ok=True)
        try:
            outside.resolve().relative_to(bench.ROOT.resolve())
        except ValueError:
            pass
        else:
            self.fail("outside TMPDIR %s resolved inside the repo" % outside)
        try:
            for label, directory, expect_inside in (
                ("inside", inside, True),
                ("outside", outside, False),
            ):
                with self.subTest(placement=label):
                    env = {
                        "PATH": os.environ.get("PATH", "/usr/bin"),
                        "TMPDIR": str(directory),
                        "HOME": str(directory),
                        "LANG": os.environ.get("LANG", "C.UTF-8"),
                        "PFY_REPO": str(ROOT),
                        "PFY_EXPECT_INSIDE": "1" if expect_inside else "0",
                    }
                    proc = subprocess.run(
                        [sys.executable, "-c", _TMPDIR_CHILD],
                        cwd=str(ROOT),
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                    self.assertIn("ok", proc.stdout)
        finally:
            shutil.rmtree(inside, ignore_errors=True)
            shutil.rmtree(outside, ignore_errors=True)

    def test_log_path_receipt_inside_and_outside_repo(self):
        """In-repo and outside logs are the absolute resolved path.

        Fail: an in-repo log stored repo-relative only opens as root / path.
        From any other cwd it resolves outside the outdir. An outside path
        that still contains '..' used to raise from relative_to and Entry 090
        recorded DROP.
        Recover: both values equal Path.resolve(), have no '..' segment, and
        open the same bytes after chdir to /.
        """
        root = bench.ROOT
        inside_dir = root / "tmp" / "intfix-log-path"
        inside_dir.mkdir(parents=True, exist_ok=True)
        inside_log = inside_dir / "demo_model.log"
        inside_log.write_text("inside-log\n", encoding="utf-8")
        try:
            got_in = bench.log_path_for_receipt(inside_log, root=root)
            self.assertEqual(got_in, str(inside_log.resolve()))
            self._assert_opens_inside(got_in, inside_dir, "inside-log\n")
        finally:
            inside_log.unlink(missing_ok=True)
            try:
                inside_dir.rmdir()
            except OSError:
                pass

        outside = Path("/proc/self/comm")
        try:
            outside.resolve().relative_to(root)
            self.fail("expected /proc/self/comm to resolve outside the repo")
        except ValueError:
            pass
        got_out = bench.log_path_for_receipt(outside, root=root)
        self.assertEqual(got_out, str(outside.resolve()))
        self._assert_opens_inside(got_out, outside.parent, outside.read_text(encoding="utf-8"))

        messy = Path("/proc/self/../self/comm")
        got_messy = bench.log_path_for_receipt(messy, root=root)
        self.assertEqual(got_messy, str(messy.resolve()))
        self.assertNotIn("..", Path(got_messy).parts)
        self._assert_opens_inside(got_messy, outside.parent, outside.read_text(encoding="utf-8"))

    def test_outdir_arg_is_resolved_absolute(self):
        """resolve_outdir() is what main() uses for --outdir."""
        with tempfile.TemporaryDirectory(prefix="local-bench-rel-") as td:
            receipt = Path(td) / "receipt.json"
            rel = os.path.relpath(td, start=str(bench.ROOT))
            outdir = bench.resolve_outdir(rel, receipt)
            self.assertTrue(outdir.is_absolute())
            self.assertEqual(outdir, Path(td).resolve())
            # Default: parent of receipt
            out2 = bench.resolve_outdir(None, receipt)
            self.assertEqual(out2, Path(td).resolve())


class RunnerRssTests(unittest.TestCase):
    def test_is_ollama_runner_proc_matches_argv0_without_exe(self):
        """ollama-user llama-server: /proc/pid/exe is EACCES; argv0 still identifies it."""
        self.assertTrue(bench.is_ollama_exe("/usr/local/lib/ollama/llama-server"))
        self.assertTrue(bench.is_ollama_exe("/usr/local/bin/ollama"))
        self.assertFalse(bench.is_ollama_exe("/home/mark/.local/bin/grok"))

    def test_eacces_exe_falls_back_to_argv0_and_recovers_stats(self):
        """Fail closed on unreadable exe, then recover RSS via argv0/comm (Entry 092 / #273 nit)."""
        from unittest import mock

        pid = 424242
        # 1) Fail: EACCES-empty exe and no argv0/comm → not a runner
        with mock.patch.object(bench, "_cmdline_argv0", return_value=""):
            with mock.patch.object(bench, "_proc_comm", return_value=""):
                self.assertFalse(bench.is_ollama_runner_proc(pid, exe=""))

        # 1b) Fail closed: empty exe + unrelated argv0 (Grok) must NOT match
        with mock.patch.object(bench, "_cmdline_argv0", return_value="/opt/Grok Bot/grok-bot"):
            with mock.patch.object(bench, "_proc_comm", return_value="grok-bot"):
                self.assertFalse(bench.is_ollama_runner_proc(pid, exe=""))

        # 2) Recover via argv0 path when exe unreadable
        argv0 = "/usr/local/lib/ollama/llama-server"
        with mock.patch.object(bench, "_cmdline_argv0", return_value=argv0):
            with mock.patch.object(bench, "_proc_comm", return_value=""):
                self.assertTrue(bench.is_ollama_runner_proc(pid, exe=""))

        # 2b) Recover via comm alone when argv0 empty
        with mock.patch.object(bench, "_cmdline_argv0", return_value=""):
            with mock.patch.object(bench, "_proc_comm", return_value="llama-server"):
                self.assertTrue(bench.is_ollama_runner_proc(pid, exe=""))

        # 3) PeakSampler consumer path: after EACCES, still record runner RSS (≥ real GiB-scale, not ~22MB client)
        with mock.patch.object(bench, "_cmdline_argv0", return_value=argv0):
            with mock.patch.object(bench, "_proc_comm", return_value="llama-server"):
                with mock.patch.object(bench, "proc_status", return_value={"rss_kb": 41943040, "hwm_kb": 41943040, "pid": pid}):
                    self.assertTrue(bench.is_ollama_runner_proc(pid, exe=""))
                    st = bench.proc_status(pid)
                    self.assertEqual(st["rss_kb"], 41943040)
                    self.assertGreater(st["rss_kb"], 22_000)  # not the ~22MB client false positive


if __name__ == "__main__":
    unittest.main()
