# Delivery-first lanes (design, 2026-11-01)

Status: design only. Branch `bot/usage-hermes-plan-1101`. Not gated, not merged. No Build run, no lane started, nothing installed. Sibling of [USAGE-REVIEW-AND-HERMES-PLAN-1101.md](USAGE-REVIEW-AND-HERMES-PLAN-1101.md).

Mark's steer (2026-11-01): design builds to deliver, not to hit caps. Oct 31 measured usage, not merges, and spent about 58 Build points with nothing landed.

## 1. The number that matters

Merged non-merge commits on `origin/main` (committer date) per point of `creditUsagePercent`, using the readings in #274 and `tmp/supervise-1031.log`:

| Window (PT) | Meter | Points | Commits on main | Commits per point |
|---|---|---:|---:|---:|
| Reset Oct 25 20:58 to Oct 30 08:52 | 0 to 8 | 8 | 35 | about 4.4 |
| Oct 30 08:52 to Oct 31 12:50 | 8 to 11 | 3 | 32 | about 10.7 |
| Oct 31 12:50 to now | 11 to at least 72 | at least 61 | 5 (none from the MVP wave) | under 0.1 |

Commit counts are a rough proxy (docs and stamp commits count the same as code), but the gap is two orders of magnitude. The wave produced real work (see the review doc); it just was not designed to land.

## 2. Sandcastle and Pocock skills: what they actually are

Sources (all read on 2026-11-01; clones at `tmp/_vendor/sandcastle` @ `85e8e6d` and `tmp/_vendor/skills` @ `4ae2317`, read-only, nothing installed):

- Repo: https://github.com/mattpocock/sandcastle (MIT, package `@ai-hero/sandcastle`, v0.12.0 in `package.json`)
- Docs: https://www.aihero.dev/sandcastle and `docs/guide/*.md` in the repo
- How it works: https://github.com/mattpocock/sandcastle/blob/main/docs/guide/how-it-works.md
- Prompts and completion signal: https://github.com/mattpocock/sandcastle/blob/main/docs/guide/prompts.md
- Native bwrap sandbox ADR: https://github.com/mattpocock/sandcastle/blob/main/docs/adr/0024-native-sandbox-providers.md
- Templates: https://github.com/mattpocock/sandcastle/tree/main/src/templates (`simple-loop`, `sequential-reviewer`, `parallel-planner`, `parallel-planner-with-review`, `blank`)
- Skills: https://github.com/mattpocock/skills (`skills/engineering/to-tickets`, `implement`, `implement-spec`, `tdd`, `code-review`, `pr`; `skills/in-progress/software-factory`, `loop-me`)

What it does, from those sources only:

| Topic | Sandcastle / skills |
|---|---|
| Isolation | `run()` takes a sandbox provider: Docker, Podman, Vercel, Daytona, and native `bwrap()` (Linux) / `seatbelt()` (macOS). Native providers mount system dirs read-only, give each run a private home and temp dir, take logins only from env vars, never fall back to no sandbox, and refuse root (ADR 0024). Git control files (`.git/config`, hooks, info) are mounted read-only so the agent cannot rewrite what git runs (how-it-works). |
| Branches | Three strategies: `head`, `merge-to-head` (temp branch in a worktree, merged back on success, kept if the run failed with commits, merge aborted on conflict so HEAD is unchanged), and named `branch` (worktree reused across runs). |
| Task definition | A prompt file with shell expansions evaluated in the sandbox at each iteration, plus `promptArgs`. Templates read the task list from the tracker. `to-tickets` turns a spec into tracer-bullet vertical slices with explicit blocking edges, each sized to one fresh context window and verifiable on its own. |
| Loop to completion | `maxIterations` (default 1), `completionSignal` (default `<promise>COMPLETE</promise>`), `idleTimeoutSeconds` (600) for a stuck agent, `completionTimeoutSeconds` (60) for a process that hangs after signalling done. `result.commits` tells the orchestrator whether anything was produced. |
| Review | `sequential-reviewer` and `parallel-planner-with-review`: the reviewer runs in the same sandbox on the same branch only if the implementer produced commits. The `code-review` skill reviews against a pinned fixed point on two axes (standards and spec) in parallel fresh-context sub-agents. |
| Merge | `parallel-planner-with-review` ends each cycle with a merge agent that merges completed branches, runs typecheck and tests after each, fixes failures, and closes the issues. Only branches with commits reach the merge phase. Outer loop capped (`MAX_ITERATIONS = 10`), replans the unblocked frontier after each merge. |
| Small units | Planner marks two issues as blocking each other when they touch overlapping files, so parallel work is conflict-free by construction. Deterministic branch names (`sandcastle/issue-{id}`) keep progress across replans. `tdd` forbids horizontal slicing and tautological tests. |
| Brakes | `software-factory`: "Accelerators without brakes make a slop cannon." Three brakes: automated checks, automated review, human review. Add one trigger at a time, throttled, and "cap every loop of runs at a few tries before a human." |
| Usage | ADR 0005 reports raw token counts per iteration, not a percentage. |
| Agents | Built-in providers: `claudeCode`, `codex`, `cursor`, `opencode`, `copilot`, `pi`. No Grok provider; a custom provider needs the CLI, output, and resume capabilities listed in `docs/agents/adding-an-agent-provider.md`. |

