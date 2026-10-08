"""atg-compile bench against a fake /v1 server, and the missing-endpoint exit."""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
import unittest
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "examples" / "atg-compile" / "bench.py"
CASES = ROOT / "data" / "decision-gates" / "atg-compile.cases.v0.json"
PIN = "543e778ed24fbf3fc903eb961feb627039019832"
SKIP_NO_ATG = (
    "ATG_REPO is unset; set ATG_REPO to a clean checkout or worktree of atg main at the pinned SHA"
)

MALFORMED = '{"nodes":[{"id":"bad-node","name":"x","edges":[]}],"edges":[{"src":"nope","dst":"also"}]}'
VALID = json.dumps(
    {
        "nodes": [
            {
                "id": "s",
                "name": "sum",
                "tool_name": "add",
                "inputs": {"a": 10, "b": 15},
                "declared_outputs": ["value"],
                "refine": False,
            }
        ],
        "edges": [],
    }
)


class _Server:
    def __init__(self, replies: list[str]):
        replies = list(replies)
        parent = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, fmt, *args):
                return

            def do_GET(self):
                if self.path.split("?")[0] != "/v1/models":
                    self._send(404, b'{"error":"not found"}')
                    return
                self._send(200, b'{"object":"list","data":[{"id":"fake-dag"}]}')

            def do_POST(self):
                n = int(self.headers.get("Content-Length") or 0)
                if n:
                    self.rfile.read(n)
                if not parent.replies:
                    self._send(500, b'{"error":"no scripted reply"}')
                    return
                content = parent.replies.pop(0)
                payload = json.dumps(
                    {"choices": [{"message": {"role": "assistant", "content": content}}]}
                ).encode()
                self._send(200, payload)

            def _send(self, code: int, body: bytes):
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        self.replies = replies
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.base = "http://127.0.0.1:%d" % self.httpd.server_address[1]

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()


def _atg_repo() -> str:
    return os.environ.get("ATG_REPO", "").strip()


def _cannot_run(proc: subprocess.CompletedProcess[str]) -> dict:
    line = next(ln for ln in proc.stdout.splitlines() if ln.startswith("{"))
    return json.loads(line)


def _marked_pids(run_id: str) -> str:
    proc = subprocess.run(["pgrep", "-af", run_id], capture_output=True, text=True)
    lines = [line for line in (proc.stdout or "").splitlines() if "pgrep" not in line]
    return "\n".join(lines)


