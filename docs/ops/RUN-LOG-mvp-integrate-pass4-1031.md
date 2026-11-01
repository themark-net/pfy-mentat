# RUN-LOG mvp-integrate-pass4-1031

Launch: 2026-11-01T02:15:51Z
Worktree: ~/DEVELOP/pfy-mentat/tmp/mvp-integrate-pass4-1031
Branch: bot/mvp-integrate-pass4-1031
HEAD at plan time: 18df7e6 (drop-in only, on top of base). Pushed tip before this card: 04b84d0 (same drop-in plus the G0 wait line in the drop-in file).
Base: origin/bot/mvp-integrate-1031 @ 1dee0b9 (ancestor of HEAD). Do not push that branch.
Wall cap: 2026-11-01T10:15:51Z (8h from launch). Calendar cap 2026-11-02T02:00Z is later, so the 8h cap binds. Stop starting new items at 2026-11-01T09:55:51Z so the handoff has 20 minutes.
Host at launch: MemAvailable 56303836 kB (about 53.7 GiB), load 6.06, nproc 32. Both are inside the pressure limits (16 GiB, load 64).

## LOOP EXIT CARD

```text
LOOP EXIT CARD
Goal (success criteria):     Merge the finished wave 6-7 lanes named in the drop-in, in order, with merge commits. Skip unfinished or already contained tips. Targeted tests after each merge. One full unittest discover under the heavy lock with in-repo TMPDIR, target 0 failures. One cloud-default ./pfy build demo on a 1-2 file fix, receipt at eval/mvp-1031/demo-receipt-pass4.json. Handoff written.
1 Goal met:                  Merge table complete, suite summary shows 0 failures (or only red-base failures recorded), demo receipt file exists, handoff committed and pushed.
2 Turn cap:                  10 named merge slots, plus 1 suite, plus 1 demo, plus at most 2 fixes for failures the merges caused. No unrelated MVP backlog after that.
3 Budget cap:                No local model. At most one cloud-default ./pfy build. No second cloud build once a receipt exists.
4 Wall clock:                2026-11-01T10:15:51Z. Handoff buffer starts 2026-11-01T09:55:51Z.
5 No progress:               Same failure twice with no new information, or 3 items in a row skipped.
6 Human interrupt:           User stop. Do not ask questions. No merge to main, no PR, no force push, no tags.
7 Error threshold:           Same failure twice, or 3 consecutive same-class failures. Record and stop.
8 External event:            Named tip already contained in HEAD, or its run log has no final state line (skip that tip). Never merge mvp3 branches, backlog branches, or bot/mvp-probe-fix2-1031.
Loop type:                   goal
Human gate:                  None during the run. After the run: Tester plus Reviewer if runtime code changed; pregate plus Reviewer if the delta is docs, eval, or tests only. This drop-in says do not run scripts/pregate.sh.
```

Drop-in exits, also binding, checked before every item:

1. Wall cap (above).
2. Lane empty: no named branch left that is finished and not contained, and the suite plus demo are done or recorded. Do not pull unrelated TODO rows into this lane.
3. No progress: same failure twice with no new information, or 3 skips in a row.
4. Host pressure: MemAvailable under 16 GiB, or load over 64 for 5 minutes. Pause 10 minutes, then stop if it persists.
5. Red base: tests that fail before this lane's change. Record them and skip that area. Do not stop the lane.

A lane counts as finished only when its own `docs/ops/RUN-LOG-<slug>.md` has a final line that starts with `state:` and the value begins with `DONE`, `lane empty`, or `wall cap`. Any other ending, or a missing log, is not finished.

## Phases

Overview: Integrate the finished wave 6-7 bot branches into `bot/mvp-integrate-pass4-1031` with merge commits, prove each merge with niced targeted tests, then run one full suite under the heavy lock and one small cloud build demo. The lead does the merges in order. They share the whole tree, so they are not parallel workstreams. The only sub-agent is project-map.

Phases:

