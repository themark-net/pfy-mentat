# Run log: mvp-dogfood4-1031

Lane: six real cloud `./pfy build` fixes from open TODO rows, then the next fitting MVP gap until an exit.
Branch: `bot/mvp-dogfood4-1031`. Worktree: `~/DEVELOP/pfy-mentat/tmp/mvp-dogfood4-1031`.
Base: `origin/bot/mvp-integrate-1031` at `1dee0b91bda11ba1fcda87819423437a3f10f289`. Drop-in commit: `a9ed73d`.
Launch clock: 2026-11-01T01:33:27Z (survey start). Exit card written: 2026-11-01T01:43:00Z.
Wall cap: 2026-11-01T09:33:27Z (8 hours), or 2026-11-02T02:00Z, whichever is first.
Stop new items by 2026-11-01T09:13:27Z so the handoff has 20 minutes.
Needs a local model: no. Cloud Grok only. Never `--local`. Do not run `scripts/pregate.sh` during the loop.

## LOOP EXIT CARD

```text
LOOP EXIT CARD
Goal (success criteria):     6 cloud ./pfy build rows, each with a receipt under eval/mvp-1031/dogfood4/, a behavior or fail/recover test, a human accept or reject with a reason, a commit, and a push. Handoff table has 6 rows and the pass rate.
1 Goal met:                  this lane compares each diff to the task, reruns the affected unittest, and records accept or reject. A failed build is a row, not a silent retry past the turn cap.
2 Turn cap:                  8 cloud builds. Stop even if a spare gap remains.
3 Budget cap:                cloud Grok only. --retries 1 (2 attempts) and --timeout 900 per build. No --local. No second model. No project-map Grok while other lanes are inside ./pfy build.
4 Wall clock:                2026-11-01T09:33:27Z or 2026-11-02T02:00Z. Leave 20 minutes for the handoff.
5 No-progress:               the same failure twice with no new information, or 3 items in a row skipped. Survey skips before item 01 do not count.
6 Human interrupt:           user stop. Do not ask. A conservative choice goes in the decisions file.
7 Error threshold:           3 consecutive cloud failures with the same reason, then stop.
8 External event:            if origin/main or another bot branch already has the fix, skip that item. If a live lane owns the file, skip it.
Loop type:                   goal
Human gate:                  no merge, no PR, no tag. This lane accepts or rejects each cherry-pick.
```

Named skills `write-loop-exits-first` and `repo-handoff-doc-required` are not files in this worktree or `~/.grok/skills`. This card, the drop-in exits, and `docs/ops/HANDOFF-mvp-dogfood4-1031.md` are the binding. Decision logged.

## Drop-in exits (check before every item)

1. Wall cap: 8 hours from 2026-11-01T01:33:27Z, or Sunday 2026-11-01 18:00 PT (2026-11-02T02:00Z). Leave 20 minutes for the handoff.
2. Lane empty: no item left that fits this lane and these rules.
3. No progress: the same failure twice with no new information, or 3 items in a row skipped.
4. Host pressure: MemAvailable under 16 GiB, or load over 64 (2 x 32 cores) for 5 minutes. Pause 10 minutes, then stop if it persists.
5. Red base: record tests that fail on the base and skip that area. Do not stop the lane.

Host at the exit card: MemAvailable about 65 GiB (68209024 kB at 2026-11-01T01:42:45Z). Load about 3.55 on 32 cores. Not under pressure.

## Phases

Overview: Land six small product fixes with the integration tip's cloud `./pfy build`. One build per item, sequential, on this branch. Receipts stay in `eval/mvp-1031/dogfood4/`. Product edits land only by an accepted cherry-pick. The red behavior test is planted by this lane before the clone, so the gate is red on the base and the runner must not edit it.

