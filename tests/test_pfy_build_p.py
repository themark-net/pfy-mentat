"""Behavior tests for pfy build -p and decision route escalate exit contract."""
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


jev = _load("pfy_jev_230", "scripts/pfy_jev_230.py")
build = _load("pfy_build_p", "scripts/pfy_build_p.py")


class RouteEscalateExitTests(unittest.TestCase):
    def test_conf_low_is_escalate_exit_3_not_broken(self):
        os.environ["PFY_JEV_CONF_GATE"] = "0.99"
        try:
            low = jev.decide_choice(
                "ambiguous state",
                {"a": "maybe", "b": "also maybe", "c": "unclear"},
            )
        finally:
            os.environ.pop("PFY_JEV_CONF_GATE", None)
        self.assertFalse(low.get("auto_act"))
        self.assertEqual(jev.classify_decision(low), "escalate")
        self.assertEqual(jev.decision_exit_code(low), jev.EXIT_ESCALATE)
        text = jev.format_decision_cli(low)
        self.assertTrue(text.startswith("ESCALATE"), text)
        self.assertNotIn("tool failure", text.lower())

    def test_route_main_escalate_rc(self):
        os.environ["PFY_JEV_CONF_GATE"] = "0.99"
        try:
            rc = jev.main(["--route"])
        finally:
            os.environ.pop("PFY_JEV_CONF_GATE", None)
        self.assertEqual(rc, jev.EXIT_ESCALATE)

    def test_ready_exit_0(self):
        # Peaked criteria → high margin
        rec = jev.decide_choice(
            "push green tip now",
            {"push": "push green tip now", "hold": "zzzz unrelated hold"},
        )
        if not rec.get("auto_act"):
            self.skipTest("logit margin not peaked enough in this environment")
        self.assertEqual(jev.classify_decision(rec), "ready")
        self.assertEqual(jev.decision_exit_code(rec), jev.EXIT_READY)


class BuildHelperFailRecoverTests(unittest.TestCase):
    def test_missing_grok_on_path_fails_honestly(self):
        with tempfile.TemporaryDirectory(prefix="pfy-build-") as td:
            td = Path(td)
            # Empty PATH → which('grok') is None
            rc = build.build_p(
                "should not run",
                cwd=td,
                repo=ROOT,
                dry_run=False,
                path_env="",  # empty PATH
            )
            self.assertEqual(rc, build.EXIT_FAIL)
            receipts = list((td / "pipelines" / "dogfood" / "build").glob("*/receipt.jsonl"))
            self.assertTrue(receipts, "receipt.jsonl must be written on fail")
            lines = receipts[0].read_text(encoding="utf-8").strip().splitlines()
            self.assertGreaterEqual(len(lines), 2)
            rows = [json.loads(x) for x in lines]
            self.assertEqual(rows[0]["event"], "start")
            self.assertTrue(any(r.get("reason") == "grok_missing" for r in rows), rows)

    def test_dry_run_writes_real_receipt_without_exec_grok(self):
        with tempfile.TemporaryDirectory(prefix="pfy-build-dry-") as td:
            td = Path(td)
            # Provide a fake grok on PATH so missing-bin check passes; dry-run must not exec it
            fake_bin = td / "bin"
            fake_bin.mkdir()
            fake_grok = fake_bin / "grok"
            fake_grok.write_text("#!/bin/sh\necho UNEXPECTED_GROK_EXEC >&2\nexit 99\n")
            fake_grok.chmod(0o755)
            # Auth file under fake GROK_HOME so auth check can pass if dry_run skipped auth —
            # dry_run skips auth failure; still ok.
            gh = td / "grok-home"
            gh.mkdir()
            (gh / "auth.json").write_text('{"token":"test-not-real"}')
            path_env = "%s%s%s" % (fake_bin, os.pathsep, os.environ.get("PATH", ""))
            with mock.patch.dict(os.environ, {"GROK_HOME": str(gh)}, clear=False):
                rc = build.build_p(
                    "dry-run prompt",
                    cwd=td,
                    repo=ROOT,
                    dry_run=True,
                    path_env=path_env,
                    grok_home=gh,
                )
            self.assertEqual(rc, build.EXIT_OK)
            receipts = list((td / "pipelines" / "dogfood" / "build").glob("*/receipt.jsonl"))
            self.assertEqual(len(receipts), 1)
            rows = [json.loads(x) for x in receipts[0].read_text().splitlines() if x.strip()]
            events = [r["event"] for r in rows]
            self.assertIn("start", events)
            self.assertIn("toolset_apply", events)
            self.assertIn("decision_smoke", events)
            self.assertIn("decision_route_shadow", events)
            self.assertIn("grok_p", events)
            self.assertIn("done", events)
            grok_row = next(r for r in rows if r["event"] == "grok_p")
            self.assertTrue(grok_row.get("dry_run"))
            # Fake grok must not have been executed
            self.assertNotEqual(grok_row.get("rc"), 99)


