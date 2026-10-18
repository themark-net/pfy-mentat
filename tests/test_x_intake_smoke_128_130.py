"""Entries 128-130 smokes (Harness Score, OpenLore): pins and missing prereqs exit 2, wrong verdicts and real-HOME
writes FAIL, timeouts FAIL with the real-HOME check kept.

The node binary is a /bin/sh stub ($NODE_BIN) that answers like the real CLI for the fixture the smoke builds, so no
Node or npm package is needed. Parent HOME is a temp dir this test owns; children get a different temp HOME, so a
planted real-HOME write uses the parent HOME's absolute path inside the stub. bwrap is found with shutil.which on the
smoke process PATH, so tests that need a write to land set PATH to an empty dir (the smoke's children use a fixed
/usr/local/bin:/usr/bin:/bin). Receipts go to a temp $PFY_SMOKE_RECEIPT_DIR.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "examples/x-intake-local/smoke_128_130.py"
_RECEIPTS = tempfile.TemporaryDirectory(prefix="pfy-xintake-128-receipts-")
RECEIPT_DIR = Path(_RECEIPTS.name)


def tearDownModule() -> None:
    _RECEIPTS.cleanup()


def _check(cid: str, passed: bool) -> dict:
    return {"id": cid, "passed": passed}


def _hs_json(ctx01: bool, hyg02: bool, hyg03: bool, root: str = "/fixture") -> str:
    return json.dumps({"tool": {"name": "harness-score", "version": "1.8.2"}, "root": root,
                       "level": {"name": "Unharnessed"},
                       "score": {"earned": 1, "max": 105},
                       "checks": [_check("CTX-01", ctx01), _check("HYG-02", hyg02), _check("HYG-03", hyg03)]})


def _write_exe(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _hs_node(base: Path, *, leaky_flagged: bool = True, nondeterministic: bool = False, plant: str = "",
             version: str = "v20.11.0", gate_rc: int = 1) -> Path:
    clean = _hs_json(True, True, True, root="NONCE" if nondeterministic else "/fixture")
    leaky = _hs_json(True, not leaky_flagged, not leaky_flagged)
    stamp = ' | sed "s/NONCE/$(date +%s%N)/"' if nondeterministic else ""
    node = base / "bin" / "node"
    _write_exe(node, (
        "#!/bin/sh\n"
        f"{plant}\n"
        f'if [ "$1" = "--version" ]; then echo {version}; exit 0; fi\n'
        'case "$*" in\n'
        f"  *--min-level*) echo 'below required' >&2; exit {gate_rc} ;;\n"
        f"  *--json*/clean) printf '%s\\n' '{clean}'{stamp} ;;\n"
        f"  *--json*/leaky) printf '%s\\n' '{leaky}' ;;\n"
        "  *) exit 9 ;;\n"
        "esac\n"
    ))
    return node


def _hs_pkg(base: Path, version: str = "1.8.2") -> Path:
    pkg = base / "harness-score" / "package"
    (pkg / "dist").mkdir(parents=True)
    (pkg / "dist" / "cli.js").write_text("// stub\n")
    (pkg / "package.json").write_text(json.dumps({"name": "harness-score", "version": version}))
    return pkg


def _ol_node(base: Path, *, version: str = "v22.20.0", flag_breaking: bool = True, always_breaking: bool = False,
             orient_first: str = "applyDiscount", sleep_on: str = "", plant: str = "",
             consumers: tuple[str, ...] = ("checkout",), stray: bool = False) -> Path:
    orient = json.dumps({"relevantFunctions": [{"name": orient_first}, {"name": "checkout"}]})
    brk = json.dumps({"overall": "breaking", "breaking": [{"name": "applyDiscount", "reasons": ["required parameter"],
                                                           "consumers": [{"name": c} for c in consumers]}]})
    clean = json.dumps({"overall": "non-breaking", "breaking": []})
    when_cap = brk if flag_breaking else clean
    when_ok = brk if always_breaking else clean
    sleep = f'case "$*" in *{sleep_on}*) sleep 5 ;; esac\n' if sleep_on else ""
    node = base / "bin" / "node"
    _write_exe(node, (
        "#!/bin/sh\n"
        f"{plant}\n"
        f'if [ "$1" = "--version" ]; then echo {version}; exit 0; fi\n'
        f"{sleep}"
        'case "$*" in\n'
        "  *' init -q'*) printf '.openlore/\\n' > .gitignore;" + (" echo x > stray.txt;" if stray else "") + " exit 0 ;;\n"
        "  *' analyze -q'*) exit 0 ;;\n"
        f"  *' orient '*) printf '%s\\n' '{orient}' ;;\n"
        "  *certify-public-surface*)\n"
        f"    if grep -q cap src/pricing.ts; then printf '%s\\n' '{when_cap}'; else printf '%s\\n' '{when_ok}'; fi ;;\n"
        "  *) exit 9 ;;\n"
        "esac\n"
    ))
    return node


def _ol_prefix(base: Path, version: str = "3.3.1") -> Path:
    prefix = base / "openlore"
    pkg = prefix / "node_modules" / "openlore"
    (pkg / "dist" / "cli").mkdir(parents=True)
    (pkg / "dist" / "cli" / "index.js").write_text("// stub\n")
    (pkg / "package.json").write_text(json.dumps({"name": "openlore", "version": version}))
    return prefix


class Base(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory(prefix="pfy-xintake-128-test-")
        self.base = Path(self._td.name)
        self.home = self.base / "realhome"
        self.home.mkdir()
        self.nobwrap = self.base / "emptypath"
        self.nobwrap.mkdir()

    def tearDown(self) -> None:
        self._td.cleanup()

    def env(self, *, no_bwrap: bool = False, **extra: str) -> dict[str, str]:
        env = os.environ.copy()
        for key in list(env):
            if key.startswith(("HARNESS_SCORE_", "OPENLORE_", "NODE_BIN")) or key == "PFY_XINTAKE_TIMEOUT":
                env.pop(key, None)
        env["HOME"] = str(self.home)  # so ~/DEVELOP/pfy-mentat/tmp lookups find nothing
        env["PFY_SMOKE_RECEIPT_DIR"] = str(RECEIPT_DIR)
        if no_bwrap:
            env["PATH"] = str(self.nobwrap)
        env.update(extra)
        return env

    def run_entry(self, entry: str, env: dict[str, str]) -> tuple[int, dict]:
        p = subprocess.run([sys.executable, SCRIPT, "--entry", entry], cwd=str(ROOT), env=env,
                           capture_output=True, text=True, timeout=120)
        self.assertNotIn("Traceback", p.stderr + p.stdout)
        receipt = json.loads((RECEIPT_DIR / entry / "latest.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["exit_code"], p.returncode)
        return p.returncode, receipt


class HarnessScoreTests(Base):
    def test_missing_package_exits_2(self) -> None:
        node = _hs_node(self.base)
        code, r = self.run_entry("harnessscore", self.env(NODE_BIN=str(node),
                                                          HARNESS_SCORE_DIR=str(self.base / "nope")))
        self.assertEqual(code, 2)
        self.assertIn("not staged", r["reason"])

    def test_version_mismatch_exits_2(self) -> None:
        node, pkg = _hs_node(self.base), _hs_pkg(self.base, "1.0.0")
        code, r = self.run_entry("harnessscore", self.env(NODE_BIN=str(node), HARNESS_SCORE_DIR=str(pkg)))
        self.assertEqual(code, 2)
        self.assertIn("1.0.0", r["reason"])

    def test_old_node_exits_2(self) -> None:
        node, pkg = _hs_node(self.base, version="v16.20.0"), _hs_pkg(self.base)
        code, r = self.run_entry("harnessscore", self.env(NODE_BIN=str(node), HARNESS_SCORE_DIR=str(pkg)))
        self.assertEqual(code, 2)
        self.assertIn("node >= 18", r["reason"])

    def test_stub_happy_path_passes(self) -> None:
        node, pkg = _hs_node(self.base), _hs_pkg(self.base)
        code, r = self.run_entry("harnessscore", self.env(NODE_BIN=str(node), HARNESS_SCORE_DIR=str(pkg)))
        self.assertEqual(code, 0, r)
        self.assertTrue(all(r["checks"].values()))
        self.assertTrue(r["checks"]["real_home_untouched"])

    def test_unflagged_leaky_env_fails(self) -> None:
        node, pkg = _hs_node(self.base, leaky_flagged=False), _hs_pkg(self.base)
        code, r = self.run_entry("harnessscore", self.env(NODE_BIN=str(node), HARNESS_SCORE_DIR=str(pkg)))
        self.assertEqual(code, 1)
        self.assertIn("leaky_env_file_flagged", r["reason"])

    def test_nondeterministic_output_fails(self) -> None:
        node, pkg = _hs_node(self.base, nondeterministic=True), _hs_pkg(self.base)
        code, r = self.run_entry("harnessscore", self.env(NODE_BIN=str(node), HARNESS_SCORE_DIR=str(pkg)))
        self.assertEqual(code, 1)
        self.assertFalse(r["checks"]["deterministic_rerun"])

    def test_gate_that_passes_below_level_fails(self) -> None:
        node, pkg = _hs_node(self.base, gate_rc=0), _hs_pkg(self.base)
        code, r = self.run_entry("harnessscore", self.env(NODE_BIN=str(node), HARNESS_SCORE_DIR=str(pkg)))
        self.assertEqual(code, 1)
        self.assertIn("gate_below_min_level_exit_1", r["reason"])

    def test_temp_home_write_fails(self) -> None:
        node, pkg = _hs_node(self.base, plant='echo x > "$HOME/x"'), _hs_pkg(self.base)
        code, r = self.run_entry("harnessscore", self.env(NODE_BIN=str(node), HARNESS_SCORE_DIR=str(pkg)))
        self.assertEqual(code, 1)
        self.assertIn("home_untouched", r["reason"])

    def test_fixture_write_fails(self) -> None:
        plant = 'for a; do last=$a; done; case "$last" in */clean) echo x > "$last/new.txt" ;; esac'
        node, pkg = _hs_node(self.base, plant=plant), _hs_pkg(self.base)
        code, r = self.run_entry("harnessscore", self.env(NODE_BIN=str(node), HARNESS_SCORE_DIR=str(pkg)))
        self.assertEqual(code, 1)
        self.assertIn("fixtures_untouched", r["reason"])

    def test_real_home_write_fails_without_bwrap(self) -> None:
        target = self.home / ".harness-score"
        plant = f"mkdir -p '{target}' && echo x >> '{target}/cache'"
        node, pkg = _hs_node(self.base, plant=plant), _hs_pkg(self.base)
        code, r = self.run_entry("harnessscore", self.env(no_bwrap=True, NODE_BIN=str(node),
                                                          HARNESS_SCORE_DIR=str(pkg)))
        self.assertTrue((target / "cache").exists())
        self.assertEqual(code, 1)
        self.assertFalse(r["checks"]["real_home_untouched"])
        self.assertIn("real_home_untouched", r["reason"])


class OpenLoreTests(Base):
    def setUp(self) -> None:
        super().setUp()
        if not shutil.which("git", path="/usr/local/bin:/usr/bin:/bin"):
            self.skipTest("git not in /usr/local/bin:/usr/bin:/bin")

    def test_missing_prefix_exits_2(self) -> None:
        node = _ol_node(self.base)
        code, r = self.run_entry("openlore", self.env(NODE_BIN=str(node), OPENLORE_DIR=str(self.base / "nope")))
        self.assertEqual(code, 2)

    def test_version_mismatch_exits_2(self) -> None:
        node, prefix = _ol_node(self.base), _ol_prefix(self.base, "3.0.0")
        code, r = self.run_entry("openlore", self.env(NODE_BIN=str(node), OPENLORE_DIR=str(prefix)))
        self.assertEqual(code, 2)
        self.assertIn("3.0.0", r["reason"])

    def test_node_20_exits_2(self) -> None:
        node, prefix = _ol_node(self.base, version="v20.19.2"), _ol_prefix(self.base)
        code, r = self.run_entry("openlore", self.env(NODE_BIN=str(node), OPENLORE_DIR=str(prefix)))
        self.assertEqual(code, 2)
        self.assertIn("22.19", r["reason"])

    def test_node_23_0_exits_2(self) -> None:
        node, prefix = _ol_node(self.base, version="v23.1.0"), _ol_prefix(self.base)
        code, _ = self.run_entry("openlore", self.env(NODE_BIN=str(node), OPENLORE_DIR=str(prefix)))
        self.assertEqual(code, 2)

    def test_stub_happy_path_passes(self) -> None:
        node, prefix = _ol_node(self.base), _ol_prefix(self.base)
        code, r = self.run_entry("openlore", self.env(NODE_BIN=str(node), OPENLORE_DIR=str(prefix)))
        self.assertEqual(code, 0, r)
        self.assertEqual(r["broken"]["consumers"], ["checkout"])
        self.assertEqual(r["restored_overall"], "non-breaking")

    def test_missed_breaking_change_fails(self) -> None:
        node, prefix = _ol_node(self.base, flag_breaking=False), _ol_prefix(self.base)
        code, r = self.run_entry("openlore", self.env(NODE_BIN=str(node), OPENLORE_DIR=str(prefix)))
        self.assertEqual(code, 1)
        self.assertIn("breaking_change_flagged", r["reason"])

    def test_false_positive_after_restore_fails(self) -> None:
        node, prefix = _ol_node(self.base, always_breaking=True), _ol_prefix(self.base)
        code, r = self.run_entry("openlore", self.env(NODE_BIN=str(node), OPENLORE_DIR=str(prefix)))
        self.assertEqual(code, 1)
        self.assertIn("restored_is_non_breaking", r["reason"])

    def test_breaking_without_consumer_fails(self) -> None:
        node, prefix = _ol_node(self.base, consumers=()), _ol_prefix(self.base)
        code, r = self.run_entry("openlore", self.env(NODE_BIN=str(node), OPENLORE_DIR=str(prefix)))
        self.assertEqual(code, 1)
        self.assertIn("breaking_names_consumer_checkout", r["reason"])

    def test_temp_home_write_fails(self) -> None:
        node, prefix = _ol_node(self.base, plant='echo x > "$HOME/x"'), _ol_prefix(self.base)
        code, r = self.run_entry("openlore", self.env(NODE_BIN=str(node), OPENLORE_DIR=str(prefix)))
        self.assertEqual(code, 1)
        self.assertIn("home_untouched", r["reason"])

    def test_stray_repo_file_fails(self) -> None:
        node, prefix = _ol_node(self.base, stray=True), _ol_prefix(self.base)
        code, r = self.run_entry("openlore", self.env(NODE_BIN=str(node), OPENLORE_DIR=str(prefix)))
        self.assertEqual(code, 1)
        self.assertIn("repo_only_gains_gitignore", r["reason"])

    def test_wrong_orient_ranking_fails(self) -> None:
        node, prefix = _ol_node(self.base, orient_first="checkout"), _ol_prefix(self.base)
        code, r = self.run_entry("openlore", self.env(NODE_BIN=str(node), OPENLORE_DIR=str(prefix)))
        self.assertEqual(code, 1)
        self.assertIn("orient_ranks_applyDiscount_first", r["reason"])

    def test_timeout_fails_and_keeps_real_home_check(self) -> None:
        target = self.home / ".openlore"
        plant = f"mkdir -p '{target}' && echo x >> '{target}/update-check.json'"
        node, prefix = _ol_node(self.base, sleep_on="analyze", plant=plant), _ol_prefix(self.base)
        code, r = self.run_entry("openlore", self.env(no_bwrap=True, NODE_BIN=str(node), OPENLORE_DIR=str(prefix),
                                                      PFY_XINTAKE_TIMEOUT="1"))
        self.assertEqual(code, 1)
        self.assertIn("openlore analyze timeout after 1s", r["reason"])
        self.assertFalse(r["checks"]["real_home_untouched"])
        self.assertIn("real HOME", r["reason"])


if __name__ == "__main__":
    unittest.main()
