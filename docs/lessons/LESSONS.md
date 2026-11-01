# Lessons we learned ourselves

A log of lessons the org learned from its own work: runs, gates, failures and fixes. It does **not** hold ideas taken from the catalog (`catalog/entries`, `sources/`) or from other people's X posts. Those live in the catalog.

Rules for an entry:

- Short title, date, what happened (cite a commit, PR, issue or handoff doc), the lesson in one or two plain sentences, and where it is enforced now (a skill, a script, a doc or a test).
- No citation, no entry. Do not invent numbers. If a fix is still on a `bot/*` branch, say so.
- `posted: no|staged|yes` tracks the X post for the lesson. Posts are staged in [docs/x-staging/](../x-staging/README.md). Bots never post.
- Each entry has an anchor (`<a id="...">`). X staging files point at it with `lesson:`.

Commit links below go to `themark-net/pfy-mentat` unless another repo is named. Branch-only commits are linked on GitHub, not by relative path.

| # | Lesson | Date | posted |
|---|--------|------|--------|
| L01 | [An AI review counts only for the exact bytes it saw](#l01-review-exact-bytes) | 2026-10-31 | staged |
| L02 | [Every parallel run gets its own TMPDIR, HOME and caches](#l02-run-isolation) | 2026-10-31 | staged |
| L03 | [Tests that need git history skip visibly in a shallow clone](#l03-shallow-clone-skip) | 2026-10-31 | no |
| L04 | [Local models as the default dev env: NO-GO versus cloud](#l04-local-vs-cloud) | 2026-10-31 | staged |
| L05 | [Read model-size claims against real RAM and VRAM first](#l05-model-size-claims) | 2026-10-31 | staged |
| L06 | [A stray background service can silently eat the host](#l06-stray-service) | 2026-10-06 | no |
| L07 | [Bot usage is a budget, and Build usage is readable without the owner](#l07-usage-budget) | 2026-10-26 | no |
| L08 | [Paper results don't carry over to real trading](#l08-paper-vs-real) | 2026-10-17 | no |
| L09 | [Tautological tests plus surviving mutants prove nothing](#l09-mutants) | 2026-10-20 | no |
| L10 | [Skip PRs on our repos, gate a pinned SHA, merge main in](#l10-pinned-sha) | 2026-10-19 | no |
| L11 | [Relaunch loops need a state line](#l11-state-line) | 2026-11-01 | no |
| L12 | [Pin the CI runner image](#l12-pin-runner-image) | 2026-10-30 | no |
| L13 | [A tool run with HOME unset writes to the real home](#l13-tool-home) | 2026-10-19 | no |
| L14 | [A Reviewer FAILs product UI that has no design pack](#l14-design-pack) | 2026-10-06 | no |

---

<a id="l01-review-exact-bytes"></a>
### L01 An AI review counts only for the exact bytes it saw

- **Date:** 2026-10-31
- **What happened:** The Tester probed the local build's review-then-commit path on `bot/mvp3-review-retry` and found four ways a commit could carry bytes the reviewer never saw: a gate step that rewrote or chmod-ed a reviewed file after review ([29da017](https://github.com/themark-net/pfy-mentat/commit/29da017)), a hardlink whose other name was outside the worktree ([915edf0](https://github.com/themark-net/pfy-mentat/commit/915edf0)), symlinks followed out of the repo, and a prompt that sliced diffs at 8000 characters and showed binaries as "Binary files differ" ([3a550e5](https://github.com/themark-net/pfy-mentat/commit/3a550e5)). The probe-fix2 findings merged into mvp3 at [16f17d8](https://github.com/themark-net/pfy-mentat/commit/16f17d8); fix3 handoff at [ff8b881](https://github.com/themark-net/pfy-mentat/commit/ff8b881).
- **Lesson:** Treat a review as a contract on content, not on file names. Hash what was reviewed, hash what is committed, and refuse with a named reason if they differ or if the reviewer could not see the whole diff.
- **Enforced:** `scripts/pfy_build_local.py` and `tests/test_pfy_build_local_review.py` on `bot/mvp3-review-retry` (not on main yet); skill `commit-integrity-and-run-isolation` (Grok Bot org skill; pfy port at [4de54fc](https://github.com/themark-net/pfy-mentat/commit/4de54fc) on `bot/doctrine-commit-integrity-1031`).
- **posted:** staged (thread 1/5 to 5/5)

<a id="l02-run-isolation"></a>
### L02 Every parallel run gets its own TMPDIR, HOME and caches

- **Date:** 2026-10-31
- **What happened:** With about 10 dev lanes on nimo, harness2 stage tests failed in tearDown because `~/.cache/uv` changed under them while a pregate ran on the same host (CI run 41262832115, pregate at 16f17d8). They passed alone. Fix: [af1c104](https://github.com/themark-net/pfy-mentat/commit/af1c104). Related: smoke 149 temp dirs under the caller TMPDIR ([d591f2b](https://github.com/themark-net/pfy-mentat/commit/d591f2b)) and absolute bench log paths for an in-repo TMPDIR ([4ff2c67](https://github.com/themark-net/pfy-mentat/commit/4ff2c67)). Lane drop-in: `docs/build-dropins/mvp-flake-harness2-1031.md` items A and C ([1f1129d](https://github.com/themark-net/pfy-mentat/commit/1f1129d)).
- **Lesson:** A test that watches shared `/tmp`, `~/.cache` or the real HOME is flaky once more than one run shares the host. Give every run its own TMPDIR, HOME and tool caches, and do not run a local pregate while a CI job runs on the same host.
- **Enforced:** `tests/test_harness2_local_stage.py` (private HOME and UV_CACHE_DIR) and a `Runner.Worker` check that makes `scripts/pregate.sh` exit 3, both on `bot/mvp-flake-harness2-1031`; heavy jobs run under `flock ~/DEVELOP/pfy-mentat/tmp/heavy-1030.lock`; skill `commit-integrity-and-run-isolation` (run isolation rule).
- **posted:** staged (standalone C)

<a id="l03-shallow-clone-skip"></a>
### L03 Tests that need git history skip visibly in a shallow clone

- **Date:** 2026-10-31
- **What happened:** CI checks out at depth 1, so the docs hygiene check for old main SHAs could not find them. The first fix skipped that check in a shallow clone ([47dcd66](https://github.com/themark-net/pfy-mentat/commit/47dcd66), on main, backlog run that ended at 2a74482). A silent `return` still counted as a pass, so it became a named `skipTest` ([a0885ed](https://github.com/themark-net/pfy-mentat/commit/a0885ed)), with a depth-1 proof red on 1f3b1a3 and green on 2a74482 ([aa7548d](https://github.com/themark-net/pfy-mentat/commit/aa7548d)).
- **Lesson:** If a test cannot run its check, it must say so. Skip with a reason, never return quietly, so a skip is never read as a pass.
- **Enforced:** `tests/test_docs_hygiene.py` (shallow-clone branch on main; the `skipTest` form on `bot/mvp-flake-harness2-1031`); skill `commit-integrity-and-run-isolation`.
- **posted:** no (draft in x-staging)

<a id="l04-local-vs-cloud"></a>
### L04 Local models as the default dev env: NO-GO versus cloud

- **Date:** 2026-10-31
- **What happened:** The same 6 real dev tasks ran both ways. Cloud Build: 6/6 gate and 6/6 accept in 583.6 s (MVP-2, [eval/mvp2/REPORT.md](../../eval/mvp2/REPORT.md), [HANDOFF-mvp2-trial.md](../ops/HANDOFF-mvp2-trial.md)). Local loop: 5/6 gate, 4/6 human accept, 3859.9 s (MVP-3, `bot/mvp3-review-retry`; numbers restated in `docs/modules/pfy-build.md` on `bot/mvp-backlog-burn-1031`). `qwen3.6:35b` on Ollama was the best runnable local worker (79.2% Choice accuracy, parse_ok 48/48, [LOCAL-BENCH-3-RESULTS.md](../dogfood/LOCAL-BENCH-3-RESULTS.md)). GLM-4.5-Air parsed 0/48 on typed Choice ([LOCAL-BENCH-5-RUNTIMES.md](../dogfood/LOCAL-BENCH-5-RUNTIMES.md)).
- **Lesson:** Measure local against cloud on real tasks before making it a default. Today local is a fallback for rate limits, not the default.
- **Enforced:** `./pfy build --local` is opt-in and a rate limit does not auto-start it (`docs/modules/pfy-build.md` on `bot/mvp-backlog-burn-1031`); default local model stays `qwen3.6:35b` ([PENDING-HANDOFF.md](../PENDING-HANDOFF.md)).
- **posted:** staged (standalone A)

<a id="l05-model-size-claims"></a>
### L05 Read model-size claims against real RAM and VRAM first

- **Date:** 2026-10-31
- **What happened:** A claim said DeepSeek-V4.1-Flash runs in 64 GB+ RAM. The smallest quant (UD-IQ1_S) is 232,979,608,420 bytes (about 233 GB). nimo RAM+VRAM is 132,524,449,792 bytes (about 132.5 GB). No download, no eval; catalog row I0, NO-GO as a local default ([c0c7948](https://github.com/themark-net/pfy-mentat/commit/c0c7948), `docs/ops/HANDOFF-mvp-dsv4-1031.md` and `eval/mvp-1031/dsv4/REPORT.md` on `bot/mvp-dsv4-1031`).
- **Lesson:** Read the actual file sizes and compare them to the host's RAM and VRAM before you download or try a model. A fit check costs seconds; a 233 GB download that OOMs the box costs hours.
- **Enforced:** the fit gate (file size plus about 8 GB of context must fit RAM+VRAM, with 50 GB disk left) in `eval/mvp-1031/dsv4/fit-receipt.json` on `bot/mvp-dsv4-1031`; the llama.cpp lane exits 2 without spawning when MemAvailable is below model size plus 25 GiB ([PENDING-HANDOFF.md](../PENDING-HANDOFF.md)).
- **posted:** staged (standalone B)

<a id="l06-stray-service"></a>
### L06 A stray background service can silently eat the host

- **Date:** 2026-10-06
- **What happened:** During local benches, the `openclaw-gateway` user service loaded `glm-4.7-flash` at `num_ctx=128000` mid-slice and degraded tok/s ([LOCAL-BENCH-3-RESULTS.md](../dogfood/LOCAL-BENCH-3-RESULTS.md)). Its heartbeat loaded that model (about 26 GB) about every 30 minutes; Mark had it stopped and disabled on 2026-10-06 ([LOCAL-BENCH-5-RUNTIMES.md](../dogfood/LOCAL-BENCH-5-RUNTIMES.md) header; the 26 GB and 30 minute figures are from the org ops journal that day).
- **Lesson:** Before trusting a benchmark or blaming a model, list what else is loaded on the host. An old service you forgot about can take a big slice of RAM on a timer.
- **Enforced:** bench and eval drop-ins require `systemctl --user is-active openclaw-gateway` to stay inactive and record it in the handoff ([hermes-eval.md](../build-dropins/hermes-eval.md)); benches record MemAvailable at model start.
- **posted:** no (draft in x-staging)

<a id="l07-usage-budget"></a>
### L07 Bot usage is a budget, and Build usage is readable without the owner

- **Date:** 2026-10-06 to 2026-10-26
- **What happened:** The usage ledger, [issue #274](https://github.com/themark-net/pfy-mentat/issues/274), opened with bots at 29% for the week while Build used about 4% for a full day of atg-framework work. From 2026-10-06 a weekday routine reads Build usage from the same billing endpoint `/usage` uses, on nimo, so Mark does not have to type `/usage` ([comment](https://github.com/themark-net/pfy-mentat/issues/274#issuecomment-6032589693)). The MVP-2 trial capped cloud tasks because bots had already used 27% of the weekly budget ([pfy-local-build-mvp2-trial.md](../build-dropins/pfy-local-build-mvp2-trial.md)). On 2026-10-26, at 27% weekly bot usage, Mark suspended bot work on the trading tools.
- **Lesson:** Bot turns are the expensive meter. Spend them on coordination, push heavy work to Build drop-ins, and cut low-value bot work early instead of near the cap.
- **Enforced:** skill `best-effort-and-bot-budget-build-max` (`bootstrap/grok-cli/skills/best-effort-and-bot-budget-build-max/`); the weekday Build usage routine logging to #274; [docs/build-dropins/](../build-dropins/README.md).
- **posted:** no

<a id="l08-paper-vs-real"></a>
### L08 Paper results don't carry over to real trading

- **Date:** 2026-10-17
- **What happened:** Mark judged past trading results poor and noted that optimistic paper results did not hold up with real money. The Kalshi scanner then got a paper harness with a realistic fill model (`themark-net/kxbtc15m-scanner` PR #10, b8e0979) and a rule that paper take-profit counts only if it could be a live round-trip: sell the bid, size at the touch, net of two taker fees, after a minimum hold (that repo's README).
- **Lesson:** A paper result is only as good as its fill model. Model queue, delay, partial fills and exact fees, report settled P&L only, and keep live trading hard-off until paper is reviewed.
- **Enforced:** `LIVE_HARD_OFF` compiled `true` in kxbtc15m-scanner (its AGENTS.md); Grok Bot org skill `paper-trading-desk` (settled P&L only, no hypotheticals).
- **posted:** no

<a id="l09-mutants"></a>
### L09 Tautological tests plus surviving mutants prove nothing

- **Date:** 2026-10-20
- **What happened:** In Gom Jobbar PR #36 (`themark-net/gom-jabbar-grok4`, the ajs-port), the Tester's mutation run left mutants alive (K1, K7, K10, K12, P3, P4, P5, P7, P9, P11). Several tests were tautologies: an empty-text check and live-smoke tests that could not fail with the bug present. Round 2 replaced them with behavior asserts and the next proof killed 19/19 mutants (that repo's `docs/ops/HANDOFF-pr36-r2-2026-10-20.md`, section S6).
- **Lesson:** A green suite means nothing if a broken guard still passes. Break each guard on purpose and make sure a named test turns red.
- **Enforced:** skill `prefer-behavior-and-fail-recover-tests` (`bootstrap/grok-cli/skills/prefer-behavior-and-fail-recover-tests/`); the Tester checklist in `commit-integrity-and-run-isolation` ends with a mutant per guard; x-intake handoffs record killed mutants (for example [x-intake-2026-10-17-handoff.md](../automation/x-intake-2026-10-17-handoff.md)).
- **posted:** no (draft in x-staging)

<a id="l10-pinned-sha"></a>
### L10 Skip PRs on our repos, gate a pinned SHA, merge main in

- **Date:** 2026-10-19
- **What happened:** Mark's 2026-10-19 rule: no PRs on his own repos. Bots gate a pinned SHA with Tester and Reviewer, then fast-forward main ([HANDOFF-x-intake-149-b2.md](../ops/HANDOFF-x-intake-149-b2.md)). When main moves during a gate, the pin is stale for a fast-forward, so the branch merges `origin/main` in instead of rebasing, which keeps the gated commits intact: Hermes eval merged main at 09b1c16 with no rebase ([HERMES-EVAL-HANDOFF.md](../eval/HERMES-EVAL-HANDOFF.md)), and backlog-catalog-1030 merged main c0d38af at [0afea54](https://github.com/themark-net/pfy-mentat/commit/0afea54).
- **Lesson:** A gate is on a SHA, not on a branch name. Check `git merge-base --is-ancestor origin/main <sha>` before you push, and if main moved, merge it in and re-gate the delta; never rebase gated work.
- **Enforced:** the fast-forward recipe `git fetch origin && git merge-base --is-ancestor origin/main <sha> && git push origin <sha>:refs/heads/main`; drop-ins say "no rebase, no force-push" (for example [pfy-local-build-mvp-fix2.md](../build-dropins/pfy-local-build-mvp-fix2.md)).
- **posted:** no (draft in x-staging)

<a id="l11-state-line"></a>
### L11 Relaunch loops need a state line

- **Date:** 2026-11-01 (UTC; evening of 2026-10-31 PT)
- **What happened:** The `bot/mvp-tmpclean2-1031` lane finished (`state: lane empty`) and was then relaunched four more times, each time only to write "lane still empty" ([53f6d7d](https://github.com/themark-net/pfy-mentat/commit/53f6d7d), [2cdd792](https://github.com/themark-net/pfy-mentat/commit/2cdd792), [6535318](https://github.com/themark-net/pfy-mentat/commit/6535318), [e7f654a](https://github.com/themark-net/pfy-mentat/commit/e7f654a); `docs/ops/RUN-LOG-mvp-tmpclean2-1031.md` on that branch).
- **Lesson:** Every run ends with one machine-readable `state:` line, and whatever relaunches a lane reads it first. A lane that says `lane empty` is not relaunched until new work lands.
- **Enforced:** skill `write-loop-exits-first` (exit card, no-progress exit); run logs end with a final `state:` line (for example [RUN-LOG-backlog-catalog-1030.md](../ops/RUN-LOG-backlog-catalog-1030.md)).
- **posted:** no (draft in x-staging)

<a id="l12-pin-runner-image"></a>
### L12 Pin the CI runner image

- **Date:** 2026-10-30
- **What happened:** `ubuntu-latest` moved to 26.04 (run 41000777422 on `catalog/x-intake-149`), where bwrap works and `rg` is missing, so 40 harness2 sandbox tests failed without any change on our side. The G0 job was pinned to `ubuntu-24.04` (comment in `.github/workflows/eval-structural.yml`) and a lint now parses `runs-on` ([53933b3](https://github.com/themark-net/pfy-mentat/commit/53933b3)).
- **Lesson:** A floating runner label is an unreviewed dependency. Pin the image and test that it stays pinned.
- **Enforced:** `tests/test_workflow_image_pin.py` on main; [HANDOFF-fix-ci-ubuntu-image.md](../ops/HANDOFF-fix-ci-ubuntu-image.md).
- **posted:** no

<a id="l13-tool-home"></a>
### L13 A tool run with HOME unset writes to the real home

- **Date:** 2026-10-19
- **What happened:** During the Hermes eval, an import smoke ran with `HERMES_HOME` unset. Hermes used the real `~/.hermes`, replaced a legacy SOUL scaffold and added backup and cache files. The bytes were restored and the extra paths removed, and the real runs were then proven clean with a sha256 manifest before and after (113,616 paths, 0 changed) ([HERMES-EVAL-HANDOFF.md](../eval/HERMES-EVAL-HANDOFF.md)).
- **Lesson:** Point every third-party tool at its own home before the first call, even a smoke. Snapshot the real home before and after, and treat any diff as a failure.
- **Enforced:** isolation proof in eval handoffs (hash manifest of the tool's home); harness2 env points all caches and state into the worktree ([harness2-local.md](../build-dropins/harness2-local.md)); real-HOME watch tests in the x-intake smokes.
- **posted:** no

<a id="l14-design-pack"></a>
### L14 A Reviewer FAILs product UI that has no design pack

- **Date:** 2026-10-06
- **What happened:** The Reviewer failed Gom Jobbar PR #34 (`themark-net/gom-jabbar-grok4`) at c337521 because Home and Admin UI decisions (0022, 0023) came without a design pack (org ops journal, 2026-10-06). The merge was held, Design wrote design pack 51 at 7106404 to cover that chrome, and PR #34 was then squash-merged at 00faa55 (that repo's `docs/PENDING-HANDOFF.md`).
- **Lesson:** Operator UI is the product, so it gets a design pass before implement. Bolted controls are fine in a lab branch, not on main.
- **Enforced:** skill `ui-is-the-app-design-in-loop` (`bootstrap/grok-cli/skills/ui-is-the-app-design-in-loop/`), listed in [AGENTS.md](../../AGENTS.md).
- **posted:** no
