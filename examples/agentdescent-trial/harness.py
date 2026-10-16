#!/usr/bin/env python3
"""AgentDescent vs DSPy vs baseline on X intake triage (eval-auto trial, Entry 119).

Usage (from the worktree root):
  python3 examples/agentdescent-trial/harness.py [--stage all|baseline|evolve|dspy]   run into tmp/agentdescent-trial-run/
  python3 examples/agentdescent-trial/harness.py --promote                            copy that run into tracked results/

Runs never write tracked files: everything goes to $TRIAL_OUT (default <worktree>/tmp/agentdescent-trial-run, gitignored).
Each stage writes its own <stage>.json, replaced wholesale; results.json is rebuilt from the stage files of the
current run dir only (no merge with older results). `--promote` is the only path into results/ and SKILL.evolved.md.
Exit codes: 0 ok, 1 a stage failed or timed out, 3 a watched real-HOME dir changed (checked in a finally, timeouts too).

Every child goes through examples/x-intake-local/smoke.py run_isolated (new session, killpg on timeout,
stripped env, temp HOME). Venv, AgentDescent run store and scratch live in <worktree>/tmp. The real skill text
is never a target: AgentDescent evolves a copy in tmp/, and `apply` is never called. ~/.agentdescent in the
real HOME is snapshotted before and after. Waits (never kills) while Ollama has another model loaded.
"""
import argparse, hashlib, json, os, shutil, sys, tempfile, threading, time, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
WT = HERE.parents[1]
sys.path.insert(0, str(WT / "examples/x-intake-local"))
from smoke import run_isolated  # noqa: E402

TMPD = WT / "tmp"
VENV = TMPD / ".venv/bin"
STORE = TMPD / "adstore"
RES = Path(os.environ.get("TRIAL_OUT") or (TMPD / "agentdescent-trial-run"))
TRACKED_RES = HERE / "results"
REAL_HOME = Path(os.environ.get("TRIAL_REAL_HOME") or os.path.expanduser("~"))
WATCH = (".agentdescent", ".cache/agentdescent", ".dspy_cache", ".cache/dspy", ".ollama")
HASH_MAX = 1 << 20  # sha256 content for files up to 1 MiB, size+mtime_ns for bigger ones (model blobs)
MODEL = "qwen3.6:35b"
BASE = "http://localhost:11434/v1"
MEM_CAP_GIB = 85


def snap_dir(p: Path):
    """Per-entry fingerprint: content sha256 (small files) or size+mtime_ns, plus dir mtimes."""
    if not p.exists() and not p.is_symlink():
        return None
    out = {}
    for f in [p, *sorted(p.rglob("*"))] if p.is_dir() else [p]:
        try:
            st = f.lstat()
        except OSError:
            continue
        rel = str(f.relative_to(p)) if f != p else "."
        if f.is_file() and not f.is_symlink() and st.st_size <= HASH_MAX:
            out[rel] = "sha:" + hashlib.sha256(f.read_bytes()).hexdigest()
        else:
            out[rel] = f"sz:{st.st_size}:mt:{st.st_mtime_ns}"
    return out


def snap(home: Path = None):
    home = home or REAL_HOME
    return {d: snap_dir(home / d) for d in WATCH}


def home_diff(before, after):
    changed = {}
    for d in WATCH:
        b, a = before.get(d), after.get(d)
        if b != a:
            if b is None or a is None:
                changed[d] = "created" if b is None else "removed"
            else:
                keys = sorted(k for k in set(b) | set(a) if b.get(k) != a.get(k))
                changed[d] = keys[:20]
    return changed


def rel(text: str) -> str:
    """Strip absolute worktree/home paths from anything we keep."""
    return text.replace(str(WT) + "/", "").replace(str(WT), ".").replace(str(REAL_HOME), "~")


def meminfo():
    d = {}
    for l in open("/proc/meminfo"):
        k, v = l.split(":"); d[k] = int(v.split()[0]) // 1024 // 1024
    return d


class MemWatch(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True); self.min_avail = 10**9; self.max_used = 0; self.stop = False
    def run(self):
        while not self.stop:
            m = meminfo(); self.min_avail = min(self.min_avail, m["MemAvailable"])
            self.max_used = max(self.max_used, m["MemTotal"] - m["MemAvailable"]); time.sleep(5)


def wait_ollama(log):
    while True:
        with urllib.request.urlopen("http://localhost:11434/api/ps", timeout=10) as r:
            names = [m["name"] for m in json.load(r).get("models", [])]
        others = [n for n in names if n != MODEL]
        if not others:
            return names
        log(f"ollama busy with {others}; waiting 60s (never killed)"); time.sleep(60)


def child_env():
    return {"OPENAI_BASE_URL": BASE, "OPENAI_API_KEY": "ollama-local-dummy", "TRIAL_MODEL": MODEL,
            "PYTHONDONTWRITEBYTECODE": "1"}


