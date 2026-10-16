# Handoff: AgentDescent eval-auto trial (Entry 119), 2026-10-15

Approved by Mark as an eval-auto trial on nimo. Branch `eval/agentdescent-trial` off origin/main `7b5107d`,
worktree `~/DEVELOP/pfy-mentat/tmp/agentdescent-trial`. Results: [REPORT.md](../../examples/agentdescent-trial/results/REPORT.md),
[results.json](../../examples/agentdescent-trial/results/results.json).

## Result

Held-out accuracy (20 cases): **baseline 0.70, AgentDescent 0.95, DSPy MIPROv2-light 1.00**.
AgentDescent: 201 s, 36 calls. DSPy: 686 s, 388 calls, ~338k tokens.

**Recommendation: adopt AgentDescent** as the eval-auto tool for tuning pfy SKILL.md text, through normal PRs only
(never `apply` outside a PR with Tester and Reviewer). It matched DSPy within one held-out case at about 1/3 the wall
time and 1/10 the calls, and its output is a four-line diff to the real skill file that a Reviewer can read. Keep DSPy
for the #230 decision bench where a compiled program with demos is the artifact anyway. Separately, the four
AgentDescent lines are a candidate edit for the real triage text (README Stage 0 / evaluation-framework Phase 0), but
that is a separate PR, not part of this one.

## Skill choice

pfy-mentat has no dedicated X intake triage SKILL.md. The written rules the daily intake applies are README.md
"Stage 0 gate" and docs/evaluation-framework.md "Phase 0". `examples/agentdescent-trial/skill/SKILL.md` copies them
verbatim plus a one-word output line; that is the "current skill". Pass/fail is exact match on CATALOG/SKIP.

## Case set

`build_cases.py` (deterministic): 28 CATALOG (Entries 086-088, 095-100, 103-121 from the intake handoffs) and 33 SKIP
(the SKIPPED lists of 2026-10-06..15 handoffs). LATER items excluded. Descriptions restate the facts in the handoffs
with the verdict removed. Stratified 2/3 split, seed 230 -> `train.jsonl` (41), `heldout.jsonl` (20).

## How to rerun

```
cd ~/DEVELOP/pfy-mentat/tmp/agentdescent-trial
uv venv tmp/.venv --python 3.12 && VIRTUAL_ENV=tmp/.venv uv pip install agentdescent==0.5.1 dspy optuna
python3 examples/agentdescent-trial/build_cases.py
python3 examples/agentdescent-trial/harness.py --stage all   # or baseline | evolve | dspy
```

Every child goes through `examples/x-intake-local/smoke.py` `run_isolated` (new session, killpg on timeout, stripped
env, temp HOME under the worktree `tmp/`). bwrap is not used because `--unshare-net` would cut `localhost:11434`;
the children get only `OPENAI_BASE_URL`, a dummy `OPENAI_API_KEY`, and the model name. AgentDescent uses
`--store tmp/adstore`. The harness snapshots real `~/.agentdescent` before and after each invocation (absent both
times), waits if Ollama has a different model loaded, and refuses to start a stage if host memory use is above 60 GiB.

## Issues hit (none blocking)

- AgentDescent spec refs take factory kwargs as top-level keys (`{"ref": ..., "model": ...}`), not under `config`.
  `openai_compatible` works against Ollama's `/v1` with `reasoning_effort: "none"` passed through as a body field.
- AgentDescent records tokens=0 from a JSON spec (usage needs a Python `Usage` object). Its `result.json`
  `baseline_score` reads 0.0, which does not match our baseline run (0.70 held-out); not investigated.
- AgentDescent stopped after round 1 because its internal held-out (30% of train) hit 1.0 >= target 0.98, so this
  trial does not exercise multi-round merging.
- MIPROv2 needs `optuna`, which plain `dspy` does not pull in; first DSPy attempt failed on that.
- Peak host memory 79 GiB (whole host, including Mark's processes) during the evolve invocation. No lock-up.

## Next

1. Tester and Reviewer gate on this PR (harness, case set, results only; no catalog or stage changes).
2. If accepted, a separate PR proposing the AgentDescent lines for the real triage text, and a TOOLS.md/stage
   move for Entry 119 backed by this receipt.
3. Rerun with raw post text and a larger held-out set before trusting the "default to CATALOG" line.