- exits | docs/ops/RUN-LOG-mvp-integrate-pass4-1031.md, docs/ops/AUTONOMOUS-DECISIONS-mvp-integrate-pass4-1031.md | both files exist with this card before any merge | none | general
- survey | remote tips and their run logs | each of the 10 named branches marked merge, skip-unfinished, skip-contained, or missing | exits | general
- merge-01 localbench-tmpdir | whole tree | merge commit or logged skip, then niced tests of touched modules | survey | general, lead
- merge-02 probe-int | whole tree | same | merge-01 | general, lead
- merge-03 pass3-review | whole tree | same | merge-02 | general, lead
- merge-04 dogfood3 | whole tree | same | merge-03 | general, lead
- merge-05 hermes-check | whole tree | same | merge-04 | general, lead
- merge-06 timeoutfix | whole tree | same | merge-05 | general, lead
- merge-07 cloud-perf | whole tree | same | merge-06 | general, lead
- merge-08 selfhost2 | whole tree | same | merge-07 | general, lead
- merge-09 mutate-cloud2 | whole tree | same | merge-08 | general, lead
- merge-10 review-quality | whole tree | same | merge-09 | general, lead
- suite | tests/ | nice -n 19 unittest discover under flock on ~/DEVELOP/pfy-mentat/tmp/heavy-1030.lock with TMPDIR in this worktree tmp/. Target 0 failures. Fix only failures a merge caused. | all merges | general, lead
- demo | eval/mvp-1031/demo-receipt-pass4.json | one cloud-default ./pfy build on a small real 1-2 file fix | suite | general, lead
- handoff | docs/ops/HANDOFF-mvp-integrate-pass4-1031.md and the final state line in this log | committed and pushed. Do not merge to main. | demo, or any earlier exit | general, lead

Risks:

- Merging a lane that is still running. Mitigation: require the final `state:` line defined above before `git merge`.
- A conflict drops behavior from one side. Mitigation: keep both sides when the texts can sit together. When they cannot, keep the incoming finished lane's behavior and its tests, and log the file. Run that module's tests.
- The full suite collides with other heavy jobs. Mitigation: flock the shared heavy lock, nice -n 19, TMPDIR under this worktree tmp/.
- The cloud demo hangs or spends twice. Mitigation: one 1-2 file fix, bounded wait, no `--local`, no second demo after a receipt exists.
- Host pressure mid-suite. Mitigation: read MemAvailable and load before each item. Pause 10 minutes once if pressure holds, then stop if it is still there.

## Survey (2026-11-01T02:45Z)

Fetched the ten named tips. Each run log's last non-empty line matches `state: DONE`, `state: lane empty`, or `state: wall cap`. None of the tips is an ancestor of HEAD `0e36b7b`. Pairwise `git merge-tree` against that HEAD was clean. Four lanes edit `scripts/pfy_build_cloud.py` (probe-int, timeoutfix, cloud-perf, review-quality). Those can still conflict with each other after the earlier merge lands. probe-int and timeoutfix also both edit `tests/test_pfy_build_cloud.py`.

| order | branch | tip | action |
|---|---|---|---|
| 1 | origin/bot/mvp-localbench-tmpdir-1031 | 76fd6a1 | merge |
| 2 | origin/bot/mvp-probe-int-1031 | b2cbd4f | merge |
| 3 | origin/bot/mvp-pass3-review-1031 | cc338de | merge |
| 4 | origin/bot/mvp-dogfood3-1031 | f50192a | merge |
| 5 | origin/bot/mvp-hermes-check-1031 | 61396e4 | merge |
| 6 | origin/bot/mvp-timeoutfix-1031 | ef622a6 | merge |
| 7 | origin/bot/mvp-cloud-perf-1031 | 7c7ca94 | merge |
| 8 | origin/bot/mvp-selfhost2-1031 | c51c0b3 | merge |
| 9 | origin/bot/mvp-mutate-cloud2-1031 | 82a52ce | merge |
| 10 | origin/bot/mvp-review-quality-1031 | 0930690 | merge |

Not in the list, and not merged: mvp3 branches, backlog branches, `bot/mvp-probe-fix2-1031`.

## Item log

item | commit | tests | result

