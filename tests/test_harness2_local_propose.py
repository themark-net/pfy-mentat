#!/usr/bin/env python3
"""Behavior of propose.py against a local bare repo under the worktree tmp/.

No model. Each test drives the real script as a subprocess.
"""
from __future__ import annotations

import json
import os
import string
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROPOSE = REPO / "examples" / "harness2-local" / "propose.py"
SCRATCH = REPO / "tmp" / "propose-tests"
BANK = REPO / "data" / "decision-gates" / "laya-trial.cases.v0.json"

GIT = [
    "git",
    "-c",
    "user.email=harness2-local@example.com",
    "-c",
    "user.name=harness2-local",
]


def _alnum(n: int, alphabet: str = string.ascii_letters + string.digits) -> str:
    # Fixed alphabet, not secrets. The tokens are fixtures.
    chars = []
    for i in range(n):
        chars.append(alphabet[(i * 17 + 3) % len(alphabet)])
    return "".join(chars)


def _tokens() -> dict[str, str]:
    return {
        "ghp_": "ghp_" + _alnum(36),
        "gho_": "gho_" + _alnum(36),
        "ghs_": "ghs_" + _alnum(36),
        "ghu_": "ghu_" + _alnum(36),
        "ghr_": "ghr_" + _alnum(36),
        "github_pat_": "github_pat_" + _alnum(60, string.ascii_letters + string.digits + "_"),
        "xai-": "xai-" + _alnum(40),
        "sk-proj-": "sk-proj-" + _alnum(32),
        "sk-ant-": "sk-ant-" + _alnum(32),
        "AKIA": "AKIA" + _alnum(16, string.digits + string.ascii_uppercase),
        "AIza": "AIza" + _alnum(35),
        "pem": "-----BEGIN PRIVATE KEY-----",
    }


BENIGN_SECRET = [
    "task-specific",
    "risk-adjusted",
    "desk-check",
    "xai-org",
    "sk-short",
    "ghp_short",
]

BENIGN_LINES = [
    "Expected: a JSON object with choice and confidence.",
    "label: a short reason for the choice",
    "Expected: check CI before deciding.",
    "expected = local runtime when available",
    "Label = keep it short",
    "case 2 - a quick example",
    "If expected: hold is wrong for busy hosts, explain why",
    "Prefer push only when CI is green.",
    'criteria: {"push": "tests pass", "hold": "busy"}',
    "Option B is usually safer than A.",
    "The correct answer must be one letter A-D.",
    "Expected output: one JSON object.",
    "label the output clearly",
    "phase-01 setup notes",
    "hd-123 is not an id",
    "Step t10: check CI first.",
    "Step t10 is check CI first",
    "answer: a JSON object",
    "Answer: explain briefly.",
    '{"choice": "push", "confidence": 0.9, "why": "CI is green and the host is idle."}',
    "Expected: escalate for the ambiguous Kronos case.",
    "answer: a.",
    "Document the rollout before editing skills.",
    "The relay listens on loopback only.",
    "Seed stays fixed for the whole run.",
    "Training uses four tasks of eight.",
    "Write the receipt under host-only.",
    "case 3 - A",
]


def _passing_receipt() -> dict:
    row = {"correct": 8, "n": 16, "wrong_but_confident": 1, "parse_ok": 1.0}
    final = {"correct": 11, "n": 16, "wrong_but_confident": 1, "parse_ok": 1.0}
    return {
        "install_mode": "workspace_config",
        "heldout": {"a1": dict(row), "a2": dict(row), "c": final},
        "relay_log": (
            "POST /v1/chat/completions model=llamacpp/qwen3.6-35b temperature: 0 seed: 230 bytes_out=4\n"
            "POST /v1/chat/completions temperature: 0.0 seed: 230 bytes_out=4\n"
        ),
    }


def _diff(lines: list[str], name: str = "NOTES.md") -> str:
    body = "".join(f"+{line}\n" for line in lines)
    return (
        f"diff --git a/{name} b/{name}\n"
        "new file mode 100644\n"
        "index 0000000..1111111\n"
        "--- /dev/null\n"
        f"+++ b/{name}\n"
        f"@@ -0,0 +1,{len(lines)} @@\n"
        f"{body}"
    )


