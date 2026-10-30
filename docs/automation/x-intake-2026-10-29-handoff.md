# X intake 2026-10-29: handoff (Entry 149)

Daily X intake routine, window 2026-10-29T00:42Z to 2026-10-30T00:35Z. Sources: Mark's 40 latest bookmarks (8 new, one on-core) and the watch-list posts (4 pages, 77 posts; nothing from @tom_doerr in the window). One catalog entry at **I0**, one stdlib smoke script with a unit-test file and a `.gitignore` line for its receipt. Catalog-only; not a Feature GO and nothing here competes with the pfy-mentat MVP. Catalog HOLD 70-75 untouched. Branch cut from `main` at `6b04ba8` (highest entry 148).

| Entry | Tool | Why | Fits nimo? |
|------|------|-----|------------|
| 149 | [MemPalace](https://github.com/MemPalace/mempalace) (MIT, v3.12.0) | Local-first verbatim agent memory with wing/room scoped search, hybrid ranking, an MCP server and a published LongMemEval score. **Eval-auto trial candidate** against cass-memory (108) and ai-memory (132) | Expected yes (Python + ChromaDB, CPU embeddings). Smoke PASS on the box; not staged on nimo yet (smoke exits 2 there until it is) |

Files: `sources/entries/149-mempalace.md`, `examples/x-intake-local/smoke_149.py` (self-contained, stdlib only), `tests/test_x_intake_smoke_149.py` (10 stub tests), `.gitignore` line for `pipelines/smoke/mempalace/`, and this handoff. No TOOLS.md rows, no `data/tools.json` rows. Written on the Grok Bot box and pushed through the GitHub connector. No PR, per Mark's 2026-10-19 rule: gate this branch at its pinned head, then fast-forward `main`.

## How to gate

```sh
python3 -m unittest tests.test_x_intake_smoke_149   # 10 tests, no MemPalace needed
python3 examples/x-intake-local/smoke_149.py         # exit 2 unless staged; PASS when staged
python3 scripts/catalog_check.py
```

To stage on nimo (inside DEVELOP only): `python3 -m venv ~/DEVELOP/pfy-mentat/tmp/mempalace/.venv && ~/DEVELOP/pfy-mentat/tmp/mempalace/.venv/bin/pip install git+https://github.com/MemPalace/mempalace.git@84582fb055a6429261f9c779da86c0561ec80adc`, then warm the embedder once with `HOME=~/DEVELOP/pfy-mentat/tmp/mempalace/home` (one `init` + `mine` + `search` on a scratch copy), then rerun the smoke.

Checked on the box: smoke PASS (2 drawers filed, both fixture queries rank the right note first, bwrap with no network, real-HOME paths unchanged). Unit tests 10 OK. `scripts/catalog_check.py` not run on the box for this branch.

## Triaged and skipped this run

- DeepSeek V4.1 Flash low-RAM long-context claim (bookmark) and @yume_arasaki's DGX Spark benchmark receipts: model news and NVIDIA-only recipes, already skipped in earlier runs.
- Prefix-aware LLM routing (@_avichawla, NVIDIA Dynamo KV router): multi-GPU cluster technique; single-node llama.cpp/vLLM prefix caching already covers nimo.
- Claude Code `/doctor prompt-audit` (@ch3nweiii): Claude Code only.
- mattpocock skills fixes (`/pr`, Codex subagent context): mattpocock/skills already cataloged.
- @alex_verem's "9 free apps" list (Open WebUI, OpenCode, ComfyUI, Vane, Meetily, Chatterbox, Immich, AppFlowy, OpenBot): already cataloged or off-core.
- Bookmarks: Grok Bot template catalogs and a Grok Bot skills site (about Grok Bot itself, not pfy-mentat), cold-email and domain stacks, a buy-borrow-die finance post (off-core; no action).

## Recommended next step (after the MVP)

Stage MemPalace on nimo, mine pfy-mentat's `docs/` handoffs into a scratch palace, and score recall on 20 questions whose answers live in those docs, side by side with cass-memory and ai-memory.
