# Handoff — orch-fixes-1011 (2026-10-11)

Not a Feature GO. Do not merge until a separate Tester and a separate Reviewer both PASS at the tip of `build/orch-fixes-1011`.

Worktree: `/home/mark/DEVELOP/pfy-mentat/tmp/orch-fixes-1011`. Founder checkout `/home/mark/DEVELOP/pfy-mentat` was not touched. No extra worktrees. Catalog HOLD 070–075 untouched. No model load, no install, no sudo.

## Head

First pushed tip: `4fe7ba776f6da53e773de9d3bae70762a0705916` (`docs: record orch-fixes-1011 head c1726a8`). Push of that commit created `build/orch-fixes-1011` on `git@github.com:themark-net/pfy-mentat.git` (exit 0). The commit that records this sentence is a docs-only follow-up and is the branch tip after the second push. A commit cannot store its own hash.

| Commit | Subject |
|--------|---------|
| `451a8d5153ac927e66f3e4c96aa271b7288722f6` | fix(x-intake): gitignore smoke receipts for entries 103-108 |
| `4c514e5` | docs: Stage A spec-edit commands and receipt git add -f |
| `a6b2a5f` | test: remove pfylib temp dirs the suite creates |
| `d2d4378c166e78ead9614f42795cc6edc3b62835` | fix(x-intake): record sha source, share timeout text, close har leaks |
| `c1726a835cbea38e7ae1924af2f002002b0eb14c` | docs: handoff orch-fixes-1011 |
| `4fe7ba776f6da53e773de9d3bae70762a0705916` | docs: record orch-fixes-1011 head c1726a8 |

Base: `a5c036231b7baa102dddce30d804fb15840d376a` (`origin/main` at start). The request named `27c2d3b`; that commit is the parent of `a5c0362`. The branch was not reset.

Compare: https://github.com/themark-net/pfy-mentat/compare/main...build/orch-fixes-1011

PR body (gh is not logged in): `docs/ops/PR-BODY-orch-fixes-1011.md`

## Tests

| | Command | Result |
|--|---------|--------|
| Baseline, before any product edit | `python3 -m unittest discover -s tests -t .` | Ran 191 tests in 5.416s · OK (skipped=4) · exit 0 |
| Final, after every fix | same command | Ran 203 tests in 6.816s · OK (skipped=4) · exit 0 |

`tests.test_hedge.DetectorTests.test_detector_runs_offline` did not fail at baseline or at the end on this host. The stdout line `FAIL: grok not on PATH` is a passing test's expected message.

`/tmp/pfylib-*` was 8523 before the baseline suite and 8590 after it (the leak). After the cleanup fix, a full run left the count unchanged at 8657. Pre-existing directories were not bulk-deleted.

## Items

| # | Status | What landed |
|---|--------|-------------|
| 1 | DONE | `pinned()` in `examples/x-intake-local/smoke.py`. Receipts for `HARNESS_SHA256`, `GRAPHJIN_SHA256`, and `CM_SHA256` store `expected.<VAR>.{value,source,pin}` with source `pin` or `env`. An override prints `WARN: $VAR=… overrides the pinned …` on stderr. Red: missing WARN and `None != 'pin'`. |
| 2 | DONE | `timeout_reason(tag)` returns `{tag} timeout`. Sandlock, sponsio, opensteps, repoharness, bugpatrol, and the 106/109 callers use it. Sponsio test asserts the reason is exactly `sponsio probe timeout`. Red: `'sponsio probe timed out' != 'sponsio probe timeout'`. Qwen and foremerge still have no timeout receipt; they did not record one before. |
| 3 | DONE | `docs/automation/agent-substrate-2026-10-08-handoff.md` has two pasteable `python3` blocks: root path `/` read-only, then `process.terminal=false`. Checked on a throwaway `/tmp` config. `runsc` was not run. |
| 4 | DONE | The six x-intake handoffs from 2026-10-05 through 2026-10-11 say a nimo receipt commit uses `git add -f pipelines/smoke/<entry>/latest.json`. `docs/ops/HANDOFF-orch-decisions-1009-2026-10-09.md` notes the temporary atg pin worktree was removed. This run did not delete `atg-eval`, `build-local-lane`, or `/tmp/atg-*` logs. |
| 5 | DONE | `.gitignore` adds `pipelines/smoke/{rulora,har,cassmemory,bugpatrol,graphjin,antislop}/`. Six smokes exited 2 and `git status --porcelain pipelines/smoke` was empty. `pipelines/smoke/kolibri1/latest.json` stays tracked. |
| 6 | DONE | `graphjin_world` closes `serve.log` when `Popen` raises. Red: the handle's `.closed` was false. |
| 7 | DONE | Har FAILs when the launch work dir is not inside the temp HOME (`Path.is_relative_to`). `clean_env` sets `XDG_CONFIG_HOME`, `XDG_CACHE_HOME`, `XDG_DATA_HOME`, and `npm_config_cache` under that HOME. `.har/otel-hooks` is a hook file. |
| 8 | DONE | `addCleanup(shutil.rmtree, …)` on the cli, toolset, hedge, loop, and attach temp dirs. `tests/test_pfylib_tmp_cleanup.py` runs those modules in a subprocess and asserts no new `/tmp/pfylib-*` path. Red: dozens of new dirs. |

