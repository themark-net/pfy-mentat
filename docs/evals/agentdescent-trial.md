# Handoff: AgentDescent eval-auto trial (Entry 119), 2026-10-15

Approved by Mark as an eval-auto trial on nimo. Branch `eval/agentdescent-trial` off origin/main `7b5107d`,
worktree `~/DEVELOP/pfy-mentat/tmp/agentdescent-trial`. Results: [REPORT.md](../../examples/agentdescent-trial/REPORT.md),
[results.json](../../examples/agentdescent-trial/results/results.json).

## Result

Held-out accuracy (20 cases): **baseline 0.70, AgentDescent 0.95, DSPy MIPROv2-light 1.00**.
AgentDescent: 201 s wall-clock (596.8 s summed across workers), 36 calls. DSPy: 686 s, 388 calls, ~338k tokens.

**Recommendation: provisional — AgentDescent as the candidate, not adopted.** n=20 held-out; DSPy scored higher;
exact McNemar baseline vs AgentDescent p=0.0625, baseline vs DSPy p=0.031, AgentDescent vs DSPy p=1.0; and the cases
were written by the trial author from handoff rows. AgentDescent's case is cost and reviewability (about 1/3 the wall
time, 1/10 the calls, a four-line diff to a SKILL.md), not accuracy. **Gate adoption on a rerun with raw post text and a
larger held-out set.** Never `apply` outside a PR with Tester and Reviewer. **Do not port the "default to CATALOG"
line** into the real triage text without a SKIP-heavy (borderline-rich) set first.

## Skill choice

pfy-mentat has no dedicated X intake triage SKILL.md. The written rules the daily intake applies are README.md
"Stage 0 gate" and docs/evaluation-framework.md "Phase 0". `examples/agentdescent-trial/skill/SKILL.md` is an **excerpt** of
them (it omits the CATEGORIZATION.md pointer and the Phase 0 AI-company routing bullet; its own header wrongly says
verbatim, kept byte-identical to what was scored; see `skill/README.md`) plus a one-word output line; that is the
"current skill". Pass/fail is exact match on CATALOG/SKIP.

## Case set

`build_cases.py` (deterministic): 28 CATALOG (Entries 086-088, 095-100, 103-121 from the intake handoffs) and 33 SKIP
(the SKIPPED lists of 2026-10-06..15 handoffs). LATER items excluded. Descriptions restate the facts in the handoffs
with the verdict removed. Stratified 2/3 split, seed 230 -> `train.jsonl` (41), `heldout.jsonl` (20).

## How to rerun

```
cd ~/DEVELOP/pfy-mentat/tmp/agentdescent-trial
uv venv tmp/.venv --python 3.12 && VIRTUAL_ENV=tmp/.venv uv pip install agentdescent==0.5.1 dspy optuna
python3 examples/agentdescent-trial/build_cases.py
python3 examples/agentdescent-trial/harness.py --stage all   # or baseline | evolve | dspy; writes tmp/agentdescent-trial-run/
python3 examples/agentdescent-trial/harness.py --promote     # only path into tracked results/ and skill/SKILL.evolved.md
python3 -m unittest tests.test_agentdescent_trial_harness
```

Runs write only under `tmp/agentdescent-trial-run/` (gitignored, `$TRIAL_OUT` overrides). Each stage writes
`stage_<name>.json`, replaced wholesale, and `results.json` is rebuilt from the current run dir's stage files (no merge
with older results). `--promote` refuses a run with errors. Exit codes: 0 ok, 1 a stage failed or timed out, 3 a
watched real-HOME dir changed.

