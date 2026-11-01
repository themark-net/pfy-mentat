"""T-0095 receipts stay I0. A pass while cloud keys or a missing pin remain is a fail."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FACTS_RE = re.compile(r"<!-- stage0-facts\n(\{.*?\})\n-->", re.S)


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _facts(rel: str) -> tuple[str, dict]:
    text = _read(rel)
    match = FACTS_RE.search(text)
    if not match:
        raise AssertionError("missing stage0-facts block in %s" % rel)
    return text, json.loads(match.group(1))


def promotion_blocked(data: dict) -> bool:
    """A Stage-0 PASS is blocked while cloud env is required or the git pin is missing.

    A pass with a pin and an empty required_env list is not blocked. That is
    the recovery: log a timed hello that needs no cloud speech account, then
    set stage0 to PASS and clear required_env.
    """
    if data.get("stage0") != "PASS":
        return False
    if data.get("required_env"):
        return True
    if not data.get("git_pin"):
        return True
    return False


class VoiceStage0RefTests(unittest.TestCase):
    def test_stage_cards_stay_i0_and_catalog_rows_stay_absent(self):
        stages = json.loads(_read("data/tool_integration_stages.json"))
        tools = json.loads(_read("data/tools.json"))
        names = {row.get("name") for row in tools.get("tools") or []}
        for card_name, entry in (
            ("Pipecat", "sources/entries/150-pipecat.md"),
            ("LiveKit", "sources/entries/151-livekit.md"),
        ):
            card = stages["tools"][card_name]
            self.assertEqual(card["integration_stage"], "I0", card_name)
            self.assertEqual(card["intent"], "ref_only", card_name)
            self.assertEqual(card["entry"], entry)
            self.assertNotIn(card_name, names)
        self.assertNotIn("freeapp", {str(n).lower() for n in names})
        joined = _read("TOOLS.md")
        self.assertNotIn("150-pipecat", joined)
        self.assertNotIn("151-livekit", joined)
        self.assertNotIn("152-freeapp", joined)

    def test_receipt_facts_stay_fail_while_the_guard_holds(self):
        """Facts are parsed. Price is a number. Keys are a list, not a prose search.

        Fail: stage0 is PASS while required_env is non-empty or git_pin is null.
        Recovery: clear required_env only after a timed hello with no cloud
        account, and set git_pin only from a published repository.
        """
        expected = {
            "sources/entries/150-pipecat.md": {
                "required_env": ["DEEPGRAM_API_KEY", "OPENAI_API_KEY", "CARTESIA_API_KEY"],
                "git_pin": "6f777a0ef3bb98163d10d708525a0db21cda5fbf",
                "license_open": True,
                "price_usd": None,
                "model_license_proprietary": False,
            },
            "sources/entries/151-livekit.md": {
                "required_env": ["LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET"],
                "git_pin": "11c8ad8d74c272cf046e65d83cfe7be46abaec64",
                "license_open": True,
                "price_usd": None,
                "model_license_proprietary": True,
            },
            "sources/entries/152-freeapp.md": {
                "required_env": [],
                "git_pin": None,
                "license_open": False,
                "price_usd": 299,
                "model_license_proprietary": False,
            },
        }
        for rel, want in expected.items():
            text, data = _facts(rel)
            self.assertEqual(data["stage0"], "FAIL", rel)
            self.assertIn("Stage-0 FAIL", text)
            self.assertNotIn("Stage-0 PASS", text)
            self.assertEqual(data["required_env"], want["required_env"], rel)
            self.assertEqual(data["git_pin"], want["git_pin"], rel)
            self.assertEqual(data["license_open"], want["license_open"], rel)
            self.assertEqual(data["price_usd"], want["price_usd"], rel)
            self.assertIn(type(data["price_usd"]), (int, type(None)))
            self.assertEqual(data["model_license_proprietary"], want["model_license_proprietary"], rel)
            self.assertFalse(promotion_blocked(data), rel)
            passed = dict(data)
            passed["stage0"] = "PASS"
            self.assertTrue(promotion_blocked(passed), rel)
        self.assertFalse(promotion_blocked({
            "stage0": "PASS",
            "required_env": [],
            "git_pin": "abc123",
        }))


if __name__ == "__main__":
    unittest.main()
