"""Entry 110 (brigade) smoke run as a subprocess with a stub binary: env stripping and timeout cleanup.

Parent HOME is a temp dir this test owns so a stub cannot touch the operator's real home.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# `--version` records whether GROK_API_KEY reached it; any other command forks a sleeping child and sleeps.
# Fail: a paid key reached the tool, or the forked child outlived the timeout (only the direct child was killed).
# Recover: the key is absent in the tool env, and no process running this stub is left after the smoke exits.
STUB = """#!/bin/sh
if [ "$1" = --version ]; then
  if [ -n "${GROK_API_KEY+x}" ]; then echo present > "$PFY_PROBE_OUT"; else echo absent > "$PFY_PROBE_OUT"; fi
  echo "brigade 0.27.0"
  exit 0
fi
if [ "$1" = --child ]; then sleep 60; exit 0; fi
"$0" --child >/dev/null 2>&1 &
sleep 60
"""


class XIntakeSmoke109111Tests(unittest.TestCase):
    def test_brigade_strips_grok_key_and_kills_process_group_on_timeout(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-parent-") as td:
            home, stub, probe = Path(td, "home"), Path(td, "brigade-stub-109"), Path(td, "probe")
            home.mkdir()
            stub.write_text(STUB, encoding="utf-8")
            stub.chmod(0o755)
            env = {k: v for k, v in os.environ.items() if not k.startswith("BRIGADE_")}
            env.update(HOME=str(home), BRIGADE_BIN=str(stub), PFY_PROBE_OUT=str(probe),
                       GROK_API_KEY="must-not-leak", PFY_XINTAKE_TIMEOUT="1")
            p = subprocess.run(["python3", "examples/x-intake-local/smoke_109_111.py", "--entry", "brigade"],
                               cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=120)
            time.sleep(0.5)
            left = subprocess.run(["pgrep", "-f", str(stub)], capture_output=True, text=True).stdout.split()
            for pid in left:
                try:
                    os.kill(int(pid), 9)
                except OSError:
                    pass
            self.assertEqual(probe.read_text().strip(), "absent")
            self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
            self.assertNotIn("Traceback", p.stderr)
            receipt = json.loads((ROOT / "pipelines/smoke/brigade/latest.json").read_text(encoding="utf-8"))
            self.assertIn("timeout", receipt["reason"])
            self.assertEqual(left, [], "a forked tool child outlived the smoke timeout")


if __name__ == "__main__":
    unittest.main()
