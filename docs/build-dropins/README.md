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

Why atg-framework first: your Build context is already warm on that repo. Its first part (client + mock PoC suite) runs now without touching the GLM bench. And its result decides whether the pfy-mentat slice can promote ATG past I1.

Skipped on purpose: Pred-foundry, the trading desks, and GrapheneOS MDM (parked or PNNL work).

## What every prompt has

Repo path and mandatory reads · its own worktree and branch (never the founder checkout) · goal · definition of done with behavior and fail-and-recover tests (no tautological units) · a handoff doc in `docs/` · push + PR body file · gates: no merge, Tester/Reviewer merge.

## Changelog

- 2026-10-06: added `atg-finish-autonomous.md` (row 1-alt) to the index, and pointed the toolsets drop-in at `sources/x-posts.md` for Entries 041, 049 and 051, which have no entry files.
- 2026-10-06: added `pfy-mentat-toolsets.md` (ranking items #3, #4, #5, #7, #8) and clarified that the Leasegrid repo is leasegrid-c.
