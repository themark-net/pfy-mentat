# Daily X intake handoff — 2026-10-06

Routine: daily X intake for pfy-mentat (Grok Bot). Sources this run: Mark's new X bookmarks since 2026-10-05 and the watch list (@tom_doerr, @yume_arasaki, @mattpocockuk, @_avichawla, @FurqanR, @aisearchio, @DanKornas, @alex_verem, @ch3nweiii) since 2026-10-06 00:30 UTC. Deduped against TOOLS.md, `data/tools*.json`, `sources/` (including the weekly Tom Dörr pull) and the routine's own log. Previous slice (Entries 086-088) merged as PR #267.

## What this slice adds

| Entry | Tool | Why | Runs on nimo? |
|------|------|-----|---------------|
| 095 | [Qwen3.8-Flash-Next](https://huggingface.co/Qwen/Qwen3.8-Flash-Next) | 180B MoE, ~6B active; smallest GGUFs ~66-68 GB fit the post-carve GPU budget | Plausible, unproven. Smoke exits 2 until a server is running it |
| 096 | [Sandlock](https://github.com/multikernel/sandlock) | Rootless Landlock + seccomp sandbox for agent commands; COW dry-run; host allowlist | If nimo's kernel is 6.12+. Smoke PASSed on the Grok Bot box |
| 097 | [Foremerge](https://github.com/naw103/foremerge) | Intent-level conflict detection for parallel agents in one repo | Yes (single binary under `~/DEVELOP/pfy-mentat/tmp`). Smoke PASSed on the Grok Bot box |

Files: `sources/entries/095-qwen38-flash-next.md`, `096-sandlock.md`, `097-foremerge.md`, `examples/x-intake-local/` (stdlib smoke + README), this handoff. No TOOLS.md rows, no `data/tools.json` rows, no stage cards, no Make target. Box receipts are not committed; commit receipts only from a real nimo run.

## Recommended next steps (not started)

1. **Eval-auto trial: Qwen3.8-Flash-Next vs `qwen3.6:35b`** on the 48-case decision benchmark. Download ISTA-DASLab GSQ-RCO Q2_0 (~66 GB) into `~/DEVELOP/pfy-mentat/tmp`, serve it with llama.cpp (try ROCm and Vulkan) under the 85 GB limit with a modest context, run the smoke, then the benchmark. Promote only on a quality win; document any lockup per the memory-edge rule. Must wait until nimo is free of the current benchmark and atg-framework runs.
2. Sandlock: check `uname -r` on nimo, unpack the release binary under `tmp/sandlock/`, run the smoke, then try wrapping one `./pfy build -p` worktree run with writes pinned to that worktree.
3. Foremerge: a two-agent trial on a scratch worktree pair under `~/DEVELOP/pfy-mentat/tmp` (no `setup`).

## Locks respected

Catalog 70-75 HOLD untouched. Nothing installed or downloaded on nimo. Mark's main checkout and stashes untouched. No accounts, sign-ins or spend. Binaries were tested only on the Grok Bot box in `/workspace`.

## Triage log

Full log is kept by the routine at `/workspace/x-intake/candidates.jsonl` on the Grok Bot box. Strong candidates held for a later run: Intent-Router (IntentSpec contracts before routing), ai-rulez (one source for AGENTS.md and other agent configs), Meta Skill, NodeDB agent memory, Better Code Review Graph, plus the earlier later-list (cloudflare/security-audit-skill, coop, hackmyagent, Andon, mcptoon, microsoft/apm). Skipped: Reflection Beam (501B, weights not out, far over nimo), CYBER-FROST (de-refused fine-tune, DGX/EXL3), deepseek-harness-jev and the @ch3nweiii Jev checklist (need a TypeSafe key), LangGraph (already tracked), Ponytail (already tracked), off-scope tools (ministack, DeskVNC, SpaceO macOS-only, altium MCP, ERPNext Jarvis, OASM), and money/news posts.

## How this fails / how we recover

| Risk | How it fails | Recovery |
|------|----------------|----------|
| Entry numbers collide | Another branch also adds 095-097 | Renumber on rebase; entries are self-contained files |
| Smoke in CI without prereqs | Exit 2 read as red | Not wired into CI or Make; exit 2 is the honest "can't run here" |
| Foremerge CLI changes | JSON shape changes in a later release and the smoke FAILs | The receipt records the raw output; fix the smoke against the pinned v0.5.1 behavior |
