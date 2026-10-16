"""Behaviour tests for examples/agentdescent-trial/harness.py (PR #297 Tester B1/B2). No model, no network."""
import importlib.util, json, os, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "examples/agentdescent-trial/harness.py"
TRACKED = ["examples/agentdescent-trial"]


def load(out: str, home: str):
    with mock.patch.dict(os.environ, {"TRIAL_OUT": out, "TRIAL_REAL_HOME": home}):
        spec = importlib.util.spec_from_file_location("ad_trial_harness", HARNESS)
        h = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(h)
    h.wait_ollama = lambda log: []
    h.meminfo = lambda: {"MemTotal": 100, "MemAvailable": 90}
    h.print = lambda *a, **k: None
    return h


def git_status():
    return subprocess.run(["git", "status", "--porcelain", "--", *TRACKED], cwd=ROOT,
                          capture_output=True, text=True).stdout


class Base(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory(); self.addCleanup(self.td.cleanup)
        self.out = Path(self.td.name, "run"); self.home = Path(self.td.name, "home"); self.home.mkdir()
        self.h = load(str(self.out), str(self.home))

    def only(self, fn, name="baseline"):
        self.h.STAGES.clear(); self.h.STAGES[name] = fn

    def stage_rec(self, name="baseline"):
        return json.loads((self.out / f"stage_{name}.json").read_text())


class RealHomeGuard(Base):
    def test_new_dir_in_real_home_exits_nonzero(self):
        def stage():
            (self.home / ".agentdescent/runs").mkdir(parents=True); return {"ok": 1}
        self.only(stage)
        self.assertEqual(self.h.main(["--stage", "baseline"]), 3)
        self.assertFalse(self.stage_rec()["guard"]["real_home_untouched"])

    def test_content_change_same_name_exits_nonzero(self):
        f = self.home / ".cache/dspy/cache.db"; f.parent.mkdir(parents=True); f.write_text("a")
        st = os.stat(f)
        def stage():
            f.write_text("b"); os.utime(f, ns=(st.st_atime_ns, st.st_mtime_ns)); return {}
        self.only(stage)
        self.assertEqual(self.h.main(["--stage", "baseline"]), 3)

    def test_each_watched_dir_is_checked(self):
        for d in (".agentdescent", ".cache/agentdescent", ".dspy_cache", ".cache/dspy", ".ollama"):
            with self.subTest(d=d):
                self.setUp()
                self.only(lambda d=d: (self.home / d).mkdir(parents=True) or {})
                self.assertEqual(self.h.main(["--stage", "baseline"]), 3)

    def test_change_then_timeout_still_checked_and_nonzero(self):
        def stage():
            (self.home / ".ollama").mkdir(); (self.home / ".ollama/x").write_text("1")
            raise subprocess.TimeoutExpired(["child"], 1)
        self.only(stage)
        self.assertEqual(self.h.main(["--stage", "baseline"]), 3)
        rec = self.stage_rec()
        self.assertIn("TimeoutExpired", rec["error"])
        self.assertIn(".ollama", rec["guard"]["changed"])

    def test_untouched_home_ok(self):
        (self.home / ".ollama/models").mkdir(parents=True)
        self.only(lambda: {"accuracy": 1.0})
        self.assertEqual(self.h.main(["--stage", "baseline"]), 0)


class StageFailure(Base):
    def test_stage_error_exits_nonzero(self):
        def stage():
            raise RuntimeError("child rc=1")
        self.only(stage)
        self.assertEqual(self.h.main(["--stage", "baseline"]), 1)
        self.assertIn("baseline", json.loads((self.out / "results.json").read_text())["errors"])

    def test_stage_timeout_exits_nonzero(self):
        def stage():
            raise subprocess.TimeoutExpired(["child"], 1)
        self.only(stage)
        self.assertEqual(self.h.main(["--stage", "baseline"]), 1)

    def test_promote_refuses_failed_run(self):
        self.only(lambda: (_ for _ in ()).throw(RuntimeError("x")))
        self.h.main(["--stage", "baseline"])
        self.assertEqual(self.h.main(["--promote"]), 1)


class RerunIsolation(Base):
    def test_rerun_writes_only_to_tmp_and_does_not_merge(self):
        before = git_status()
        self.out.mkdir(parents=True)
        (self.out / "results.json").write_text(json.dumps({"stages": {"stale": 1}, "errors": {"evolve": "old"}}))

        def fake_iso(cmd, timeout):
            out = Path(cmd[-1])
            out.write_text(json.dumps({"n": 1, "correct": 1, "accuracy": 1.0, "per_case": []}))
            return subprocess.CompletedProcess(cmd, 0, "", ""), 0.1, []
        self.h.iso = fake_iso
        self.h.STAGES = {"baseline": self.h.STAGES["baseline"]}
        self.assertEqual(self.h.main(["--stage", "baseline"]), 0)
        self.assertTrue((self.out / "score_baseline.json").exists())
        R = json.loads((self.out / "results.json").read_text())
        self.assertNotIn("stale", R["stages"]); self.assertEqual(R["errors"], {})
        self.assertEqual(git_status(), before)
        self.assertTrue(str(self.h.RES).startswith(self.td.name))

    def test_default_out_is_gitignored_tmp(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TRIAL_OUT", None)
            spec = importlib.util.spec_from_file_location("h2", HARNESS)
            h = importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
        rel = h.RES.relative_to(ROOT)
        self.assertEqual(rel.parts[0], "tmp")
        r = subprocess.run(["git", "check-ignore", "-q", str(rel / "results.json")], cwd=ROOT)
        self.assertEqual(r.returncode, 0)


class PromoteGuards(Base):
    """B1'/B2' at 07bca20: promote must honour guards and refuse stale/mixed records."""

    def setUp(self):
        super().setUp()
        import shutil
        self.inp = Path(self.td.name, "inputs"); (self.inp / "skill").mkdir(parents=True)
        for n in self.h.INPUTS:
            shutil.copy2(HARNESS.parent / n, self.inp / n)
        self.tracked = self.inp / "results"; self.tracked.mkdir()
        self.h.HERE = self.inp; self.h.TRACKED_RES = self.tracked

    def writer(self, name, files, fail=False, touch_home=False):
        def stage():
            for f in files:
                (self.h.RES / f).write_text(f"{name} output")
            if touch_home:
                (self.home / ".agentdescent").mkdir(exist_ok=True)
            if fail:
                raise RuntimeError(f"{name} failed")
            return {"accuracy": 1.0, "stage": name}
        return stage

    def stages(self, **fns):
        self.h.STAGES.clear(); self.h.STAGES.update(fns)

    def test_promote_refuses_when_guard_failed_on_successful_stage(self):
        self.stages(baseline=self.writer("baseline", ["score_baseline.json"], touch_home=True))
        self.assertEqual(self.h.main(["--stage", "baseline"]), 3)
        rec = self.stage_rec()
        self.assertNotIn("error", rec)
        self.assertFalse(rec["guard"]["real_home_untouched"])
        self.assertNotEqual(self.h.main(["--promote"]), 0)
        self.assertFalse((self.tracked / "score_baseline.json").exists())
        self.assertFalse((self.tracked / "results.json").exists())

    def _repro(self):
        self.stages(baseline=self.writer("baseline", ["score_baseline.json"]),
                    evolve=self.writer("evolve", ["score_agentdescent.json", "SKILL.evolved.md"]),
                    dspy=self.writer("dspy", ["dspy.log"], fail=True))
        self.assertEqual(self.h.main(["--stage", "all"]), 1)
        (self.inp / "skill/SKILL.md").write_text((self.inp / "skill/SKILL.md").read_text() + "\nedited\n")
        self.assertEqual(self.h.main(["--stage", "baseline"]), 0)

    def test_repro_results_not_mixed_with_stale_records(self):
        self._repro()
        R = json.loads((self.h.RES / "results.json").read_text())
        self.assertEqual(sorted(R["stages"]), ["baseline"])
        self.assertEqual(R["errors"], {})
        self.assertEqual(sorted(R["refused_stale"]), ["dspy", "evolve"])

    def test_repro_promote_skips_failed_runs_logs(self):
        self._repro()
        self.assertEqual(self.h.main(["--promote"]), 0)
        self.assertTrue((self.tracked / "score_baseline.json").exists())
        self.assertFalse((self.tracked / "dspy.log").exists())
        self.assertFalse((self.tracked / "score_agentdescent.json").exists())
        self.assertFalse((self.inp / "skill/SKILL.evolved.md").exists())

    def test_stage_all_clears_run_dir(self):
        self.h.RES.mkdir(parents=True, exist_ok=True)
        (self.h.RES / "dspy.log").write_text("old")
        self.stages(baseline=self.writer("baseline", ["score_baseline.json"]))
        self.assertEqual(self.h.main(["--stage", "all"]), 0)
        self.assertFalse((self.h.RES / "dspy.log").exists())

    def test_promote_refuses_after_inputs_change(self):
        self.stages(baseline=self.writer("baseline", ["score_baseline.json"]))
        self.assertEqual(self.h.main(["--stage", "all"]), 0)
        (self.inp / "heldout.jsonl").write_text("{}\n")
        self.assertNotEqual(self.h.main(["--promote"]), 0)
        self.assertFalse((self.tracked / "score_baseline.json").exists())


if __name__ == "__main__":
    unittest.main()