def iso(cmd, timeout):
    with tempfile.TemporaryDirectory(prefix="home-", dir=TMPD) as home:
        t0 = time.time()
        p = run_isolated(cmd, home=home, cwd=str(TMPD), timeout=timeout, path=f"{VENV}:/usr/bin:/bin",
                         extra=child_env(), bwrap_writable=None)  # bwrap --unshare-net would cut localhost:11434
        leftover = sorted(str(x.relative_to(home)) for x in Path(home).rglob("*"))
        return p, round(time.time() - t0, 1), leftover


def score(skill: Path, cases: Path, tag: str):
    out = RES / f"score_{tag}.json"
    p, wall, left = iso([str(VENV / "python"), str(HERE / "child.py"), "score", str(skill), str(cases), str(out)], 3600)
    if p.returncode != 0:
        raise RuntimeError(f"score {tag} rc={p.returncode}: {p.stderr[-800:]}")
    r = json.loads(out.read_text()); r["child_wall_s"] = wall; r["temp_home_leftover"] = left
    out.write_text(json.dumps(r, indent=1)); return r


def spec_for(target: Path):
    oa = "agentdescent.agents:openai_compatible"
    return {"version": 1, "kind": "text", "name": "x-intake-triage", "target": str(target),
            "data": {"path": str(HERE / "train.jsonl"), "prompt": "prompt", "gold": "gold", "id": "id"},
            "score": "exact",
            "agent": {"ref": oa, **{"model": MODEL, "default_base_url": BASE, "max_tokens": 16,
                                            "temperature": 0, "reasoning_effort": "none", "timeout": 300.0}},
            "reflect": {"ref": oa, **{"model": MODEL, "default_base_url": BASE, "max_tokens": 12000,
                                   "temperature": 0.6, "stream": True, "timeout": 1200.0}},
            "evolve": {"rounds": 6, "n_workers": 4, "seed": 230}}


def evolve(log):
    work = TMPD / "ad-target"; work.mkdir(parents=True, exist_ok=True)
    target = work / "SKILL.md"; shutil.copy2(HERE / "skill/SKILL.md", target)
    before_sha = hashlib.sha256((HERE / "skill/SKILL.md").read_bytes()).hexdigest()
    spec = work / "spec.json"; spec.write_text(json.dumps(spec_for(target), indent=1))
    (RES / "agentdescent_spec.json").write_text(rel(spec.read_text()))
    ad = str(VENV / "agentdescent")
    p, _, _ = iso([ad, "--store", str(STORE), "--json", "plan", str(spec)], 300)
    (RES / "agentdescent_plan.txt").write_text(rel(p.stdout[-6000:] + p.stderr[-2000:]))
    if p.returncode != 0:
        raise RuntimeError(f"agentdescent plan rc={p.returncode}: {p.stderr[-800:]}")
    p, wall, left = iso([ad, "--store", str(STORE), "--json", "evolve", str(spec)], 4 * 3600)
    (RES / "agentdescent_evolve.log").write_text(rel(p.stdout[-20000:] + "\n--- stderr ---\n" + p.stderr[-8000:]))
    if p.returncode != 0:
        raise RuntimeError(f"agentdescent evolve rc={p.returncode}: {p.stderr[-800:]}")
    runs = sorted(STORE.glob("*")); run_id = runs[-1].name
    s, _, _ = iso([ad, "--store", str(STORE), "--json", "show", run_id, "--diff"], 300)
    show = json.loads(s.stdout)
    (RES / "agentdescent_show.json").write_text(rel(json.dumps(show, indent=1)))
    # evidence for call/round counts: AgentDescent's own result.json and rounds.jsonl
    rd = STORE / run_id
    for src, dst in (("result.json", "agentdescent_result.json"), ("rounds.jsonl", "agentdescent_rounds.jsonl")):
        if (rd / src).exists():
            (RES / dst).write_text(rel((rd / src).read_text()))
    evolved = RES / "SKILL.evolved.md"; evolved.write_text(show.get("rendered", ""))
    after_sha = hashlib.sha256((HERE / "skill/SKILL.md").read_bytes()).hexdigest()
    return {"run_id": run_id, "evolve_wall_s": wall, "temp_home_leftover": left,
            "final_reward_train_internal": show.get("final_reward"), "outcomes": show.get("outcomes"),
            "stop_reason": show.get("stop_reason"), "usage": show.get("usage"),
            "baseline_skill_untouched": before_sha == after_sha, "tmp_target_changed":
            hashlib.sha256(target.read_bytes()).hexdigest() != before_sha}


