"""Entry 148 smoke (SkillSpector): missing binary, bad timeout and version pin exit 2; a scanner that calls the
malicious fixture safe, misses a rule family, exits 0 on it, or writes into its HOME FAILs; a correct stub PASSes.
Stubs are tiny Python scripts (shebang = this interpreter) with knobs baked in; receipts go to a temp dir."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "examples/x-intake-local/smoke_148.py"

STUB = r'''
import json, sys, os, pathlib
a = sys.argv[1:]
if a[:1] == ["--version"]:
    print("SkillSpector v" + K["version"]); sys.exit(0)
src = pathlib.Path(a[1]); out = pathlib.Path(a[a.index("-o") + 1])
bad = "evil.example" in (src / "SKILL.md").read_text()
if K.get("touch_home"):
    pathlib.Path(os.environ["HOME"], ".skillspector-cache").write_text("x")
if bad and not K.get("blind"):
    ids = [i for i in K["ids"]]
    ra = {"score": K["score"], "recommendation": "DO_NOT_INSTALL"}
    code = K["bad_exit"]
else:
    ids, ra, code = [], {"score": 0, "recommendation": "SAFE"}, 0
out.write_text(json.dumps({"risk_assessment": ra, "issues": [{"rule_id": i} for i in ids],
                           "metadata": {"llm_requested": False}}))
sys.exit(code)
'''

BASE = {"version": "2.12.0", "ids": ["P1", "SC2", "TM2"], "score": 93, "bad_exit": 1}


class Smoke148(unittest.TestCase):
    def run_smoke(self, knobs=None, env=None):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            env2 = {"PATH": os.environ.get("PATH", ""), "HOME": str(td / "realhome"),
                    "PFY_SMOKE_RECEIPT_DIR": str(td / "r")}
            (td / "realhome").mkdir()
            if knobs is not None:
                stub = td / "skillspector"
                stub.write_text(f"#!{sys.executable}\nK = {knobs!r}\n" + STUB, encoding="utf-8")
                stub.chmod(0o755)
                env2["SKILLSPECTOR_BIN"] = str(stub)
            else:
                env2["SKILLSPECTOR_BIN"] = str(td / "missing")
            env2.update(env or {})
            p = subprocess.run([sys.executable, str(SCRIPT)], env=env2, capture_output=True, text=True, timeout=120)
            rec = json.loads((td / "r" / "latest.json").read_text())
            return p.returncode, rec

    def test_pass(self):
        code, rec = self.run_smoke(dict(BASE))
        self.assertEqual(code, 0, rec)

    def test_missing_binary_exit_2(self):
        self.assertEqual(self.run_smoke(None)[0], 2)

    def test_bad_timeout_exit_2(self):
        self.assertEqual(self.run_smoke(dict(BASE), {"PFY_XINTAKE_TIMEOUT": "nope"})[0], 2)

    def test_version_pin_exit_2(self):
        self.assertEqual(self.run_smoke(dict(BASE, version="9.9.9"))[0], 2)

    def test_blind_scanner_fails(self):
        code, rec = self.run_smoke(dict(BASE, blind=True))
        self.assertEqual(code, 1)
        self.assertIn("bad_do_not_install", rec["failed"])

    def test_missing_supply_chain_fails(self):
        code, rec = self.run_smoke(dict(BASE, ids=["P1", "TM2"]))
        self.assertEqual(code, 1)
        self.assertIn("bad_flags_supply_chain", rec["failed"])

    def test_missing_prompt_injection_fails(self):
        code, rec = self.run_smoke(dict(BASE, ids=["PE3", "SC2"]))
        self.assertEqual(code, 1)
        self.assertIn("bad_flags_prompt_injection", rec["failed"])

    def test_low_score_fails(self):
        code, rec = self.run_smoke(dict(BASE, score=40))
        self.assertIn("bad_score_ge_70", rec["failed"])

    def test_bad_exit_zero_fails(self):
        code, rec = self.run_smoke(dict(BASE, bad_exit=0))
        self.assertIn("bad_exit_nonzero", rec["failed"])

    def test_temp_home_write_fails(self):
        code, rec = self.run_smoke(dict(BASE, touch_home=True))
        self.assertEqual(code, 1)
        self.assertIn("temp_home_empty", rec["failed"])


if __name__ == "__main__":
    unittest.main()
