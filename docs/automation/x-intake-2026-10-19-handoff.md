# X intake 2026-10-19: handoff (Entries 131-133)

Daily X intake routine, window 2026-10-18T00:36Z to 2026-10-20T00:36Z (about 48 h, because the 2026-10-18 run didn't complete). Sources: Mark's latest 40 bookmarks (15 not seen before) and 272 watch-list posts. Three catalog entries at **I0**, one stdlib smoke script with a unit-test file, a folder README paragraph and `.gitignore` lines for receipts. Catalog-only; not a Feature GO. Catalog HOLD 70-75 untouched. #303 (128-130) merged at `b36234b`; this branch is cut from `main` at `b36234b`, where 130 is the highest entry.

| Entry | Tool | Why | Fits nimo? |
|------|------|-----|------------|
| 131 | [JevAgentHarness](https://github.com/JevAgentHarness/JevAgentHarness) (MIT, Python, `f2932199e1ef`) | OpenAI-compatible proxy that routes each agent step to a strong or fast model using a decision model. Its local lane speaks `POST /v1/systemone`, the wire Laya (086) serves and ADR-0016's `typesafe` lane expects. **Possible eval-auto trial** | Yes: venv under `tmp/`. Decision weights are CC BY-NC. Smoke PASS on the Grok Bot box |
| 132 | [ai-memory](https://github.com/akitaonrails/ai-memory) (MIT, Rust, v3.1.1) | Self-hosted shared memory (markdown wiki) and claim-once handoffs across 20+ harnesses, Grok Build CLI and Hermes Agent among them; zero-LLM by default. **Possible eval-auto trial** | Yes for the binary under `tmp/` with a data dir in `~/DEVELOP`. `install.sh`/`setup` (user service, harness config) need Mark. Smoke PASS on the Grok Bot box |
| 133 | [headson](https://github.com/kantord/headson) (MIT, Rust, 0.17.1) | Structure-aware head/tail: valid-JSON previews of big JSON/YAML within a byte budget, to keep receipts and API output from flooding context | Yes: one 6.4 MB static binary under `tmp/`. Smoke PASS on the Grok Bot box |

Files: `sources/entries/131-jevagentharness.md`, `132-ai-memory.md`, `133-headson.md`, `examples/x-intake-local/smoke_131_133.py` (imports `TMP`, `find_bin`, `pinned`, `run_isolated`, `timeout_reason` and `write` from `smoke.py` and `home_sig`, `finish`, `as_json`, `tmo` from `smoke_128_130.py`; every child goes through `run_isolated`; the real-HOME dirs are fingerprinted with `home_sig` before the run and in a finally), `tests/test_x_intake_smoke_131_133.py` (38 stub-based tests), a paragraph in `examples/x-intake-local/README.md`, `.gitignore` lines for `pipelines/smoke/{jah,aimemory,headson}/`, and this handoff. No TOOLS.md rows, no `data/tools.json` rows, no stage cards, no Make target. Box receipts are not committed.

Written by the routine through the GitHub connector rather than `./pfy build -p`: docs plus one stdlib script, nimo not needed.

## How to gate

On nimo each `python3 examples/x-intake-local/smoke_131_133.py --entry jah|aimemory|headson` should exit 2 with an operator reason until staged:

- jah: `git clone https://github.com/JevAgentHarness/JevAgentHarness ~/DEVELOP/pfy-mentat/tmp/jevagentharness && cd $_ && git checkout f2932199e1ef1d9f089b51d39430c87be0f560b5 && python3 -m venv .venv && .venv/bin/pip install .` (deps `aiohttp`, `pyyaml`; 11 packages). No API keys, no model download.
- aimemory: `mkdir -p ~/DEVELOP/pfy-mentat/tmp/ai-memory && cd $_ && curl -LO https://github.com/akitaonrails/ai-memory/releases/download/v3.1.1/ai-memory-linux-x86_64.tar.gz && tar xzf ai-memory-linux-x86_64.tar.gz` (tarball sha256 `d055aef2989eeceb08da7a2db3533d9389a689058c57b5f8a03d5f4439225a2d`, matching the release's `.sha256`; binary `ai-memory` sha256 `be9f539cbaaa8c583dd94a58c3817c35321f3d887e8195df91bf74f9c5eefa4b`). Never run `install.sh`, `ai-memory setup`, `ai-memory run` or a marketplace plugin install.
- headson: `mkdir -p ~/DEVELOP/pfy-mentat/tmp/headson && cd $_ && curl -LO https://github.com/kantord/headson/releases/download/headson-v0.17.1/hson-x86_64-unknown-linux-musl.tar.gz && tar xzf hson-x86_64-unknown-linux-musl.tar.gz` (tarball sha256 `90f5880efcacd16000e12e6f461e7e486ea56636d2f67243de2a65160006ac58`; binary `hson` sha256 `1a5920a7088db2f2eaf3e53c588fb5133b020a4b9aa417631977e16ead136422`).

Receipts go to `pipelines/smoke/<entry>/latest.json` (gitignored; `$PFY_SMOKE_RECEIPT_DIR` overrides).

What was checked on the Grok Bot box (all in `/tmp`, temp HOMEs, bubblewrap 0.12.0 with no network):

- **jah PASS** (0.1.0): stub upstream and stub System-One server on loopback, two `jah serve` configs. Rules: strong/fast/strong/strong as `first_steps`, `routine`, `hard` (traceback), `finish_check` (fast text answer redone by strong). Local Jev: System-One request with `model: agentdecision-4b` and `hard`/`routine` options; a decision HTTP 400 fell back to strong as `decision_error`. No auth header anywhere; no prompt text in the step logs.
- **aimemory PASS** (3.1.1): `init`, loopback `serve --transport http` with embeddings off, page write/search hit/search miss/read, markdown under `wiki/`, a cross-project message claimed once with the untrusted notice, then an empty second pop.
- **headson PASS** (0.17.1): a 315,843-byte fixture to a 600-byte strict-JSON preview with keys and first row; byte-identical rerun; `--tail` keeps the last row; `--grep FAIL` keeps the FAIL value.
- Negative paths: wrong pins (`JAH_VERSION=9.9.9`, `AI_MEMORY_VERSION=1.0.0`, `HSON_VERSION=0.1.0`) give 2; a missing binary gives 2; `PFY_XINTAKE_TIMEOUT=0.001` gives 1 with "jah version timeout after 0.001s".
- Unit tests: 38/38 OK in 16 s (stub `jah` is a small fake proxy that reads the driver's config; stub `ai-memory` keeps pages and messages in the data dir and serves `/healthz`; stub `hson`). Each check has a test that turns it false: no routing, no finish check, Jev never asked, decision errors routed fast, prompt text logged, auth header sent, proxy never up; double claim, no markdown on disk, search false positive, missing notice, server never healthy; over budget, dropped key, not JSON, nondeterministic, `--tail`/`--grep` ignored, fixture written; temp HOME writes; real-HOME writes and a chmod-only change (without bwrap); timeouts that keep the real-HOME check.
- **Not run here** (no checkout on the box): `scripts/catalog_check.py` and the full suite. 131-133 don't collide with main's entries (highest 130). Please run both on the head.

## Findings worth knowing

- **JevAgentHarness detects repeated actions**: identical tool calls go strong as `repeated_action`, before the error rule. With no decision key every step falls back to strong (`decision_error`), which is safe but saves nothing, so read `jah report` after any trial. The finish check adds a second upstream call per final answer. AgentDecision-4B/0.8B weights are **CC BY-NC 4.0**: Mark's own work only, not the paid AI-box offer.
- **ai-memory's CLI needs its server** (offline `write-page`/`search` fail), and `message send` to a project the server hasn't seen returns 404. `init` writes a root bearer token file into the data dir: keep the data dir out of git and never open or paste that file. Popped messages carry an untrusted-input notice.
- **headson `--grep` can exceed the budget** (658 bytes at `-c 600`), and the kept match lost its row `id`. The head preview samples across the array (ids 0, 149, 150, 449), not the first N rows.

## Recommended next steps (not started)

1. **Eval-auto trial: JevAgentHarness in shadow mode** vs the current ADR-0016 lane (CUA-S1-FORMS primary local). Decision model: Laya (086) or AgentDecision-4B served locally on `/v1/systemone`; tiers on Ollama (`qwen3.6:35b` strong, a small model fast). Run the 48-case decision benchmark and a few Build-sized tasks; measure the share of steps moved to fast, the success delta and the `decision_error` share. It would replace nothing at first; if it holds, it becomes the routing layer in front of the local lane and fills the `typesafe` slot without a key.
2. **Eval-auto trial: ai-memory vs cass-memory (108) and opencode-mem** for cross-harness memory. One loopback server on nimo with a data dir in `~/DEVELOP`; register its MCP by hand in Hermes Agent and Grok Build only (no `setup`), hand one task Build → Hermes and back, and check that each handoff is claimed once and the next session picks it up. It would replace ad hoc handoff notes in docs/automation if it holds.
3. headson: try it in the skills that paste smoke receipts and `gh api` output; truncate after `--grep`.

## LATER (logged, not cataloged this run)

- **AI Job Search** (Mark's bookmark). Relevant to Gom Jabbar and the remote job-search track; look at it with that work, not as a catalog tool.
- **Pipelock**, **Kontext**, **Code Buster**, **Forgetful**, **Cognee-RS**, **mcpc**, **numbat** (@DanKornas). Agent security, context and memory tools; Forgetful and Cognee-RS overlap 132 and 108.
- **Happy** (@DanKornas, MIT). App and CLI that drives Claude, Codex and Grok from one place.
- **Dexto** (@DanKornas, license NOASSERTION). YAML-defined agent harness with SDKs.
- **searxNcrawl** (@DanKornas). Self-hosted search and crawl MCP; would need a SearXNG instance.
- **earshot**, **c9watch**, **Agent Standup**, **Agent HUD** (@DanKornas). Session monitors and speech tools.
- **CAT** (license NOASSERTION), **cc-fleet**, **Open Agent Email** (@DanKornas).
- @mattpocockuk's ~5,000-token pre-commit hook prompt. Compare with the Tester checklist.
- @aisearchio's MOSS Image and Spectrum (media models). Check size and weights before any bench slot.
- @tom_doerr's Alexandrie left to Mark's weekly tom_doerr automation.

TRADING (parked desks, no action): bookmarks for a Polymarket both-sides bot (@rcom1337), a Grok trading bot (@Principia_X), @MrMilkTrading, a Grok portfolio post (@ralliesarena), a Jane Street/Kelly sizing thread (@velesxbt); @ch3nweiii's posts on @hanakoxbt.

SKIPPED: macOS-only tools, Roblox, LinkedIn and SEO tools, off-scope @DanKornas repos (browser forks, Salesforce, RAG sites, team chat platforms), money and marketing bookmarks, papers and opinion posts, and replies.

## Locks respected

Catalog 70-75 HOLD untouched. Nothing installed or downloaded on nimo. Mark's main checkout and stashes untouched; no pfy-mentat checkout was made (files read through the GitHub connector). No accounts, sign-ins, paid keys or spend. JevAgentHarness, ai-memory and headson ran only on the Grok Bot box in `/tmp` with temp HOMEs; no model or agent CLI was started, and ai-memory's token file was never opened.

## How this fails / how we recover

| Risk | How it fails | Recovery |
|------|----------------|----------|
| Entry numbers collide | Another branch also adds 131-133 | Renumber on rebase; entries are self-contained files |
| Smoke in CI without prereqs | Exit 2 read as red | Not wired into CI or Make; exit 2 is the honest "can't run here" |
| A tool writes to the real HOME | `~/.jah`, `~/.local/share/ai-memory`, `~/.config/ai-memory` or `~/.local/state/headson` changes on nimo | The smokes fingerprint those dirs (`home_sig`) before the run and in a finally, and FAIL on any change, also on timeout. Writes outside the watched dirs are not seen |
| Loopback port race | A free port is taken between pick and bind | The driver reports `*_proxy_up`/`server_healthy` false and the smoke FAILs; rerun |
| `smoke_128_130` helpers change | Import breaks | The tests import the smoke end to end; move `home_sig` into `smoke.py` if it's reused again |
