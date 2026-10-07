"""llamacpp-nommap lane: memory floor refuses start; health and stop do not load a model."""
from __future__ import annotations

import json
import socket
import subprocess
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pfylib import hedge  # noqa: E402


class _Boom:
    def __call__(self, *args, **kwargs):
        raise AssertionError("llama-server spawn is not allowed in this test: %r" % (args,))


class LaneTests(unittest.TestCase):
    def test_lane_is_named_in_eval_lanes_and_not_a_spend_lane(self):
        lanes = json.loads((ROOT / "data/eval-lanes.json").read_text(encoding="utf-8"))
        row = next(item for item in lanes["lanes"] if item["id"] == "llamacpp-nommap")
        self.assertEqual(row["default_model"], "qwen3.6:35b")
        self.assertEqual(row["default_model_runtime"], "ollama")
        self.assertEqual(row["opt_in_model"], "qwen3-coder-next")
        self.assertEqual(row["health"], "GET /v1/models")
        self.assertNotIn("llamacpp-nommap", hedge.LANES)
        self.assertEqual(hedge.DEFAULT_OLLAMA_MODEL, "qwen3.6:35b")
        self.assertEqual(hedge.NOMMAP_OPT_IN_MODEL, "qwen3-coder-next")

    def test_missing_path_refuses_and_names_the_default_model(self):
        rec = hedge.start_llamacpp_nommap(None, popen=_Boom())
        self.assertEqual(rec["exit_code"], 2)
        self.assertFalse(rec["started"])
        self.assertIn("qwen3.6:35b", rec["reason"])
        self.assertIn("qwen3-coder-next", rec["reason"])
        self.assertTrue(rec["next_step"])

    def test_memory_floor_refuses_on_injected_memavailable(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp) / "qwen3-coder-next.gguf"
            model.write_bytes(b"x" * 4096)
            rec = hedge.start_llamacpp_nommap(
                model,
                meminfo_text="MemAvailable:          1048576 kB\nMemFree: 1 kB\n",
                popen=_Boom(),
                root_dir=ROOT,
            )
        self.assertEqual(rec["exit_code"], 2)
        self.assertFalse(rec["started"])
        self.assertNotIn("proc", rec)
        self.assertIn("MemAvailable", rec["reason"])
        self.assertIn("1.000 GiB", rec["reason"])
        self.assertIn("25 GiB", rec["reason"])
        self.assertIn("25 GiB", rec["next_step"])
        self.assertIn("free memory", rec["next_step"])

    def test_high_injected_memavailable_spawns_via_fake_popen_only(self):
        import tempfile

        seen = {}

        class _Proc:
            pid = 4242

            def poll(self):
                return None

        def fake_popen(argv, **kwargs):
            seen["argv"] = list(argv)
            seen["kwargs"] = dict(kwargs)
            return _Proc()

        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp) / "qwen3-coder-next.gguf"
            model.write_bytes(b"gguf")
            rec = hedge.start_llamacpp_nommap(
                model,
                meminfo_text="MemAvailable:       104857600 kB\n",
                popen=fake_popen,
                root_dir=ROOT,
                port=18080,
            )
        self.assertEqual(rec["exit_code"], 0, rec.get("reason"))
        self.assertTrue(rec["started"])
        self.assertEqual(seen["argv"][0], "bash")
        self.assertTrue(seen["argv"][1].endswith("run_nommap_server.sh"))
        self.assertTrue(seen["argv"][2].endswith("qwen3-coder-next.gguf"))
        self.assertEqual(seen["argv"][3], "18080")
        self.assertTrue(seen["kwargs"].get("start_new_session"))
        self.assertNotIn("llama-server", Path(seen["argv"][0]).name)

    def test_health_closed_port_exits_2(self):
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        rec = hedge.health_llamacpp_nommap("http://127.0.0.1:%d" % port, timeout=1.0)
        self.assertEqual(rec["exit_code"], 2)
        self.assertFalse(rec["ok"])
        self.assertIn("/v1/models", rec["reason"])
        self.assertTrue(rec["next_step"])

    def test_health_and_stop_do_not_start_llama_server(self):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):
                return

            def do_GET(self):
                if self.path.split("?")[0] != "/v1/models":
                    self.send_error(404)
                    return
                raw = b'{"data":[{"id":"fake"}]}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        proc = subprocess.Popen(["sleep", "30"], start_new_session=True)
        try:
            port = server.server_address[1]
            rec = hedge.health_llamacpp_nommap("http://127.0.0.1:%d" % port, timeout=2.0)
            self.assertTrue(rec["ok"], rec)
            self.assertIn("fake", rec["body"])
            stopped = hedge.stop_llamacpp_nommap(proc, timeout=2.0)
            self.assertTrue(stopped["stopped"])
            self.assertIsNotNone(proc.wait(timeout=2))
        finally:
            server.shutdown()
            server.server_close()
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=2)


if __name__ == "__main__":
    unittest.main()
