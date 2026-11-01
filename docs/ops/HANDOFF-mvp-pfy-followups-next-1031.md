# Handoff mvp-pfy-followups-next-1031

Branch: `bot/mvp-pfy-followups-next-1031`
Worktree: `/home/mark/DEVELOP/pfy-mentat/tmp/mvp-pfy-followups-next-1031`
Base: `origin/main` `c0d38afc0f21376e01d0aa57de31d29c2b21d2ca`
Exit: lane empty (2026-11-01T02:16:12Z). Wall cap was 2026-11-01T09:34:35Z. Host was not pressured.
Decisions: `docs/ops/AUTONOMOUS-DECISIONS-mvp-pfy-followups-next-1031.md`
Run log: `docs/ops/RUN-LOG-mvp-pfy-followups-next-1031.md`

The tip of this branch is the commit that adds this handoff. Item SHAs below are the fix commits, already pushed.

## Item table

| Source | Item | Status at main | Fix SHA | Test |
| --- | --- | --- | --- | --- |
| #300 fix2 deferred 4 | smolvm evidence: stderr `Pulling image` wins when a guest cache line is also present; cache-only still counts | open | `96a5b8f` | `tests.test_x_intake_smoke_109_111`: 13 OK in 3.180s |
| #300 fix2 deferred 2 | overtime daemon-stop timeout with no lock fails the smoke | open | `d97f0c2` | `tests.test_x_intake_smoke_112_114`: 8 OK in 9.831s |
| #300 fix2 deferred 1 | overtime `new` and festival `fest --version` name the step | open | `80a233f` | `tests.test_x_intake_smoke_112_114`: 8 OK in 9.799s |
| #300 fix2 deferred 1 | openqodex `review`, `review --agent`, `review --finalize`, and `git <sub>` name the step | open | `b3e7dd4` | `tests.test_x_intake_smoke_115_116`: 4 OK in 1.769s |
| #300 fix2 deferred 3 | 117 and 119 tests write receipts under a temp dir | open | `34de313` | 117 + 119 + `tests.test_x_intake_receipts_117_119`: 21 OK in 9.874s |
| #300 fix2 deferred 3 | 098-100 and 103-111 tests write receipts under a temp dir | open | `39d76d0` | those two modules: 12 OK in 1.943s |
| mvp2 t2, same lane after the deferred list | 119 `tree_sig` hashes file content | open (size and mtime) | `20ca8ca` | `tests.test_x_intake_tree_sig_content` + 119 module: 14 OK in 8.274s |
| mvp2 t6, same lane | 112, 115, and 117 `tree_sig` hash file content | open (size and mtime) | `abeed59` | content test + those three modules: 20 OK in 12.937s |

#300 items 1-11 and fix rounds 1-2 (pin, `scrub_env`, shared `timeout_reason`, receipt dir for 112 and 115) were already on `origin/main`. `origin/bot/pfy-followups-1030` is contained in main and did not take the deferred list.

## Skipped

- #303 OpenLore `analyze` exits 0 when its index panics: already mitigated on main. The smoke ranks `applyDiscount`, uses a writable `TMPDIR`, and sets `OPENLORE_NO_UPDATE_NOTIFIER=1`. Decision 5. The 2026-10-17 handoff round 2 already records full suite 421 OK and catalog_check PASS.
- #303 "catalog_check and the full suite were not run on its head": closed by that same round 2 record. This lane still ran catalog_check (below). A full `unittest discover` was not repeated.
- #300 item 12 live smolvm digest: blocked. `~/DEVELOP/pfy-mentat/tmp/smolvm/smolvm` is absent. `/dev/kvm` exists. No download. Decision 6.
- #303 recommended next steps (Harness Score eval-auto across other repos, OpenLore versus codebase-memory, hal0 only if Mark wants a packaged runtime) and the LATER list: other checkouts, a model comparison, or Mark. Decision 8.
- Smokes 122 and 128 stay as they are (decision 7). Smokes 148 and 149 still sign size and mtime. They are later intakes, outside mvp2 t2 and t6. Decision 8.

No three-skip streak. The skips above were already-done or blocked, and the taken items landed.

## Test evidence

- `python3 scripts/catalog_check.py` at 2026-11-01T02:11:53Z: PASS. n_json=8, toolsets=8, linked=2, catalog_tool null 6, tools_md=52, stage_cards=52, i1_cards_open=0, stage_only=4 (Exo, LiveKit, Pipecat, claude-code-unified-agents). Exit 0.
- `nice -n 19 python3 -m unittest` on all 21 `tests/test_x_intake*.py` modules: Ran 460 tests in 219.082s, OK (skipped=1). Exit 0. `TMPDIR` was this worktree's `tmp/`.
- During that run, two receipts printed `{"status": "FAIL", "failed": ["real_home_unchanged"]}`. Those lines are the 148 and 149 negative-path tests, which require that key. The suite result is OK.
- Pregate not run: this lane's drop-in forbids `scripts/pregate.sh`.
- No local model. No `scripts/pregate.sh`. No full discover.

## How each change fails and recovers

- d4. Fail: stderr has `Pulling image <ref>` and stdout has a cache line, and the evidence was the cache line. Recover: the stderr pull is recorded. A cache-only stdout line is still evidence. Missing evidence still fails the smoke.
- d2. Fail: `daemon stop` times out and `overtimed.lock` is already gone, and the smoke exited 0 with "daemon stopped". Recover: exit 1 and the reason is `overtime daemon stop timeout after <seconds>s`. A timeout already named on `new` is kept when the stop in `finally` also times out.
- d1 overtime and festival. Fail: the reason was `overtime timeout` or `festival timeout`. Recover: `new timeout after <seconds>s` and `version timeout after <seconds>s`. Other overtime timeouts stay labeled `overtime`.
- d1 openqodex. Fail: the reason was `openqodex timeout after 1s` when `review` timed out. Recover: the step name is `review`, `review --agent`, `review --finalize`, or `git <sub>`. `main` keeps a reason the step already set.
- d3. Fail: wrong-version and skip-path tests wrote `pipelines/smoke/<entry>/latest.json` inside the repo. Those paths are gitignored, so a clean porcelain check missed them. Recover: `PFY_SMOKE_RECEIPT_DIR` is a temp dir. The 117 and 119 acceptance test asserts the repo receipt bytes are unchanged. kolibri1 stays tracked (`git check-ignore` returns 1).
- tree_sig (119, then 112, 115, 117). Fail: an mtime-only touch changed the signature, so a real-HOME check false-failed, and a same-size edit that restored mtime was invisible. An unreadable file was skipped. Recover: the signature hashes content in 1 MiB chunks, ignores mtime, changes on the byte edit, and records `path:unreadable` until the file can be opened again.

## Cross-lane requests

None. Every edit stayed in the x-intake smoke modules, their tests, and this run's docs.

## Gate

Runtime smoke changes: Tester plus Reviewer on `bot/mvp-pfy-followups-next-1031`.

Pregate plus Reviewer would cover a docs-only or test-only branch. This branch changes smoke runtime, so the gate is Tester plus Reviewer. Pregate was not run.

## Next step

Review and test this branch. Leave the merge to the owner. Live smolvm stays blocked until `~/DEVELOP/pfy-mentat/tmp/smolvm/smolvm` exists. The parked #303 trials need a lane that can use the other product repos.
