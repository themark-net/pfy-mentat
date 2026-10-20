#!/usr/bin/env python3
"""Map the decision harness out and back. Subprocess only. No model."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SURFACE = REPO / "examples" / "harness2-local" / "surface.py"
SOURCES = (
    "examples/typed-decisions-local/trial.py",
    ".grok/skills/jev-decision/SKILL.md",
    "AGENTS.md",
)
SKILL = ".grok/skills/jev-decision/SKILL.md"
CASES = "data/decision-gates/laya-trial.cases.v0.json"


def _snap(root: Path) -> dict[str, bytes]:
    out = {}
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        out[path.relative_to(root).as_posix()] = path.read_bytes()
    return out


class SurfaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch = REPO / "tmp" / "h2surf" / self.id().rsplit(".", 1)[-1]
        if self.scratch.exists():
            shutil.rmtree(self.scratch)
        self.repo = self.scratch / "repo"
        self.harness = self.scratch / "harness"
        self.repo.mkdir(parents=True)
        for rel in SOURCES:
            dest = self.repo / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / rel, dest)
        self.before = _snap(self.repo)

    def tearDown(self) -> None:
        shutil.rmtree(self.scratch, ignore_errors=True)

    def _run(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SURFACE), *args],
            cwd=REPO,
            text=True,
            capture_output=True,
            check=False,
        )

    def _export(self) -> subprocess.CompletedProcess[str]:
        return self._run(["export", "--repo", str(self.repo), "--dest", str(self.harness)])

    def _adopt(self) -> subprocess.CompletedProcess[str]:
        self.receipt = self.scratch / "receipt.json"
        return self._run(
            [
                "adopt",
                "--repo",
                str(self.repo),
                "--harness",
                str(self.harness),
                "--receipt",
                str(self.receipt),
            ]
        )

    def _receipt(self) -> dict:
        return json.loads(self.receipt.read_text(encoding="utf-8"))

    def test_round_trip_is_byte_identical(self) -> None:
        exported = self._export()
        self.assertEqual(exported.returncode, 0, exported.stderr)
        prompt = (self.harness / "systemprompt.md").read_text(encoding="utf-8")
        self.assertIn("jev-decision", prompt)
        self.assertIn("0.85", prompt)
        guards = (self.harness / "guardrails.md").read_text(encoding="utf-8")
        self.assertIn("Commit secrets, API keys, or `auth.json`", guards)
        self.assertIn("no Feature GO from the port", guards)
        tool = (self.harness / "tool_descriptions" / "tool_guidance.md").read_text(encoding="utf-8")
        self.assertIn("Custom Scripts, Tools & Automation", tool)
        skill = (self.harness / "skills" / "jev-decision" / "SKILL.md").read_bytes()
        self.assertEqual(skill, (self.repo / SKILL).read_bytes())
        adopted = self._adopt()
        self.assertEqual(adopted.returncode, 0, adopted.stderr)
        self.assertEqual(_snap(self.repo), self.before)
        self.assertEqual(self._receipt()["written"], [])
        self.assertEqual(self._receipt()["rejected_rule_edits"], [])

    def test_skill_edit_maps_to_that_file_only(self) -> None:
        exported = self._export()
        self.assertEqual(exported.returncode, 0, exported.stderr)
        path = self.harness / "skills" / "jev-decision" / "SKILL.md"
        path.write_text(path.read_text(encoding="utf-8") + "Extra mapped line.\n", encoding="utf-8")
        adopted = self._adopt()
        self.assertEqual(adopted.returncode, 0, adopted.stderr)
        after = _snap(self.repo)
        changed = [rel for rel, body in after.items() if self.before.get(rel) != body]
        self.assertEqual(changed, [SKILL])
        self.assertIn(b"Extra mapped line.\n", after[SKILL])
        self.assertEqual(self._receipt()["written"], [SKILL])

    def test_guardrail_edit_is_rejected(self) -> None:
        exported = self._export()
        self.assertEqual(exported.returncode, 0, exported.stderr)
        path = self.harness / "guardrails.md"
        path.write_text(path.read_text(encoding="utf-8").replace("## Do not", "## Do change", 1), encoding="utf-8")
        adopted = self._adopt()
        self.assertEqual(adopted.returncode, 2, adopted.stderr)
        self.assertIn("AGENTS.md", adopted.stderr)
        edits = self._receipt()["rejected_rule_edits"]
        self.assertTrue(edits)
        self.assertTrue(all(row["path"] == "AGENTS.md" for row in edits))
        self.assertEqual(_snap(self.repo), self.before)

    def test_disallowed_paths_are_named(self) -> None:
        for rel in (".github/workflows/x.yml", CASES):
            if self.harness.exists():
                shutil.rmtree(self.harness)
            exported = self._export()
            self.assertEqual(exported.returncode, 0, exported.stderr)
            planted = self.harness / rel
            planted.parent.mkdir(parents=True, exist_ok=True)
            planted.write_text("planted\n", encoding="utf-8")
            adopted = self._adopt()
            self.assertEqual(adopted.returncode, 2, adopted.stderr)
            self.assertIn(rel, adopted.stderr)
            self.assertIn(rel, self._receipt()["rejected_paths"])
            self.assertEqual(_snap(self.repo), self.before)
            self.assertFalse((self.repo / rel).exists())

    def test_missing_skill_recovers(self) -> None:
        skill = self.repo / SKILL
        saved = skill.read_bytes()
        skill.unlink()
        missing = self._export()
        self.assertEqual(missing.returncode, 2, missing.stderr)
        self.assertIn(SKILL, missing.stderr)
        self.assertFalse(self.harness.exists())
        skill.parent.mkdir(parents=True, exist_ok=True)
        skill.write_bytes(saved)
        restored = self._export()
        self.assertEqual(restored.returncode, 0, restored.stderr)
        adopted = self._adopt()
        self.assertEqual(adopted.returncode, 0, adopted.stderr)
        self.assertEqual(_snap(self.repo), self.before)


if __name__ == "__main__":
    unittest.main()
