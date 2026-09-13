# Module: Catalog ask / queue (`scripts/pfy_catalog_ask_queue_209.py`)

**Purpose:** Usable catalog browse from Tools, ask the attached TUI to implement a tool for the next launch, or queue a GitHub issue for Design→DevBot. Cite #209.

## Human operator

- What: Tools lists a usable catalog subset (name, category, github, stage, notes, status) — not a scores-only dump. **Ask TUI implement** writes a paste/auto-handoff prompt. **Queue for org** opens a GitHub issue.
- How: [docs/ops/catalog-ask-queue.md](../ops/catalog-ask-queue.md)
- Failures: no attached harness → FAIL + Attach grok|opencode|hermes. HOLD 70–75 or incomplete → SKIP (not auto-lifted). One integration at a time.
- Recovery: Attach a TUI; pick a complete non-HOLD row; finish or cancel the pending item.

## Agent

- Entry: `scripts/pfy_catalog_ask_queue_209.py` (`--selftest` / `--browse` / `--ask NAME` / `--queue NAME` / `--status`).
- Callers: `./pfy catalog …` payload; board `catalog_ask` / `catalog_queue`; `POST /catalog/ask` `/catalog/queue`; Tools HTML+tk.
- Invariants: no Env nav tab; no scores-only dump; HOLD 70–75 not auto-lifted; no Mark git/npm/CI; do not reopen #76.
- Issue **#209** only.

## Architecture link

Operator-stack layer (board/gui + `./pfy` catalog), not a catalog triple-write.
