#!/usr/bin/env python3
"""AgentDescent vs DSPy vs baseline on X intake triage (eval-auto trial, Entry 119).

Usage (from the worktree root):  python3 examples/agentdescent-trial/harness.py [--stage all|baseline|evolve|dspy]

Every child goes through examples/x-intake-local/smoke.py run_isolated (new session, killpg on timeout,
stripped env, temp HOME). Venv, AgentDescent run store and scratch live in <worktree>/tmp. The real skill text
is never a target: AgentDescent evolves a copy in tmp/, and `apply` is never called. ~/.agentdescent in the
real HOME is snapshotted before and after. Waits (never kills) while Ollama has another model loaded.
Writes examples/agentdescent-trial/results/results.json.
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
RES = HERE / "results"
MODEL = "qwen3.6:35b"
BASE = "http://localhost:11434/v1"
REAL_AD = Path(os.path.expanduser("~")) / ".agentdescent"
MEM_CAP_GIB = 85


def snap(p: Path):
    if not p.exists():
        return {"exists": False}
    h = hashlib.sha256()
    n = 0
    for f in sorted(p.rglob("*")):
        h.update(str(f).encode()); n += 1
    return {"exists": True, "entries": n, "sha": h.hexdigest()[:16]}


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
    shutil.copy2(spec, RES / "agentdescent_spec.json")
    ad = str(VENV / "agentdescent")
    p, _, _ = iso([ad, "--store", str(STORE), "--json", "plan", str(spec)], 300)
    (RES / "agentdescent_plan.txt").write_text(p.stdout[-6000:] + p.stderr[-2000:])
    if p.returncode != 0:
        raise RuntimeError(f"agentdescent plan rc={p.returncode}: {p.stderr[-800:]}")
    p, wall, left = iso([ad, "--store", str(STORE), "--json", "evolve", str(spec)], 4 * 3600)
    (RES / "agentdescent_evolve.log").write_text(p.stdout[-20000:] + "\n--- stderr ---\n" + p.stderr[-8000:])
    if p.returncode != 0:
        raise RuntimeError(f"agentdescent evolve rc={p.returncode}: {p.stderr[-800:]}")
    runs = sorted(STORE.glob("*")); run_id = runs[-1].name
    s, _, _ = iso([ad, "--store", str(STORE), "--json", "show", run_id, "--diff"], 300)
    show = json.loads(s.stdout)
    (RES / "agentdescent_show.json").write_text(json.dumps(show, indent=1))
    evolved = HERE / "skill/SKILL.evolved.md"; evolved.write_text(show.get("rendered", ""))
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
    (RES / "dspy.log").write_text(p.stdout[-20000:] + "\n--- stderr ---\n" + p.stderr[-12000:])
    if p.returncode != 0:
        raise RuntimeError(f"dspy rc={p.returncode}: {p.stderr[-800:]}")
    r = json.loads((out / "dspy_result.json").read_text()); r["child_wall_s"] = wall; r["temp_home_leftover"] = left
    shutil.copy2(out / "dspy_program.json", RES / "dspy_program.json")
    return r


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--stage", default="all")
    a = ap.parse_args()
    RES.mkdir(exist_ok=True); TMPD.mkdir(exist_ok=True)
    rp = RES / "results.json"
    R = json.loads(rp.read_text()) if rp.exists() else {"model": MODEL, "base_url": BASE, "stages": {}}
    log = lambda m: print(time.strftime("%H:%M:%S"), m, flush=True)
    real_before = snap(REAL_AD)
    mw = MemWatch(); mw.start()
    stages = ["baseline", "evolve", "dspy"] if a.stage == "all" else [a.stage]
    try:
        for st in stages:
            R.setdefault("ollama_ps_at_start", {})[st] = wait_ollama(log)
            m = meminfo()
            if m["MemTotal"] - m["MemAvailable"] > MEM_CAP_GIB - 25:
                raise RuntimeError(f"memory too high to start {st}: used {m['MemTotal']-m['MemAvailable']} GiB")
            log(f"stage {st} start"); t0 = time.time()
            try:
                if st == "baseline":
                    R["stages"]["baseline"] = score(HERE / "skill/SKILL.md", HERE / "heldout.jsonl", "baseline")
                elif st == "evolve":
                    R["stages"]["agentdescent"] = evolve(log)
                    R["stages"]["agentdescent"]["heldout"] = score(HERE / "skill/SKILL.evolved.md", HERE / "heldout.jsonl", "agentdescent")
                elif st == "dspy":
                    R["stages"]["dspy"] = dspy_stage()
            except Exception as e:  # recorded as a blocker, the next stage still runs
                R["stages"].setdefault("errors", {})[st] = str(e)[-1500:]; log(f"stage {st} ERROR {e}")
            log(f"stage {st} done in {time.time()-t0:.0f}s")
    finally:
        mw.stop = True
        real_after = snap(REAL_AD)
        R.setdefault("real_home_agentdescent", []).append({"before": real_before, "after": real_after,
                                                           "untouched": real_before == real_after})
        R.setdefault("memory", []).append({"min_MemAvailable_GiB": mw.min_avail, "max_used_GiB": mw.max_used,
                                           "cap_GiB": MEM_CAP_GIB})
        rp.write_text(json.dumps(R, indent=1))
        log(f"wrote {rp}; real ~/.agentdescent untouched={real_before == real_after}")


if __name__ == "__main__":
    main()
