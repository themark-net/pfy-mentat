# RUN LOG — orch-fixes-1011

Started: 2026-10-12T07:01:06Z (request date 2026-10-11). Clock exit ~6h after start.
Worktree: `/home/mark/DEVELOP/pfy-mentat/tmp/orch-fixes-1011`
Branch: `build/orch-fixes-1011` (no upstream). Tip at plan time: `a5c036231b7baa102dddce30d804fb15840d376a`, equal to `origin/main`. Named base `27c2d3b` is an ancestor (one commit behind). No remote branch already contains these fixes.
Lead commits only. Agents do not commit. No extra worktrees. Founder checkout untouched.

## Overview

Eight small fixes on the x-intake smokes, the agent-substrate Stage A commands, the x-intake handoff wording, smoke receipt gitignore, and pfylib temp-dir cleanup. Shared smoke files are one workstream. Docs, gitignore, and pfylib tests are separate workstreams and run together after the baseline suite is recorded.

## Phases

- baseline | (no product edits) | `python3 -m unittest discover -s tests -t .` recorded before any product edit, including the known `test_hedge` `test_detector_runs_offline` result | none | lead
- smoke-contract | `examples/x-intake-local/smoke.py`, `smoke_098_100.py`, `smoke_103_105.py`, `smoke_106_108.py`, `smoke_109_111.py`, `tests/test_x_intake_smoke_098_100.py`, new `tests/test_x_intake_smoke_103_105.py`, new `tests/test_x_intake_smoke_106_108.py` | Items 1, 2, 6, 7. Receipt `expected.<VAR>.source` is `pin` or `env` for `HARNESS_SHA256`, `GRAPHJIN_SHA256`, `CM_SHA256`, and an env override prints the WARN line. Every smoke timeout reason is `smoke.timeout_reason(tag)`. A sponsio timeout test asserts that text. `graphjin_world` closes the server log if `Popen` raises. `smoke_har` FAILs when the work dir is outside the temp HOME, points `XDG_CONFIG_HOME`, `XDG_CACHE_HOME`, `XDG_DATA_HOME`, and `npm_config_cache` under that HOME, and treats `~/.har/otel-hooks` like the other hook files. Each new test was red before the fix and green after. | baseline | general
- handoff-docs | `docs/automation/agent-substrate-2026-10-08-handoff.md`, `docs/automation/x-intake-2026-10-0{5,6,7,9}.md` and `x-intake-2026-10-{10,11}-handoff.md`, `docs/ops/HANDOFF-orch-decisions-1009-2026-10-09.md` | Items 3 and 4. Stage A spec edits are runnable copy-paste `python3` blocks, checked against a throwaway config under `/tmp`. Each named x-intake handoff says `git add -f` for a nimo receipt. The 2026-10-09 handoff notes the temp atg pin worktree was removed. No markdown-grep unit test. | baseline | general
- smoke-gitignore | `.gitignore` only | Item 5. Ignore `pipelines/smoke/{rulora,har,cassmemory,bugpatrol,graphjin,antislop}/`. After those six smokes, `git status --porcelain pipelines/smoke` is empty. `pipelines/smoke/kolibri1/latest.json` stays tracked. | baseline | general
- pfylib-tmp | `tests/test_cli.py`, `tests/test_toolsets.py`, `tests/test_hedge.py`, `tests/test_loop_paint.py`, `tests/test_attach.py`, plus one behavior test | Item 8. A full run of the leaking modules leaves no new `/tmp/pfylib-*` directory. Pre-existing `/tmp/pfylib-*` dirs are not bulk-deleted. Red before `addCleanup`, green after. | baseline | general
- handoff | `docs/ops/HANDOFF-orch-fixes-1011-2026-10-11.md`, `docs/ops/PR-BODY-orch-fixes-1011.md`, this log, `docs/TODO.md` done row, decisions file | Final counts, per-item status, decisions path. Push only `build/orch-fixes-1011`. Compare URL printed. No merge. | all other phases | lead

## Final

- Baseline: Ran 191 tests in 5.416s · OK (skipped=4) · exit 0
- Final: Ran 203 tests in 6.816s · OK (skipped=4) · exit 0
- `test_detector_runs_offline`: passed both times on this host
- Items 1–8: DONE
- Decisions: 17 lines, `docs/ops/AUTONOMOUS-DECISIONS-2026-10-11.md`
- Compare: https://github.com/themark-net/pfy-mentat/compare/main...build/orch-fixes-1011

## Risks

- Shared smoke files: one agent owns every file under `examples/x-intake-local/` and the x-intake tests, so the other agents do not edit them.
- Baseline `test_detector_runs_offline` may fail with status `partial` on this box. Same failure at the end is not a regression. Any other new failure stops the run.
- Swap is partly used (~6.7 GiB of 8 GiB) with ~66 GiB RAM available. Do not load a model. Stop if the host runs out of memory.
- `git status --porcelain pipelines/smoke` can show receipts from the 109 suite (`brigade` and neighbors). Those are not item 5. Delete only untracked receipt dirs this run created, and do not commit them.
- Catalog HOLD entries 070–075 stay untouched. No Feature GO.

## Gate log

- baseline | DONE | tests: `python3 -m unittest discover -s tests -t .` → Ran 191 tests in 5.416s · OK (skipped=4) · exit 0. `test_detector_runs_offline` did not fail on this host. The line `FAIL: grok not on PATH` is a passing test's stdout. Untracked `pipelines/smoke/brigade/` from `tests/test_x_intake_smoke_109_111.py` was removed (not a product file). `/tmp/pfylib-*` grew from 8523 to 8590 during this run. | files: 0 product | err: none
- smoke-contract | DONE | tests: red `Ran 16 tests` FAILED (failures=11) including `sponsio probe timed out` != `sponsio probe timeout`, missing WARN lines, `None != 'pin'`, log handle `False is not true`, XDG not under temp HOME, otel-hooks exit 0. Green: `python3 -m unittest tests.test_x_intake_smoke_098_100 tests.test_x_intake_smoke_103_105 tests.test_x_intake_smoke_106_108 tests.test_x_intake_smoke_109_111` → Ran 17 tests in 3.248s OK. Full suite after: Ran 203 tests in 6.816s OK (skipped=4). `/tmp/pfylib-*` 8657 before and after that full run. | files: 8 | err: none | commit d2d4378c166e78ead9614f42795cc6edc3b62835
- handoff-docs | DONE | tests: fixture under /tmp, both python snippets; root.path `/`, readonly true, terminal false. No markdown unit. | files: 8 | err: none | commit 4c514e5
- smoke-gitignore | DONE | tests: six smokes exit 2; `git status --porcelain pipelines/smoke` empty; kolibri1/latest.json still tracked (`git check-ignore` exit 1) | files: 1 | err: none | commit 451a8d5153ac927e66f3e4c96aa271b7288722f6
- pfylib-tmp | DONE | tests: red `AssertionError` listing new `/tmp/pfylib-{attach,test,cli,hedge,loop}-*` dirs (`Ran 1 test` FAILED). Green: `python3 -m unittest tests.test_pfylib_tmp_cleanup` Ran 1 test in 0.461s OK (lead re-ran). Subprocess of the five modules: Ran 77 tests OK. `test_detector_runs_offline` did not fail. | files: 6 | err: none | commit a6b2a5f
- handoff | DONE | commit c1726a835cbea38e7ae1924af2f002002b0eb14c then a child commit that names it | files: handoff, PR body, this log, TODO, decisions | err: none

## Push

Child of `c1726a835cbea38e7ae1924af2f002002b0eb14c` is the tip. The push result line is appended after `git push`.
