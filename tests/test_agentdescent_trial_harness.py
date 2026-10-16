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


class PromoteBase(Base):
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

    def complete(self):
        self.full(); self.assertEqual(self.h.main(["--stage", "all"]), 0)

    def leftovers(self):
        return sorted(p.name for d in (self.inp, self.inp / "skill") for p in d.iterdir()
                      if p.name.startswith((".results.", ".SKILL.evolved.md.", ".promote-journal")))

    def crash_at(self, point):
        def f(p):
            if p == point:
                raise self.h.Crash(p)
        self.h._fault = f
        with self.assertRaises(self.h.Crash):
            self.h.main(["--promote"])
        self.h._fault = lambda p: None

    def incomplete_promote_recovers(self, expect, old_contents=None):
        (self.h.RES / "stage_dspy.json").unlink()              # the run is now incomplete
        self.h.msgs.clear()
        rc = self.h.main(["--promote"])
        self.assertEqual(rc, 1)
        self.assertTrue(any("incomplete run" in m for m in self.h.msgs), self.h.msgs)   # recovered, then refused
        self.assertFalse(any("Traceback" in m for m in self.h.msgs))
        self.assertEqual(self.leftovers(), [])
        if expect == "before_old_contents":
            self.assertEqual({p.name for p in self.tracked.iterdir()}, old_contents)
        else:
            self.assertEqual(self.tracked_state(), expect)


class PromoteGuards(PromoteBase):
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


