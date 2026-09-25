"""pfylib.registry: loaders + validate() (ADR-0017)."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pfylib import registry  # noqa: E402


class RegistryLoadTests(unittest.TestCase):
    def test_root_and_state_dir(self):
        self.assertEqual(registry.root(ROOT), ROOT)
        self.assertTrue((registry.root() / "data" / "toolsets.json").is_file())
        self.assertEqual(registry.state_dir("/tmp/x"), registry.state_dir("/tmp/x"))

    def test_harness_axis_is_role_harness_only(self):
        hids = registry.harness_ids(ROOT)
        self.assertGreaterEqual(len(hids), 5)
        for expected in ("grok", "opencode", "claude-code", "codex", "hermes"):
            self.assertIn(expected, hids)
        for not_a_harness in ("ollama", "freetoken", "agent-cage"):
            self.assertNotIn(not_a_harness, hids)

    def test_toolsets_seeded(self):
        tids = registry.toolset_ids(ROOT)
        self.assertEqual(set(tids), {"jev", "gab", "opencontext", "code-graph", "orchestration", "catalog-ask"})
        self.assertEqual(len(tids), len(set(tids)))
        jev = registry.toolset("jev", ROOT)
        self.assertIsNotNone(jev)
        self.assertIn("local", jev["lanes"])
        self.assertIsNone(registry.toolset("nope", ROOT))
        self.assertIsNone(registry.harness("nope", ROOT))

    def test_repo_data_validates(self):
        self.assertEqual(registry.validate(root_dir=ROOT), [])


class RegistryValidateTests(unittest.TestCase):
    def setUp(self):
        self.ts = registry.load_toolsets(ROOT)
        self.hs = registry.load_harnesses(ROOT)

    def _problems(self, ts):
        return registry.validate(ts, self.hs)

    def test_missing_cell_reported(self):
        ts = copy.deepcopy(self.ts)
        del ts["toolsets"][0]["implementation"]["grok"]
        probs = self._problems(ts)
        self.assertTrue(any("x grok: missing cell" in p for p in probs), probs)

    def test_bad_status_reported(self):
        ts = copy.deepcopy(self.ts)
        ts["toolsets"][0]["implementation"]["grok"]["status"] = "ready"
        self.assertTrue(any("status 'ready' not in" in p for p in self._problems(ts)))

    def test_unknown_harness_and_bad_lane(self):
        ts = copy.deepcopy(self.ts)
        ts["toolsets"][0]["implementation"]["vscode"] = {"status": "stub", "how": "x"}
        ts["toolsets"][1]["lanes"] = ["edge"]
        probs = self._problems(ts)
        self.assertTrue(any("unknown harness 'vscode'" in p for p in probs))
        self.assertTrue(any("lanes must be non-empty subset" in p for p in probs))

    def test_catalog_tool_must_be_present_string_or_null(self):
        ts = copy.deepcopy(self.ts)
        del ts["toolsets"][0]["catalog_tool"]
        ts["toolsets"][1]["catalog_tool"] = 7
        probs = self._problems(ts)
        self.assertTrue(any("missing catalog_tool" in p for p in probs))
        self.assertTrue(any("catalog_tool must be string or null" in p for p in probs))

    def test_duplicate_id_and_empty_rows(self):
        ts = copy.deepcopy(self.ts)
        ts["toolsets"].append(copy.deepcopy(ts["toolsets"][0]))
        self.assertTrue(any("duplicate id" in p for p in self._problems(ts)))
        self.assertTrue(any("empty or missing" in p for p in self._problems({"toolsets": []})))


if __name__ == "__main__":
    unittest.main()