def dspy_stage():
    out = TMPD / "dspy-out"; out.mkdir(parents=True, exist_ok=True)
    p, wall, left = iso([str(VENV / "python"), str(HERE / "child.py"), "dspy", str(HERE / "skill/SKILL.md"),
                         str(HERE / "train.jsonl"), str(HERE / "heldout.jsonl"), str(out)], 4 * 3600)
    (RES / "dspy.log").write_text(rel(p.stdout[-20000:] + "\n--- stderr ---\n" + p.stderr[-12000:]))
    if p.returncode != 0:
        raise RuntimeError(f"dspy rc={p.returncode}: {p.stderr[-800:]}")
    r = json.loads((out / "dspy_result.json").read_text()); r["child_wall_s"] = wall; r["temp_home_leftover"] = left
    shutil.copy2(out / "dspy_program.json", RES / "dspy_program.json")
    return r


STAGES = {}  # filled below; tests replace entries


def _baseline():
    return score(HERE / "skill/SKILL.md", HERE / "heldout.jsonl", "baseline")


def _evolve():
    r = evolve(print)
    r["heldout"] = score(RES / "SKILL.evolved.md", HERE / "heldout.jsonl", "agentdescent")
    return r


STAGES.update(baseline=_baseline, evolve=_evolve, dspy=lambda: dspy_stage())
KEY = {"baseline": "baseline", "evolve": "agentdescent", "dspy": "dspy"}


def build_results():
    """results.json from this run dir's stage files only."""
    R = {"model": MODEL, "base_url": BASE, "stages": {}, "errors": {}}
    for st, key in KEY.items():
        f = RES / f"stage_{st}.json"
        if f.exists():
            d = json.loads(f.read_text())
            if d.get("error"):
                R["errors"][st] = d["error"]
            else:
                R["stages"][key] = d["result"]
            R.setdefault("guards", {})[st] = d.get("guard")
    (RES / "results.json").write_text(json.dumps(R, indent=1))
    return R


PROMOTE = ["results.json", "score_baseline.json", "score_agentdescent.json", "agentdescent_spec.json",
           "agentdescent_plan.txt", "agentdescent_evolve.log", "agentdescent_show.json", "agentdescent_result.json",
           "agentdescent_rounds.jsonl", "dspy.log", "dspy_program.json"]


def promote():
    if not (RES / "results.json").exists():
        print(f"nothing to promote in {RES}", file=sys.stderr); return 1
    R = json.loads((RES / "results.json").read_text())
    if R.get("errors"):
        print(f"refusing to promote a run with errors: {sorted(R['errors'])}", file=sys.stderr); return 1
    for name in PROMOTE:
        if (RES / name).exists():
            shutil.copy2(RES / name, TRACKED_RES / name)
    if (RES / "SKILL.evolved.md").exists():
        shutil.copy2(RES / "SKILL.evolved.md", HERE / "skill/SKILL.evolved.md")
    print(f"promoted {RES} -> {TRACKED_RES}"); return 0


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--stage", default="all"); ap.add_argument("--promote", action="store_true")
    a = ap.parse_args(argv)
    if a.promote:
        return promote()
    RES.mkdir(parents=True, exist_ok=True); TMPD.mkdir(exist_ok=True)
    log = lambda m: print(time.strftime("%H:%M:%S"), m, flush=True)
    stages = list(STAGES) if a.stage == "all" else [a.stage]
    failed, home_changed = [], {}
    for st in stages:
        rec = {"stage": st, "started": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
        before = snap()
        mw = MemWatch(); mw.start()
        try:
            rec["ollama_ps_at_start"] = wait_ollama(log)
            m = meminfo()
            if m["MemTotal"] - m["MemAvailable"] > MEM_CAP_GIB - 25:
                raise RuntimeError(f"memory too high to start {st}: used {m['MemTotal']-m['MemAvailable']} GiB")
            log(f"stage {st} start"); t0 = time.time()
            rec["result"] = STAGES[st]()
            rec["wall_s"] = round(time.time() - t0, 1)
        except BaseException as e:  # failures and timeouts both fail the run
            rec["error"] = f"{type(e).__name__}: {str(e)[-1500:]}"; failed.append(st); log(f"stage {st} ERROR {rec['error']}")
            if isinstance(e, KeyboardInterrupt):
                raise
        finally:
            mw.stop = True
            diff = home_diff(before, snap())
            rec["guard"] = {"real_home_untouched": not diff, "changed": diff, "watched": list(WATCH),
                            "min_MemAvailable_GiB": mw.min_avail, "max_used_GiB": mw.max_used, "cap_GiB": MEM_CAP_GIB}
            if diff:
                home_changed[st] = diff
            (RES / f"stage_{st}.json").write_text(rel(json.dumps(rec, indent=1)))
    build_results()
    if home_changed:
        log(f"REAL HOME CHANGED: {home_changed}"); return 3
    if failed:
        log(f"stages failed: {failed}"); return 1
    log(f"ok; outputs in {RES} (run --promote to copy into results/)"); return 0


if __name__ == "__main__":
    sys.exit(main())
