"""Issue #25 catalog text: the Laguna lab stays unchecked until a receipt exists."""
from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOD = ROOT / "docs/ops/laguna-local-dod.md"
ENTRY = ROOT / "sources/entries/073-laguna-s-2-1.md"
PULL_BOX = "- [ ] `ollama pull` / llama.cpp load succeeds; one completion via OpenAI-compatible API"


class LagunaSmokeNoteTests(unittest.TestCase):
    def test_pull_box_stays_open_and_no_weights_are_tracked(self):
        dod = DOD.read_text(encoding="utf-8")
        entry = ENTRY.read_text(encoding="utf-8")
        self.assertIn(PULL_BOX, dod)
        self.assertNotIn("- [x] `ollama pull`", dod)
        self.assertIn("did not pull weights", entry)
        tracked = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.lower()
        self.assertNotIn(".gguf", tracked)
        self.assertNotIn("laguna-s-2.1", tracked)

    def test_x_com_200_stays_content_unverified(self):
        """A 200, even with the claim text in the body, is not a verified post.

        Fail: the entry source says verified, or the probe helper returns
        verified for status 200. Recovery: set the source back to
        content-unverified. Read the post before claiming its words.
        """
        import importlib.util

        spec = importlib.util.spec_from_file_location("catalog_check", ROOT / "scripts" / "catalog_check.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        entry = ENTRY.read_text(encoding="utf-8")
        url = "https://x.com/i/status/2079613777343848465"
        claim = "Terminal-Bench 2.1: 70.2"
        for body in ("", claim):
            verdict = mod.x_post_status_verdict(200, url, body=body)
            self.assertEqual(verdict, "content-unverified")
            self.assertNotEqual(verdict, "verified")
        self.assertIn("- **Source**: %s" % verdict, entry)
        self.assertEqual(mod.x_entry_source_problems(entry), [])
        labeled = entry.replace("content-unverified", "verified", 1)
        problems = mod.x_entry_source_problems(labeled)
        self.assertTrue(problems)
        self.assertTrue(any("not prove the post" in item or "not be labeled verified" in item for item in problems))


if __name__ == "__main__":
    unittest.main()