exits | 0e36b7b | none | exit card pushed before any merge
survey | d98ed10 | git fetch plus run-log tail and merge-tree | all ten finished, none contained, all clean vs 0e36b7b
merge localbench-tmpdir | 2279366 | nice -n 19 python3 -m unittest tests.test_local_bench | tip 76fd6a1, clean, 18 OK in 1.343s
merge probe-int | 450c339 | nice -n 19 python3 -m unittest tests.test_pfy_build_cloud | tip b2cbd4f, clean, 67 OK in 21.580s
merge pass3-review | 3122349 | nice -n 19 python3 -m unittest tests.test_workflow_image_pin | tip cc338de, clean, 33 OK in 20.244s
merge dogfood3 | 8e9354d | nice -n 19 python3 -m unittest tests.test_smoke_098_bad_timeout tests.test_smoke_103_bad_timeout tests.test_smoke_106_bad_timeout tests.test_smoke_128_bad_timeout tests.test_smoke_131_bad_timeout tests.test_x_intake_smoke_098_100 tests.test_x_intake_smoke_103_105 tests.test_x_intake_smoke_106_108 tests.test_x_intake_smoke_128_130 tests.test_x_intake_smoke_131_133 | tip f50192a, clean, 119 OK in 29.411s
merge hermes-check | 7689bcb | nice -n 19 python3 -m unittest tests.test_hermes_bakeoff | tip 61396e4, clean, 32 OK skipped=1 in 3.187s
merge timeoutfix | d6c2cbf | nice -n 19 python3 -m unittest tests.test_pfy_build_cloud tests.test_pfy_build_p | tip ef622a6, 3 conflicts in scripts/pfy_build_cloud.py, both behaviors kept, 88 OK skipped=1 in 32.644s
merge cloud-perf | 6b89b7a | nice -n 19 python3 -m unittest tests.test_pfy_build_phase_clock tests.test_pfy_build_cloud tests.test_pfy_build_p | tip 7c7ca94, 6 conflicts in scripts/pfy_build_cloud.py, both behaviors kept, 99 OK skipped=1 in 44.249s
merge selfhost2 | 38002cb | nice -n 19 python3 -m unittest tests.test_adapter_install_symlink tests.test_adapter_symlink_file_ops tests.test_adapter_tree_hash_symlink tests.test_agentdescent_snap tests.test_apply_mcp_symlink tests.test_backup_once_symlink tests.test_harness2_surface_symlink tests.test_hedge_ledger_symlink tests.test_kolibri_receipt_absolute tests.test_setup_ledger_symlink tests.test_smoke_137_tree_hash_symlink tests.test_smoke_140_tree_hash_symlink tests.test_typed_decisions_receipt_absolute tests.test_x_intake_smoke_137_139 tests.test_x_intake_smoke_140_142 tests.test_hedge tests.test_harness2_local_surface tests.test_agentdescent_trial_harness tests.test_pfy_launcher_p1 | tip c51c0b3, clean, 150 OK in 70.509s then 112 OK in 4.038s
merge mutate-cloud2 | e8534cf | nice -n 19 python3 -m unittest tests.test_mut_cloud2_harness tests.test_mut_cloud2_survivors tests.test_mut_cloud_harness tests.test_mut_cloud_survivors | tip 82a52ce, clean, anchors C9 C22 C38 C39 retargeted in 7ad4a40, 17 OK in 13.433s
merge review-quality | 2fd2625 | nice -n 19 python3 -m unittest tests.test_review_quality_replay tests.test_pfy_build_cloud | tip 0930690, clean, diffs b09 and g07 retargeted in da6542c, replay 7 OK in 0.275s, cloud tests passed in the 79-test run (1 replay apply failure before the retarget)
catch-up fetch | 5a146b8 | git fetch of the ten tips | 2026-11-01T03:16Z all ten tips still contained. No extra merge. Pregate not started by this lane.
suite | 3c712b1 tree | TMPDIR=$PWD/tmp/suite-pass4 nice -n 19 flock heavy lock python3 -m unittest discover -s tests -t . | Ran 1320 in 938.736s. Failures 1, skipped 16. 2026-11-01T03:31:34Z to 2026-11-01T03:47:13Z. G0 was idle. This lane did not run pregate.
built-by subjects | pending | nice -n 19 python3 -m unittest tests.test_selfhost_1031_log | 3 OK in 0.114s. Base 1dee0b9 of the same test was OK, so the failure came in with the merges. Accept the hard 72 cut, the current ellipsis subject, and 13 amended selfhost2 cherry-picks. A third subject still fails.
