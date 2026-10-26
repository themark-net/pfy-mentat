# Grok Build drop-ins

Ready-to-paste prompts that move the heavy work from bots to Grok Build. On 2026-10-05/06 bots used about 29 % of their weekly budget, while Build did all of atg-framework for about 4 %. When a bot asks Build to do the work, the bot still pays to babysit it. These prompts are meant for **Mark to paste into Build himself**. Usage figures are logged on issue #274.

## How to use

1. Open Grok Build on nimo in the repo named at the top of the prompt.
2. Paste everything below the `---` line. Prompts marked "founder RELEASE" count as your go for that one slice. Lotline needs its three FOUNDER lines filled first.
3. Build works in its own worktree and branch, leaves a handoff in the repo's `docs/`, pushes, and opens a PR (or prints the compare URL plus a PR body file, since gh is not logged in on nimo). It never merges. Tester and Reviewer gate the merge.
4. Only one model-loading prompt at a time: atg-framework and pfy-mentat both do live runs on nimo and need a quiet host (`ollama ps` empty, no other bench).

## Prompts (run in this order)

| Order | File | Repo | Slice | Founder gate? | Loads a model? |
|---|---|---|---|---|---|
| **1 (run first)** | [atg-framework.md](atg-framework.md) | `~/DEVELOP/atg-framework` | OpenAI-compatible client + paper PoC suite + live toy | No (NEXT.md step 1) | Only at the end, if the host is quiet |
| 1-alt (long unattended run) | [atg-finish-autonomous.md](atg-finish-autonomous.md) | `~/DEVELOP/atg-framework` | One-paste, no-questions, resumable orchestrator for all of atg (phases A to G, including the pfy-mentat integration). Use it instead of row 1 when you want Build to run for hours on its own | Phase F carries a scoped founder override of NEXT.md step 3 | Yes, after a quiet-host gate (polls up to 3 h) |
| 2 | [pfy-mentat.md](pfy-mentat.md) | `~/DEVELOP/pfy-mentat` | llama-server lane + atg-compile bench + ATG card refresh | No (BEST_EFFORT) | Live part only, quiet host |
| 2b | [pfy-mentat-toolsets.md](pfy-mentat-toolsets.md) | `~/DEVELOP/pfy-mentat` | Next toolsets: destructive_command_guard, Bumblebee, DSPy decision-bench tuning, opencode-mem, ngram-mod | No (BEST_EFFORT) | DSPy and ngram-mod only, quiet host |
| 3 | [gom-jabbar.md](gom-jabbar.md) | `~/DEVELOP/jobbar-master/current` | Reconcile the 09-25 local UI line with origin/main for T-0049 (draft PR) | Mark decides whether the UI lands | No |
| 4 | [practiceminder.md](practiceminder.md) | `~/DEVELOP/practiceminder` | M3 LockAdapter + emergency unlock (#8) | **Yes**: pasting = RELEASE | No |
| 5 | [leasegrid.md](leasegrid.md) | `~/DEVELOP/leasegrid-c` (repo leasegrid-c) | #26 relative recovery-file path (Android) | **Yes**: pasting = RELEASE | No |
| 6 | [lotline.md](lotline.md) | `~/DEVELOP/lotline` | Phase B kit (deal-sheet checker, kill clock, release check) | Partly: 3 FOUNDER inputs | No |
| eval (done 2026-10-19) | [hermes-eval.md](hermes-eval.md) | `~/DEVELOP/pfy-mentat` | Hermes Agent vs current local path, Entry 134 | No (BEST_EFFORT, not a Feature GO) | Finished. Do not start another copy while a bench holds Ollama |
| **H1 (founder HIGH, 2026-10-19)** | [harness2-local.md](harness2-local.md) | `~/DEVELOP/pfy-mentat` (worktree `tmp/h1-harness2`, branch `bot/h1-harness2`) | Harness² fully local (own `llama-server`, `qwen3.6:35b`): pinned stage, network-limited sandbox, 48-case decision adapter, edits land only on a `bot/h2-proposal-*` branch. 2026-10-20 live result: held-out gain 0, receipt `pipelines/dogfood/harness2-local/receipt.json`, no proposal branch | Grok Bot launches it on nimo; no spend | Yes: `qwen3.6:35b`, quiet host, run alone |
| **H2 (founder HIGH, 2026-10-19)** | [skill-discovery.md](skill-discovery.md) | `~/DEVELOP/pfy-mentat` (worktree `tmp/build-skill-discovery`) | Free local discover: index Monid's MIT connector registry, our catalog, public SKILL.md sets and the MCP registry; local-model ranking; intake stubs; Monid paid runs OFF | Grok Bot launches it on nimo after H1; paid runs need a separate founder OK | Short rerank only, after H1 |
| **MVP-1** | [pfy-local-build-mvp.md](pfy-local-build-mvp.md) | `~/DEVELOP/pfy-mentat` (worktree `tmp/mvp-local-build`, branch `bot/mvp-local-build`) | Headless `./pfy build --local`: a local-model build-only run to a tested branch, plus an 8-task coding eval. Live on nimo 2026-10-26: 8/8 PASS, 572s, `qwen3.6:35b`. Not a Feature GO | No | Yes, item 3 only, quiet host |

Why atg-framework first: your Build context is already warm on that repo. Its first part (client + mock PoC suite) runs now without touching the GLM bench. And its result decides whether the pfy-mentat slice can promote ATG past I1.

Skipped on purpose: Pred-foundry, the trading desks, and GrapheneOS MDM (parked or PNNL work).

## What every prompt has

Repo path and mandatory reads · its own worktree and branch (never the founder checkout) · goal · definition of done with behavior and fail-and-recover tests (no tautological units) · a handoff doc in `docs/` · push + PR body file · gates: no merge, Tester/Reviewer merge.

## Changelog

- 2026-10-25: added `pfy-local-build-mvp.md` (MVP-1): headless `./pfy build --local` on `bot/mvp-local-build`. No founder gate. Loads a model only in item 3 on a quiet host. Not a Feature GO.
- 2026-10-19: added `skill-discovery.md` (H2, founder HIGH): free local discover over open registries; Monid paid runs stay off.
- 2026-10-19: added `harness2-local.md` (H1, founder HIGH): Harness² on local models only, sandboxed, proposals as a branch for Tester and Reviewer.
- 2026-10-20: H1 live run finished on `bot/h1-harness2`. Held-out gain 0 (15/16 vs 15/16). Receipt `pipelines/dogfood/harness2-local/receipt.json`. Entry 136 moved from I0 to I1. Not a Feature GO.
- 2026-10-19: added `hermes-eval.md` (Entry 134 bake-off; first written as 131, renumbered on 2026-10-20 because #304 took 131). The run is on `bot/hermes-eval`. Verdict NO-WIN. Not a Feature GO.
- 2026-10-06: added `atg-finish-autonomous.md` (row 1-alt) to the index, and pointed the toolsets drop-in at `sources/x-posts.md` for Entries 041, 049 and 051, which have no entry files.
- 2026-10-06: added `pfy-mentat-toolsets.md` (ranking items #3, #4, #5, #7, #8) and clarified that the Leasegrid repo is leasegrid-c.