class TransactionalPromote(PromoteBase):
    """B5/B6 @ d915467 and the two surviving mutants."""

    def complete(self):
        self.full(); self.assertEqual(self.h.main(["--stage", "all"]), 0)

    def leftovers(self):
        return sorted(p.name for d in (self.inp, self.inp / "skill") for p in d.iterdir()
                      if p.name.startswith((".results.", ".SKILL.evolved.md.", ".promote-journal")))

    # --- B5: stale DSPy outputs
    def test_b5_dspy_child_writing_nothing_fails_and_promote_refuses(self):
        def child_ok(cmd, timeout):
            out = Path(cmd[-1]); (out / "dspy_result.json").write_text(json.dumps({"accuracy": 1.0}))
            (out / "dspy_program.json").write_text("{}")
            return subprocess.CompletedProcess(cmd, 0, "", ""), 0.1, []
        self.full(dspy=self.h.dspy_stage); self.h.iso = child_ok
        self.assertEqual(self.h.main(["--stage", "all"]), 0)
        (self.inp / "skill/SKILL.md").write_text((self.inp / "skill/SKILL.md").read_text() + "\nedited\n")
        self.h.iso = lambda cmd, timeout: (subprocess.CompletedProcess(cmd, 0, "", ""), 0.1, [])
        self.full(dspy=self.h.dspy_stage)
        self.assertEqual(self.h.main(["--stage", "all"]), 1)
        self.assertIn("wrote no", self.stage_rec("dspy")["error"])
        self.refused("failed stages")

    def test_b5_dspy_stale_out_cleared_even_without_new_run(self):
        self.h.RES.mkdir(parents=True); out = self.h.RES / "dspy-out"; out.mkdir()
        (out / "dspy_result.json").write_text("{}"); (out / "dspy_program.json").write_text("{}")
        self.h.iso = lambda cmd, timeout: (subprocess.CompletedProcess(cmd, 0, "", ""), 0.1, [])
        with self.assertRaises(RuntimeError):
            self.h.dspy_stage()

    def test_b5_dspy_out_is_inside_run_dir(self):
        seen = []
        def child(cmd, timeout):
            seen.append(Path(cmd[-1])); return subprocess.CompletedProcess(cmd, 0, "", ""), 0.1, []
        self.h.RES.mkdir(parents=True); self.h.iso = child
        with self.assertRaises(RuntimeError):
            self.h.dspy_stage()
        self.assertEqual(seen[0].parent, self.h.RES)

    # --- B6: faults at each step roll back
    def fault_at(self, point=None, rename_n=None):
        before = self.tracked_state()
        if point:
            def f(p):
                if p == point:
                    raise OSError(f"injected at {p}")
            self.h._fault = f
        if rename_n:
            real, calls = self.h._rename, []
            def r(a, b):
                calls.append(1)
                if len(calls) == rename_n:
                    raise OSError(f"injected at rename {rename_n}")
                return real(a, b)
            self.h._rename = r
        self.assertEqual(self.h.main(["--promote"]), 1)
        self.assertEqual(self.tracked_state(), before)
        self.assertEqual(self.leftovers(), [])

    def test_b6_fault_at_first_rename(self):
        self.complete(); self.fault_at(rename_n=1)

    def test_b6_fault_at_second_rename(self):
        self.complete(); self.fault_at(rename_n=2)

    def test_b6_fault_between_renames(self):
        self.complete(); self.fault_at("after_old_rename")

    def test_b6_fault_before_skill_replace(self):
        self.complete(); self.fault_at("before_skill_replace")

    def test_b6_fault_before_commit(self):
        self.complete(); self.fault_at("before_commit")

    def test_b6_fault_at_skill_replace(self):
        self.complete()
        def boom(a, b):
            raise OSError("injected at skill replace")
        self.h._replace = boom
        before = self.tracked_state()
        self.assertEqual(self.h.main(["--promote"]), 1)
        self.assertEqual(self.tracked_state(), before)

    def test_b6_rollback_when_no_old_evolved(self):
        (self.inp / "skill/SKILL.evolved.md").unlink()
        self.complete(); self.fault_at("before_commit")
        self.assertFalse((self.inp / "skill/SKILL.evolved.md").exists())

    def test_b6_leftover_temp_files_cleaned_at_start(self):
        self.complete()
        (self.inp / ".results.new-dead").mkdir(); (self.inp / ".results.new-dead/x").write_text("1")
        (self.inp / "skill/.SKILL.evolved.md.new").write_text("half")
        self.assertEqual(self.h.main(["--promote"]), 0)
        self.assertEqual(self.leftovers(), [])
        self.assertEqual((self.inp / "skill/SKILL.evolved.md").read_text(), "evolve output")

    def test_b6_crash_mid_swap_recovered_from_journal(self):
        self.complete()
        before = self.tracked_state()
        old = self.inp / ".results.old-dead"
        self.tracked.rename(old)                         # simulated crash right after the first rename
        (self.inp / ".promote-journal.json").write_text(json.dumps(
            {"state": "swapping", "old": str(old), "new": str(self.inp / ".results.new-dead"),
             "skill_backup": None, "skill_touched": False}))
        self.assertEqual(self.h.recover(), None)
        self.assertEqual(self.tracked_state(), before)
        self.assertEqual(self.leftovers(), [])

    def test_b6_crash_after_commit_finishes_cleanup(self):
        self.complete(); self.assertEqual(self.h.main(["--promote"]), 0)
        after = self.tracked_state()
        old = self.inp / ".results.old-dead"; old.mkdir()
        (self.inp / ".promote-journal.json").write_text(json.dumps({"state": "committed", "tag": "dead"}))
        self.assertEqual(self.h.recover(), None)
        self.assertEqual(self.tracked_state(), after); self.assertEqual(self.leftovers(), [])

    def test_b6_old_set_without_journal_restored_only_when_results_missing(self):
        self.complete()
        names = {p.name for p in self.tracked.iterdir()}
        self.tracked.rename(self.inp / ".results.old-orphan")
        self.incomplete_promote_recovers(expect="before_old_contents", old_contents=names)
        self.assertTrue(any(m.startswith("recovery: rolled back") for m in self.h.msgs), self.h.msgs)

    def test_diff_generated_on_promote(self):
        self.complete(); self.assertEqual(self.h.main(["--promote"]), 0)
        d = (self.tracked / "agentdescent_vs_baseline.diff").read_text()
        self.assertIn("+evolve output", d)

    # --- surviving mutants
    def test_two_new_agentdescent_dirs_rejected(self):
        store = Path(self.td.name, "store"); store.mkdir(); self.h.STORE = store
        existing = set(store.glob("*")); (store / "a").mkdir(); (store / "b").mkdir()
        with self.assertRaises(RuntimeError):
            self.h.created_run_dir(existing)

    def test_truthy_non_true_guard_refused(self):
        for v in (1, "yes", [1]):
            with self.subTest(v=v):
                self.setUp(); self.complete()
                self.tamper("evolve", lambda d: d["guard"].update(real_home_untouched=v))
                self.refused("real-HOME guard")


