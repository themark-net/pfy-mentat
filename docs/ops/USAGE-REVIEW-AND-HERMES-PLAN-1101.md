# Usage review (Oct 25 to Nov 1) and Hermes plan (week of Nov 1)

Written 2026-11-01 PT by Grok Bot, read-only review. Branch `bot/usage-hermes-plan-1101`. Not gated, not merged. No Build run, no lane started, no process stopped.

Sources read: issue #274 (usage ledger), `git log origin/main`, all `origin/bot/*` tips and their `RUN-LOG-*` state lines, `tmp/supervise-1031.log`, `tmp/supervise-1031.sh`, `tmp/supervise-throttle-1031.sh`, `HANDOFF-mvp-integrate-pass4-1031.md`, `MERGE-PLAN-1031.md` (on `bot/mvp-merge-plan-1031`), `docs/eval/HERMES-EVAL-HANDOFF.md`, `HANDOFF-mvp-hermes-check-1031.md`, `docs/ops/HANDOFF-hermes-wire.md`, `docs/plans/hermes-bot-interface.md`, and the Hermes and Ollama install on nimo.

## Part 1. Value review of last week

### Usage numbers that a log actually records

Only numbers written in a log are used. Nothing below is estimated.

| When (PT) | creditUsagePercent | GrokBuild | GrokTasks | Source |
|---|---:|---:|---:|---|
| Mon 10-26 08:52 | 1 | 1 | - | #274 |
| Tue 10-27 08:58 | 4 | 3 | 1 | #274 |
| Wed 10-28 08:54 | 6 | 4 | 1 | #274 |
| Thu 10-29 08:55 | 7 | 5 | 2 | #274 |
| Fri 10-30 08:52 | 8 | 5 | 3 | #274 (last ledger entry) |
| Sat 10-31 12:50 | 11 | 8 | 3 | supervise-1031.log |
| Sat 10-31 15:01 | 30 | 26 | 3 | supervise-1031.log |
| Sat 10-31 17:30 | 52 | 48 | 3 | supervise-1031.log |
| Sat 10-31 20:01 | 70 | 66 | 3 | supervise-1031.log |
| Sat 10-31 20:23 | 72 | - | - | throttle relaunch line `credit=72` |

After 20:23 no number is logged. The throttle supervisor ended at 01:03 Nov 1 without a `credit >= 83` line. No reset entry was written to #274 for this week.

