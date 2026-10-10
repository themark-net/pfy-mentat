# Daily X intake handoff — 2026-10-09

Routine: daily X intake for pfy-mentat (Grok Bot). Sources this run: Mark's new X bookmarks and the watch list (@tom_doerr, @FurqanR, @DanKornas and the rest of the routine's list) since the last run. Deduped against TOOLS.md, `data/tools*.json`, `sources/` (including the weekly Tom Dörr pull) and the routine's own log; none of the three tools below appeared anywhere in the catalog. Previous X intake slice (Entries 098-100) merged as PR #281; Entries 101-102 came in from other work.

## What this slice adds

| Entry | Tool | Why | Runs on nimo? |
|------|------|-----|---------------|
| 103 | [BugPatrol](https://github.com/agent-labs-dev/bugpatrol) | Autonomous QA patrol: explorer, judge, fixer (off by default), retest in the running app; agents on CLI agents or a custom OpenAI-compatible endpoint | Yes, Node 22+ CLI under `tmp/`, model via local Ollama only. Smoke PASSed on the Grok Bot box against a fake local endpoint |
| 104 | [GraphJin](https://github.com/dosco/graphjin) | Governed GraphQL + MCP over DBs, files and code, with `read_only` sources and production query allow-lists; SQLite supported | Yes, single Go binary under `tmp/`. Smoke PASSed on the Grok Bot box |
| 105 | [anti-slop](https://github.com/miqdadbadjuber/anti-slop) | SKILL.md rule packs that filter generic AI UI, copy and code comments; Design Bot and Reviewer lanes | Yes, plain files in a clone under `tmp/`. Smoke PASSed on the Grok Bot box |

Files: `sources/entries/103-bugpatrol.md`, `104-graphjin.md`, `105-anti-slop.md`, `examples/x-intake-local/smoke_103_105.py` (three new checks that reuse the helpers in `smoke.py`; `smoke.py` and `smoke_098_100.py` are unchanged), the folder README, and this handoff. No TOOLS.md rows, no `data/tools.json` rows, no stage cards, no Make target. Box receipts are not committed; commit receipts only from a real nimo run.

This slice was written by the routine directly through the GitHub connector rather than `./pfy build -p`, since it is docs plus one stdlib script and nimo was not needed for it.

## How to gate

On nimo each `python3 examples/x-intake-local/smoke_103_105.py --entry bugpatrol|graphjin|antislop` should exit 2 with an operator reason, since nothing is staged under `~/DEVELOP/pfy-mentat/tmp` yet. To get a PASS, stage what the reason names:

- bugpatrol: `npm install --prefix ~/DEVELOP/pfy-mentat/tmp/bugpatrol bugpatrol@0.3.0`, plus Node 22+ (the official node-v22 linux-x64 tarball unpacked to `~/DEVELOP/pfy-mentat/tmp/bugpatrol/node` if the system Node is older). No model is used; the smoke serves its own fake endpoint.
- graphjin: `graphjin_3.21.6_linux_amd64.tar.gz` from the v3.21.6 release, checked against `checksums.txt`, extracted to `~/DEVELOP/pfy-mentat/tmp/graphjin/graphjin` (binary sha256 `e6f0fd88f99b07e8036ba7db76f24f0fceab697935559d154e823b5951f46805`).
- antislop: `git clone https://github.com/miqdadbadjuber/anti-slop ~/DEVELOP/pfy-mentat/tmp/anti-slop`.

Or point `$BUGPATROL_BIN`/`$BUGPATROL_NODE`, `$GRAPHJIN_BIN`, `$ANTISLOP_DIR` at a staged copy. Receipts go to `pipelines/smoke/<entry>/latest.json`. Each smoke FAILs (exit 1) on a model call to anything but the local endpoint, a no-endpoint config being accepted, a candidate from a model that never called a tool, a write landing under `read_only`, a refused control insert, an ad-hoc query running in production, or invalid skill frontmatter.

What was checked on the Grok Bot box (all in `/tmp`): the PASS path for all three, and the negative paths: Node 20 only gives exit 2, a wrong `$GRAPHJIN_SHA256` gives exit 2 without exec, a skill renamed to `AntiSlop UI` gives exit 1, and a 0.01s timeout gives exit 1 with "graphjin did not come up".

## Recommended next steps (not started)

1. **Eval-auto trial: BugPatrol vs the Tester-bot GUI checks / CUA lane** on one pfy-mentat GUI PR. Throwaway worktree under `~/DEVELOP/pfy-mentat/tmp`, explorer and judge on `via: custom` at nimo's Ollama `/v1/chat/completions` with the decision-bench pick, fixer and GitHub off, `bugpatrol review <pr> --dry-run`. Compare its findings with Tester's on the same PR. Start with a CLI or HTTP API target; a web target needs Playwright Chromium with `PLAYWRIGHT_BROWSERS_PATH` under `tmp/` (the default cache is outside `~/DEVELOP`) and a local model that can read screenshots. Run it when nimo isn't in a benchmark.
2. GraphJin: point a `read_only: true`, `production: true` instance at a copy of one pfy-mentat SQLite file (or a CodeSQL index of the repo) and try its MCP stdio server from one bot lane with saved queries only.
3. anti-slop: one with/without run in the Design Bot lane (core + `antislop-ui`) and one Reviewer audit (After mode) on a docs PR; keep it only if it finds something our own checks miss without blocking normal output.

## LATER (logged, not cataloged this run)

- **Codync** — https://github.com/leepokai/Codync (Apache-2.0, Rust). Message local coding agents (Claude Code, Codex, Cursor, Gemini and more) as bots from phone/desktop/terminal. Overlaps what Grok Bot already does for Mark; revisit if we want a self-hosted bot bridge on nimo.
- **llm_wiki** — https://github.com/nashsu/llm_wiki (TypeScript, desktop app, no SPDX license detected at this read). An LLM incrementally builds and maintains a linked wiki from your documents instead of per-query RAG. Revisit for pfy-mentat `sources/` and handoff-doc upkeep once the license is clear and it can run on a local model.

## Locks respected

Catalog 70-75 HOLD untouched. Nothing installed or downloaded on nimo. Mark's main checkout untouched; the repo was not cloned anywhere. No accounts, sign-ins, paid keys or spend. Tools were tested only on the Grok Bot box in `/tmp`, and BugPatrol only ever talked to a stdlib fake model on 127.0.0.1.

## How this fails / how we recover

| Risk | How it fails | Recovery |
|------|----------------|----------|
| Entry numbers collide | Another branch also adds 103-105 | Renumber on rebase; entries are self-contained files |
| Smoke in CI without prereqs | Exit 2 read as red | Not wired into CI or Make; exit 2 is the honest "can't run here" |
| BugPatrol config or output changes | 0.x release renames keys or the candidate summary | Smoke FAILs with a "shape changed?" reason; pin `bugpatrol@0.3.0` |
| GraphJin enforcement changes | `read_only` or allow-list behavior shifts in a release | Binary sha is pinned; the control run proves the read_only check still bites |
| anti-slop renames skills | Frontmatter or folder names change | Smoke FAILs; pin the checked commit `388cbe3b6c37` |
