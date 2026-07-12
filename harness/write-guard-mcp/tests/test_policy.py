"""Unit tests for write-guard policy (stdlib unittest)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from write_guard.policy import Policy, decide, match_globs, under_roots  # noqa: E402


class TestPolicy(unittest.TestCase):
    def setUp(self) -> None:
        self.pol = Policy(
            roots=["/workspace"],
            deny_globs=["**/.env", "**/auth.json", "**/*secret*"],
            allow_write_globs=["/workspace/**"],
            deny_write_globs=["/workspace/.write-guard-audit.jsonl"],
            allow_delete_globs=[],
            default_mode="enforce",
        )

    def test_under_roots(self) -> None:
        self.assertTrue(under_roots("/workspace/a", ["/workspace"]))
        self.assertFalse(under_roots("/tmp/a", ["/workspace"]))

    def test_deny_env_enforce(self) -> None:
        d = decide("/workspace/.env", op="write", mode="enforce", policy=self.pol)
        self.assertFalse(d.allow)

    def test_allow_normal_enforce(self) -> None:
        d = decide("/workspace/src/a.py", op="write", mode="enforce", policy=self.pol)
        self.assertTrue(d.allow)

    def test_audit_allows_env_with_flag(self) -> None:
        d = decide("/workspace/.env", op="write", mode="audit", policy=self.pol)
        self.assertTrue(d.allow)
        self.assertIn("deny_globs", d.reason)

    def test_delete_default_deny(self) -> None:
        d = decide("/workspace/x", op="delete", mode="enforce", policy=self.pol)
        self.assertFalse(d.allow)

    def test_secret_name(self) -> None:
        d = decide("/workspace/my_secret_token", op="write", mode="enforce", policy=self.pol)
        self.assertFalse(d.allow)

    def test_match_auth_json(self) -> None:
        self.assertIsNotNone(match_globs("/workspace/foo/auth.json", ["**/auth.json"]))


if __name__ == "__main__":
    unittest.main()
