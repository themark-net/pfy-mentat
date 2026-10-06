# Daily X intake handoff — 2026-10-05

Routine: daily X intake for pfy-mentat (Grok Bot). It catches tools from Mark's X bookmarks and a watch list, dedupes them against this repo's catalog (TOOLS.md, `data/tools*.json`, `sources/` including the weekly Tom Dörr pull described in `docs/automation/tom-doer-monitor.md`), and lands at most three I0 entries per run.

## What this slice adds

| Entry | Tool | Why | Runs on nimo? |
|------|------|-----|---------------|
| 086 | [Laya](https://github.com/NandhaKishorM/laya) | Open-weight typed decisions (choice / score / yes-no) on CPU. `laya-serve` speaks the same `POST /v1/systemone` wire protocol as TypeSafe Jev | Likely (322M–421M params, CPU fp32). Smoke PASSed on the Grok Bot box CPU (billing, 0.9865, 16.9 s incl. first download). On nimo it exits 2 until a venv exists under `~/DEVELOP/pfy-mentat/tmp/` |
| 087 | [Bespoke Nimble](https://github.com/bespokelabsai/nimble) | Open data + recipe + 9B model for Jev-style decisions, with published evals | No as documented (needs NVIDIA BF16 or Apple Silicon). Smoke exits 2 |
| 088 | [Beacon](https://github.com/asymptote-labs/agent-beacon) | Cross-harness session capture (lists Grok Build) that turns corrections into reusable skills | Only via user-mode install, Local destination, skills install off. Smoke exits 2 until installed |

Files: `sources/entries/086-laya.md`, `087-bespoke-nimble.md`, `088-agent-beacon.md`, `examples/typed-decisions-local/` (stdlib smoke + README), this handoff. No TOOLS.md rows, no `data/tools.json` rows, no stage cards, no Make target, no env var. `scripts/catalog_check.py` is unaffected.

## Recommended next step (not started)

Eval-auto trial of Laya against the ADR-0016 decision lanes: run `laya-serve` bound to 127.0.0.1 on nimo, repoint the `typesafe` lane's base URL at it, and score it against CUA-S1-FORMS on the same live Choice options at the ~0.85 gate. If it holds up, it fills the TypeSafe slot locally with no key. This needs a separate slice and is not a Feature GO.

## Locks respected

Catalog 70–75 HOLD untouched. Nothing installed on nimo. Mark's main checkout and stashes untouched. No accounts, sign-ins or spend.

## Triage log

Full candidate log (every post seen, verdict and reason) is kept outside the repo by the routine at `/workspace/x-intake/candidates.jsonl` on the Grok Bot box. Notable skips this run: repowise (already Entry 006), Kolibri-1 (already Entry 085), mattpocock/skills v1.3 (already Entry 008; `/retro` and `/pr` are worth a note on that row later), the Jev-API stack from @ch3nweiii (JevRouter, blink, jev-guard, Edward, foreman and others all need a TypeSafe key), fastbrowse (Jev-based), kimi-k3-in-c (claims a 2.78T model on one CPU in 8 GB RAM; read as an offload demo, not a serving path, and not checked), and trailofbits/coop (isolated VM for Claude Code/Codex; overlaps agent-cage, a candidate for a later run). Trading tools (hypergrok-trading-desk, tradingview-mcp) were logged for the parked desks only.

## How this fails / how we recover

| Risk | How it fails | Recovery |
|------|----------------|----------|
| Entry numbers collide | Another branch also adds 086–088 | Renumber on rebase; entries are self-contained files |
| Smoke run in CI without prereqs | CI calls the smoke and treats exit 2 as red | It's not wired into CI or Make. Exit 2 is the honest "can't run here" |
| Receipts committed by accident | A local run writes `pipelines/smoke/<entry>/latest.json` | Same pattern as Kolibri-1; commit receipts only from a real nimo run |
