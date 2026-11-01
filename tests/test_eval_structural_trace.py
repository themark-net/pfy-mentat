"""The structural runner keeps a failing unittest traceback.

Fail: summarize_unittest returns only the FAIL: name, the way
eval-structural.log did at pregate 16f17d8.
Recover: the detail contains the traceback and the assertion text.
A passing run stays a one-line summary with no traceback.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "examples" / "eval-harness" / "run_structural.py"


def _load():
    spec = importlib.util.spec_from_file_location("run_structural_under_test", RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {RUNNER}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _scratch() -> Path:
    path = ROOT / "tmp" / "structural-trace"
    path.mkdir(parents=True, exist_ok=True)
    return path


class StructuralTraceTests(unittest.TestCase):
    def test_failing_unittest_traceback_is_kept_and_a_pass_has_none(self):
        mod = _load()
        with tempfile.TemporaryDirectory(dir=_scratch()) as tmp:
            suite = Path(tmp)
            (suite / "test_cache.py").write_text(
                textwrap.dedent(
                    """\
                    import unittest

                    class CacheTests(unittest.TestCase):
                        def test_operator_cache_changed(self):
                            self.assertEqual([], [".cache/uv"], "operator cache changed")
                    """
                ),
                encoding="utf-8",
            )
            failed = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", str(suite), "-t", str(suite)],
                cwd=suite,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(failed.returncode, 0)
            out = (failed.stdout or "") + (failed.stderr or "")
            ok, detail = mod.summarize_unittest(failed.returncode, out)
            self.assertFalse(ok)
            self.assertIn("Traceback (most recent call last)", detail)
            self.assertIn("AssertionError", detail)
            self.assertIn("operator cache changed", detail)
            self.assertIn(".cache/uv", detail)
            # The old log line was only the FAIL: name. That shape is not enough.
            self.assertNotEqual(
                detail.strip(),
                "FAIL: test_operator_cache_changed "
                "(test_cache.CacheTests.test_operator_cache_changed)",
            )

            (suite / "test_cache.py").write_text(
                textwrap.dedent(
                    """\
                    import unittest

                    class CacheTests(unittest.TestCase):
                        def test_private_cache_stays(self):
                            self.assertEqual([], [])
                    """
                ),
                encoding="utf-8",
            )
            passed = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", str(suite), "-t", str(suite)],
                cwd=suite,
                capture_output=True,
                text=True,
            )
            self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)
            passed_out = (passed.stdout or "") + (passed.stderr or "")
            ok, detail = mod.summarize_unittest(passed.returncode, passed_out)
            self.assertTrue(ok)
            self.assertNotIn("Traceback", detail)
            self.assertIn("OK", detail)


if __name__ == "__main__":
    unittest.main()
