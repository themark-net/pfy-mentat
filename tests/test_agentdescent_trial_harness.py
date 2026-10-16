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
    h.msgs = []
    h.print = lambda *a, **k: h.msgs.append(" ".join(map(str, a)))
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
    """Promote/run-mixing gates (Tester B1'/B2' @07bca20, B1''/B2'' @ac1c803). Tracked results/ starts NON-empty."""

    def setUp(self):
        super().setUp()
        import shutil
        self.inp = Path(self.td.name, "inputs"); (self.inp / "skill").mkdir(parents=True)
        for n in self.h.INPUTS:
            shutil.copy2(HARNESS.parent / n, self.inp / n)
        self.tracked = self.inp / "results"; self.tracked.mkdir()
        for n, body in (("results.json", "{\"old\": 1}"), ("agentdescent_result.json", "OLD AD"),
                        ("agentdescent_rounds.jsonl", "OLD ROUNDS"), ("dspy.log", "OLD DSPY"), ("old_marker.txt", "OLD")):
            (self.tracked / n).write_text(body)
        (self.inp / "skill/SKILL.evolved.md").write_text("OLD EVOLVED")
        self.h.HERE = self.inp; self.h.TRACKED_RES = self.tracked

    def tracked_state(self):
        files = {str(f.relative_to(self.inp)): f.read_bytes() for f in self.inp.rglob("*")
                 if f.is_file() and ("results" in f.parts or f.name == "SKILL.evolved.md")}
        return files

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

    def full(self, **over):
        fns = dict(baseline=self.writer("baseline", ["score_baseline.json"]),
                   evolve=self.writer("evolve", ["score_agentdescent.json", "agentdescent_result.json",
                                                 "agentdescent_rounds.jsonl", "SKILL.evolved.md"]),
                   dspy=self.writer("dspy", ["dspy.log", "dspy_program.json"]))
        fns.update(over)
        self.h.STAGES.clear(); self.h.STAGES.update(fns)

    def refused(self, why):
        before = self.tracked_state()
        self.h.msgs.clear()
        self.assertNotEqual(self.h.main(["--promote"]), 0)
        self.assertEqual(self.tracked_state(), before)
        self.assertTrue(any(why in m for m in self.h.msgs), (why, self.h.msgs))

    def tamper(self, st, fn):
        f = self.h.RES / f"stage_{st}.json"; d = json.loads(f.read_text()); fn(d); f.write_text(json.dumps(d))

    # --- complete run promotes and replaces the whole tracked set
    def test_complete_run_replaces_tracked_set(self):
        self.full(); self.assertEqual(self.h.main(["--stage", "all"]), 0)
        self.assertEqual(self.h.main(["--promote"]), 0)
        self.assertFalse((self.tracked / "old_marker.txt").exists())
        self.assertEqual((self.tracked / "dspy.log").read_text(), "dspy output")
        self.assertEqual((self.inp / "skill/SKILL.evolved.md").read_text(), "evolve output")
        self.assertEqual(sorted(p.name for p in self.inp.iterdir() if p.name.startswith(".results")), [])

    # --- B1'': evolve rerun with no AgentDescent output leaves no old files behind
    def test_b1pp_evolve_rerun_without_output_leaves_no_old_files(self):
        self.full(); self.assertEqual(self.h.main(["--stage", "all"]), 0)
        self.full(evolve=self.writer("evolve", ["score_agentdescent.json"]))
        self.assertEqual(self.h.main(["--stage", "evolve"]), 0)
        self.assertFalse((self.h.RES / "agentdescent_result.json").exists())
        self.assertFalse((self.h.RES / "SKILL.evolved.md").exists())
        self.assertEqual(self.h.main(["--promote"]), 0)
        for n in ("agentdescent_result.json", "agentdescent_rounds.jsonl", "old_marker.txt"):
            self.assertFalse((self.tracked / n).exists(), n)
        self.assertFalse((self.inp / "skill/SKILL.evolved.md").exists())

    def test_agentdescent_run_dir_is_the_one_created_not_newest_by_name(self):
        store = Path(self.td.name, "store"); (store / "99999999-old").mkdir(parents=True)
        self.h.STORE = store
        existing = set(store.glob("*"))
        with self.assertRaises(RuntimeError):
            self.h.created_run_dir(existing)
        (store / "00000000-new").mkdir()
        self.assertEqual(self.h.created_run_dir(existing).name, "00000000-new")

    def test_evolve_reads_the_run_dir_it_created(self):
        store = Path(self.td.name, "store"); old = store / "99999999-old"; old.mkdir(parents=True)
        (old / "result.json").write_text("OLD RESULT"); (old / "rounds.jsonl").write_text("OLD ROUNDS")
        self.h.STORE = store; self.h.TMPD = Path(self.td.name, "wt-tmp"); self.h.TMPD.mkdir()
        self.h.RES.mkdir(parents=True, exist_ok=True)

        def fake_iso(cmd, timeout):
            if "evolve" in cmd:
                new = store / "00000000-new"; new.mkdir()
                (new / "result.json").write_text("NEW RESULT"); (new / "rounds.jsonl").write_text("NEW ROUNDS")
            out = json.dumps({"rendered": "evolved", "final_reward": 1.0}) if "show" in cmd else "{}"
            return subprocess.CompletedProcess(cmd, 0, out, ""), 0.1, []
        self.h.iso = fake_iso
        r = self.h.evolve(lambda m: None)
        self.assertEqual(r["run_id"], "00000000-new")
        self.assertEqual((self.h.RES / "agentdescent_result.json").read_text(), "NEW RESULT")

    # --- B2'': incomplete runs are refused, tracked untouched
    def test_b2pp_baseline_only_promote_refused(self):
        self.full(); self.h.STAGES.pop("evolve"); self.h.STAGES.pop("dspy")
        self.assertEqual(self.h.main(["--stage", "all"]), 0)
        self.refused("incomplete run")

    def test_b2pp_after_input_edit_baseline_rerun_refused(self):
        self.full(dspy=self.writer("dspy", ["dspy.log"], fail=True))
        self.assertEqual(self.h.main(["--stage", "all"]), 1)
        (self.inp / "skill/SKILL.md").write_text((self.inp / "skill/SKILL.md").read_text() + "\nedited\n")
        self.assertEqual(self.h.main(["--stage", "baseline"]), 0)
        self.assertFalse((self.h.RES / "dspy.log").exists())          # new run id cleared the dir
        self.assertFalse((self.h.RES / "stage_evolve.json").exists())
        R = json.loads((self.h.RES / "results.json").read_text())
        self.assertEqual(sorted(R["stages"]), ["baseline"])
        self.refused("incomplete run")

    # --- each overlapping check on its own
    def test_failed_stage_refused(self):
        self.full(dspy=self.writer("dspy", ["dspy.log"], fail=True))
        self.assertEqual(self.h.main(["--stage", "all"]), 1)
        self.refused("failed stages")

    def test_guard_false_refused(self):
        self.full(evolve=self.writer("evolve", ["score_agentdescent.json"], touch_home=True))
        self.assertEqual(self.h.main(["--stage", "all"]), 3)
        self.refused("real-HOME guard")

    def test_missing_guard_field_refused(self):
        self.full(); self.assertEqual(self.h.main(["--stage", "all"]), 0)
        self.tamper("dspy", lambda d: d.pop("guard"))
        self.refused("real-HOME guard")

    def test_guard_field_without_flag_refused(self):
        self.full(); self.assertEqual(self.h.main(["--stage", "all"]), 0)
        self.tamper("dspy", lambda d: d["guard"].pop("real_home_untouched"))
        self.refused("real-HOME guard")

    def test_record_run_id_mismatch_refused(self):
        self.full(); self.assertEqual(self.h.main(["--stage", "all"]), 0)
        self.tamper("evolve", lambda d: d.update(run_id="other"))
        self.refused("incomplete run")

    def test_record_input_hash_mismatch_refused(self):
        self.full(); self.assertEqual(self.h.main(["--stage", "all"]), 0)
        self.tamper("baseline", lambda d: d["inputs"].update({"heldout.jsonl": "0" * 64}))
        self.refused("incomplete run")

    def test_input_change_after_run_refused(self):
        self.full(); self.assertEqual(self.h.main(["--stage", "all"]), 0)
        (self.inp / "heldout.jsonl").write_text("{}\n")
        self.refused("no current run")

    def test_harness_or_child_change_after_run_refused(self):
        for n in ("harness.py", "child.py"):
            with self.subTest(n=n):
                self.setUp()
                self.full(); self.assertEqual(self.h.main(["--stage", "all"]), 0)
                (self.inp / n).write_text((self.inp / n).read_text() + "\n# changed\n")
                self.refused("no current run")

    def test_missing_run_json_refused(self):
        self.full(); self.assertEqual(self.h.main(["--stage", "all"]), 0)
        (self.h.RES / "run.json").unlink()
        self.refused("no current run")

    def test_stage_record_missing_result_refused(self):
        self.full(); self.assertEqual(self.h.main(["--stage", "all"]), 0)
        self.tamper("baseline", lambda d: d.pop("result"))
        self.refused("failed stages")

    def test_stage_deletes_own_outputs_when_starting(self):
        self.full(); self.assertEqual(self.h.main(["--stage", "all"]), 0)
        self.full(dspy=self.writer("dspy", []))
        self.assertEqual(self.h.main(["--stage", "dspy"]), 0)
        self.assertFalse((self.h.RES / "dspy.log").exists())
        self.assertTrue((self.h.RES / "score_baseline.json").exists())

    def test_new_run_id_without_run_json_clears_dir(self):
        self.h.RES.mkdir(parents=True); (self.h.RES / "stage_evolve.json").write_text("{}")
        (self.h.RES / "agentdescent_rounds.jsonl").write_text("stale")
        self.full(); self.assertEqual(self.h.main(["--stage", "baseline"]), 0)
        self.assertFalse((self.h.RES / "stage_evolve.json").exists())
        self.assertFalse((self.h.RES / "agentdescent_rounds.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
