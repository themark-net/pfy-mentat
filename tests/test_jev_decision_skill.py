"""SoT jev-decision skill keeps the headless wrap and the escalate exit.

Reads bootstrap/grok-cli/skills/jev-decision/SKILL.md. Delete the prefer
`./pfy build -p` guidance or the exit-3 escalate contract and this goes red.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOT = ROOT / "bootstrap" / "grok-cli" / "skills" / "jev-decision" / "SKILL.md"

# Ordered contract: 0 ready, then 3 escalate (valid / not broken), then 1 fail.
# Anchored on `decision route` so older "FAIL+next" lock text cannot pass.
_ROUTE_EXIT = re.compile(
    r"(?is)decision route"
    r".{0,500}\b0\b.{0,16}ready"
    r".{0,160}\b3\b.{0,16}escalate"
    r".{0,160}not broken"
    r".{0,160}\b1\b.{0,16}fail"
)
_PREFER_BUILD = re.compile(
    r"(?is)prefer\b.{0,300}\./pfy build -p.{0,300}grok -p"
)


class JevDecisionSkillContractTest(unittest.TestCase):
    def test_sot_prefers_pfy_build_p_and_documents_exit_3_escalate(self):
        text = SOT.read_text(encoding="utf-8")
        # Fail: headless line dropped → bots call bare grok -p and skip the receipt.
        # Recover: put back prefer `./pfy build -p` over `grok -p` and the receipt path.
        self.assertRegex(text, _PREFER_BUILD)
        self.assertIn("pipelines/dogfood/build/", text)
        # Fail: exit 3 dropped → conf-low looks like a crash and scripts may auto-act.
        # Recover: restore 0=ready, 3=escalate (valid, not broken; no silent auto-act), 1=fail.
        self.assertRegex(text, _ROUTE_EXIT)
