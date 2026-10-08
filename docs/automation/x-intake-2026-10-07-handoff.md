# Daily X intake handoff — 2026-10-07

Routine: daily X intake for pfy-mentat (Grok Bot). Sources this run: Mark's new X bookmarks since the last run and the watch list (@tom_doerr, @yume_arasaki, @mattpocockuk, @_avichawla, @FurqanR, @aisearchio, @DanKornas, @alex_verem, @ch3nweiii) since 2026-10-07 00:28 UTC. Deduped against TOOLS.md, `data/tools*.json`, `sources/` (including the weekly Tom Dörr pull) and the routine's own log. Previous slice (Entries 095-097) merged as PR #278.

## What this slice adds

| Entry | Tool | Why | Runs on nimo? |
|------|------|-----|---------------|
| 098 | [Sponsio](https://github.com/SponsioLabs/Sponsio) | Deterministic tool-call contracts (LTL monitors), block/escalate/redirect, no LLM at runtime; shell, filesystem, destructive bundles | Yes, pure Python in a venv under `tmp/`. Smoke PASSed on the Grok Bot box |
| 099 | [Open Steps](https://github.com/kharmanskyi/open-steps) | Done-or-not / check-work skills plus a stop hook that refuses to end a session until it writes a report | Yes, bash + git. Smoke PASSed on the Grok Bot box |
| 100 | [repository-harness](https://github.com/hoangnb24/repository-harness) | AGENTS.md + docs map protocol with a checksum-verified three-way-merge updater | Yes, single binary under `tmp/`. Smoke PASSed on the Grok Bot box |

Files: `sources/entries/098-sponsio.md`, `099-open-steps.md`, `100-repository-harness.md`, `examples/x-intake-local/smoke_098_100.py` (three new checks that reuse the helpers in `smoke.py`, which is unchanged), the folder README, and this handoff. No TOOLS.md rows, no `data/tools.json` rows, no stage cards, no Make target. Box receipts are not committed; commit receipts only from a real nimo run.

This slice was written by the routine directly through the GitHub connector rather than `./pfy build -p`, since it is docs plus one stdlib script and nimo was not needed for it.

## Recommended next steps (not started)

1. **Eval-auto trial: Sponsio vs the planned destructive_command_guard step** in the toolset drop-in (`docs/build-dropins/pfy-mentat-toolsets.md`). Run the CUA lane or one `./pfy build -p` worktree loop in Sponsio observe mode with the shell + filesystem bundles plus two org rules written as contracts (no writes outside `~/DEVELOP`, tests before merge). Promote to enforce only if it catches a seeded bad call with no false blocks on a normal run.
2. Open Steps: wire only `stop-report.sh` around one long Build run on a scratch worktree and check whether it gets a handoff out of the run without a human prompt. Keep the pack's merge-when-green behavior off.
3. repository-harness: run `harness install --dry-run --json` against a scratch copy of a small product repo and diff its AGENTS.md/docs layout against our `agents-md-in-every-product-repo` router before deciding anything.

## Locks respected

Catalog 70-75 HOLD untouched. Nothing installed or downloaded on nimo. Mark's main checkout and stashes untouched. No accounts, sign-ins or spend. Tools were tested only on the Grok Bot box in `/tmp`.

## Triage log

Full log is kept by the routine at `/workspace/x-intake/candidates.jsonl` on the Grok Bot box. Held for a later run: Honeycomb (cross-harness agent memory, AGPL-3.0 plus a Deeplake/pg_deeplake backend; compare with opencode-mem), project-progress-mcp (Zig MCP for project goals and progress; no license file), morluto/rea (agent reverse-engineering MCP, MIT), good-css (frontend CSS skill, for Design), Voxyz "project map" subagent idea, skillshare (overlaps Entry 075 asm). Skipped: toolgate and the @_avichawla Jev RAG post (need a TypeSafe key), DSH Mobile (DeepSeek harness port), VibeFrame (paid video providers), CYBER-FROST part 2 (DGX/EXL3), Kandinsky 6 and video-shotcraft (video generation), Airgorah (WiFi attack tool), ReachAI, IDEM, ArtCraft, tlgr, Termish, IELTS, bunqueue and other off-scope tools, plus health, crypto and news posts. Futures-Ledger-Forge is logged only, tagged for the parked trading desks.

## How this fails / how we recover

| Risk | How it fails | Recovery |
|------|----------------|----------|
| Entry numbers collide | Another branch also adds 098-100 (095 already collided once) | Renumber on rebase; entries are self-contained files |
| Smoke in CI without prereqs | Exit 2 read as red | Not wired into CI or Make; exit 2 is the honest "can't run here" |
| Sponsio alpha API changes | `guard_before` result shape changes and the probe FAILs | The receipt records the raw output; pin 0.2.0a17 in the venv |
| Open Steps hook contract changes | Stop hook stops using exit 2 | Smoke FAILs on the dirty-stop check; pin the checked commit `4fa744ba8ea0` |