Not found: any Sandcastle feature that measures merge throughput, and no Grok agent provider. Nothing here was run.

## 3. Our setup next to it

| Concern | Ours today | Sandcastle | Gap |
|---|---|---|---|
| Unit of work | A lane with a drop-in and a list of items; 61 lanes on Oct 31 | One ticket, one branch, one fresh context | Our lanes were themes ("dogfood", "realfail"), not deliverables |
| Done | Run-log `state: lane empty` or turn cap; handoff pushed | `<promise>COMPLETE</promise>` plus commits, then merged | Our "done" never included landing |
| Exits | `write-loop-exits-first` exit card (goal, 8 turns, budget, wall, no-progress, errors) | `maxIterations`, idle and completion timeouts | Ours is good on paper; the supervisor ignored it (7 relaunches of tmpclean2) |
| Isolation | git worktree under `tmp/`, `TMPDIR` per lane, bwrap only inside `./pfy build` | worktree plus bwrap/Docker around the whole agent, read-only git control files | We trust the agent with the full home and `.git/config` |
| Review | Tester plus Reviewer at an exact SHA, both PASS, any new commit resets | Reviewer in the same sandbox after implement; merger runs tests | Ours is stricter, but it ran after integration, on 600-commit tips, so it never ran |
| Merge | Bots fast-forward main after a double PASS; integrate lanes merged 10 to 50 branches | Merge agent per cycle, small branches, tests after each merge | Big-bang integration is the opposite of their model |
| Parallelism | Supervisor launched to a usage target | Frontier of unblocked, non-overlapping tickets | We parallelized overlapping files (`pfy_build_cloud.py` had 3 and 6 conflicts in pass 4) |
| Gate capacity | One heavy lock; pregate about 1065 s, full suite 900 to 940 s | Typecheck and tests inside each sandbox | We ignored the gate as the bottleneck; 27 lanes ended "pregate not run" |
| Orchestration | `supervise-1031.sh`, `orchestrator-loop-decide-and-ship` | TypeScript `run()` loops | Ours already exists in bash and skills |

## 4. Delivery-first lane design

1. **A lane is one slice.** One deliverable, one branch cut from current `origin/main`, sized to land in one gate pass. Before work starts, the drop-in names the exit test (a behaviour test that fails on main today) and the files the lane may touch. No theme lanes, no "keep finding work" lanes.
2. **Done means on main.** A lane is DONE only when its tip is fast-forwarded to `origin/main` after pregate, CI, and Tester plus Reviewer at that pinned SHA. "Pushed", "lane empty", and "handoff written" are intermediate states, not done.
3. **WIP equals gate capacity.** With one heavy lock and about 17 to 18 minutes per pregate, the gate takes about 3 tips an hour at best. Cap: at most 1 slice in gate and 2 slices building. A new lane starts only when a slice lands or is killed. The supervisor counts slices waiting for the gate, not usage percent.
4. **Land in sequence, never integrate big.** Slices that touch the same file are chained (the second is cut after the first lands), as Sandcastle's planner does. No integrate branch above about 10 commits or 1 runtime file. Each slice rebases on main itself before gating; a conflict means the slice was cut wrong, not a merge job.
5. **Kill rule.** A lane that has not produced a gateable tip (exit test green, targeted tests green, diff inside the declared files) after 3 Build tries is killed and its slice is re-cut smaller or dropped. One relaunch maximum per try. Never relaunch a lane whose last state is done or empty. A gate FAIL gives one fix try, then the slice is re-cut.
6. **Metrics replace the usage target.** Primary: merged commits per usage point (daily, from the meter and `git log origin/main`), and lead time from lane start to landing (median and worst). Secondary: slices killed, gate FAILs per slice, gate queue length. Usage percent becomes a ceiling, not a goal. Doc-only stamp commits are excluded from the count.