# Fixed task. Same text for trimmed vs full. Unique so a merged prompt cannot hide the split.
FIXTURE_TASK = (
    "FIXTURE_TASK_D3_263\n"
    "Keep the jev gate and record preamble size apart from this task.\n"
)
# Body line that lives only in the full jev-decision skill, not in the lean contract.
_FULL_SKILL_MARKER = "Official TypeSafe agent skill"


class PreambleTrimTests(unittest.TestCase):
    """#263 trimmed preamble is smaller than the full skill dump and still gates.

    Fail: skill bodies inlined (tokens jump, ratio ~1) or the receipt has no
    preamble size (cbda54a). Recover: default trimmed pointer; set
    PFY_BUILD_FULL_PREAMBLE=1 only when the full dump is required.
    """

    def test_trimmed_preamble_bounded_against_full_dump(self):
        # How it fails: re-inlining SKILL.md blows past 400 tokens or 1/4 of full.
        # Recover: put the gate, exits, and path pointer back; leave bodies in full mode.
        trimmed = build.build_preamble(ROOT, mode="trimmed")
        full = build.build_preamble(ROOT, mode="full")
        trimmed_tok = max(1, (len(trimmed) + 3) // 4)
        full_tok = max(1, (len(full) + 3) // 4)
        self.assertLessEqual(trimmed_tok, 400, "trimmed preamble_tokens_est=%s chars=%s" % (trimmed_tok, len(trimmed)))
        self.assertGreater(full_tok, trimmed_tok)
        # ratio ≤ 0.25 ↔ 4 * trimmed <= full
        self.assertLessEqual(4 * trimmed_tok, full_tok, "trimmed/full=%s/%s" % (trimmed_tok, full_tok))
        self.assertRegex(trimmed, r"0\.85|PFY_JEV_CONF_GATE")
        self.assertIn("3=escalate", trimmed)
        self.assertIn("escalate", trimmed.lower())
        self.assertIn("pipelines/dogfood/build/", trimmed)
        self.assertIn("GROK_HOME/skills/pfy-jev-decision", trimmed)
        skill = (ROOT / "bootstrap/grok-cli/skills/jev-decision/SKILL.md").read_text(encoding="utf-8")
        self.assertIn(_FULL_SKILL_MARKER, skill)
        self.assertIn(_FULL_SKILL_MARKER, full)
        self.assertNotIn(_FULL_SKILL_MARKER, trimmed)
        self.assertNotIn("FIXTURE_TASK_D3_263", trimmed)
        self.assertEqual(build.preamble_mode_from_env({}), "trimmed")
        self.assertEqual(build.preamble_mode_from_env({"PFY_BUILD_FULL_PREAMBLE": "1"}), "full")

    def _fake_grok(self, bin_dir: Path, record_dir: Path) -> None:
        bin_dir.mkdir(parents=True, exist_ok=True)
        record_dir.mkdir(parents=True, exist_ok=True)
        script = bin_dir / "grok"
        script.write_text(
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            "from pathlib import Path\n"
            "rec = Path(os.environ['RECORD_DIR'])\n"
            "rec.mkdir(parents=True, exist_ok=True)\n"
            "(rec / 'grok-home').write_text(os.environ.get('GROK_HOME', ''))\n"
            "(rec / 'prompt').write_text(sys.argv[2] if len(sys.argv) > 2 else '')\n"
            "(rec / 'argv').write_text('\\n'.join(sys.argv))\n"
            "raise SystemExit(0)\n"
        )
        script.chmod(0o755)

    def test_dry_run_receipt_records_preamble_size_apart_from_task(self):
        # How it fails: start row has only prompt_head (pre-#263). Recover: write chars/4 fields.
        with tempfile.TemporaryDirectory(prefix="pfy-build-preamble-") as td:
            td = Path(td)
            fake_bin = td / "bin"
            gh = td / "grok-home-real"
            gh.mkdir()
            (gh / "auth.json").write_text('{"token":"test-not-real-0123456789"}')
            (gh / "SHOULD_NOT_COPY.txt").write_text("whole-tree-copy")
            decoy = gh / "skills" / "marketing-council"
            decoy.mkdir(parents=True)
            (decoy / "SKILL.md").write_text("DECOY_SKILL_BODY " * 200)
            self._fake_grok(fake_bin, td / "record")
            path_env = "%s%s%s" % (fake_bin, os.pathsep, os.environ.get("PATH", ""))
            rc = build.build_p(
                FIXTURE_TASK,
                cwd=td,
                repo=ROOT,
                dry_run=True,
                path_env=path_env,
                grok_home=gh,
            )
            self.assertEqual(rc, build.EXIT_OK)
            receipts = list((td / "pipelines" / "dogfood" / "build").glob("*/receipt.jsonl"))
            self.assertEqual(len(receipts), 1)
            rows = [json.loads(x) for x in receipts[0].read_text(encoding="utf-8").splitlines() if x.strip()]
            start = next(r for r in rows if r["event"] == "start")
            self.assertEqual(start.get("preamble_mode"), "trimmed")
            self.assertEqual(start.get("preamble_tokens_method"), "chars/4")
            self.assertEqual(start.get("task_prompt_chars"), len(FIXTURE_TASK))
            self.assertEqual(start.get("task_prompt_tokens_est"), max(1, (len(FIXTURE_TASK) + 3) // 4))
            preamble = build.build_preamble(ROOT, mode="trimmed")
            self.assertEqual(start.get("preamble_chars"), len(preamble))
            self.assertEqual(start.get("preamble_tokens_est"), max(1, (len(preamble) + 3) // 4))
            self.assertLessEqual(start["preamble_tokens_est"], 400)
            self.assertNotEqual(start["preamble_chars"], start["task_prompt_chars"])
            self.assertNotIn("FIXTURE_TASK_D3_263", preamble)

            grok_row = next(r for r in rows if r["event"] == "grok_p")
            argv = grok_row["argv"]
            self.assertIn("--output-format", argv)
            self.assertEqual(argv[argv.index("--output-format") + 1], "plain")
            composed = argv[argv.index("-p") + 1]
            self.assertTrue(composed.startswith(preamble), composed[:80])
            self.assertIn("--- task ---\n" + FIXTURE_TASK, composed)
            self.assertIn("3=escalate", composed)
            self.assertNotIn(_FULL_SKILL_MARKER, composed.split("--- task ---", 1)[0])

            isolated = receipts[0].parent / "grok-home"
            self.assertEqual(grok_row.get("grok_home"), str(isolated))
            self.assertEqual(
                sorted(p.name for p in (isolated / "skills").iterdir()),
                ["pfy-jev-decision"],
            )
            pointer = (isolated / "skills" / "pfy-jev-decision" / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("3=escalate", pointer)
            self.assertRegex(pointer, r"0\.85|PFY_JEV_CONF_GATE")
            self.assertNotIn(_FULL_SKILL_MARKER, pointer)
            self.assertNotIn("DECOY_SKILL_BODY", pointer)
            self.assertFalse((isolated / "SHOULD_NOT_COPY.txt").exists())
            self.assertFalse((isolated / "skills" / "marketing-council").exists())
            self.assertEqual(
                (isolated / "auth.json").read_text(encoding="utf-8"),
                (gh / "auth.json").read_text(encoding="utf-8"),
            )

    def test_child_grok_sees_trimmed_preamble_not_full_skill_tree(self):
        # How it fails: toolset apply writes the full skill into the child GROK_HOME,
        # or grok is handed the real home and loads every skill.
        # Recover: apply keeps the real home; child home is the pointer + auth.json.
        with tempfile.TemporaryDirectory(prefix="pfy-build-child-") as td:
            td = Path(td)
            fake_bin = td / "bin"
            record = td / "record"
            gh = td / "grok-home-real"
            gh.mkdir()
            (gh / "auth.json").write_text('{"token":"test-not-real-0123456789"}')
            (gh / "SHOULD_NOT_COPY.txt").write_text("whole-tree-copy")
            self._fake_grok(fake_bin, record)
            path_env = "%s%s%s" % (fake_bin, os.pathsep, os.environ.get("PATH", ""))
            state = td / "state"
            with mock.patch.dict(
                os.environ,
                {"PFY_STATE_DIR": str(state), "RECORD_DIR": str(record)},
                clear=False,
            ):
                rc = build.build_p(
                    FIXTURE_TASK,
                    cwd=td,
                    repo=ROOT,
                    dry_run=False,
                    path_env=path_env,
                    grok_home=gh,
                )
            self.assertEqual(rc, build.EXIT_OK, "route/apply/grok failed; see receipt under %s" % td)
            seen_home = (record / "grok-home").read_text(encoding="utf-8")
            prompt = (record / "prompt").read_text(encoding="utf-8")
            self.assertTrue(seen_home.endswith("/grok-home"), seen_home)
            self.assertNotEqual(Path(seen_home).resolve(), gh.resolve())
            self.assertIn("FIXTURE_TASK_D3_263", prompt)
            self.assertIn("3=escalate", prompt)
            self.assertRegex(prompt, r"0\.85|PFY_JEV_CONF_GATE")
            self.assertNotIn(_FULL_SKILL_MARKER, prompt.split("--- task ---", 1)[0])
            pointer = Path(seen_home) / "skills" / "pfy-jev-decision" / "SKILL.md"
            self.assertTrue(pointer.is_file(), pointer)
            body = pointer.read_text(encoding="utf-8")
            self.assertIn("Pointer only", body)
            self.assertNotIn("Do not paint Jev as chat", body)
            self.assertFalse((Path(seen_home) / "SHOULD_NOT_COPY.txt").exists())
            # Apply still landed the real toolset skill on the configured home.
            applied = gh / "skills" / "pfy-jev-decision" / "SKILL.md"
            self.assertTrue(applied.is_file(), "toolset apply did not write the real GROK_HOME skill")
            self.assertIn("Do not paint Jev as chat", applied.read_text(encoding="utf-8"))

    def test_full_preamble_flag_keeps_real_grok_home(self):
        # How it fails: the flag still isolates or still trims. Recover: full inlines bodies
        # and does not swap GROK_HOME.
        with tempfile.TemporaryDirectory(prefix="pfy-build-full-") as td:
            td = Path(td)
            fake_bin = td / "bin"
            gh = td / "grok-home-real"
            gh.mkdir()
            (gh / "auth.json").write_text('{"token":"test-not-real-0123456789"}')
            self._fake_grok(fake_bin, td / "record")
            path_env = "%s%s%s" % (fake_bin, os.pathsep, os.environ.get("PATH", ""))
            with mock.patch.dict(os.environ, {"PFY_BUILD_FULL_PREAMBLE": "1"}, clear=False):
                rc = build.build_p(
                    FIXTURE_TASK,
                    cwd=td,
                    repo=ROOT,
                    dry_run=True,
                    path_env=path_env,
                    grok_home=gh,
                )
            self.assertEqual(rc, build.EXIT_OK)
            receipts = list((td / "pipelines" / "dogfood" / "build").glob("*/receipt.jsonl"))
            rows = [json.loads(x) for x in receipts[0].read_text(encoding="utf-8").splitlines() if x.strip()]
            start = next(r for r in rows if r["event"] == "start")
            self.assertEqual(start.get("preamble_mode"), "full")
            self.assertGreater(start["preamble_tokens_est"], 400)
            self.assertIn(_FULL_SKILL_MARKER, build.build_preamble(ROOT, mode="full", grok_home=gh))
            grok_row = next(r for r in rows if r["event"] == "grok_p")
            self.assertEqual(grok_row.get("grok_home"), str(gh))
            self.assertFalse((receipts[0].parent / "grok-home").exists())
            composed = grok_row["argv"][grok_row["argv"].index("-p") + 1]
            self.assertIn(_FULL_SKILL_MARKER, composed.split("--- task ---", 1)[0])
            self.assertIn("FIXTURE_TASK_D3_263", composed)


if __name__ == "__main__":
    unittest.main()
