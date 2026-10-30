"""Entry 149 smoke (MemPalace): missing binary, missing model cache, bad or non-positive timeout, inexact version pin
and unusable bwrap exit 2; a store that ranks the wrong note first, files the wrong drawer count, fails a step, or
writes into the real HOME FAILs; a correct stub PASSes. Sandbox tests kill the no-sandbox mutants: the child must get
no network (a loopback connect never reaches the listener), a read-only root (a write outside the smoke's temp dir
fails) and a temp HOME holding the copied model cache. Stubs are tiny Python scripts (shebang = this interpreter)
with knobs baked in; receipts go to a temp dir. Tests that need a real scan skip when bwrap is not usable, like
Entry 148; the no-bwrap exit-2 contract is asserted on every host."""
from __future__ import annotations

import importlib.util
import json
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "examples/x-intake-local/smoke_149.py"
MODEL_REL = ".cache/chroma/onnx_models/all-MiniLM-L6-v2"


def _bwrap_usable() -> bool:
    """Same probe the smoke uses (smoke_149.bwrap_ok), so tests skip exactly when the smoke would exit 2."""
    spec = importlib.util.spec_from_file_location("smoke_149_probe", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.bwrap_ok()


BWRAP_OK = _bwrap_usable()
needs_bwrap = unittest.skipUnless(BWRAP_OK, "SKIP: bwrap-missing; confinement was not demonstrated")

STUB = r'''
import os, sys, pathlib, socket
a = sys.argv[1:]
if a[:1] == ["--version"]:
    print("MemPalace " + K["version"]); sys.exit(0)
if K.get("dial"):
    s = socket.socket()
    s.settimeout(2)
    try:
        s.connect(("127.0.0.1", K["dial"]))
    except OSError:
        pass
    finally:
        s.close()
if K.get("probe"):
    try:
        pathlib.Path(K["probe"]).write_text("escaped")
    except OSError:
        pass
if K.get("expect_temp_home"):
    h = os.environ.get("HOME", "")
    if h == K["expect_temp_home"] or "pfy-smoke-149-" not in h or not pathlib.Path(h, K["model_rel"]).is_dir():
        sys.exit(9)
if K.get("touch_real"):
    try:
        pathlib.Path(K["touch_real"], ".mempalace").mkdir(exist_ok=True)
    except OSError:
        pass
cmd = a[2]
if cmd == "init":
    sys.exit(K.get("init_exit", 0))
if cmd == "mine":
    print("  Drawers filed: %d" % K["drawers"]); sys.exit(K.get("mine_exit", 0))
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
                if k.get("expect_temp_home"):
                    k["expect_temp_home"] = str(real)
                    k["model_rel"] = MODEL_REL
                if k.get("probe"):
                    k["probe"] = str(td / "escaped.txt")
                stub = td / "mempalace"
                stub.write_text(f"#!{sys.executable}\nK = {k!r}\n" + STUB, encoding="utf-8")
                stub.chmod(0o755)
                env2["MEMPALACE_BIN"] = str(stub)
            else:
                env2["MEMPALACE_BIN"] = str(td / "missing")
            env2.update(env or {})
            p = subprocess.run([sys.executable, str(SCRIPT)], env=env2, capture_output=True, text=True, timeout=120)
            rec = json.loads((td / "r" / "latest.json").read_text())
            self.escaped = (td / "escaped.txt").exists()
            return p.returncode, rec

    @needs_bwrap
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

    @needs_bwrap
    def test_wrong_ranking_fails(self):
        code, rec = self.run_smoke(dict(BASE, swap=True))
        self.assertEqual(code, 1)
        self.assertIn("q0_ranks_auth.md", rec["failed"])

    @needs_bwrap
    def test_wrong_drawer_count_fails(self):
        code, rec = self.run_smoke(dict(BASE, drawers=0))
        self.assertEqual(code, 1)
        self.assertIn("mine_filed_2", rec["failed"])

    @needs_bwrap
    def test_init_failure_fails(self):
        code, rec = self.run_smoke(dict(BASE, init_exit=3))
        self.assertEqual(code, 1)
        self.assertIn("init_ok", rec["failed"])

    @needs_bwrap
    def test_search_failure_fails(self):
        code, rec = self.run_smoke(dict(BASE, search_exit=1))
        self.assertEqual(code, 1)
        self.assertIn("q1_ok", rec["failed"])

    @needs_bwrap
    def test_real_home_write_fails(self):
        # The test-only bind makes the real HOME writable inside bwrap, so the check has to notice the write.
        code, rec = self.run_smoke(dict(BASE, touch_real=True), {"PFY_SMOKE_REAL_HOME_BIND": "1"})
        self.assertEqual(code, 1, rec)
        self.assertIn("real_home_unchanged", rec["failed"])

    def test_no_bwrap_exits_2_never_runs_unsandboxed(self):
        # B2: without bwrap the smoke must not fall back to running MemPalace with network and a writable root.
        with tempfile.TemporaryDirectory() as empty:
            code, rec = self.run_smoke(dict(BASE, probe=True), {"PATH": empty})
        self.assertEqual(code, 2, rec)
        self.assertIn("bwrap is not usable", rec["reason"])
        self.assertFalse(self.escaped, "MemPalace ran unsandboxed")
        self.assertNotIn("init_exit", rec["checks"])

    def test_zero_timeout_exit_2(self):
        # The reason matters: without the <=0 guard a zero timeout still exits 2, via a --version TimeoutExpired.
        code, rec = self.run_smoke(dict(BASE), {"PFY_XINTAKE_TIMEOUT": "0"})
        self.assertEqual(code, 2, rec)
        self.assertEqual(rec["reason"], "bad PFY_XINTAKE_TIMEOUT")

    def test_negative_timeout_exit_2(self):
        # The reason matters: without the <=0 guard a zero timeout still exits 2, via a --version TimeoutExpired.
        code, rec = self.run_smoke(dict(BASE), {"PFY_XINTAKE_TIMEOUT": "-5"})
        self.assertEqual(code, 2, rec)
        self.assertEqual(rec["reason"], "bad PFY_XINTAKE_TIMEOUT")

    @needs_bwrap
    def test_version_pin_is_exact(self):
        # The version probe runs inside bwrap, so without it the smoke exits 2 on the bwrap reason first.
        for v in ("3.12.0.1", "13.12.0", "3.12.0rc1"):
            code, rec = self.run_smoke(dict(BASE, version=v))
            self.assertEqual(code, 2, (v, rec))
            self.assertIn("version pin", rec["reason"])

    @needs_bwrap
    def test_mine_failure_fails(self):
        code, rec = self.run_smoke(dict(BASE, mine_exit=4))
        self.assertEqual(code, 1, rec)
        self.assertIn("mine_ok", rec["failed"])

    @needs_bwrap
    def test_child_gets_temp_home_with_model_cache(self):
        # The stub exits 9 on every step if HOME is the real HOME, is not the smoke's temp dir, or lacks the cache.
        code, rec = self.run_smoke(dict(BASE, expect_temp_home=True))
        self.assertEqual(code, 0, rec)

    @needs_bwrap
    def test_child_has_no_network(self):
        # Mutant: --unshare-net dropped, or the sandbox forced off. The listener must see no connection.
        srv = socket.socket()
        srv.bind(("127.0.0.1", 0))
        srv.listen(8)
        srv.settimeout(0.5)
        try:
            code, rec = self.run_smoke(dict(BASE, dial=srv.getsockname()[1]))
            try:
                conn, _ = srv.accept()
            except (socket.timeout, TimeoutError):
                reached = False
            else:
                conn.close()
                reached = True
        finally:
            srv.close()
        self.assertEqual(code, 0, rec)
        self.assertEqual(rec["sandbox"], "bwrap --unshare-net")
        self.assertFalse(reached, "a loopback connect from the child reached the host")

    @needs_bwrap
    def test_child_root_is_read_only(self):
        # Mutant: --bind / / instead of --ro-bind, or the sandbox forced off. A write outside the temp dir must fail.
        code, rec = self.run_smoke(dict(BASE, probe=True))
        self.assertEqual(code, 0, rec)
        self.assertFalse(self.escaped, "the child wrote outside the smoke's temp dir")


if __name__ == "__main__":
    unittest.main()
