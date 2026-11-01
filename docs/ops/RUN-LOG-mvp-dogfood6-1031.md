# RUN LOG mvp-dogfood6-1031

Lane mvp-dogfood6-1031. Branch `bot/mvp-dogfood6-1031`. Worktree `/home/mark/DEVELOP/pfy-mentat/tmp/mvp-dogfood6-1031`. Base `origin/bot/mvp-integrate-1031` at `1dee0b91bda11ba1fcda87819423437a3f10f289`. Drop-in commit `528288d`.

Launch clock: 2026-11-01T02:33:54Z. Wall cap: 2026-11-01T10:33:54Z (8 hours). New items stop by 2026-11-01T10:13:54Z. Calendar cap 2026-11-02T02:00Z is later, so the 8 hour cap wins. Leave 20 minutes for the handoff.

Needs a local model: no. Cloud Grok only. Never `--local` on `./pfy`. Do not run `scripts/pregate.sh`.

```text
LOOP EXIT CARD
Goal (success criteria): six cloud ./pfy build rows in eval/mvp-1031/dogfood6/, each human-accepted or rejected with a reason, pass rate in the handoff
1 Goal met:              handoff row per build; targeted unittest green for every accept
2 Turn cap:              8 cloud builds (the six plus two recovery attempts)
3 Budget cap:            cloud Grok only, no --local, no spend outside ./pfy build
4 Wall clock:            2026-11-01T10:33:54Z, stop new items at 10:13:54Z
5 No-progress:           same failure twice with no new information, or 3 items in a row skipped
6 Human interrupt:       user stop
7 Error threshold:       3 consecutive same failure, then stop
8 External event:        item already on this tip or on origin/main, or another bot branch already has the fix, or a live lane owns the file
Loop type:               goal
Human gate:              no merge, no PR, no tag. Tester plus Reviewer after the branch lands.
```

Named skills `write-loop-exits-first` and `repo-handoff-doc-required` are not files in this worktree or `~/.grok/skills`. This card, the drop-in exits, and `docs/ops/HANDOFF-mvp-dogfood6-1031.md` are the binding. Decision logged.

## Drop-in exits (check before every item)

1. Wall cap: 8 hours from 2026-11-01T02:33:54Z, or Sunday 2026-11-01 18:00 PT (2026-11-02T02:00Z). Leave 20 minutes for the handoff.
2. Lane empty: no item left that fits this lane and these rules.
3. No progress: the same failure twice with no new information, or 3 items in a row skipped. Survey skips before item 01 do not count.
4. Host pressure: MemAvailable under 16 GiB, or load over 64 (2 x 32 cores) for 5 minutes. Pause 10 minutes, then stop if it persists.
5. Red base: record tests that fail on the base and skip that area. Do not stop the lane.

Host at the exit card: MemAvailable about 54 GiB (56779348 kB at 2026-11-01T02:33:54Z). Load about 3.66 on 32 cores. Not under pressure. `Runner.Worker` was pid 1511538 at launch and was gone before the first test.

## Phases

Overview: Land six small cloud builds sourced from the dogfood4 follow-up (symlink writes still follow the target) and the same contract on free files. One `./pfy build` per item, never `--local`. Receipt JSON under `eval/mvp-1031/dogfood6/`. Human-accept or reject each result. The lead runs the builds in order on this branch. Product edits land only by an accepted cherry-pick. The red behavior test is planted before the clone.

- exits | docs/ops/RUN-LOG-mvp-dogfood6-1031.md, docs/ops/AUTONOMOUS-DECISIONS-mvp-dogfood6-1031.md | both files exist and are pushed before the first build | none | lead
- 01 hermes-driver-symlink | pfylib/hermes_bot_driver.py, tests/test_hermes_driver_symlink.py, eval/mvp-1031/dogfood6/01-hermes-driver-symlink/ | `_write` and `_config` replace a symlink and leave the target bytes; a regular file still updates | exits | lead
- 02 attach-session-symlink | pfylib/attach.py, tests/test_attach_session_symlink.py, eval/mvp-1031/dogfood6/02-attach-session-symlink/ | session reach write replaces a symlink; read does not return the target text | 01 | lead
- 03 attach-pid-symlink | pfylib/attach.py, tests/test_attach_pid_symlink.py, eval/mvp-1031/dogfood6/03-attach-pid-symlink/ | terminal pid write replaces a symlink; read does not return the target pid | 02 | lead
- 04 attach-receipt-symlink | pfylib/attach.py, tests/test_attach_receipt_symlink.py, eval/mvp-1031/dogfood6/04-attach-receipt-symlink/ | spawn receipt write replaces a symlink and leaves the target bytes | 03 | lead
- 05 hermes-arm-symlink | examples/hermes-bakeoff/hermes_arm.py, tests/test_hermes_arm_symlink.py, eval/mvp-1031/dogfood6/05-hermes-arm-symlink/ | `_write_config` replaces `config.yaml` when it is a symlink | 04 | lead
- 06 opencode-arm-symlink | examples/hermes-bakeoff/opencode_arm.py, tests/test_opencode_arm_symlink.py, eval/mvp-1031/dogfood6/06-opencode-arm-symlink/ | `_write_config` replaces `opencode.json` when it is a symlink | 05 | lead
- 07 think-proxy-symlink | examples/hermes-bakeoff/think_proxy.py, tests/test_think_proxy_symlink.py, eval/mvp-1031/dogfood6/07-think-proxy-symlink/ | `write_forced_log` replaces a symlink and leaves the target bytes | 06 | lead
- 08 make-tasks-symlink | examples/hermes-bakeoff/make_tasks.py, tests/test_make_tasks_symlink.py, eval/mvp-1031/dogfood6/08-make-tasks-symlink/ | `main` replaces `OUT` when it is a symlink | 07 | lead
- handoff | docs/ops/HANDOFF-mvp-dogfood6-1031.md, this log | state line, push | always last | lead