- prep | docs/ops/RUN-LOG-mvp-dogfood4-1031.md, docs/ops/AUTONOMOUS-DECISIONS-mvp-dogfood4-1031.md | exit card committed and pushed before a cloud build | none | general
- select | this log, task queue below | each task names one free file and a behavior that is wrong on this tip | prep | general
- build | eval/mvp-1031/dogfood4/<n>-<slug>/, tmp/target-<n> | receipt, diff, command, wall, exit, attempts, review, human verdict | select | general, lead only (one branch)
- handoff | docs/ops/HANDOFF-mvp-dogfood4-1031.md | 6-row table, pass rate, final state line, pushed, not merged | build | general

These six builds share one branch, so they are one workstream. The lead runs them. No parallel implementer.

Risks:
- Review diff cap is 12000 characters. Each task is one file and one helper. Mitigation: reject a diff that edits a second product file or a test.
- A model that edits the planted test trips `tests-tampered` because the test is in the clone HEAD and `--writable-test` is not passed.
- Full `unittest discover` would take the shared heavy lock. Mitigation: `--test-cmd` is one module.
- The throwaway clone is `tmp/target-<n>` inside this worktree. Never Mark's checkout and never another lane's worktree.
- Secrets in receipts. Mitigation: class-only scan before commit. Never print a matched value.
- dogfood5 is a live sibling sourcing FINDINGs. This lane does not take those rows. probe-int, cloud-perf, and timeoutfix own `scripts/pfy_build_cloud.py`. localbench owns the in-repo TMPDIR bench test. selfhost2 already handed off its symlink fixes on other files.

## Task queue

Open TODO rows were surveyed and skipped (voice shelf, local model, docker, parked env, hardware, ADR, OQ). The next gaps are fail-closed bugs on files no `origin/bot/mvp-*` commit since the integrate tip has edited. dogfood3's bad-timeout smokes are not repeated.

| n | slug | source | file | why it fits |
| --- | --- | --- | --- | --- |
| 01 | toolset-symlink | `apply` write, append-marker, and json-merge follow an in-root symlink | pfylib/toolsets.py | probed: a link to real.txt became "new" in the target and stayed a symlink |
| 02 | modules-symlink | `save_selection` writes through a symlink; `load_selection` reads through it | pfylib/loop_paint.py | same contract as 01, different file |
| 03 | opencode-config-symlink | `write_opencode_config` writes through a symlink | pfylib/bot_interface.py | same contract, bot config path |
| 04 | hiroute-term-wait | `term_wait` turns a bad `HIROUTE_TERM_WAIT` into 45 | examples/x-intake-local/smoke_146_147.py | fail-open env, file not in dogfood3 |
| 05 | skillup-fixture-digest | `fixture_unchanged` compares names only and `is_file` follows links | examples/x-intake-local/smoke_146_147.py | after 04, so the clone has the term-wait check |
| 06 | taste-fixture-digest | `fixtures_untouched` calls `tree_hash`, which reads symlink targets | examples/x-intake-local/smoke_143_145.py | do not edit smoke_140; selfhost2 owns that copy |

Each build: throwaway clone under `tmp/target-<n>`, `./pfy build` with `--repo` that clone, `--base HEAD`, `--retries 1`, `--timeout 900`, a focused `--test-cmd`, and `--receipt-dir` at `eval/mvp-1031/dogfood4/<n>-<slug>/`. No `--local`. No `--writable-test`.

## Items

item | commit | tests | result
01 toolset-symlink | d900cc3 | tests.test_toolset_apply_symlink tests.test_toolsets 29 OK | accept
02 modules-symlink | 2e8d20e | tests.test_loop_paint_symlink tests.test_loop_paint 11 OK | accept
03 opencode-config-symlink | d2dc658 | tests.test_bot_interface_opencode_symlink tests.test_bot_interface 22 OK | accept
04 hiroute-term-wait | d507591 | tests.test_smoke_146_term_wait 3 OK; tests.test_x_intake_smoke_146_147 35 OK | accept
05 skillup-fixture-digest | e6aad0d | tests.test_smoke_146_fixture_digest tests.test_smoke_146_term_wait tests.test_x_intake_smoke_146_147 41 OK | accept
