# RUN LOG mvp-dogfood5-1031

Lane mvp-dogfood5-1031. Branch `bot/mvp-dogfood5-1031`. Worktree `~/DEVELOP/pfy-mentat/tmp/mvp-dogfood5-1031`. Base `origin/bot/mvp-integrate-1031` at `1dee0b91bda11ba1fcda87819423437a3f10f289`.

Launch clock: 2026-11-01T01:32:49Z (grok process etime at 2026-11-01T01:44:09Z was 11:20). Wall cap: 2026-11-01T09:32:49Z. New items stop by 2026-11-01T09:12:49Z. Calendar cap 2026-11-02T02:00Z is later, so the 8 hour cap wins. Leave 20 minutes for the handoff.

```text
LOOP EXIT CARD
Goal (success criteria): six cloud ./pfy build rows in eval/mvp-1031/dogfood5/, each human-accepted or rejected with a reason, pass rate in the handoff
1 Goal met:              handoff 6-row table; targeted unittest green for every accept
2 Turn cap:              8 item attempts (the six builds plus two recovery attempts)
3 Budget cap:            cloud Grok only, no --local, no spend outside ./pfy build
4 Wall clock:            2026-11-01T09:32:49Z, stop new items at 09:12:49Z
5 No-progress:           same failure twice with no new information, or 3 items in a row skipped
6 Human interrupt:       user stop
7 Error threshold:       3 consecutive same failure, then stop
8 External event:        item already on this tip or on origin/main, or a live lane commits the same function
Loop type:               goal
Human gate:              no merge, no PR. Tester plus Reviewer after the branch lands.
```

Overview: Land six small cloud builds sourced from open FINDING and follow-up rows. One `./pfy build` per item, never `--local`. Receipt JSON under `eval/mvp-1031/dogfood5/`. Human-accept or reject each result. The lead runs the builds in order on this branch.

Phases:

- exits | docs/ops/RUN-LOG-mvp-dogfood5-1031.md, docs/ops/AUTONOMOUS-DECISIONS-mvp-dogfood5-1031.md | both files exist before the first build | none | lead
- 01 diff-aims | scripts/pfy_build_cloud.py diff_aims_at_root, tests/test_cloud_diff_aims_at_root.py, eval/mvp-1031/dogfood5/01-diff-aims/ | deletion of `rm -rf /` can pass; an added `rm -rf /tmp/x` stays rejected | exits | lead
- 02 env-bak | scripts/pfy_build_cloud.py _protected, tests/test_cloud_env_bak_protected.py, eval/mvp-1031/dogfood5/02-env-bak/ | `.env.bak` is protected-path-changed and the marker stays out of the receipt; `.env.example` can land | 01 | lead
- 03 reap-oserror | scripts/pfy_build_cloud.py reap, tests/test_cloud_reap_receipt_oserror.py, eval/mvp-1031/dogfood5/03-reap-oserror/ | unwritable abort receipt returns exit 1; a writable dir still writes ABORTED and returns 0 | 02 | lead
- 04 smoke137-timeout | examples/x-intake-local/smoke_137_139.py, tests/test_smoke_137_bad_timeout.py, eval/mvp-1031/dogfood5/04-smoke137-timeout/ | bad PFY_XINTAKE_TIMEOUT exits 2 before neatroots lookup; unset still reports neatroots not found | 03 | lead
- 05 agenc-smoke-tmp | bootstrap/agenc/smoke.sh, tests/test_agenc_smoke_tmpdir.py, eval/mvp-1031/dogfood5/05-agenc-smoke-tmp/ | the LLM tee path stays under TMPDIR | 04 | lead
- 06 agenc-install-tmp | bootstrap/agenc/install.sh, tests/test_agenc_install_tmpdir.py, eval/mvp-1031/dogfood5/06-agenc-install-tmp/ | the Node tarball path stays under TMPDIR | 05 | lead
- handoff | docs/ops/HANDOFF-mvp-dogfood5-1031.md, this log | state line, push | always last | lead

Risks:

- probe-int is live and its drop-in also names scripts/pfy_build_cloud.py. Mitigation: edit only the three named functions, and skip the rest of that file if their worktree shows a diff on it before this lane commits.
- selfhost2 changed smoke_137 tree_hash. Mitigation: the timeout edit stays in main and the docstring, and imports timeout_problem from smoke_140_142.
- A cloud receipt can contain an em dash or a secret-shaped token. Mitigation: scan before commit; replace an em dash in prose with " - "; do not commit a real secret.
- Host pressure or a busy runner. Mitigation: targeted tests only; pregate at most once at the end if Runner.Worker is idle and the heavy lock is free.

Item log (append one line each): `item | commit | tests | result`

Survey skips, recorded before item 01, do not count as a no-progress streak. Detail is in the decisions file.

2026-11-01T01:47:00Z: pass3 findings 3, 4, and 7 skipped. probe-int modified `scripts/pfy_build_cloud.py` before this lane committed a product edit. The red test was not pushed.

2026-11-01T01:52:00Z: item 04 red test `tests.test_smoke_137_bad_timeout` FAILED (failures=5). Unset and empty still report the neatroots prereq miss. Cloud build starts next.