These six builds share one branch, so they are one workstream. The lead runs them. No parallel implementer.

Risks:

- Review diff cap is 12000 characters. Each task is one file and one helper. Mitigation: reject a diff that edits a second product file or a test.
- A model that edits the planted test trips `tests-tampered` because the test is in the clone HEAD and `--writable-test` is not passed.
- Full `unittest discover` would take the shared heavy lock. Mitigation: `--test-cmd` is one module.
- The throwaway clone is `tmp/target-<n>` inside this worktree. Never Mark's checkout and never another lane's worktree.
- Secrets in receipts. Mitigation: class-only scan before commit. Never print a matched value.
- cloud347 owns `scripts/pfy_build_cloud.py` and `scripts/pfy_build_local.py`. flake-harness2 owns `tests/test_harness2_local_stage.py`. Mitigation: do not edit those files.
- A cloud receipt can contain an em dash. Mitigation: replace an em dash in prose with " - " before commit; do not change status, exit, or review.

## Task queue

Each build: throwaway clone under `tmp/target-<n>`, `./pfy build` with `--repo` that clone, `--base HEAD`, `--retries 1`, `--timeout 900`, a focused `--test-cmd`, and `--receipt-dir` at `eval/mvp-1031/dogfood6/<n>-<slug>/`. No `--local`. No `--writable-test`. `git clone --local` is a git transport flag for the throwaway clone, not `./pfy build --local`.

| n | slug | source | file | why it fits |
| --- | --- | --- | --- | --- |
| 01 | hermes-driver-symlink | dogfood4 follow-up: `write_text` follows a symlink | pfylib/hermes_bot_driver.py | no other branch has changed this blob since integrate |
| 02 | attach-session-symlink | same follow-up, session reach | pfylib/attach.py | same, public read and write |
| 03 | attach-pid-symlink | same follow-up, terminal pid | pfylib/attach.py | after 02, so the clone has the session helper |
| 04 | attach-receipt-symlink | same follow-up, spawn receipt | pfylib/attach.py | after 03 |
| 05 | hermes-arm-symlink | same contract, bake-off config | examples/hermes-bakeoff/hermes_arm.py | blob matches integrate on every commit |
| 06 | opencode-arm-symlink | same contract, bake-off opencode.json | examples/hermes-bakeoff/opencode_arm.py | checked free before the build |
| 07 | think-proxy-symlink | same contract, forced-log writer | examples/hermes-bakeoff/think_proxy.py | blob matches every commit; checked free |
| 08 | make-tasks-symlink | same contract, task-file writer | examples/hermes-bakeoff/make_tasks.py | last build in the turn cap of 8 |

## Items

item | commit | tests | result
01 hermes-driver-symlink | ebb808d | tests.test_hermes_driver_symlink 4 OK | accept
02 attach-session-symlink | 29ee1cc | tests.test_attach_session_symlink tests.test_attach 38 OK | accept
03 attach-pid-symlink | 3675945 | tests.test_attach_pid_symlink tests.test_attach_session_symlink tests.test_attach 42 OK | accept
04 attach-receipt-symlink | 1c100a5 | tests.test_attach_receipt_symlink tests.test_attach_pid_symlink tests.test_attach_session_symlink tests.test_attach 46 OK | accept
05 hermes-arm-symlink | 839ae5e | tests.test_hermes_arm_symlink tests.test_hermes_bakeoff 35 OK (1 skipped) | accept
06 opencode-arm-symlink | 51ed297 | tests.test_opencode_arm_symlink tests.test_hermes_bakeoff 35 OK (1 skipped) | accept
07 think-proxy-symlink | 4340a72 | tests.test_think_proxy_symlink tests.test_hermes_bakeoff 35 OK (1 skipped) | accept
08 make-tasks-symlink | a7008f4 | tests.test_make_tasks_symlink tests.test_hermes_bakeoff 35 OK (1 skipped) | accept

## Survey skips

Recorded before item 01. They do not count as a no-progress streak. Detail is in the decisions file.