What the logs say: Oct 25 to Oct 30 used about 8 points in five days. Oct 31 alone moved the meter from 11 to at least 72 in under eight hours, almost all of it GrokBuild (8 to 66 by 20:01). The Grok Bot weekly meter is not in this API response (#274 says so), so the bot share cannot be read from these logs. The billing response says `isUnifiedBillingUser: true`. Grok Bot ran out on Nov 1 after that Build burn, which fits a shared pool, but no log shows that link directly. Treat it as likely, not proven.

### Oct 25 to Oct 30: landed on main

| Workstream | On main (SHA) | Notes |
|---|---|---|
| pfy-local-build MVP step 1 | `b63d8d0` `fbbaf90` `da2ce97` `e63a95b` `81d0415` `2fadea1` `997d892` | Headless `pfy build --local`, live eval 8/8, two gate fix rounds (Tester FAIL `42fcc22` found real blockers) |
| mvp2 trial | `03c801b` `7d07b61` `5da10a0` `b46ef0c` `85c53dc` | Local vs cloud arms, recorded NO-GO. `bot/mvp2-trial` still has 5 unmerged commits (`50220ce`) |
| Pregate | `172f5df` `412e970` `b368c44` `406591a` `6b04ba8` | Local pregate, Tester/Reviewer blockers fixed |
| CI ubuntu pin | `603c2c3` `7b8bc7d` | Hosted G0 pinned to ubuntu-24.04 |
| X intake 146 to 149 | `1607e9b` `2f2b20e` `fa5f5ee` `68774f9` `b0a83bc` `e5a76d7` `996ea3d` | x148 bwrap fix `7cea199`, `8430e90` |
| backlog-catalog-1030 loop | `ceb3294` .. `e04e926`, then `1f3b1a3` `47dcd66` `2a74482` | About 20 commits, mostly docs and run-log stamps; real items T-0002, T-0095, smoke 149, image-pin lint `53933b3`, T-0124 `6c8d00a` |
| pfy-followups-1030 | `53aae59` `654efa7` `b6c3498` `c0d38af` | Real fix: bwrap probe mounts (`c0d38af`) |

This stretch was good value per point: about 8 points bought the local-build MVP, the pregate, the CI pin, and four X intakes, all on main.

### Oct 31: the MVP parallel wave

`origin/main` tip is `2a74482` (Oct 31 18:51). No commit from any `bot/mvp-*-1031` lane is on main. 61 `bot/mvp*` branches were pushed for this wave.

Where the work sits:

- `bot/mvp-integrate-1031` @ `1dee0b9`: pass 3 integrate. Suite 1243 tests, 1 failure fixed by `918fa8e`. Demo 3 PASS. sixtask-int VERDICT GO.
- `bot/mvp-integrate-pass4-1031` @ `e0b6d57`: ten more lanes merged on top. 599 non-merge commits ahead of main, 287 of them `docs:`. Diff vs main: 939 files, +55097/-600, of which `scripts/` and `pfylib/` are 16 files, +4590/-300. Suite 1320 tests, 1 merge-caused failure fixed in `bbd8254`. Demo pass 4 FAIL (review reject, the diff also edited the shared `_run` helper). Not gated: Tester, Reviewer, and pregate were never run on it.
- `MERGE-PLAN-1031.md` built a second scratch stack (`cee9bdd`, detached, not on origin) that overlaps the integrate branches.
- Still outside both integrate branches on purpose: `bot/mvp3-review-retry` (`4be797e`), `bot/mvp3-followups-1031`, `bot/mvp3-s2s5-1031`, `bot/mvp-probe-fix2-1031` (cherry-picked in the scratch stack only), `bot/mvp-backlog-fu-1031`, `bot/mvp-pfy-followups-next-1031`, `bot/mvp-tautology-scan-1031`, `bot/mvp-probe-s2s5-1031`, `bot/mvp-pregate-fixture-tmp-1031`, `bot/flake-pgrep-x-1031`, `bot/lessons-xstaging-1031`, `bot/doctrine-commit-integrity-1031`, `bot/mvp-plan-1031`, `bot/mvp-merge-plan-1031`.

### Real value found (Tester-style findings and accepted product items)

| Lane | Evidence from its run log state line |
|---|---|
| mvp-mutate-preflight-1031 | 27 mutants: 21 survived before, 26 killed after (1 equivalent) |
| mvp-mutate-cloud / cloud2 | 16 then 27 killed, 0 survived |
| mvp-review-quality-1031 | Reviewer false accepts 3 to 0 |
| mvp-probe-int-1031 | 11 probes, 4 findings fixed |
| mvp-probe-fix2-1031 | 2 findings fixed (`29da017` mode bit, `915edf0` hardlink) |
| mvp-probe-s2s5-1031 | 48 probes, 1 defect fixed (`abc8985`) |
| mvp-realfail2 / realfail3 | 1 and 2 FINDINGs on real failure cases |
| mvp-sixtask then sixtask-int | NO-GO (4/6, tests-tampered finding) turned into GO (6/6 twice) |
| mvp-selfhost / selfhost2 | 13 human-accepted product items each lane |
| mvp-preflight-1031 | Only lane with a pregate PASS (`0fbf426`) |
| mvp-dogfood3..6 | Pass rates 5/6, 7/8, 3 accepted plus 1 reject, 8/8 |

This is real MVP progress, but it is stranded: none of it is on main, and the pass 4 demo failed.

### Waste the logs record

| Kind | Evidence |
|---|---|
| Relaunch loop | `mvp-tmpclean2-1031` relaunched 7 times (16:35 to 17:20), then ended `lane empty` |
| Relaunch | `mvp-gom-dogfood-1031` relaunched twice (15:06, 15:52) |
| Killed relaunch | `lg-018-fixes-1031` relaunched at 20:23 then killed (already lane empty) |
| Duplicate pregate | 20:25 killed a duplicate backlog pregate queue |
| Killed pregate | 21:29 killed fix3 pregate `ff8b881` (collided with G0), requeued |
| Pregate never finished | `pregate integrate tip 0c3f133 queued` at 14:56 has no exit line |
| Gate starvation | 27 lane run logs end with `pregate not run: host busy` or `lane forbids pregate`. The heavy lock serialized every suite, so lanes finished but nothing could be gated |
| Overlapping lanes | dogfood x6 plus gom-dogfood plus selfhost x2 (all cloud-build dogfood); realfail x3; mutate x3; review-fix x2; docs plus docs-final; tmpclean x2; integrate pass 1 to 4 plus a separate merge-plan scratch stack |
| Polling lanes | mvp-cloudfix (4 polls, no new findings), mvp-timeoutfix (60 quiet minutes, 3 polls), mvp-tmpclean2 (resume recheck only). Build sessions used as timers |
| Dead-end lane | mvp-dsv4-1031: model fit gate fails by about 109 GB, decidable without a Build session |
| Commit overhead | 11 commits only to stamp a handoff SHA; 287 of 599 integrate commits are `docs:` |

No log splits the Oct 31 usage per lane, so the share of the 58 Build points that went to waste is not stated here.

### Verdict

Mixed. Oct 25 to 30 was high value per point and landed on main. Oct 31 bought real findings and an integrated MVP candidate, but at a high rate (about 58 Build points in under 8 hours) and with zero commits on main, a failed pass 4 demo, and no gate run on the integrate tip. The usage also coincided with Grok Bot running out on Nov 1, which broke the X intake. The value is real only once `bot/mvp-integrate-1031` or pass 4 is gated and landed.

### Recommendation for this week

1. First Build spend: gate and land what exists. Tester plus Reviewer plus pregate on `bot/mvp-integrate-1031` @ `1dee0b9` (demo 3 PASS, GO) first, then decide pass 4 (`e0b6d57`) after a small fix for the dotenv rule that does not touch `_run`. No new MVP lanes until main moves.
2. Cap parallel Build lanes at the number the gate can absorb (the heavy lock runs one suite at a time). Budget a gate slot per lane before launching it.
3. Supervisor rules: no relaunch of a lane whose run log says lane empty; max 1 relaunch; no Build session used only to poll. Polling goes to Hermes or a plain script.
4. Bot share: Grok Bot only for coordinating, owner chat, X reads, and gate verdicts. Everything recurring moves to nimo (Part 2). Add a stop rule on the shared credit, for example hold Build lanes when `creditUsagePercent` reaches a mid-week line Mark sets, so bots keep headroom until the Sunday reset. Mark sets the number; this doc does not invent one.
5. Log usage daily to #274 from nimo (Part 2, job 1), including a reset entry, so next week's review has real per-day numbers.

## Part 2. Hermes readiness on nimo

### What is installed and how it runs

| Item | Found |
|---|---|
| Hermes | `~/.local/bin/hermes`, Hermes Agent v0.16.0 (2026.6.5), upstream `c6b0eb4d`, Python 3.11.15, project `~/.hermes/hermes-agent` |
| Default model in `~/.hermes/config.yaml` | `minimax-m3:cloud`, provider `ollama-launch`, base `http://127.0.0.1:11434/v1`. This is an Ollama Cloud model, not local |
| Hermes cron | `hermes cron list`: no scheduled jobs |
| Hermes gateway | not running; no Hermes systemd unit |
| Last activity | `state.db` dated 2026-06-16; newest session file 2026-09-24 |
| Grok via API | Hermes code supports `api.x.ai`, but no `XAI_*` or `GROK_*` variable is set in `~/.hermes/.env` (names checked, values not read). Not configured |
| Ollama | `ollama serve` up 9 days. `qwen3.6:35b` (22 GB) pulled, also `qwen3-coder:30b`, `gemma4:26b`, `deepseek-v4-flash:cloud`. `ollama ps` empty now |
| Host | 107 GB RAM, 53 GB used now. `nimo-miner-guard` scales miner threads down when Ollama is busy |
| pfy wiring | `bot/hermes-wire` is on main: `./pfy bot` with `PFY_BOT_INTERFACE=hermes`, default off, driver `pfylib/hermes_bot_driver.py`, model `PFY_BOT_MODEL` default `qwen3.6:35b` |
| Pinned driver install | `tmp/hermes-agent` and `tmp/.venv-hermes` do not exist in the repo tmp, so the flag would print FAIL and fall back to opencode today |
| gh on nimo | `gh auth status` exit 1 (not logged in) |
| Existing nimo timers | `founder-build-babysit` (hourly, pushes tip branches), `grokbot-watchdog` (every 2 min) |

### Eval status

- Bake-off 2026-10-19 (`docs/eval/HERMES-EVAL-HANDOFF.md`, on main via `24fe672`): NO-WIN on `qwen3.6:35b`. 26/27 vs 25/27, valid tool calls 82.61% vs 97.83%.
- `bot/mvp-hermes-check-1031` @ `61396e4`: recomputed from `results.json`, numbers reproduce, NO-WIN stands, two prose corrections. Not on main.
- Re-run on `bot/hermes-wire` (matched thinking, tool_search off): 26/27 both, valid 100% both, p50 7.0s vs 7.2s, RSS 240 MiB vs 1.03 GiB. Still NO-WIN; the founder chose Hermes anyway for RAM.

Read: Hermes on local qwen3.6 is reliable at tool calls for small, labeled tasks. It is not shown to be good at Tester or Reviewer judgment.

### Costs

- Local Ollama (`qwen3.6:35b`): no metered cost and no Grok usage. Costs are RAM (about 23 GB while loaded), CPU time taken from the miner, and contention with the pregate heavy lock.
- Ollama Cloud (`minimax-m3:cloud`, Hermes default today): billed by the Ollama account plan. The plan and its limits were not checked here.
- Grok via xAI API: pay per token on a separate xAI API account, not the Grok Bot meter. Not configured. Prices not looked up here.
- Plain scripts on systemd timers: free. Several jobs below need no model at all.

### Which recurring bot jobs move to Hermes

| Rank | Job | Needs a model? | Fit | Proposed home |
|---|---|---|---|---|
| 1 | Usage logging (#274) | No | High. `tmp/usage-1031.py` already reads the meter on nimo | systemd timer or Hermes cron runs the script; Hermes on local qwen only formats the comment. Posting needs a GitHub write path (blocker B5) |
| 2 | Pregate and CI watching | Little | High. Today it is `pgrep -x Runner.Worker`, `flock heavy-1030.lock`, exit codes | Script plus Hermes cron; Hermes summarizes failures with local qwen |
| 3 | Lane supervision | Some | High. `supervise-1031.sh` is already bash; the waste was missing rules, not missing intelligence | Hermes cron with hard rules (max 1 relaunch, never relaunch lane empty, stop at a credit line), local qwen for the run-log read |
| 4 | Gating watchers (detect tips that need a gate, queue them) | Some | Medium. Detection and queueing yes; the PASS or FAIL verdict stays with Grok Tester and Reviewer | Hermes cron, local qwen |
| 5 | Catalog intake (entry drafts, smoke receipts) | Yes | Medium. Drafting from fetched pages fits local qwen; scoring and gate stay with Grok | Hermes one-shot (`hermes -z`), local qwen, output to a branch for gate |
| 6 | X intake | Yes | Low until X access exists on nimo | Stays on Grok Bot this week, but only the X read and pick; the write-up hands off to job 5 |

### Blockers (concrete)

- B1. Chat only. The `./pfy bot` Hermes driver runs with `enabled_toolsets=[]` because its isolated config sets approvals off (`docs/plans/hermes-bot-interface.md`). Watcher jobs need shell, file, and git tools. Needs approvals on, or a narrow allowlisted toolset in a sandbox, as its own gated change.
- B2. Driver not installed. `tmp/hermes-agent` and `tmp/.venv-hermes` are missing, so `PFY_BOT_INTERFACE=hermes` falls back to opencode today.
- B3. Wrong model by default. Mark's `~/.hermes` uses `minimax-m3:cloud`, not local qwen. Ops jobs need a separate `HERMES_HOME` (the driver already refuses `~/.hermes`) pinned to `qwen3.6:35b`.
- B4. No scheduler or report path. Hermes cron is empty and no gateway runs, so there is no way yet for a Hermes job to report to Mark. Options: Hermes cron plus a GitHub comment, or the existing systemd timer pattern.
- B5. No GitHub write from nimo. `gh` is not logged in. CI status reads and #274 comments need a scoped token or reuse of the SSH push path. Needs Mark's decision.
- B6. No X access on nimo. X intake depends on Grok Bot's X tools.
- B7. Grok API not configured. No xAI key in Hermes, so a Grok fallback for harder jobs is not available; adding one is a cost decision for Mark.
- B8. Host contention. A loaded 23 GB model plus suites under the heavy lock plus the miner; jobs must unload the model (`keep_alive: 0`) and avoid suite windows.
- B9. Judgment quality. NO-WIN eval and no Tester-quality evidence, so gate verdicts stay with Grok.
- B10. The "Hermes wiring" TODO: the `./pfy bot` flag landed, but the ops-runner wiring (B1 to B5) has no branch, drop-in, or T-id yet.

### Suggested order (no work started)

1. Land the gate on the integrate branch (Part 1).
2. One small gated change: install the pinned driver under tmp, a dedicated ops `HERMES_HOME` on `qwen3.6:35b`, and a systemd timer for job 1 (usage logging) with no model.
3. Then jobs 2 and 3 as Hermes cron jobs with an allowlisted toolset (B1) once Mark picks the GitHub write path (B5).
4. Jobs 4 and 5 after a week of clean runs.