Supporting rules:

- Receipts and run logs that assert on a lane's own branch history (for example `tests.test_selfhost_1031_log`) stay out of main; they break on cherry-pick and do not test the product.
- Lane docs land as one handoff per slice, not a run log plus stamp commits.
- Hermes and plain scripts do all waiting and polling (section 6); Build sessions never poll.

## 5. Adopt, install, or build

Adopt now (ideas and text only; free, nothing to install):

1. The `to-tickets` slicing rules: vertical tracer-bullet slices, explicit blocking edges, overlap on files counts as blocking, one fresh context per slice.
2. The completion contract: an explicit completion signal plus "commits produced" as the only success, an idle timeout for stuck runs, a short grace window after the signal (maps onto our exit card).
3. Review only when there are commits; the reviewer sees the slice diff against a pinned base (`code-review`'s fixed point), which matches our Tester plus Reviewer at a SHA.
4. The `software-factory` brakes: one trigger at a time, throttled, and a hard cap of a few tries per loop before a human.
5. ADR 0024's isolation rules as a checklist for our lanes: read-only `.git/config` and hooks, private home and temp, logins only from env, never fall back to unsandboxed.
6. The `pr` skill's body shape (Evidence before and after, Merge danger: door and blast radius) for our handoff and gate request.

Do not install yet:

- Sandcastle itself. It is TypeScript, has no Grok agent provider, and its native `bwrap()` provider on Ubuntu 24.04 and later needs an AppArmor profile written with `sudo` (its own docs give the command). That is a host change, so it is a Mark decision. If he wants it later, the cheapest trial is `opencode` as the agent with local Ollama, `bwrap()` as the sandbox, in a scratch repo under `tmp/_vendor`, all free and local.
- The Pocock skills as installed skills. They assume Claude Code and an issue tracker set up by `/setup-matt-pocock-skills`. Port the rules into our own skills instead.

Build ourselves (small, bash or Python, free, on nimo):

1. `scripts/slice-gate-queue`: a FIFO of slice tips waiting for pregate under the existing heavy lock, one at a time, writing PASS or FAIL with the SHA. Replaces ad hoc `flock` calls and the killed duplicate pregates.
2. A slice supervisor that replaces `supervise-1031.sh`: starts a lane only when WIP is under the cap, enforces the 3-try kill rule and the one-relaunch rule, and never reads usage percent as a launch signal.
3. A delivery ledger: one line per slice (start, first gateable tip, gate result, landed SHA, tries) plus the daily meter reading, so merged commits per point and lead time are computed, not estimated. Comment into #274 once a day.
4. A drop-in template with the exit test, the allowed files, and the blocking slices filled in before launch; the launcher refuses a drop-in without them.
5. Update `orchestrator-loop-decide-and-ship` and `write-loop-exits-first`: goal met means landed on main, add the WIP cap and the 3-try kill rule.

## 6. Hermes as the watcher

Hermes runs on nimo with local `qwen3.6:35b` (no Grok usage) and does the waiting, never the building or the verdict:

- Watches the gate queue and CI, and posts the result line to the delivery ledger.
- Watches lanes: run-log state, process alive, tip pushed, exit test green. Applies the kill rule mechanically and records why.
- Wakes a Grok bot only on events that need judgment: a slice ready for Tester plus Reviewer, a gate FAIL, a killed lane that needs re-cutting.
- Writes the daily metrics line.

Blockers are the ones in the review doc: the driver runs chat-only (no tools), the pinned driver is not installed, the default model is Ollama Cloud, no Hermes cron or report path, `gh` not logged in on nimo. Until those are fixed, the same watcher logic runs as plain scripts on a systemd timer, which costs nothing.

## 7. First application: land `1dee0b9`, then mvp3 `4be797e`, in thin slices

Facts: `bot/mvp-integrate-1031` @ `1dee0b9` is 619 files, +40387/-555 against main, of which 13 runtime files carry +3648/-284. `bot/mvp3-review-retry` @ `4be797e` is 48 files, and its only runtime file is `scripts/pfy_build_local.py` (+1485/-199). Both touch `scripts/pfy_build_local.py` and `tests/test_pfy_build_local_review.py`, so mvp3 is blocked by the integrate slice for that file.

Method for every slice: cut `bot/land-<n>` from current `origin/main`, take only the listed paths from the source tip (`git checkout 1dee0b9 -- <paths>` or a cherry-pick of the matching commits), run the listed tests plus the exit test, then queue the tip for pregate, CI, and Tester plus Reviewer. Next slice starts from the new main.

| # | Slice | Paths from `1dee0b9` | Exit test | Blocked by |
|---|---|---|---|---|
| L1 | Gate tooling | `scripts/check_workflow_image_pin.py`, `scripts/pregate.sh`, `.github/workflows/eval-structural.yml`, `tests/test_workflow_image_pin.py`, `tests/test_ci_discover_cover.py` | `tests.test_workflow_image_pin`, `tests.test_ci_discover_cover` | none |
| L2 | Build preflight | `pfylib/build_preflight.py`, `tests/test_build_preflight.py`, `tests/test_mut_preflight_*.py` | `tests.test_build_preflight` | none |
| L3 | tmp hygiene | `tests/support_tmpclean_leaker.py`, `tests/test_pfylib_tmp_cleanup.py`, `tests/test_tmpdir_scripts.py`, `scripts/eval-auto.sh`, `scripts/smoke-product-levers.sh` | those modules | none |
| L4 | Attach and `./pfy` surface | `pfylib/attach.py`, `scripts/pfy`, `scripts/pfy_enterable_162.py`, `tests/test_attach.py`, `tests/test_enterable_not_ok.py` | `tests.test_attach` | L2 if `scripts/pfy` imports preflight |
| L5 | Local build | `scripts/pfy_build_local.py`, `scripts/pfy_local_build_eval.py`, `tests/test_pfy_build_local*.py`, `tests/test_pfy_local_build_eval.py` | `tests.test_pfy_build_local`, `tests.test_pfy_build_local_review` | L2, L4 |
| L6 | Cloud build core | `scripts/pfy_build_cloud.py`, `tests/test_pfy_build_cloud.py` | `tests.test_pfy_build_cloud` | L2, L5 (shared helpers) |
| L7 | Docs and quickstart | `docs/modules/*`, the build docs, `tests/test_pfy_build_docs.py` | `tests.test_pfy_build_docs` | L5, L6 |
| L8 | Catalog and smoke fixes | `scripts/catalog_stage_eval.py`, `tests/test_catalog_stage_*.py`, `tests/test_tree_sig_*.py`, `tests/test_smoke_*_receipt_absolute.py`, related `sources/entries` | those modules | none |
| L9 | Eval evidence | `eval/mvp-1031/check_receipt.py`, the demo receipt and REPORT only, `tests/test_mvp_1031_receipt.py` | `tests.test_mvp_1031_receipt` | L6 |
| M1 | mvp3 local review | rebase `4be797e`'s `scripts/pfy_build_local.py` and its three test modules onto main after L5 | `tests.test_pfy_build_local_review` | L5 |
| M2 | mvp3 eval | `eval/mvp3/*` report and receipts, one handoff | its report test if any | M1 |

L6 may be too big for one gate pass (1562 new lines). If the first Tester pass cannot finish, re-cut it by phase (runner and gate, failure classification, review step) along the test classes. After L9 and M2, the pass 4 lanes (`timeoutfix` budget helpers, `cloud-perf` phase clock, `probe-int` symlink checks, the dotenv rule without editing `_run`) each become one more slice on top of main.

Left out on purpose: per-lane run logs, stamp commits, build drop-ins for finished lanes, `eval/gom-dogfood-1031` and `eval/selfhost-1031` bulk receipts, and tests that assert on lane branch history. They stay on their branches as records.

Expected cost: L1 to L4 and L8 are mostly existing code plus tests, so most are a Tester plus Reviewer pass and a pregate, not new Build work. At WIP 2 and about 3 gate passes an hour, L1 to L9 plus M1 and M2 can land in two working days if no slice fails twice. Measure it with the delivery ledger rather than trusting this estimate.

## Next

Mark decides: approve the lane design and the L1 to M2 order, and whether Sandcastle with `bwrap()` is worth the AppArmor host change later. No lane is started by this doc.