def _leak_lines() -> list[str]:
    bank = json.loads(BANK.read_text(encoding="utf-8"))
    note = next(
        case["note"]
        for case in bank["cases"]
        if isinstance(case.get("note"), str) and "\n" not in case["note"] and len(case["note"]) >= 20
    )
    case_id = next(case["id"] for case in bank["cases"] if case["id"] == "ph-01-green-idle")
    return [
        "answer: B",
        "answer: escalate",
        "T07: local",
        "t07 → hold",
        "t07 is push",
        "PH-03 is push",
        "see PH-03",
        "Expected: escalate.",
        "expected: hold",
        '"expected": "push",',
        "case 4: label D (correct)",
        "t07 = escalate",
        "label: B correct",
        "case 17: label C",
        note,
        '"label": "push", "correct": true',
        'expected = "escalate"',
        "ground truth: skip_install",
        "answer key = D",
        "held-out: 12/16",
        case_id,
        "see ph-03",
    ]


class ProposeTests(unittest.TestCase):
    def setUp(self) -> None:
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.d = Path(self.tmp.name)
        self.empty = self.d / "empty-gitconfig"
        self.empty.write_text("", encoding="utf-8")
        self.env = os.environ.copy()
        self.env["GIT_CONFIG_NOSYSTEM"] = "1"
        self.env["GIT_CONFIG_GLOBAL"] = str(self.empty)
        self.env["GIT_TERMINAL_PROMPT"] = "0"
        self.env["GIT_AUTHOR_NAME"] = "harness2-local"
        self.env["GIT_AUTHOR_EMAIL"] = "harness2-local@example.com"
        self.env["GIT_COMMITTER_NAME"] = "harness2-local"
        self.env["GIT_COMMITTER_EMAIL"] = "harness2-local@example.com"
        # A host paid key must not leak into the child unless a test sets one.
        xdir = str(REPO / "examples" / "x-intake-local")
        import sys

        if xdir not in sys.path:
            sys.path.insert(0, xdir)
        import smoke

        for name in smoke.PAID_KEYS:
            self.env.pop(name, None)
        seed = self.d / "seed"
        self.remote = self.d / "remote.git"
        self._git("init", "-b", "main", str(seed))
        (seed / "README").write_text("base\n", encoding="utf-8")
        self._git("-C", str(seed), "add", "README")
        self._git("-C", str(seed), "commit", "-m", "base")
        self._git("clone", "--bare", str(seed), str(self.remote))
        self.main_sha = self.heads()["main"]

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _git(self, *args: str) -> subprocess.CompletedProcess[str]:
        proc = subprocess.run(
            [*GIT, *args],
            cwd=str(self.d),
            env=self.env,
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )
        if proc.returncode != 0:
            raise AssertionError(proc.stderr or proc.stdout)
        return proc

    def heads(self) -> dict[str, str]:
        proc = self._git("ls-remote", "--heads", str(self.remote))
        found = {}
        for line in proc.stdout.splitlines():
            sha, ref = line.split()
            found[ref.removeprefix("refs/heads/")] = sha
        return found

    def assert_main_unchanged(self) -> None:
        found = self.heads()
        self.assertEqual(found.get("main"), self.main_sha)
        self.assertEqual(set(found), {"main"})

    def run_propose(
        self,
        lines: list[str],
        receipt: dict | None = None,
        *,
        branch: str = "",
        remote: Path | None = None,
        work_name: str = "work",
        extra_env: dict | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], Path, Path]:
        diff_path = self.d / f"{work_name}.diff"
        receipt_path = self.d / f"{work_name}.json"
        out = self.d / f"{work_name}.out.json"
        work = self.d / work_name
        diff_path.write_text(_diff(lines), encoding="utf-8")
        receipt_path.write_text(json.dumps(receipt or _passing_receipt()), encoding="utf-8")
        env = dict(self.env)
        if extra_env:
            env.update(extra_env)
        cmd = [
            "python3",
            str(PROPOSE),
            "--receipt",
            str(receipt_path),
            "--diff",
            str(diff_path),
            "--remote",
            str(remote or self.remote),
            "--work-dir",
            str(work),
            "--out",
            str(out),
            "--date",
            "20261020",
        ]
        if branch:
            cmd.extend(["--branch", branch])
        proc = subprocess.run(cmd, env=env, text=True, capture_output=True, timeout=60, check=False)
        return proc, out, work

    def test_passing_receipt_pushes_and_leaves_main(self) -> None:
        proc, out, _work = self.run_propose(["The relay stays on loopback."])
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("pushed bot/h2-proposal-20261020-", proc.stdout)
        name = proc.stdout.strip().split()[-1]
        self.assertRegex(name, r"^bot/h2-proposal-20261020-[0-9a-f]{12}$")
        found = self.heads()
        self.assertEqual(found["main"], self.main_sha)
        self.assertIn(name, found)
        self.assertNotEqual(found[name], self.main_sha)
        body = self._git("--git-dir", str(self.remote), "log", "-1", "--format=%B", name).stdout
        self.assertIn("before: a1 8/16, a2 8/16", body)
        self.assertIn("after: 11/16", body)
        saved = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(saved["status"], "DONE")
        self.assertEqual(saved["branch"], name)
        self.assertIsNone(saved["negative_finding"])

    def test_plus_one_gain_writes_no_ref(self) -> None:
        receipt = _passing_receipt()
        receipt["heldout"]["c"]["correct"] = 9
        proc, out, _work = self.run_propose(["The relay stays on loopback."], receipt)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("negative_finding: gain", proc.stdout)
        self.assert_main_unchanged()
        saved = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(saved["negative_finding"], "gain")
        self.assertEqual(saved["status"], "DONE")

    def test_wrong_but_confident_rise_writes_no_ref(self) -> None:
        receipt = _passing_receipt()
        receipt["heldout"]["c"]["wrong_but_confident"] = 4
        proc, _out, _work = self.run_propose(["The relay stays on loopback."], receipt)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("negative_finding: wrong-but-confident", proc.stdout)
        self.assert_main_unchanged()

    def test_temperature_drift_writes_no_ref(self) -> None:
        receipt = _passing_receipt()
        receipt["relay_log"] = "POST /v1/chat/completions temperature: 0.7 seed: 230 bytes_out=1\n"
        proc, _out, _work = self.run_propose(["The relay stays on loopback."], receipt)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("negative_finding: temperature", proc.stdout)
        self.assert_main_unchanged()

    def test_seed_drift_writes_no_ref(self) -> None:
        receipt = _passing_receipt()
        receipt["relay_log"] = "POST /v1/chat/completions temperature: 0 seed: 231 bytes_out=1\n"
        proc, _out, _work = self.run_propose(["The relay stays on loopback."], receipt)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("negative_finding: seed", proc.stdout)
        self.assert_main_unchanged()

    def test_parse_ok_drop_writes_no_ref(self) -> None:
        receipt = _passing_receipt()
        receipt["heldout"]["c"]["parse_ok"] = 0.5
        proc, _out, _work = self.run_propose(["The relay stays on loopback."], receipt)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("negative_finding: parse_ok", proc.stdout)
        self.assert_main_unchanged()

    def test_install_mode_disagreement_writes_no_ref(self) -> None:
        receipt = _passing_receipt()
        receipt["heldout"]["c"]["install_mode"] = "other"
        proc, _out, _work = self.run_propose(["The relay stays on loopback."], receipt)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("negative_finding: install_mode", proc.stdout)
        self.assert_main_unchanged()

    def test_gain_must_exceed_a_wide_base_gap(self) -> None:
        receipt = _passing_receipt()
        receipt["heldout"]["a1"]["correct"] = 10
        receipt["heldout"]["a2"]["correct"] = 8
        receipt["heldout"]["c"]["correct"] = 12
        proc, _out, _work = self.run_propose(["The relay stays on loopback."], receipt, work_name="gap")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("negative_finding: gain", proc.stdout)
        self.assert_main_unchanged()
        receipt["heldout"]["c"]["correct"] = 13
        again, _out2, _work2 = self.run_propose(
            ["The relay stays on loopback."],
            receipt,
            work_name="gap-ok",
        )
        self.assertEqual(again.returncode, 0, again.stderr + again.stdout)
        self.assertIn("pushed ", again.stdout)
        self.assertEqual(self.heads()["main"], self.main_sha)

    def test_other_protected_names_exit_2(self) -> None:
        for name in ("master", "stage", "dev", "build/h1"):
            proc, _out, _work = self.run_propose(
                ["The relay stays on loopback."],
                branch=name,
                work_name="prot-" + name.replace("/", "-"),
            )
            self.assertEqual(proc.returncode, 2, name + proc.stdout + proc.stderr)
            self.assertIn(f"BLOCKED: protected branch {name}", proc.stdout)
        self.assert_main_unchanged()

    def test_target_main_exits_2(self) -> None:
        proc, _out, _work = self.run_propose(["The relay stays on loopback."], branch="main")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("BLOCKED: protected branch main", proc.stdout)
        self.assert_main_unchanged()

    def test_reused_name_gets_a_suffix(self) -> None:
        self._git(
            "--git-dir",
            str(self.remote),
            "update-ref",
            "refs/heads/bot/h2-proposal-reused",
            self.main_sha,
        )
        proc, _out, _work = self.run_propose(
            ["The relay stays on loopback."],
            branch="bot/h2-proposal-reused",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("pushed bot/h2-proposal-reused-2", proc.stdout)
        found = self.heads()
        self.assertEqual(found["bot/h2-proposal-reused"], self.main_sha)
        self.assertIn("bot/h2-proposal-reused-2", found)
        self.assertNotEqual(found["bot/h2-proposal-reused-2"], self.main_sha)

    def test_unreachable_remote_leaves_workdir_and_retry_pushes(self) -> None:
        missing = self.d / "missing.git"
        proc, _out, work = self.run_propose(
            ["The relay stays on loopback."],
            remote=missing,
            work_name="left-behind",
        )
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertTrue(work.is_dir())
        self.assertIn("BLOCKED: remote unreachable", proc.stdout)
        self.assert_main_unchanged()
        again, _out2, _work2 = self.run_propose(
            ["The relay stays on loopback."],
            work_name="retry",
        )
        self.assertEqual(again.returncode, 0, again.stderr + again.stdout)
        self.assertIn("pushed ", again.stdout)
        self.assertEqual(self.heads()["main"], self.main_sha)

    def test_secret_shapes_are_masked_and_write_no_ref(self) -> None:
        tokens = _tokens()
        proc, _out, _work = self.run_propose(list(tokens.values()))
        blob = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 2, blob)
        for token in tokens.values():
            self.assertNotIn(token, blob)
            self.assertIn(token[:4] + "***", proc.stdout)
        self.assert_main_unchanged()

    def test_gho_token_is_refused(self) -> None:
        token = _tokens()["gho_"]
        proc, _out, _work = self.run_propose([token])
        blob = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 2, blob)
        self.assertIn("gho_***", proc.stdout)
        self.assertNotIn(token, blob)
        self.assert_main_unchanged()

    def test_benign_secret_text_pushes(self) -> None:
        proc, _out, _work = self.run_propose(BENIGN_SECRET)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("pushed ", proc.stdout)
        self.assertNotIn("BLOCKED: secret", proc.stdout)

    def test_paid_key_value_is_masked(self) -> None:
        value = "paid-value-0123456789abcdef"
        proc, _out, _work = self.run_propose(
            [f"note {value} end"],
            extra_env={"OPENAI_API_KEY": value},
        )
        blob = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 2, blob)
        self.assertIn("paid***", proc.stdout)
        self.assertNotIn(value, blob)
        self.assert_main_unchanged()

    def test_label_b_correct_is_a_negative_finding(self) -> None:
        proc, out, _work = self.run_propose(["label: B correct"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("negative_finding: label-leak", proc.stdout)
        self.assert_main_unchanged()
        text = out.read_text(encoding="utf-8")
        saved = json.loads(text)
        self.assertEqual(saved["negative_finding"], "label-leak")
        self.assertEqual(saved["status"], "DONE")
        self.assertEqual(saved["item"], 5)
        self.assertEqual(len(saved["lines"]), 1)
        self.assertNotIn("B correct", text)
        self.assertNotIn("label:", text)

    def test_named_leak_lines_all_block(self) -> None:
        lines = _leak_lines()
        self.assertGreaterEqual(len(lines), 22)
        proc, out, _work = self.run_propose(lines)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        saved = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(saved["negative_finding"], "label-leak")
        self.assertEqual(len(saved["lines"]), len(lines))
        text = out.read_text(encoding="utf-8")
        self.assertNotIn("ph-01-green-idle", text)
        self.assertNotIn("skip_install", text)
        self.assertNotIn(lines[14], text)
        self.assert_main_unchanged()

    def test_false_positive_budget_blocks_only_case_3(self) -> None:
        self.assertEqual(len(BENIGN_LINES), 28)
        proc, out, _work = self.run_propose(BENIGN_LINES)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        saved = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(saved["negative_finding"], "label-leak")
        diff = (self.d / "work.diff").read_text(encoding="utf-8")
        blocked = [diff.splitlines()[n - 1][1:] for n in saved["lines"]]
        self.assertEqual(blocked, ["case 3 - A"])
        self.assert_main_unchanged()

    def test_warn_only_lines_push_with_leak_warnings(self) -> None:
        lines = [line for line in BENIGN_LINES if line != "case 3 - A"]
        proc, _out, _work = self.run_propose(lines)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        name = proc.stdout.strip().split()[-1]
        body = self._git("--git-dir", str(self.remote), "log", "-1", "--format=%B", name).stdout
        self.assertIn("Leak warnings:", body)
        self.assertIn("Prefer push only when CI is green.", body)
        self.assertIn("Expected: escalate for the ambiguous Kronos case.", body)
        self.assertEqual(self.heads()["main"], self.main_sha)


if __name__ == "__main__":
    unittest.main()
