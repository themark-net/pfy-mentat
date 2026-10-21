"""Bake-off behavior tests. Offline. No Ollama. No network.

The live mark is deselected unless HERMES_BAKEOFF_LIVE=1.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BAKE = ROOT / "examples" / "hermes-bakeoff"
if str(BAKE) not in sys.path:
    sys.path.insert(0, str(BAKE))

from guard import assert_hermes_home  # noqa: E402
from make_tasks import build  # noqa: E402
from mcp_framing import read_message, write_message  # noqa: E402
from mcp_server import parse_ts, stamp_now  # noqa: E402
from schema import validate_args  # noqa: E402
from score import count_attempts, margin_verdict, narrate_flag, normalize_client_calls, score_task  # noqa: E402

try:
    import pytest
except ModuleNotFoundError:  # pragma: no cover - unittest path on a machine without pytest
    class _Mark:
        def live(self, obj):
            return obj

        def __getattr__(self, _name):
            def deco(*args, **_kwargs):
                if args and callable(args[0]):
                    return args[0]

                def wrap(fn):
                    return fn

                return wrap

            return deco

    class pytest:  # type: ignore
        mark = _Mark()

        @staticmethod
        def skip(reason):
            raise unittest.SkipTest(reason)


def _arm(success, valid=1.0, narrate=0.0, p50=10.0, peak=1024):
    return {
        "task_success": success,
        "valid_tool_call_rate": valid,
        "narrate_rate": narrate,
        "p50_s": p50,
        "peak_rss_bytes": peak,
    }


class HermesBakeoffTests(unittest.TestCase):
    def test_check_fails_closed_when_ollama_is_unreachable(self):
        proc = subprocess.run(
            [
                sys.executable,
                str(BAKE / "run.py"),
                "--check",
                "--base-url",
                "http://127.0.0.1:59999",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("FAIL", proc.stdout + proc.stderr)

    def test_check_fails_closed_when_model_tag_is_missing(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                body = json.dumps({"models": [{"name": "other:1"}]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, fmt, *args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        port = server.server_address[1]
        import threading

        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            proc = subprocess.run(
                [
                    sys.executable,
                    str(BAKE / "run.py"),
                    "--check",
                    "--base-url",
                    f"http://127.0.0.1:{port}/v1",
                    "--model",
                    "qwen3.6:35b",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=15,
            )
        finally:
            server.shutdown()
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("FAIL: model tag missing", proc.stdout + proc.stderr)

    def test_schema_invalid_call_is_not_success(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "calls.jsonl"
            proc = subprocess.Popen(
                [
                    sys.executable,
                    str(BAKE / "mcp_server.py"),
                    "--log",
                    str(log),
                    "--task-id",
                    "bad",
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
            )
            try:
                write_message(
                    proc.stdin,
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {"protocolVersion": "2024-11-05", "capabilities": {}},
                    },
                )
                reply = read_message(proc.stdout)
                self.assertEqual(reply["id"], 1)
                write_message(
                    proc.stdin,
                    {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
                )
                write_message(
                    proc.stdin,
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/call",
                        "params": {"name": "submit_choice", "arguments": {"choice": 3}},
                    },
                )
                reply = read_message(proc.stdout)
                self.assertTrue(reply["result"]["isError"])
            finally:
                proc.kill()
                proc.wait(timeout=5)
            rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(rows), 1)
            self.assertFalse(rows[0]["schema_valid"])
            task = {
                "id": "bad",
                "kind": "choice",
                "requires_call": True,
                "oracle": {
                    "required": [
                        {"tool": "submit_choice", "args": {"case_id": "ph-01-green-idle", "choice": "push"}}
                    ]
                },
            }
            scored = score_task(task, rows, "")
            self.assertFalse(scored["pass"])
            ok, _error = validate_args("submit_choice", {"choice": 3})
            self.assertFalse(ok)

    def test_ttft_keeps_milliseconds_and_rejects_whole_second_stamps(self):
        """A whole-second server stamp must not score. TTFT stays sub-second."""
        import tempfile

        from run import score_one

        stamped = stamp_now()
        self.assertRegex(stamped, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
        whole = stamped.split(".", 1)[0] + "Z"
        with self.assertRaises(ValueError):
            parse_ts(whole)

        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "calls.jsonl"
            proc = subprocess.Popen(
                [
                    sys.executable,
                    str(BAKE / "mcp_server.py"),
                    "--log",
                    str(log),
                    "--task-id",
                    "ttft",
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
            )
            try:
                write_message(
                    proc.stdin,
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {"protocolVersion": "2024-11-05", "capabilities": {}},
                    },
                )
                self.assertEqual(read_message(proc.stdout)["id"], 1)
                write_message(
                    proc.stdin,
                    {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
                )
                write_message(
                    proc.stdin,
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/call",
                        "params": {
                            "name": "submit_choice",
                            "arguments": {
                                "case_id": "ph-01-green-idle",
                                "choice": "push",
                                "reason": "green",
                            },
                        },
                    },
                )
                reply = read_message(proc.stdout)
                self.assertFalse(reply["result"]["isError"])
            finally:
                if proc.stdin:
                    proc.stdin.close()
                if proc.stdout:
                    proc.stdout.close()
                proc.kill()
                proc.wait(timeout=5)
            rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(rows), 1)
            self.assertRegex(rows[0]["ts"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
            parsed = parse_ts(rows[0]["ts"])
            task = {
                "id": "ttft",
                "kind": "choice",
                "requires_call": True,
                "oracle": {
                    "required": [
                        {"tool": "submit_choice", "args": {"case_id": "ph-01-green-idle", "choice": "push"}}
                    ]
                },
            }
            sampled = {
                "timed_out": False,
                "stderr": "",
                "returncode": 0,
                "stdout": "",
                "wall_s": 1.0,
                "started": parsed - 0.25,
                "peak": {"agent_peak_rss_bytes": 1000, "ollama_peak_rss_bytes": 0},
            }
            missing = Path(tmp) / "no-arm.json"
            scored = score_one(task, missing, log, sampled)
            self.assertEqual(scored["ttft_s"], 0.25)
            whole_row = dict(rows[0])
            whole_row["ts"] = rows[0]["ts"].split(".", 1)[0] + "Z"
            whole_log = Path(tmp) / "whole.jsonl"
            whole_log.write_text(json.dumps(whole_row) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                score_one(task, missing, whole_log, sampled)

    def test_narrate_detects_fenced_json_and_ignores_a_real_call(self):
        fenced = "I would answer like this:\n```json\n{name: submit_choice, arguments: {choice: push}}\n```"
        self.assertTrue(narrate_flag(fenced, structured_reached_server=False, requires_call=True))
        self.assertFalse(narrate_flag(fenced, structured_reached_server=True, requires_call=True))
        task = {
            "kind": "choice",
            "requires_call": True,
            "oracle": {"required": [{"tool": "submit_choice", "args": {"case_id": "x", "choice": "push"}}]},
        }
        real = [{"name": "submit_choice", "schema_valid": True, "arguments": {"case_id": "x", "choice": "push", "reason": "ok"}}]
        self.assertFalse(score_task(task, real, fenced)["narrate"])
        self.assertTrue(score_task(task, [], fenced)["narrate"])

    def test_oracle_fails_when_the_right_tool_has_wrong_args(self):
        task = {
            "kind": "choice",
            "requires_call": True,
            "oracle": {
                "required": [
                    {"tool": "submit_choice", "args": {"case_id": "ph-01-green-idle", "choice": "push"}}
                ]
            },
        }
        calls = [
            {
                "name": "submit_choice",
                "schema_valid": True,
                "arguments": {"case_id": "ph-01-green-idle", "choice": "hold", "reason": "guess"},
            }
        ]
        scored = score_task(task, calls, "")
        self.assertFalse(scored["pass"])
        self.assertIn("submit_choice", scored["reason"])

    def test_hermes_tool_call_wrapper_is_not_a_second_invalid_attempt(self):
        client = [
            {"name": "tool_search", "arguments": {"queries": ["submit"]}},
            {
                "name": "tool_call",
                "arguments": {
                    "calls": [
                        {
                            "name": "mcp__bakeoff__submit_choice",
                            "arguments": {"case_id": "ph-01-green-idle", "choice": "push", "reason": "ok"},
                        }
                    ]
                },
            },
        ]
        baked, meta = normalize_client_calls(client)
        server = [
            {
                "name": "submit_choice",
                "schema_valid": True,
                "arguments": {"case_id": "ph-01-green-idle", "choice": "push", "reason": "ok"},
            }
        ]
        attempts, valid = count_attempts(server, baked)
        self.assertEqual(meta, 2)
        self.assertEqual(baked[0]["name"], "submit_choice")
        self.assertEqual((attempts, valid), (1, 1))

    def test_margin_just_below_ten_points_is_no_win(self):
        verdict, reasons = margin_verdict(_arm(0.599), _arm(0.50))
        self.assertEqual(verdict, "NO-WIN")
        self.assertTrue(reasons)
        verdict, reasons = margin_verdict(_arm(0.60), _arm(0.50))
        self.assertEqual(verdict, "WIN")
        self.assertEqual(reasons, [])
        # A peak over 2 GiB fails even when accuracy clears the margin.
        huge = 2 * 1024 ** 3 + 1
        verdict, _reasons = margin_verdict(_arm(0.80, peak=huge), _arm(0.50))
        self.assertEqual(verdict, "NO-WIN")

    def test_hermes_home_guard_refuses_unset_and_real_home(self):
        with self.assertRaises(SystemExit) as unset:
            assert_hermes_home("")
        self.assertIn("FAIL", str(unset.exception))
        old = os.environ.pop("HERMES_HOME", None)
        try:
            with self.assertRaises(SystemExit) as again:
                assert_hermes_home(None)
            self.assertIn("unset", str(again.exception))
        finally:
            if old is not None:
                os.environ["HERMES_HOME"] = old
        forbidden = Path.home() / ".hermes" / "bakeoff-should-not-exist"
        with self.assertRaises(SystemExit) as under:
            assert_hermes_home(str(forbidden))
        self.assertIn("FAIL", str(under.exception))
        self.assertFalse(forbidden.exists())

    def test_committed_labels_match_laya_and_fixture_oracles(self):
        path = ROOT / "data" / "decision-gates" / "hermes-bakeoff.tasks.v0.json"
        committed = json.loads(path.read_text(encoding="utf-8"))
        fresh = build()
        self.assertEqual(committed["n_tasks"], fresh["n_tasks"])
        self.assertGreaterEqual(committed["n_tasks"], 20)
        self.assertEqual(
            [task["id"] for task in committed["tasks"]],
            [task["id"] for task in fresh["tasks"]],
        )
        laya = json.loads((ROOT / "data" / "decision-gates" / "laya-trial.cases.v0.json").read_text(encoding="utf-8"))
        labels = {case["id"]: case["label"] for case in laya["cases"]}
        choice = [task for task in committed["tasks"] if task["kind"] == "choice"]
        self.assertGreaterEqual(len(choice), 12)
        families = {task["family"] for task in choice}
        self.assertGreaterEqual(len(families), 4)
        for task in choice:
            self.assertEqual(task["label"], labels[task["source_case_id"]])
            required = task["oracle"]["required"][0]
            self.assertEqual(required["args"]["choice"], labels[task["source_case_id"]])
        fetchish = [task for task in committed["tasks"] if task["kind"] in ("fetch", "chain")]
        self.assertGreaterEqual(len(fetchish), 8)
        negatives = [task for task in committed["tasks"] if task["kind"] == "negative"]
        self.assertGreaterEqual(len(negatives), 2)
        self.assertTrue(committed["labels_before_models"])


@pytest.mark.live
def test_live_two_tasks_per_arm():
    if os.environ.get("HERMES_BAKEOFF_LIVE") != "1":
        pytest.skip("live deselected; set HERMES_BAKEOFF_LIVE=1")
    proc = subprocess.run(
        [
            sys.executable,
            str(BAKE / "run.py"),
            "--live",
            "--limit",
            "2",
            "--skip-ctx-probe",
            "--num-ctx",
            "65536",
            "--keep-model",
            "--out",
            str(ROOT / "tmp" / "bakeoff" / "live-pytest.json"),
            "--work",
            str(ROOT / "tmp" / "bakeoff" / "live-pytest"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=900,
    )
    if proc.returncode != 0:
        raise AssertionError(proc.stdout[-500:] + proc.stderr[-500:])
    payload = json.loads((ROOT / "tmp" / "bakeoff" / "live-pytest.json").read_text(encoding="utf-8"))
    assert len(payload["rows"]["hermes"]) == 2
    assert len(payload["rows"]["baseline"]) == 2


if __name__ == "__main__":
    unittest.main()