class CrashRecovery(PromoteBase):
    """B7 @ b826c43: kill at each phase, then a garbled/empty/torn journal, then a promote from an INCOMPLETE run."""

    PRE_COMMIT = ["staged", "after_old_rename", "before_skill_replace", "before_commit"]
    POST_COMMIT = ["committed", "bak_moved", "trashed"]

    def run_case(self, point, journal):
        self.complete()
        before = self.tracked_state()
        self.crash_at(point)
        j = self.inp / ".promote-journal.json"
        if journal == "empty":
            j.write_text("")
        elif journal == "garbled":
            j.write_bytes(b"\x00{\"state\": \"comm")
        elif journal == "torn":                                 # a half-written 2nd (committed) write
            j.write_text('{"state": "committed", "ta')
        elif journal == "missing":
            j.unlink(missing_ok=True)
        self.assertTrue(self.leftovers() or point == "trashed")
        return before

    REFUSE_AFTER = ["before_skill_replace", "before_commit", "committed", "bak_moved"]  # results/ present + old set

    def refuses_stale(self):
        state, left = self.tracked_state(), self.leftovers()
        self.h.msgs.clear()
        self.assertEqual(self.h.main(["--promote"]), 1)
        self.assertTrue(any("stale .results.old-" in m for m in self.h.msgs), self.h.msgs)
        self.assertEqual(self.tracked_state(), state); self.assertEqual(self.leftovers(), left)

    def check(self, point, journal):
        before = self.run_case(point, journal)
        if journal != "ok" and point in self.REFUSE_AFTER:
            self.refuses_stale()     # unreadable journal + valid-looking results/: never replace results/
        elif point in self.POST_COMMIT and journal == "ok":
            # roll forward: the promoted set stays
            (self.h.RES / "stage_dspy.json").unlink()
            self.assertEqual(self.h.main(["--promote"]), 1)
            self.assertEqual((self.tracked / "dspy.log").read_text(), "dspy output")
            self.assertEqual((self.inp / "skill/SKILL.evolved.md").read_text(), "evolve output")
            self.assertEqual(self.leftovers(), [])
        elif point == "trashed":
            # old set already retired: whatever the journal says, the new set is consistent and stays
            (self.h.RES / "stage_dspy.json").unlink()
            self.assertEqual(self.h.main(["--promote"]), 1)
            self.assertEqual((self.tracked / "dspy.log").read_text(), "dspy output")
            self.assertEqual((self.inp / "skill/SKILL.evolved.md").read_text(), "evolve output")
            self.assertEqual(self.leftovers(), [])
        else:
            self.incomplete_promote_recovers(before)

    def test_every_phase_with_every_journal_state(self):
        for point in self.PRE_COMMIT + self.POST_COMMIT:
            for journal in ("ok", "empty", "garbled", "missing"):
                with self.subTest(point=point, journal=journal):
                    self.setUp(); self.check(point, journal)

    def test_torn_second_write(self):
        for point in ("before_commit", "committed"):
            with self.subTest(point=point):
                self.setUp(); self.run_case(point, "torn")
                self.refuses_stale()

    def test_kill_after_rename_1_then_incomplete_promote(self):
        before = self.run_case("after_old_rename", "ok")
        self.assertFalse(self.tracked.exists())
        self.incomplete_promote_recovers(before)

    def test_kill_after_rename_2_then_incomplete_promote(self):
        before = self.run_case("before_skill_replace", "ok")
        self.assertEqual((self.tracked / "dspy.log").read_text(), "dspy output")
        self.incomplete_promote_recovers(before)

    def test_no_evolved_before_kill_after_skill_replace(self):
        (self.inp / "skill/SKILL.evolved.md").unlink()
        before = self.run_case("before_commit", "ok")
        self.incomplete_promote_recovers(before)
        self.assertFalse((self.inp / "skill/SKILL.evolved.md").exists())

    def test_journal_write_is_temp_fsync_rename(self):
        calls = []
        real_fsync, real_replace = os.fsync, os.replace
        with mock.patch.object(self.h.os, "fsync", side_effect=lambda fd: (calls.append("fsync"), real_fsync(fd))), \
             mock.patch.object(self.h.os, "replace", side_effect=lambda a, b: (calls.append(("replace", Path(a).name)), real_replace(a, b))):
            self.h.write_journal("swapping", "t")
        self.assertEqual(calls[0], "fsync")
        self.assertEqual(calls[1], ("replace", ".promote-journal.json.tmp"))
        self.assertEqual(calls[2], "fsync")          # the directory
        self.assertEqual(json.loads((self.inp / ".promote-journal.json").read_text())["state"], "swapping")

    def test_unreadable_state_gives_message_not_traceback(self):
        self.complete()
        (self.inp / ".results.old-a").mkdir(); (self.inp / ".results.old-b").mkdir()
        self.h.msgs.clear()
        self.assertEqual(self.h.main(["--promote"]), 1)
        self.assertTrue(any("ambiguous promote leftovers" in m for m in self.h.msgs))