class AtgCompileBenchTests(unittest.TestCase):
    def test_case_set_has_ten_distinct_tasks(self):
        data = json.loads(CASES.read_text(encoding="utf-8"))
        ids = [case["id"] for case in data["cases"]]
        self.assertEqual(len(ids), 10)
        self.assertEqual(len(set(ids)), 10)
        self.assertEqual(ids[1], "ac-02-add-ten-fifteen")
        self.assertEqual(data["atg_sha"], PIN)
        self.assertEqual(data["atg_branch"], "main")

    def test_unset_atg_repo_exits_2_with_next_step(self):
        import tempfile

        env = os.environ.copy()
        env.pop("ATG_REPO", None)
        with tempfile.TemporaryDirectory() as tmp:
            receipt = Path(tmp) / "receipt.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(BENCH),
                    "--base-url",
                    "http://127.0.0.1:9",
                    "--model",
                    "fake-dag",
                    "--receipt",
                    str(receipt),
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=20,
                env=env,
            )
        self.assertEqual(proc.returncode, 2, proc.stdout + "\n" + proc.stderr)
        self.assertIn("next step", (proc.stdout + proc.stderr).lower())
        rec = _cannot_run(proc)
        self.assertEqual(rec["verdict"], "FAIL_CANNOT_RUN")
        self.assertFalse(rec["claims_pass"])
        self.assertEqual(rec["reason"], "ATG_REPO is unset")
        self.assertIn(PIN, rec["next_step"])
        self.assertIn("clean checkout", rec["next_step"])
        self.assertIn("main", rec["next_step"])
        self.assertNotIn("DEVELOP", rec["next_step"])
        self.assertFalse(receipt.exists())

    def test_wrong_head_exits_2_without_receipt(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "atg"
            repo.mkdir()
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.email=atg-bench@example.com",
                    "-c",
                    "user.name=atg-bench",
                    "commit",
                    "--allow-empty",
                    "-m",
                    "not-the-pin",
                ],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            )
            receipt = Path(tmp) / "receipt.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(BENCH),
                    "--base-url",
                    "http://127.0.0.1:9",
                    "--model",
                    "fake-dag",
                    "--receipt",
                    str(receipt),
                    "--atg-repo",
                    str(repo),
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=20,
            )
        self.assertEqual(proc.returncode, 2, proc.stdout + "\n" + proc.stderr)
        self.assertIn("next step", (proc.stdout + proc.stderr).lower())
        rec = _cannot_run(proc)
        self.assertIn("HEAD", rec["reason"])
        self.assertIn(PIN, rec["reason"])
        self.assertIn("clean checkout", rec["next_step"])
        self.assertFalse(rec["claims_pass"])
        self.assertFalse(receipt.exists())

    def test_no_default_tmp_worktree_literal_in_tests_data_or_bench(self):
        banned = "/tmp/" + "atg-finish"
        roots = [ROOT / "tests", ROOT / "data", BENCH]
        hits = []
        for root in roots:
            files = [root] if root.is_file() else [path for path in root.rglob("*") if path.is_file()]
            for path in files:
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                if banned in text:
                    hits.append(str(path.relative_to(ROOT)))
        self.assertEqual(hits, [])

    def test_e2e_malformed_then_valid_scores_one_each(self):
        import tempfile

        repo = _atg_repo()
        if not repo:
            self.skipTest(SKIP_NO_ATG)
        server = _Server([MALFORMED, VALID])
        try:
            with tempfile.TemporaryDirectory() as tmp:
                receipt = Path(tmp) / "receipt.json"
                run_id = "atg-bench-%s" % uuid.uuid4().hex
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(BENCH),
                        "--base-url",
                        server.base,
                        "--model",
                        "fake-dag",
                        "--limit",
                        "2",
                        "--receipt",
                        str(receipt),
                        "--atg-repo",
                        repo,
                        "--health-timeout",
                        "2",
                        "--run-id",
                        run_id,
                    ],
                    cwd=str(ROOT),
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                self.assertEqual(proc.returncode, 0, proc.stdout + "\n" + proc.stderr)
                self.assertTrue(receipt.is_file())
                data = json.loads(receipt.read_text(encoding="utf-8"))
                self.assertEqual(data["n_valid"], 1)
                self.assertEqual(data["n_invalid"], 1)
                self.assertEqual(data["n_sink_correct"], 1)
                self.assertEqual(data["repairs"], 0)
                self.assertFalse(data["claims_pass"])
                self.assertEqual(data["integration_stage"], "I1")
                self.assertEqual(data["atg_sha"], PIN)
                by = {row["id"]: row for row in data["cases"]}
                self.assertFalse(by["ac-01-mul-six-seven"]["valid_dag"])
                self.assertTrue(by["ac-02-add-ten-fifteen"]["valid_dag"])
                self.assertTrue(by["ac-02-add-ten-fifteen"]["sink_correct"])
                self.assertEqual(by["ac-01-mul-six-seven"]["llm_calls"], 1)
                self.assertEqual(by["ac-02-add-ten-fifteen"]["llm_calls"], 1)
                self.assertEqual(server.replies, [])
                self.assertNotIn(run_id, _marked_pids(run_id))
        finally:
            server.stop()

    def test_endpoint_down_exits_2_without_pass_receipt_or_orphan(self):
        import tempfile

        repo = _atg_repo()
        if not repo:
            self.skipTest(SKIP_NO_ATG)
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        with tempfile.TemporaryDirectory() as tmp:
            receipt = Path(tmp) / "receipt.json"
            run_id = "atg-bench-%s" % uuid.uuid4().hex
            proc = subprocess.run(
                [
                    sys.executable,
                    str(BENCH),
                    "--base-url",
                    "http://127.0.0.1:%d" % port,
                    "--model",
                    "fake-dag",
                    "--limit",
                    "2",
                    "--receipt",
                    str(receipt),
                    "--atg-repo",
                    repo,
                    "--health-timeout",
                    "1",
                    "--run-id",
                    run_id,
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=20,
            )
        self.assertEqual(proc.returncode, 2, proc.stdout + "\n" + proc.stderr)
        text = (proc.stdout + proc.stderr).lower()
        self.assertIn("next step", text)
        rec = _cannot_run(proc)
        self.assertTrue(rec["reason"].startswith("GET "), rec["reason"])
        self.assertNotIn('"claims_pass": true', proc.stdout)
        self.assertFalse(receipt.exists())
        self.assertNotIn(run_id, _marked_pids(run_id))


if __name__ == "__main__":
    unittest.main()
