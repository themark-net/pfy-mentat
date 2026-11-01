# Handoff: mvp-dogfood5-1031

Lane mvp-dogfood5-1031, wave 7. Branch `bot/mvp-dogfood5-1031`. Worktree `~/DEVELOP/pfy-mentat/tmp/mvp-dogfood5-1031`. Base `origin/bot/mvp-integrate-1031` at `1dee0b91bda11ba1fcda87819423437a3f10f289`. Drop-in `59efe4e31f170ce33a27929b664b534e49afbfbf`. Exit card `e280fb1474e9a4be71e7ffad0c645fb424f97a91`.

Exit: lane empty. Three cloud `./pfy build` items accepted. One human reject was retried and the retry was accepted. Pass rate of the three final cloud items is 3/3. Counting the install reject as its own human verdict, the accept rate is 3/4. No merge, no PR, no tag. No `--local`. `scripts/pregate.sh` was not run.

## Six rows

| n | task | exit | attempts | review | wall s | commit | human |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | diff-aims | skipped | 0 | | | none | skip, probe-int owns cloud.py |
| 02 | env-bak | skipped | 0 | | | none | skip, same file |
| 03 | reap-oserror | skipped | 0 | | | none | skip, same file |
| 04 | smoke137-timeout | 0 | 1 | accept | 95 | d75d407865ef | accept |
| 05 | agenc-smoke-tmp | 0 | 1 | accept | 118 | ef1f2c26fc5f | accept |
| 06 | agenc-install-tmp | 0 | 1 | accept | 116 | 482805021d01 | accept |

Pass rate 3/3 on rows 04-06. Rows 01-03 did not call `./pfy build`. Row 04 had an earlier runner failure (`commit-recheck-failed`, 296s, review accept, branch not kept). Row 06 had an earlier human reject (cloud `4def314cd67a`, wall 121s, review accept) that was not cherry-picked.

## Items done

Each accept is a product commit by `pfy-cloud-build <pfy-cloud-build@localhost>` plus a Built-by trailer. The red behavior test is the parent commit. Receipts live under `eval/mvp-1031/dogfood5/`.

- 04 smoke_137. Red tests `aa53cefe957ff67abf2a30f71cf5cf43283e1364` and `7d7c5f49bafc0337bce23d1afd999a1667bfc0af`. Product `d75d407865efcda24be06e1b895fae8950b74faf`. Cloud `cc05a173ea0bee987de4f519e602a29cc0cbd4ee`. Imports `timeout_problem` from `smoke_140_142`. It does not copy the function. `tree_hash` is untouched. After land: `tests.test_smoke_137_bad_timeout` and `tests.test_x_intake_smoke_137_139`, 57 OK.
- 05 agenc smoke tee. Red test `d29136701c6ce061c8d4ae66cd129eb9f1e487bb`. Product `ef1f2c26fc5f2fc6f29bf5eb0581e2abf1565775`. Cloud `01115aaf1c096ee155369b349081ebd003a7ab62`. `bootstrap/agenc/smoke.sh` only (4 insertions, 2 deletions). After land: `tests.test_agenc_smoke_tmpdir`, 2 OK.
- 06 agenc install tarball. Red tests `4cdfe78c6382fe4640250990d150fc4259ebc885` and `df8d34ffbbae457a854b9dbd968f3fead9d0d3b3`. Product `482805021d01d4bb95d6a6129891f1f9a2055242`. Cloud `bc672303791a7b5d3e45f1bfe009c38ded53c258`. Keeps `mkdir -p "$NODE_CACHE"` and puts the tarball under TMPDIR. After land: `tests.test_agenc_install_tmpdir`, 2 OK.

## Rejected attempts

- 04 attempt 1. Runner `commit-recheck-failed`, exit 1, two attempts, review accept both times, gate before 1 and after 0. The fresh extract has no `tmp/` directory, and the first test passed `dir=ROOT / "tmp"` without creating it. Receipt: `eval/mvp-1031/dogfood5/04-smoke137-recheck-fail/`. The retry test creates that directory. Failure class: test scratch directory missing on the fresh extract.
- 06 attempt 1. FINDING-D5-01. Cloud run exited 0, review accept, wall 121s, attempts 1. Cloud commit `4def314cd67a10d906153f44a3d32eaeda3d5143` stayed on `tmp/target-03`. The diff moved the tarball and deleted `mkdir -p "$NODE_CACHE"`, so `tar -C "$NODE_CACHE"` has no directory when TMPDIR is set. Receipt and `diff.patch` are in `eval/mvp-1031/dogfood5/06-agenc-install-reject/`. Failure class: extract directory dropped.

## How each change fails and recovers

- smoke_137. A set `PFY_XINTAKE_TIMEOUT` that is not a finite number of seconds > 0 (`abc`, `0`, `-1`, `nan`, `inf`) exits 2 before the entry. The receipt reason names `PFY_XINTAKE_TIMEOUT`. Unset or empty still calls the entry, so a missing neatroots app reports `neatroots not found ($NEATROOTS_APP or tmp/neatroots/app with neatroots/dist/cli.js); unpack the v0.2.9 neatroots.tar.gz there, see the handoff. Never run install.sh`.
- agenc smoke. With `AGENC_SMOKE_LLM=1`, a non-PONG answer exits 1 and the message names the log under TMPDIR. A PONG answer exits 0 and that log file holds the text. Unset TMPDIR uses `${ROOT}/tmp`. The run does not create `/tmp/agenc-smoke-llm.txt`.
- agenc install. An old node chooses `"${TMPDIR:-$NODE_CACHE}/${platform}.tar.xz"`. The test curl exits 1, so nothing is downloaded, and `NODE_CACHE` already exists for the later extract. A node at major 25 or newer returns before any tarball path is chosen.