## Decisions

17 lines in `docs/ops/AUTONOMOUS-DECISIONS-2026-10-11.md`.

## Left alone

- Entries 109–111 already had `pinned()` for `SMOLVM_SHA256`, `RUNX_SHA256`, and `BRIGADE_VERSION`. They now import the shared function.
- No Feature GO. Nothing merged or deployed. The first push was not a force-push. The Tester FAIL follow-up below rebases onto `origin/main` and is pushed with `--force-with-lease` on this branch only.

## Tester FAIL follow-up

Rebased onto `c1c94fe9b3cfb70ec4d02e9f461d6dd2d9d7f84a` (`origin/main`, docs-only #288). No conflicts. Rebase rewrote the seven commits in the table above. Pre-rebase tip `fe094911bc2704c8a2a60a38e8f83050ce04e48a` is not on this branch after the rebase.

| Rebased commit | Subject |
|----------------|---------|
| `879057ef3f31618be64af57a78b491d5757487c0` | fix(x-intake): gitignore smoke receipts for entries 103-108 |
| `bd4438ed66cf194d01a54914a16f712db5bf7aff` | docs: Stage A spec-edit commands and receipt git add -f |
| `47515cae96669c3e1118696f0066775c7b53eef6` | test: remove pfylib temp dirs the suite creates |
| `a48e632470953f9636ef8faea845a6ddf98b74da` | fix(x-intake): record sha source, share timeout text, close har leaks |
| `e3b18c93b74adc0cffa45f345dc79bd2146bb8fd` | docs: handoff orch-fixes-1011 |
| `e66eab712e171a8c5a2ec3d5eb466a6242a225d2` | docs: record orch-fixes-1011 head c1726a8 |
| `5362fb7f006a845ad89ad8e141464968bde14dda` | docs: record orch-fixes-1011 push of 4fe7ba7 |

| | Command | Result |
|--|---------|--------|
| After the FAIL fix | `python3 -m unittest discover -s tests -t .` | Ran 204 tests in 7.004s · OK (skipped=4) · exit 0 |

- `.gitignore` adds `pipelines/smoke/{laya,nimble,beacon,qwen38flash,sandlock,foremerge,smolvm,brigade,runx}/`. `git check-ignore` matches `pipelines/smoke/<entry>/latest.json` for each of those entries (the paths the 2026-10-05, 2026-10-06, and 2026-10-11 handoffs cite). `pipelines/smoke/kolibri1/latest.json` stays tracked: `git check-ignore` exits 1 and `git ls-files --error-unmatch` succeeds.
- `tests/test_pfylib_tmp_cleanup.py` asserts only that the nested module run adds no `/tmp/pfylib-*` directory. It does not require that subprocess to exit 0.
- `test_har_work_dir_sibling_prefix_fails` launches a work dir of `HOME + "-evil"` (same shape as `/tmp/foo-evil` vs `/tmp/foo`). The smoke FAILs with `work dir is not under the temp HOME` because `Path.is_relative_to` rejects the sibling. The test shows `str.startswith` accepts that sibling.

`pipelines/smoke/brigade/latest.json` from the 109 test is gitignored, so a suite run leaves `git status` clean of smoke receipts.

Decisions: 18 lines in `docs/ops/AUTONOMOUS-DECISIONS-2026-10-11.md`.

Follow-up: Tester FAIL fix is `3bf7079975274c1bc0e1e6d7b5b7d69c0ea14e9b` (`fix(x-intake): gitignore claimed nimo receipts and reject a har sibling dir`). The commit that records this sentence is the branch tip and cannot store its own hash.

## Push

`git push git@github.com:themark-net/pfy-mentat.git build/orch-fixes-1011` created the branch (exit 0) at `4fe7ba776f6da53e773de9d3bae70762a0705916`. The follow-up that records this paragraph is pushed the same way. No merge.
