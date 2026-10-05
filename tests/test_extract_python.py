"""Behavior: extract_python must keep imports above def (NameError: re)."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "examples" / "eval-harness"
sys.path.insert(0, str(HARNESS))


def _load():
    spec = importlib.util.spec_from_file_location(
        "run_scored_task", HARNESS / "run_scored_task.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class ExtractPythonImportPreambleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_keeps_import_re_above_slugify(self):
        raw = """import re

def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r'[\\s_]+', '-', s)
    s = re.sub(r'[^a-z0-9-]', '', s)
    return s.strip('-')
"""
        code = self.mod.extract_python(raw)
        self.assertIn("import re", code)
        ns: dict = {}
        exec(compile(code, "<candidate>", "exec"), ns, ns)
        self.assertEqual(ns["slugify"]("Hello World"), "hello-world")
        self.assertEqual(ns["slugify"]("  Foo__Bar!! "), "foo-bar")
        self.assertEqual(ns["slugify"]("---"), "")

    def test_keeps_import_inside_fenced_block(self):
        raw = """Here you go:
```python
import re

def slugify(s: str) -> str:
    return re.sub(r'[\\s_]+', '-', s.lower()).strip('-')
```
thanks
"""
        code = self.mod.extract_python(raw)
        self.assertTrue(code.lstrip().startswith("import re"))
        ns: dict = {}
        exec(compile(code, "<candidate>", "exec"), ns, ns)
        self.assertEqual(ns["slugify"]("Hello World"), "hello-world")

    def test_import_inside_function_still_works(self):
        raw = """def slugify(s: str) -> str:
    import re
    return re.sub(r'\\W+', '-', s.lower()).strip('-')
"""
        code = self.mod.extract_python(raw)
        ns: dict = {}
        exec(compile(code, "<candidate>", "exec"), ns, ns)
        self.assertEqual(ns["slugify"]("Hello World"), "hello-world")

    def test_drops_prose_before_def_but_keeps_imports(self):
        raw = """Sure, here is a solution:
import re
from string import ascii_lowercase  # noqa: F401

def slugify(s: str) -> str:
    return re.sub(r'\\s+', '-', s.lower()).strip('-')
"""
        code = self.mod.extract_python(raw)
        self.assertNotIn("Sure", code)
        self.assertIn("import re", code)
        self.assertIn("from string import ascii_lowercase", code)


if __name__ == "__main__":
    unittest.main()