Each planted module was red first. smoke_137 was `FAILED (failures=5)` with the neatroots prereq string. The agenc smoke module was `FAILED (failures=2)` with tee path `/tmp/agenc-smoke-llm.txt`. The install module was `FAILED (failures=1)` with `/tmp/node-v25.9.0-linux-x64.tar.xz`. The new-node install case passed on the red tree.

## Skipped

Survey skips, logged before item 01, do not count toward the 3-skip exit. Detail is `docs/ops/AUTONOMOUS-DECISIONS-mvp-dogfood5-1031.md`.

- realfail3 unwritable tmp and hung gate. Tests already on this tip.
- pass3 findings 1 and 2. Review code in `scripts/pfy_build_local.py`. This lane does not edit that file. `origin/bot/mvp-probe-fix2-1031` already has the symlink skip and `gate-modified-reviewed-file`.
- review-quality local `_review_prompt`. Same forbidden file. The cloud sentence is on `origin/bot/mvp-review-quality-1031`.
- pass3 findings 3, 4, and 7. At 01:47Z `mvp-probe-int-1031` had `scripts/pfy_build_cloud.py` modified, so the unpushed red test was reset and not pushed. At 02:16Z that worktree is clean and the grok process is gone, and the file still has the old root regex, the old `DEFAULT_PROTECT`, and reap's `except OSError: pass` before `return 0`. Their branch also carries a large cloud.py diff (build-busy and the hunks around it). This lane does not edit that file. The cross-lane request below stands.
- dogfood2 smoke files (`smoke_109` through `smoke_122`, `smoke_148`, `smoke_149`) and dogfood3's landed smokes (`smoke_098`, `smoke_103`, `smoke_106`, `smoke_128`, `smoke_131`). Those branches already changed them.
- `pipelines/dogfood/local-bench-5/run_runtime_matrix.sh` hardcoded `/tmp/rt-*.log` and `.stop`. mvp-localbench-tmpdir owns that script.
- smoke_149 `.cache/chroma` fingerprint and harness2 mode 751 prune. Both need a human cap or allowlist. OQ drafts are below. `docs/OPEN_QUESTIONS.md` was not edited.
- dogfood2 F1 subject cut. `commit_subject` on this tip already keeps whole words. F2 and F3 are receipt fields in `scripts/pfy_build_cloud.py`, which this lane is leaving to probe-int's branch.
- `command echo` and `busybox echo`. pass3 recorded that as not filed. A shell parser is out of scope.
- TODO rows T-0091, T-0094, T-0081, T-0064, T-0043, T-0062, T-0046, T-0016, T-0005. Parked, shelved, hardware, or an open OQ. dogfood4 is taking the open TODO code rows. `docs/TODO.md` was not edited.

## Test evidence

Targeted, niced, no full discover, no heavy lock:

- `tests.test_smoke_137_bad_timeout` `tests.test_x_intake_smoke_137_139`: 57 OK
- `tests.test_agenc_smoke_tmpdir`: 2 OK
- `tests.test_agenc_install_tmpdir`: 2 OK

Receipts were scanned before commit for AKIA, BEGIN PRIVATE, ghp_, xai-, sk-, and Bearer. No match. Added lines in the three product diffs have no em dash and no en dash.

## Cross-lane requests

probe-int, or the integrator who merges `bot/mvp-probe-int-1031`: apply these on that branch's `scripts/pfy_build_cloud.py`, where the three bugs are still present.

1. Finding 3. `diff_aims_at_root` should match added lines only (a line that starts with `+` and does not start with `+++`). Deleting `rm -rf /` can pass. An added `rm -rf /tmp/x` stays rejected. A red test was written here, proved the deletion is rejected today, and was reset off this branch before any push.
2. Finding 4. Treat basename `.env` and `.env.*` as protected, with `.env.example` left unprotected. `.env.bak` must be `protected-path-changed`.
3. Finding 7. When reap must write an ABORTED receipt and that write raises `OSError`, return exit 1. A writable directory still writes ABORTED and returns 0.

mvp-localbench-tmpdir: `pipelines/dogfood/local-bench-5/run_runtime_matrix.sh` still writes `/tmp/rt-${LABEL}-${BACKEND}.log` and a matching `.stop` file. This lane did not edit it.

## Gate

Tester plus Reviewer. The three accepts change a smoke main and two bootstrap scripts. Docs, receipts, and the planted tests ride along. Pregate was not run.

pregate not run: host busy.

At 2026-11-01T02:15:33Z, `pgrep -f 'Runner[.]Worker'` was empty and MemAvailable was about 54 GiB, load about 6.5 on 32 cores. `flock -n ~/DEVELOP/pfy-mentat/tmp/heavy-1030.lock` failed. This lane did not wait on the lock. This lane's drop-in also says not to run `scripts/pregate.sh`.

## OQ draft

Do not file these in `docs/OPEN_QUESTIONS.md` from this lane.

- smoke_149 `home_sig` still reads `.cache/chroma` bodies. A bounded fingerprint needs a size cap written down before anyone implements it.
- harness2 mode 751 sandbox prune needs an allowlist. This lane does not invent one.

## Project map

`.project-map/index.html` was not drawn. dogfood4, backlog-fu, flake-harness2, integrate-pass4, and pfy-followups-next still had live grok processes at handoff. Same rate-limit choice as the exit card.

## Next step

Merge this branch only through the integrator, with Tester plus Reviewer on the smoke main and the two agenc scripts. Apply pass3 findings 3, 4, and 7 on top of probe-int's `scripts/pfy_build_cloud.py`. Leave `run_runtime_matrix.sh` to mvp-localbench-tmpdir. Run pregate when the heavy lock is free and `Runner.Worker` is idle.
