#!/usr/bin/env python3
"""Child process for the trial (always started through smoke.run_isolated by harness.py).

  child.py score <skill.md> <cases.jsonl> <out.json>   one call per case, AgentDescent's text template
  child.py dspy  <skill.md> <train.jsonl> <heldout.jsonl> <outdir>   one DSPy MIPROv2(light) pass, then held-out eval

Endpoint from $OPENAI_BASE_URL, model from $TRIAL_MODEL. The key is a dummy local value; nothing is printed.
"""
import json, os, sys, time, urllib.request, re

BASE = os.environ["OPENAI_BASE_URL"].rstrip("/")
MODEL = os.environ.get("TRIAL_MODEL", "qwen3.6:35b")
TEMPLATE = "{skill}\n\n{prompt}"  # agentdescent evolvespec._TEXT_TEMPLATE


def norm(s):
    return re.sub(r"\s+", " ", (s or "").casefold()).strip(" .,:;!?\"'`*")


def call(prompt):
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                       "max_tokens": 16, "temperature": 0, "reasoning_effort": "none"}).encode()
    req = urllib.request.Request(f"{BASE}/chat/completions", data=body,
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer local"})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.load(r)
    return d["choices"][0]["message"].get("content") or "", d.get("usage") or {}


def load(p):
    return [json.loads(l) for l in open(p) if l.strip()]


def score(skill_p, cases_p, out_p):
    skill = open(skill_p).read()
    rows, tok, t0 = [], {"prompt": 0, "completion": 0}, time.time()
    for c in load(cases_p):
        out, u = call(TEMPLATE.format(skill=skill, prompt=c["prompt"]))
        tok["prompt"] += u.get("prompt_tokens", 0); tok["completion"] += u.get("completion_tokens", 0)
        rows.append({"id": c["id"], "gold": c["gold"], "out": out.strip()[:40], "ok": norm(out) == norm(c["gold"])})
    res = {"n": len(rows), "correct": sum(r["ok"] for r in rows), "wall_s": round(time.time() - t0, 1),
           "tokens": tok, "per_case": rows}
    res["accuracy"] = round(res["correct"] / res["n"], 4)
    json.dump(res, open(out_p, "w"), indent=1)


def dspy_pass(skill_p, train_p, held_p, outdir):
    import dspy
    from typing import Literal
    lm = dspy.LM(f"openai/{MODEL}", api_base=BASE, api_key="local", temperature=0, max_tokens=4000,
                 reasoning_effort="none", cache=False)
    dspy.configure(lm=lm)
    skill = open(skill_p).read()

    class Triage(dspy.Signature):
        candidate: str = dspy.InputField()
        decision: Literal["CATALOG", "SKIP"] = dspy.OutputField()
    Triage.__doc__ = skill
    prog = dspy.Predict(Triage)
    mk = lambda rows: [dspy.Example(candidate=r["prompt"], decision=r["gold"], id=r["id"]).with_inputs("candidate") for r in rows]
    train, held = mk(load(train_p)), mk(load(held_p))
    metric = lambda ex, pred, trace=None: norm(getattr(pred, "decision", "")) == norm(ex.decision)
    t0 = time.time()
    opt = dspy.MIPROv2(metric=metric, auto="light", seed=230, num_threads=1)
    tuned = opt.compile(prog, trainset=train, requires_permission_to_run=False)
    t_opt = time.time() - t0
    tuned.save(os.path.join(outdir, "dspy_program.json"))
    t1 = time.time(); rows = []
    for ex in held:
        try:
            p = tuned(candidate=ex.candidate); out = p.decision
        except Exception as e:  # parse failure counts as wrong
            out = f"ERR {type(e).__name__}"
        rows.append({"id": ex.id, "gold": ex.decision, "out": str(out)[:40], "ok": norm(out) == norm(ex.decision)})
    tok = {"prompt": 0, "completion": 0}
    for h in lm.history:
        u = h.get("usage") or {}
        tok["prompt"] += u.get("prompt_tokens", 0) or 0; tok["completion"] += u.get("completion_tokens", 0) or 0
    res = {"n": len(rows), "correct": sum(r["ok"] for r in rows), "optimize_wall_s": round(t_opt, 1),
           "eval_wall_s": round(time.time() - t1, 1), "tokens_all_calls": tok, "lm_calls": len(lm.history),
           "per_case": rows}
    res["accuracy"] = round(res["correct"] / res["n"], 4)
    sig = tuned.signature
    res["tuned_instructions"] = sig.instructions
    res["n_demos"] = len(getattr(tuned, "demos", []) or [])
    json.dump(res, open(os.path.join(outdir, "dspy_result.json"), "w"), indent=1)


if __name__ == "__main__":
    {"score": score, "dspy": dspy_pass}[sys.argv[1]](*sys.argv[2:])