Every child goes through `examples/x-intake-local/smoke.py` `run_isolated` (new session, killpg on timeout, stripped
env, temp HOME under the worktree `tmp/`). **No bwrap**, because `--unshare-net` would cut `localhost:11434`, so **children have network egress** (only env and
HOME are isolated). The children get only `OPENAI_BASE_URL`, a dummy `OPENAI_API_KEY`, and the model name. AgentDescent uses
`--store tmp/adstore`. Around every stage, in a `finally` that also runs on failure and timeout, the harness fingerprints real
`~/.agentdescent`, `~/.cache/agentdescent`, `~/.dspy_cache`, `~/.cache/dspy` and `~/.ollama` (sha256 for files up to
1 MiB, size+mtime_ns above that, so model blobs aren't hashed) and exits 3 on any change. The recorded run used the
earlier guard (`~/.agentdescent` names only, absent before and after); it was not rerun after the guard change, waits if Ollama has a different model loaded, and refuses to start a stage if host memory use is above 60 GiB.

## Issues hit (none blocking)

- AgentDescent spec refs take factory kwargs as top-level keys (`{"ref": ..., "model": ...}`), not under `config`.
  `openai_compatible` works against Ollama's `/v1` with `reasoning_effort: "none"` passed through as a body field.
- AgentDescent records tokens=0 from a JSON spec (usage needs a Python `Usage` object). Its `result.json`
  `fusion_trials[0].baseline_score` = 0.0 is a placeholder written for an unranked fusion trial (`fusion.py` `_record`,
  `ranked: false`), not a score. Its stop decision rests on `held_out_reward` 1.0 on its own internal split, which we
  did not verify; it may rest on unreliable internal scoring. Call count 36 is in `results/agentdescent_result.json`.
- AgentDescent stopped after round 1 because its internal held-out (30% of train) hit 1.0 >= target 0.98, so this
  trial does not exercise multi-round merging.
- MIPROv2 needs `optuna`, which plain `dspy` does not pull in; first DSPy attempt failed on that.
- Peak host memory 79 GiB (whole host, including Mark's processes) during the evolve invocation. No lock-up.

## Tester FAIL @ cce6e2c fixed

- B1: five-dir content guard in a `finally` (timeouts too), exit 3 on change, exit 1 on stage failure or timeout.
- B2: runs go to gitignored `tmp/`, explicit `--promote`, no results merging.
- Claims: 36 calls backed by `agentdescent_result.json`/`agentdescent_rounds.jsonl`; SKILL.md labelled an excerpt;
  recommendation now provisional with McNemar p-values; baseline_score explained; relative paths in committed logs; no
  bwrap / egress noted.
- `tests/test_agentdescent_trial_harness.py`: each fix was reverted in turn and the tests went red.

## Tester FAIL @ 07bca20 fixed

- B1': each stage record keeps its guard result; `--promote` refuses (exit 1) if any matching stage's guard failed or is missing.
- B2': `run.json` holds a run id plus SHA-256 of `skill/SKILL.md`, `cases.jsonl`, `train.jsonl`, `heldout.jsonl`; each stage record is stamped with both. `results.json` and `--promote` use only records matching the current run id and hashes (others listed under `refused_stale`); a single stage after an input change starts a new run id; `--stage all` clears the run dir first; promote copies only the files of matching, successful stages.
- Timing: AgentDescent 201 s wall-clock, 596.8 s summed across workers.

## Tester FAIL @ ac1c803 fixed

- Any new run id (no run.json, or input hashes changed) clears the whole run dir before the stage runs. Each stage deletes
  its own outputs and record when it starts. The AgentDescent run dir is the one this invocation created (set
  difference of the store before/after, exactly one), never the newest by name.
- `--promote` accepts only a COMPLETE run: baseline, evolve and dspy all present, matching run id and hashes, with a
  result, no error, and `guard.real_home_untouched is True`. Otherwise exit 1 and tracked files are untouched. On success it
  builds the new set in a temp dir next to `results/`, swaps it in by rename, and removes everything not produced by
  this run (including a stale `skill/SKILL.evolved.md`). run.json hashes also cover `harness.py` and `child.py`.
- `REPORT.md` moved from `results/` to `examples/agentdescent-trial/REPORT.md` so a promote can't delete it.
- The committed `results/` set predates run ids and stage records; a fresh `--stage all` plus `--promote` would replace it.

## Next

1. Tester and Reviewer gate on this PR (harness, case set, results only; no catalog or stage changes).
2. If accepted, a separate PR proposing the AgentDescent lines for the real triage text, and a TOOLS.md/stage
   move for Entry 119 backed by this receipt.
3. Rerun with raw post text and a larger held-out set before trusting the "default to CATALOG" line.
