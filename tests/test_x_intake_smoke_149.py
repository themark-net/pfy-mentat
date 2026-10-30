"""Entry 149 smoke (MemPalace): missing binary, missing model cache, bad timeout and version pin exit 2; a store
that ranks the wrong note first, files the wrong drawer count, fails a step, or writes into the real HOME FAILs; a
correct stub PASSes. Stubs are tiny Python scripts (shebang = this interpreter) with knobs baked in; receipts go to
a temp dir."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "examples/x-intake-local/smoke_149.py"

STUB = r'''
import os, sys, pathlib
a = sys.argv[1:]
if a[:1] == ["--version"]:
    print("MemPalace " + K["version"]); sys.exit(0)
if K.get("touch_real"):
    try:
        pathlib.Path(K["touch_real"], ".mempalace").mkdir(exist_ok=True)
    except OSError:
        pass
cmd = a[2]
if cmd == "init":
    sys.exit(K.get("init_exit", 0))
if cmd == "mine":
    print("  Drawers filed: %d" % K["drawers"]); sys.exit(0)
q = a[3]
first, second = ("auth.md", "ci.md") if "auth" in q else ("ci.md", "auth.md")
if K.get("swap"):
    first, second = second, first
print("  [1] proj / documentation\n      Source: %s\n  [2]\n      Source: %s" % (first, second))
sys.exit(K.get("search_exit", 0))
'''

BASE = {"version": "3.12.0", "drawers": 2}


class Smoke149(unittest.TestCase):
    def run_smoke(self, knobs=None, env=None, model=True):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            real = td / "realhome"
            real.mkdir()
            mh = td / "mphome"
            if model:
                (mh / ".cache/chroma/onnx_models/all-MiniLM-L6-v2").mkdir(parents=True)
            env2 = {"PATH": os.environ.get("PATH", ""), "HOME": str(real), "MEMPALACE_HOME": str(mh),
                    "PFY_SMOKE_RECEIPT_DIR": str(td / "r")}
            if knobs is not None:
                k = dict(knobs)
                if k.get("touch_real"):
                    k["touch_real"] = str(real)
                stub = td / "mempalace"
                stub.write_text(f"#!{sys.executable}\nK = {k!r}\n" + STUB, encoding="utf-8")
                stub.chmod(0o755)
                env2["MEMPALACE_BIN"] = str(stub)
            else:
                env2["MEMPALACE_BIN"] = str(td / "missing")
            env2.update(env or {})
            p = subprocess.run([sys.executable, str(SCRIPT)], env=env2, capture_output=True, text=True, timeout=120)
            rec = json.loads((td / "r" / "latest.json").read_text())
            return p.returncode, rec

    def test_pass(self):
        code, rec = self.run_smoke(dict(BASE))
        self.assertEqual(code, 0, rec)

    def test_missing_binary_exit_2(self):
        self.assertEqual(self.run_smoke(None)[0], 2)

    def test_missing_model_cache_exit_2(self):
        code, rec = self.run_smoke(dict(BASE), model=False)
        self.assertEqual(code, 2)
        self.assertIn("not cached", rec["reason"])

    def test_bad_timeout_exit_2(self):
        self.assertEqual(self.run_smoke(dict(BASE), {"PFY_XINTAKE_TIMEOUT": "nope"})[0], 2)

    def test_version_pin_exit_2(self):
        self.assertEqual(self.run_smoke(dict(BASE, version="9.9.9"))[0], 2)

    def test_wrong_ranking_fails(self):
        code, rec = self.run_smoke(dict(BASE, swap=True))
        self.assertEqual(code, 1)
        self.assertIn("q0_ranks_auth.md", rec["failed"])

    def test_wrong_drawer_count_fails(self):
        code, rec = self.run_smoke(dict(BASE, drawers=0))
        self.assertEqual(code, 1)
        self.assertIn("mine_filed_2", rec["failed"])

    def test_init_failure_fails(self):
        code, rec = self.run_smoke(dict(BASE, init_exit=3))
        self.assertEqual(code, 1)
        self.assertIn("init_ok", rec["failed"])

    def test_search_failure_fails(self):
        code, rec = self.run_smoke(dict(BASE, search_exit=1))
        self.assertEqual(code, 1)
        self.assertIn("q1_ok", rec["failed"])

    def test_real_home_write_fails(self):
        # No bwrap on PATH, so the stub can reach the real HOME (bwrap's read-only bind would block it).
        code, rec = self.run_smoke(dict(BASE, touch_real=True), {"PATH": "/nonexistent"})
        self.assertEqual(code, 1)
        self.assertIn("real_home_unchanged", rec["failed"])


if __name__ == "__main__":
    unittest.main()