class StaleOldSet(PromoteBase):
    """B8 @ c4904511: a stale .results.old-* with no journal must never replace a valid results/."""

    def stale(self, variant):
        self.complete()
        old = self.inp / ".results.old-stale"; old.mkdir(); (old / "results.json").write_text("STALE")
        if variant == "absent_marker":
            (self.inp / "skill/.SKILL.evolved.md.absent-stale").write_text("")
        elif variant == "stale_bak":
            (self.inp / "skill/.SKILL.evolved.md.bak-stale").write_text("STALE SKILL")
        return {str(p.relative_to(self.inp)): p.read_bytes() for p in self.inp.rglob("*") if p.is_file()}

    def assert_refused_unchanged(self, snap):
        self.h.msgs.clear()
        self.assertEqual(self.h.main(["--promote"]), 1)
        msg = " ".join(self.h.msgs)
        self.assertIn("stale .results.old-stale", msg); self.assertIn("rm -rf", msg)
        self.assertFalse(any(m.startswith("recovery:") for m in self.h.msgs))
        now = {str(p.relative_to(self.inp)): p.read_bytes() for p in self.inp.rglob("*") if p.is_file()}
        self.assertEqual(now, snap)

    def test_b8_repro_complete_and_incomplete_promote(self):
        for variant in ("plain", "absent_marker", "stale_bak"):
            for complete in (True, False):
                with self.subTest(variant=variant, complete=complete):
                    self.setUp(); snap = self.stale(variant)
                    if not complete:
                        (self.h.RES / "stage_dspy.json").unlink()
                        snap = {k: v for k, v in snap.items() if not k.endswith("stage_dspy.json")}
                    self.assertTrue((self.inp / "skill/SKILL.evolved.md").exists())
                    self.assert_refused_unchanged(snap)

    def test_b8_garbled_journal_with_valid_results_refused(self):
        snap = self.stale("plain")
        (self.inp / ".promote-journal.json").write_text("{garbled")
        snap[".promote-journal.json"] = b"{garbled"
        self.assert_refused_unchanged(snap)

    def test_b8_swapping_journal_with_other_tag_refused(self):
        snap = self.stale("plain")
        j = json.dumps({"state": "swapping", "tag": "other"}).encode()
        (self.inp / ".promote-journal.json").write_bytes(j); snap[".promote-journal.json"] = j
        self.assert_refused_unchanged(snap)

    def test_forged_committed_journal_mismatched_tag_refused(self):
        snap = self.stale("plain")
        j = json.dumps({"state": "committed", "tag": "forged"}).encode()
        (self.inp / ".promote-journal.json").write_bytes(j); snap[".promote-journal.json"] = j
        self.h.msgs.clear()
        self.assertEqual(self.h.main(["--promote"]), 1)
        self.assertTrue(any("committed journal for tag 'forged'" in m for m in self.h.msgs), self.h.msgs)
        now = {str(p.relative_to(self.inp)): p.read_bytes() for p in self.inp.rglob("*") if p.is_file()}
        self.assertEqual(now, snap)

    def test_results_missing_message(self):
        self.complete()
        import shutil; shutil.rmtree(self.tracked)
        self.h.msgs.clear()
        self.assertEqual(self.h.main(["--promote"]), 1)
        self.assertTrue(any("results/ is missing and no .results.old-*" in m and "git checkout" in m
                            for m in self.h.msgs), self.h.msgs)

    def test_os_error_message(self):
        self.complete()
        self.tracked.rename(self.inp / ".results.old-x")      # results/ missing -> recovery will rename
        with mock.patch.object(self.h.os, "rename", side_effect=PermissionError("denied")):
            self.h.msgs.clear()
            self.assertEqual(self.h.main(["--promote"]), 1)
        msg = " ".join(self.h.msgs)
        self.assertIn("could not recover promote leftovers (PermissionError", msg)
        self.assertIn("git checkout -- examples/agentdescent-trial/results", msg)
        self.assertNotIn("Traceback", msg)


if __name__ == "__main__":
    unittest.main()
