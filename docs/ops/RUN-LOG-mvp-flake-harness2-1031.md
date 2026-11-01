# Run log: mvp-flake-harness2-1031

Launch: 2026-11-01T02:05:36Z
Branch: `bot/mvp-flake-harness2-1031`
Base: `origin/bot/mvp-integrate-1031` (`1dee0b91bda11ba1fcda87819423437a3f10f289`)
Worktree: `~/DEVELOP/pfy-mentat/tmp/mvp-flake-harness2-1031`

## LOOP EXIT CARD

```text
LOOP EXIT CARD
Goal (success criteria):     stage-script test is deterministic under load; eval-structural.log contains a failing unittest traceback; every discover-only flake in 3 heavy runs is fixed or recorded as red-base
1 Goal met:                  targeted unittest modules green, then 3x niced discover under the heavy lock
2 Turn cap:                  8 items (3 named, then further flake fixes). Stop after that even if the lane could continue
3 Budget cap:                no local model, no paid API, cloud Grok session only
4 Wall clock:                8h from launch (2026-11-01T10:05:36Z) or 2026-11-02T02:00Z, whichever first. Stop new items at 2026-11-01T09:45:36Z so the handoff can be written
5 No-progress:               same failure twice with no new information, or 3 items skipped in a row
6 Human interrupt:           user stop. Do not ask questions. Conservative choice goes in the decisions file
7 Error threshold:           3 consecutive same failures, then stop
8 External event:            n/a (no PR merge). Skip work already on origin/main or the base
Loop type:                   goal
Human gate:                  no merge, no PR. Push the bot branch only
```

Named skills `write-loop-exits-first` and `repo-handoff-doc-required` are not files in this worktree or `~/.grok/skills`. This card, the drop-in exit list, and `docs/ops/HANDOFF-mvp-flake-harness2-1031.md` are the binding.

## Plan

Overview: The pregate at 16f17d8 failed `test_stub_tools_see_state_caches_and_home_stays` inside `pfylib_unittests` and printed only the test name. Make that test deterministic, make the structural runner keep the unittest traceback, then sweep discover three times for other flakes.

Phases:
- exits | docs/ops/RUN-LOG-mvp-flake-harness2-1031.md, docs/ops/AUTONOMOUS-DECISIONS-mvp-flake-harness2-1031.md | card written before code | none | general
- flake-stage | tests/test_harness2_local_stage.py, examples/harness2-local/stage.sh only if the script is the cause | 20 niced runs plus a private CPU burner stay green; a private-home write still fails and a clean rerun passes | exits | general
- traceback | examples/eval-harness/run_structural.py, tests for that runner | a failing unittest's traceback is in the check detail the log prints | exits | general
- discover-sweep | tests that flake in 1 or 2 of 3 heavy discovers | each intermittent failure fixed or recorded red-base | traceback | general
- handoff | docs/ops/HANDOFF-mvp-flake-harness2-1031.md, this log | state line and handoff pushed | all | general

Risks:
- Live `~/.cache/uv` and `~/.npm` change while other lanes run. Mitigation: do not write those trees; fingerprint only the private HOME the stage script is given.
- Full discover holds the heavy lock for a long time. Mitigation: one flock, nice 19, in-repo TMPDIR, three runs only.
- Shared worktree. Mitigation: no implementation sub-agents. project-map writes only `.project-map/`.

## Resume 2026-11-01T02:45Z

Operator items A, B, and C run before the original 1, 2, 3. Item A is the cause of item 1 (tearDown hashed the operator `~/.cache/uv`). Wall check at resume: now is before 2026-11-01T09:45:36Z. Host: MemAvailable about 45 GiB, load about 3 on 32 cores. No Runner.Worker.

## Items

(in progress) A / item 1 private HOME and UV cache for harness2 stage tests
(done) B docs hygiene shallow skipTest | a0885ed | TMPDIR=$PWD/tmp nice -n 19 python3 -m unittest tests.test_docs_hygiene | 3 OK in 0.067s
(done) C pregate refuses Runner.Worker | b8ec41d | TMPDIR=$PWD/tmp nice -n 19 python3 -m unittest tests.test_pregate_runner_gate | 2 OK in the combined 2.980s run (the third test was the traceback check)
(done) item 2 structural traceback | 871075c | TMPDIR=$PWD/tmp nice -n 19 python3 -m unittest tests.test_eval_structural_trace | ok in the combined run (traceback assertions held; hygiene failure in that run was fixed before a0885ed)
(pending) item 3 discover x3

B | a0885ed | TMPDIR=$PWD/tmp nice -n 19 python3 -m unittest tests.test_docs_hygiene | 3 OK in 0.067s
C | b8ec41d | TMPDIR=$PWD/tmp nice -n 19 python3 -m unittest tests.test_pregate_runner_gate | 2 OK
item 2 | 871075c | TMPDIR=$PWD/tmp nice -n 19 python3 -m unittest tests.test_eval_structural_trace | ok (Traceback, AssertionError, operator cache changed; passing run has no Traceback)
