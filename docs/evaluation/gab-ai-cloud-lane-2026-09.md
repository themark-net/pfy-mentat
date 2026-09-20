# Evaluation: Gab AI — published code, model-selection posture, cloud lane (research 2026-09)

**Status:** research note, read-only · **Date:** 2026-09-20 (rev. 2, refocused on published code + model evaluation per owner) · **Scope:** what Gab AI has actually published as code or harness adapters, how it selects among many models, and what the #228 lane / ADR-0017 hedge can borrow from it · **Related:** [ADR-0017](../adr/0017-product-catalog-evaluation-handoff-harness.md), [ADR-0014](../adr/0014-pluggable-local-inference-spine.md), [gab-228.md](../ops/gab-228.md), `scripts/pfy_gab_228.py`, `scripts/fixtures/gab_models_v1.json`, `examples/eval-harness/`.
**Method:** primary artifacts only where marked *high*: the npm tarball of `@gabai/pi-gab-ai@0.3.0` (read in full), a live `GET https://gab.ai/v1/models` (2026-09-20 05:52 UTC, 134 ids / 59 text), live `GET /v1/agent-setup` for all four clients plus 18 non-clients, gab.ai docs pages with `Last updated` stamps, GitHub/GitLab/npm/Hugging Face API probes, Gab's own news posts, the Gab AI Inc. SEC Reg A annual report. No authenticated calls; no billing observed on a real invoice. **Outage note:** between ~06:00 and ~06:20 UTC every gab.ai path (docs, `/v1/models`, `/llms.txt`, `/v1/agent-setup`) returned Cloudflare **502 Bad Gateway**; API endpoints were re-verified after recovery, docs pages were not (their content is from 05:5x captures or search-index text).

## Summary (5 lines)

1. **Published code is one small MIT package.** `@gabai/pi-gab-ai` (npm, 0.1.0→0.3.0, last 2026-08-14, ~1,800 lines TS) is a **Pi client plugin** — a provider registration over the OpenAI-completions API plus 16 Gab-API tools — not a router, not a model, not an SDK. The only other Gab code on the public web is the AGPL Gab Social archive zip (Mastodon fork, June 2026), an empty `Hoist` repo, and 2019–2024 Dissenter browser repos. **No model code, weights, evals, or router source exist anywhere public.**
2. **The real "adapters" are server-side.** `GET /v1/agent-setup?client=cursor|opencode|openclaw|claude-code` (exactly four; any other value returns the four-client bundle) emits harness configs from the live catalog, but with 8–12-slug model prefixes; docs pages add Codex and Pi recipes. These map one-to-one onto this repo's toolset × harness matrix cells and are worth *citing and consuming*, not cataloguing as code.
3. **Model selection is metadata-driven and opaque.** Each model carries `capabilities.*`, `credit_cost{base_cost, context_threshold}`, `context_window`, `recommended_for`; but `recommended_for` is `["coding","agents"]` on 52 of 59 text models (a blanket tag), and the `auto` router's tier→slug mapping is undisclosed by design ("configurable and can change … not a stable API contract", "admin quick default"). No benchmarks, no eval methodology, no model cards are published; Torba's only stated criterion is affordability ("we take multiple open source models and build layers on top").
4. **Reusable as process, not code:** classify the kickoff once (quick / standard / hard + non-coding intents) → pick the cheapest tier whose capability flags satisfy the task → pin it for the tool loop → record the *resolved* model and *settled* cost as a receipt, distinct from the pre-call *hold* estimate → pin cheap explicit models for side-calls (compaction, titles). Gab's user-facing "model comparison" tool (same real prompt, 2–5 models, explicit criteria, repeat for variance, structured verdict) is a sane shape for our model-lane golden runs.
5. Billing (credits, 1-credit floor, `usage.credits_used`, `/v1/credits`, 10k req/day) and ToS (API automation OK; no competing-model use of Output; one key per operator) are unchanged from rev. 1 and trimmed below. Catalog verdict unchanged: Stage 0 self-host **FAIL**, provisional **C-tier** *Proxy & Routing*, cite-and-consume.

## A. Published code inventory

Everything attributable to Gab AI Inc. / Andrew Torba / `gab-ai-inc` / `GabOpenSource` / `@gabai` that is code or code-adjacent. "Stage 0" = CATEGORIZATION.md gate (self-hostable <5 min · licence OK · runnable hello-world).

| # | Artifact | URL | Licence | Last activity | What it is | Stage 0 | Catalog or cite? |
|---|----------|-----|---------|---------------|------------|---------|------------------|
| A1 | **`@gabai/pi-gab-ai`** (npm) | https://www.npmjs.com/package/@gabai/pi-gab-ai · docs https://gab.ai/docs/pi-cli | **MIT** (LICENSE in tarball) | 0.3.0 published **2026-08-14**; 0.1.0/0.2.0 on 2026-05-19; maintainer `gabai <legal@gab.ai>` | Pi (`@earendil-works/pi-coding-agent`) **extension**: registers provider `gab` (`api: "openai-completions"`, base `https://gab.ai/v1`), `/gab` command, 16 `gab_*` tools. See A1 review below. | PASS/PASS/PASS — but only meaningful inside Pi | **Cite.** Not a tool in its own right; useful as the reference for how Gab expects a harness to consume `/v1/models?type=text`. Catalog only if Pi itself is catalogued. |
| A2 | `gitlab.com/GabAIInc/pi-gab-ai` (source repo named in package.json) | https://gitlab.com/GabAIInc/pi-gab-ai | MIT (per package) | unknown | Declared source of A1 | — | **Not verifiable:** web URL returns 302 (login), GitLab group API 404. Treat the npm tarball as the source of truth. No `test/` directory ships in the tarball although `package.json` references `test/*.test.mjs`. |
| A3 | **`GET /v1/agent-setup?client=…`** (exactly 4 clients; any other value returns the 4-client bundle) | https://gab.ai/v1/agent-setup?client=cursor · opencode · openclaw · claude-code | n/a (API output) | live; catalog-driven | Server-generated **harness adapter configs** (see A-adapters table) | n/a (SaaS) | **Consume.** These are the direct analogue of our `toolset plan(gab, <harness>)` output; model lists are 8–12-slug prefixes, so always merge with `/v1/models`. |
| A4 | Docs SDK snippets (Python/Node OpenAI SDK, cURL, Codex env, Claude Code env, Cursor custom-model steps, OpenCode `opencode.json`) | https://gab.ai/docs/api · /docs/api-auth · /docs/api-endpoints · /docs/codex-cli · /docs/claude-code · /docs/cursor-ide · /docs/opencode · /docs/pi-cli | n/a | pages stamped 2026-08-08 … 2026-09-08 | Standard OpenAI/Anthropic SDK usage with base URL swapped | n/a | Cite. |
| A5 | `GabOpenSource/gab-social` | https://github.com/GabOpenSource/gab-social (also `code.gab.com/gab/social` → 301 here) | **AGPL-3.0** (README statement) | pushed **2026-06-08**; 34 ★, 7 forks, 6 issues | Archive **zip** (`gab-opensource.zip`, ~52 MB) of the Gab Social Mastodon fork; no browsable tree | FAIL (zip drop, no quickstart) | Cite only; not AI. |
| A6 | `GabOpenSource/Hoist` — "Make third-party first-party." | https://github.com/GabOpenSource/Hoist | none | created 2026-05-16 | **Empty** (size 0, no README, no licence) | FAIL | Ignore; watch name only. |
| A7 | `gab-ai-inc/*` (7 repos: `defiant-browser`, `defiant-core`, `defiant-ui`, `dissenter-ios`, `gab-dissenter-extension`, `gab-share-extension`, `defiant-extension-list`) | https://github.com/gab-ai-inc | MPL-2.0 / Apache-2.0 | last push **2024-06-09** (most 2019–2021) | Dissenter browser (Brave fork) and extensions | n/a | Cite as history; no AI. |
| A8 | Third-party, **not Gab**: `indyfive11/gabagent` (Claude-Code-style CLI on Gab API, env `GABAI_API_KEY`) | https://github.com/indyfive11/gabagent | see repo | 2026 | Hobby client; origin of the repo's `GABAI_API_KEY` fallback | — | Cite only; do not treat as Gab's variable name. |
| A9 | `GET /openapi.json`, `GET /llms-full.txt` | https://gab.ai/openapi.json · /llms-full.txt | n/a | referenced in docs | **404** on 2026-09-20 05:5x (before the outage) — documented but not served | — | Nothing to cite. |
| A10 | Hugging Face | api: `?author=GabAI`, search "gab arya" | — | — | **No models, no org.** | — | Nothing exists. |
| A11 | Model weights, model cards, training reports, eval harnesses, router source, Arya system prompt (official) | — | — | — | **Nothing published.** The 2024 Arya prompt exists only as third-party leak reproductions (WIRED, HN). | — | Nothing exists. |
| A12 | Gists / Torba personal GitHub / GabAIInc GitHub org | — | — | — | None found (`api.github.com/orgs/GabAI` 404; no gists surfaced). | — | Nothing exists. |

### A1 review — `@gabai/pi-gab-ai@0.3.0` (tarball read in full)

Files: `extensions/gab-ai.ts` (1,085 lines), `extensions/catalog.ts` (517), `extensions/auth.ts` (171), `scripts/smoke-test.mjs` (99), README, CHANGELOG, LICENSE. Zero runtime deps; optional peer `@earendil-works/pi-coding-agent`.

- **What it does.** `pi.registerProvider("gab", { baseUrl, api: "openai-completions", models })` with a **bundled** 43-model chat catalog, replaced at startup and on `/gab refresh` by `GET /v1/models?type=text` filtered by `isChatModel()` = `capabilities.text && !images/video/audio/embeddings && (function_calling || recommended_for ∋ "coding")`. Auth: `GAB_API_KEY` → `GAB_AI_API_KEY` → Pi auth store (`getProviderAuthStatus`/`getApiKeyForProvider`, with `~/.pi/agent/auth.json` fallback, 0600). Base override `GAB_AI_BASE_URL` / `GAB_BASE_URL`. Tools: `gab_get_credits`, `gab_get_usage`, `gab_list_models`, `gab_generate_image`, `gab_edit_image`, `gab_generate_video`, `gab_text_to_speech`, `gab_create_embeddings`, `gab_upload_file`/`list`/`get`/`delete`, `gab_list_api_keys`/`create`/`delete`, `gab_export_account_data`. Destructive/secret tools require `confirm=true`.
- **Router client or agent plugin?** Agent **plugin**. It contains no routing logic; `auto` is not even in the bundled catalog (it appears only if `/v1/models` returns it and it passes `isChatModel`). All per-model `cost` fields are hard-coded `ZERO_COST` — the plugin does **not** surface Gab's `credit_cost` to Pi.
- **Code quality (3 lines).** Clean, typed, defensive TS with sane fallbacks and a real smoke script; conservative compat flags (`supportsReasoningEffort: false`, `supportsStrictMode: false`, `supportsUsageInStreaming: false`) that **contradict Gab's own docs** claiming `reasoning_effort` and strict `json_schema` support — i.e., the client trusts less than the docs promise. No unit tests shipped despite `npm test` pointing at `test/*.test.mjs`; catalog is a hand-maintained literal that drifts (bundled `hermes-4-405b` no longer exists live; 17 live text ids, including `auto`, `arya-agent`, `glm-5-3*`, `qwen-3-8-flash`, `gpt-6-astra`, are absent from the bundle).

### A-adapters — `agent-setup` payloads (harness adapters)

**The enumerable set is exactly four:** `cursor | opencode | openclaw | claude-code`. Verified live (2026-09-20 06:2x UTC, after the outage): any other or missing `client=` value (I sent `codex`, `pi`, `continue`, `aider`, `cline`, `roo`, `kilo`, `zed`, `windsurf`, `goose`, `crush`, `gemini-cli`, `hermes`, `grok`, `copilot`, `litellm`, `openrouter`, `bogus`, and none) returns HTTP 200 with a **bundle** `{"clients":["cursor","opencode","openclaw","claude-code"], cursor:{…}, opencode:{…}, openclaw:{…}, "claude-code":{…}}` — i.e., the server itself declares the list. Codex and Pi have docs pages but no adapter; they use env vars / the npm package. Every model list in these payloads is a **12-slug (or 8-slug) alphabetical prefix** of the 59 text models (`auto`, `arya`, claude-*, deepseek-*), so a consumer must still read `/v1/models`.

| client | Captured | Payload shape (observed) | Maps to repo harness | Notes for `toolset plan(gab, h)` |
|--------|----------|--------------------------|----------------------|----------------------------------|
| `opencode` | Yes (05:5x and 06:2x, identical) | `{client, notes[2], config{$schema, provider{"gab-ai"{npm:"@ai-sdk/openai", name, options{baseURL}, models{id→{name, limit{context,output}, modalities{input,output}, tool_call:true}}}}}}` — 12 models. Notes: "Use `@ai-sdk/openai` — not `@ai-sdk/openai-compatible`. The openai package sends tool turns to /v1/responses (1 credit each, with context-window usage). The compatible package uses /v1/chat/completions and bills every tool turn at the model base_cost." / "Use auto on the agent/main model only." | `opencode` (`$PFY_STATE_DIR/opencode.json`) | Directly mergeable into our `opencode.json` provider map. **Docs page still says `@ai-sdk/openai-compatible`** → drift; the payload is newer. |
| `claude-code` | Yes (06:2x) | `{client, env{ANTHROPIC_BASE_URL:"https://gab.ai", ANTHROPIC_AUTH_TOKEN:"YOUR_GAB_API_KEY", ANTHROPIC_MODEL:"auto", ANTHROPIC_SMALL_FAST_MODEL:"arya"}, notes[3]}`. Notes: no `/v1` in base URL; "`ANTHROPIC_MODEL=auto` is the agent/main model only. Compact, title, and small-fast calls use `ANTHROPIC_SMALL_FAST_MODEL` (arya or the admin quick default) — do not set those to auto."; "Each billed request counts against the daily X-RateLimit budget even when Auto classifies once and sticks the model for the tool loop." No model list. | `claude-code` | Two-slot pattern: routed main model + pinned cheap side-model. Copy as **process** (§B.6). |
| `cursor` | Yes (06:2x) | `{client, notes[4], openai{baseURL:"https://gab.ai/v1", apiKeyEnv:"GAB_API_KEY", protocol:"openai"}, anthropic{baseURL:"https://gab.ai", apiKeyEnv, protocol:"anthropic"}, models[12]{id, name, context_window, max_output_tokens, function_calling, thinking, vision, aliases[], protocol:"openai"|"anthropic"}}`. Claude slugs are tagged `protocol:"anthropic"`; everything else `openai`. Notes: "Set the Agent / Composer model to auto. Pin a concrete slug for Tab and inline complete — those must not use Auto." | (not a repo harness) | Same two-slot pattern; the per-model `protocol` field is the only place Gab states *which wire shape to use per slug*. |
| `openclaw` | Yes (06:2x) | `{client, yaml:"providers:\n  gab-ai:\n    type: openai\n    base_url: https://gab.ai/v1\n    api_key: …\n    models: [8 slugs]", models[8]}` — plain OpenAI-provider YAML, 8 slugs, no notes. | (not a repo harness) | Trivial; equivalent to a LiteLLM/OpenAI-compatible provider stanza. |
| Codex | n/a | `OPENAI_BASE_URL=https://gab.ai/v1`, `OPENAI_API_KEY`; agent model `auto`, smoke-test on pinned slug; `/v1/responses` with `previous_response_id` | `codex` | Env-only; maps to our attach env chain. |
| Pi | n/a | `pi install npm:@gabai/pi-gab-ai`; `GAB_API_KEY`/`GAB_AI_API_KEY` | (not a repo harness) | Package, see A1. |
| Grok CLI, OpenCode-via-env, Hermes, Gemini CLI, Continue, Aider | — | **Nothing published by Gab.** | `grok`, `hermes`, `gemini`, `continue` | Our cells for these would be `stub` or hand-built OpenAI-compatible provider entries. |

**Explicitly absent:** no SDK of Gab's own (they point at OpenAI/Anthropic SDKs), no CLI, no Docker image, no LiteLLM provider entry authored by Gab, no MCP server, no GitHub Action, no eval harness, no router source, no weights.

## B. Model evaluation and selection posture

### B.1 What the catalog metadata says (and does not)

Per text model, `/v1/models` exposes: `id`, `owned_by`, `aliases[]`, `recommended_for[]`, `capabilities{text, streaming, thinking, web_search, function_calling, image_input, file_input, audio_input, video_input, …}`, `context_window`, `max_output_tokens`, `credit_cost{base_cost, context_threshold} | null`, `is_plus_only`, `created`; `auto` additionally has `routing: true` and a `description`.

Observations on the 59 text ids (live 2026-09-20):

- **`recommended_for` does not discriminate.** 52/59 = `["coding","agents"]`, 6 = `[]` (the 5 speech-to-text ids + `gemma-4-26b`), 1 = `["routing","agents","coding"]` (`auto`). Gab's own docs say it is set on "function-calling text models" — it is a derived flag, not a curated recommendation. The Pi plugin uses it exactly that way (fallback for `function_calling`).
- **`capabilities` is the only real selector**: `function_calling` false on the 5 transcription ids only; `thinking` false on 9 (`minimax-m2-5`, `qwen-3-5-397b`, `qwen-3-7-plus`, `claude-sonnet-4-5`, `o3`, `gemini-2-5-pro`, …); `image_input` varies; `web_search: true` on **all** (a Gab-side feature, not a model property).
- **`credit_cost` is the cost tier.** `base_cost` 1–60, `context_threshold` 20k (most) / 50–60k (Anthropic 4.5, OpenAI 5.1, o3, Gemini 2.5 Pro) / 512 (audio). `null` on `auto`, `arya`, `gemini-3-1-flash-lite` — meaning "priced elsewhere", not free (`arya` = "1 credit per 32,000 input tokens, min 1" per `llms.txt`).
- **Provider spread:** OpenAI 12 · Anthropic 10 · Google 8 · Alibaba 7 · DeepSeek 6 · Z.ai 4 · MiniMax 3 · Moonshot 2 · Gab-branded 3 · Meta 1 · ElevenLabs 2 · NVIDIA 1. Gab-branded ids are aliases onto third-party slugs (`arya` → `google/gemini-3.5-flash-lite` today, `google/gemini-3.8-flash` in the repo fixture; `arya-agent` → `deepseek/deepseek-v4.1-flash`).
- **Churn:** since the 2026-08-14 plugin bundle, 1 id removed (`hermes-4-405b`) and ≥17 added. Since the repo fixture (24 ids), 0 removed, 35 added, 1 alias moved.

### B.2 Compact table — 59 text models (live 2026-09-20 05:52 UTC, sorted by `base_cost` then id)

`tools` = `capabilities.function_calling`, `think` = `capabilities.thinking`, `img` = `image_input`. `—` = null.

| id | provider | base | ctx_thr | ctx | max_out | tools | think | img | recommended_for | first alias |
|---|---|--:|--:|--:|--:|:-:|:-:|:-:|---|---|
| `arya-agent` | Gab AI | 1 | 20000 | 1048576 | 384000 | y | y | y | coding,agents | deepseek/deepseek-v4.1-flash |
| `gemini-35-flash-lite` | Google | 1 | 20000 | 1048576 | 65536 | y | y | y | coding,agents | google/gemini-3.5-flash-lite |
| `glm-5-3-flash` | Z.ai | 1 | 20000 | 1048576 | 131072 | y | y | y | coding,agents | glm-5.3-flash |
| `minimax-m2-5` | MiniMax | 1 | 20000 | 1000000 | 1000000 | y | n | n | coding,agents | minimax-m2.5 |
| `qwen-3-7-flash` | Alibaba | 1 | 20000 | 1000000 | 65536 | y | y | y | coding,agents | qwen-3.7-flash |
| `qwen-3-8-flash` | Alibaba | 1 | 20000 | 1000000 | 131072 | y | y | y | coding,agents | qwen-3.8-flash |
| `deepseek-v4-1-flash` | DeepSeek | 2 | 20000 | 1048576 | 384000 | y | y | y | coding,agents | deepseek-v4.1-flash |
| `deepseek-v4-flash` | DeepSeek | 2 | 20000 | 1048576 | 32000 | y | y | n | coding,agents | deepseek/deepseek-v4-flash |
| `deepseek-v4-flash-0731` | DeepSeek | 2 | 20000 | 1048576 | 32000 | y | y | n | coding,agents | deepseek/deepseek-v4-flash-0731 |
| `deepseek-v4-flash-vision-exp` | DeepSeek | 2 | 20000 | 1048576 | 65536 | y | y | y | coding,agents | deepseek/deepseek-v4-flash-vision-exp |
| `minimax-m3` | MiniMax | 2 | 20000 | 1000000 | 32768 | y | y | y | coding,agents | minimax/minimax-m3 |
| `qwen-3-5-397b` | Alibaba | 2 | 20000 | 262144 | 65536 | y | n | n | coding,agents | qwen-3.5-397b |
| `qwen-3-5-397b-thinking` | Alibaba | 2 | 20000 | 262144 | 65536 | y | y | n | coding,agents | qwen-3.5-397b-thinking |
| `qwen-3-7-plus` | Alibaba | 2 | 20000 | 1000000 | 65536 | y | n | y | coding,agents | qwen-3.7-plus |
| `claude-haiku-4-5` | Anthropic | 3 | 60000 | 200000 | 64000 | y | y | n | coding,agents | claude-haiku-4.5 |
| `kimi-k2-6` | Moonshot | 3 | 20000 | 262144 | 262144 | y | y | n | coding,agents | kimi-k2.6 |
| `minimax-m2-7` | MiniMax | 3 | 20000 | 204800 | 16384 | y | y | y | coding,agents | minimax-m2.7 |
| `elevenlabs-scribe-v2` | ElevenLabs | 5 | 512 | — | — | n | n | n | — | elevenlabs/speech-to-text/scribe-v2 |
| `gemma-4-26b` | Google | 5 | 20000 | 262144 | 16384 | y | y | y | — | gemma-4.26b |
| `glm-5-1` | Z.ai | 5 | 20000 | 202752 | 65535 | y | y | y | coding,agents | glm-5.1 |
| `glm-5-2` | Z.ai | 5 | 20000 | 1000000 | 65535 | y | y | y | coding,agents | glm-5.2 |
| `glm-5-3` | Z.ai | 5 | 20000 | 1048576 | 131072 | y | y | n | coding,agents | glm-5.3 |
| `gpt-4o-mini-transcribe` | OpenAI | 5 | 512 | 16000 | 2000 | n | n | n | — | openai/gpt-4o-mini-transcribe |
| `wizper` | NVIDIA | 5 | 512 | — | — | n | n | n | — | — |
| `o3` | OpenAI | 6 | 50000 | 200000 | 100000 | y | n | n | coding,agents | openai/o3 |
| `gpt-5-3-codex` | OpenAI | 7 | 20000 | 400000 | 128000 | y | y | y | coding,agents | gpt-5.3-codex |
| `claude-sonnet-4` | Anthropic | 8 | 20000 | 1000000 | 64000 | y | y | y | coding,agents | claude-sonnet-4-6 |
| `claude-sonnet-4-5` | Anthropic | 8 | 50000 | 200000 | 64000 | y | n | y | coding,agents | claude-sonnet-4.5 |
| `claude-sonnet-5` | Anthropic | 8 | 20000 | 1000000 | 128000 | y | y | y | coding,agents | anthropic/claude-sonnet-5 |
| `deepseek-v4-pro` | DeepSeek | 8 | 20000 | 1048576 | 64000 | y | y | n | coding,agents | deepseek/deepseek-v4-pro |
| `gemini-3-5-flash` | Google | 8 | 20000 | 1048576 | 65536 | y | y | y | coding,agents | gemini-3.5-flash |
| `gemini-3-7-flash` | Google | 8 | 20000 | 1048576 | 65536 | y | y | y | coding,agents | gemini-3.7-flash |
| `gemini-3-8-flash` | Google | 8 | 20000 | 1048576 | 65536 | y | y | y | coding,agents | gemini-3.8-flash |
| `gemini-36-flash` | Google | 8 | 20000 | 1048576 | 65536 | y | y | y | coding,agents | google/gemini-3.6-flash |
| `gpt-5-4` | OpenAI | 8 | 20000 | 1050000 | 128000 | y | y | y | coding,agents | gpt-5.4 |
| `gpt-5-6-terra` | OpenAI | 8 | 20000 | 1050000 | 128000 | y | y | y | coding,agents | gpt-5.6-terra |
| `kimi-k3` | Moonshot | 8 | 20000 | 1048576 | 32768 | y | y | y | coding,agents | moonshotai/kimi-k3 |
| `muse-spark-1-2` | Meta | 8 | 20000 | 1048576 | 65536 | y | y | y | coding,agents | muse-spark-1.2 |
| `qwen-3-7-max` | Alibaba | 8 | 20000 | 1000000 | 65536 | y | y | n | coding,agents | qwen-3.7-max |
| `deepseek-v4-pro-0813` | DeepSeek | 10 | 20000 | 1048576 | 64000 | y | y | n | coding,agents | deepseek-v4-pro |
| `gpt-4o-transcribe` | OpenAI | 10 | 512 | 16000 | 2000 | n | n | n | — | openai/gpt-4o-transcribe |
| `gpt-5-6-terra-pro` | OpenAI | 10 | 20000 | 1050000 | 128000 | y | y | y | coding,agents | gpt-5.6-terra-pro |
| `claude-opus-4-6` | Anthropic | 12 | 20000 | 1000000 | 128000 | y | y | y | coding,agents | claude-opus-4.6 |
| `gpt-5-1` | OpenAI | 12 | 60000 | 400000 | 128000 | y | y | y | coding,agents | gpt-5.1 |
| `qwen-3-8-max` | Alibaba | 12 | 20000 | 1000000 | 131072 | y | y | y | coding,agents | qwen-3.8-max |
| `claude-opus-4-7` | Anthropic | 14 | 20000 | 1000000 | 128000 | y | y | y | coding,agents | claude-opus-4.7 |
| `elevenlabs-scribe-v1` | ElevenLabs | 14 | 512 | — | — | n | n | n | — | elevenlabs/speech-to-text |
| `gpt-5-5` | OpenAI | 15 | 20000 | 1050000 | 128000 | y | y | y | coding,agents | gpt-5.5 |
| `claude-opus-4-8` | Anthropic | 16 | 20000 | 1000000 | 128000 | y | y | y | coding,agents | claude-opus-4.8 |
| `gemini-2-5-pro` | Google | 18 | 60000 | 1048576 | 65536 | y | n | y | coding,agents | gemini-2.5-pro |
| `gpt-5-6-sol` | OpenAI | 22 | 20000 | 1050000 | 128000 | y | y | y | coding,agents | gpt-5.6-sol |
| `claude-opus-5` | Anthropic | 25 | 20000 | 1000000 | 128000 | y | y | y | coding,agents | anthropic/claude-opus-5 |
| `gpt-5-6-sol-pro` | OpenAI | 28 | 20000 | 1050000 | 128000 | y | y | y | coding,agents | gpt-5.6-sol-pro |
| `claude-fable-5` | Anthropic | 46 | 20000 | 1000000 | 128000 | y | y | y | coding,agents | anthropic/claude-fable-5 |
| `claude-fable-5-1` | Anthropic | 46 | 20000 | 1000000 | 128000 | y | y | y | coding,agents | claude-fable-5.1 |
| `gpt-6-astra` | OpenAI | 60 | 20000 | 1050000 | 128000 | y | y | y | coding,agents | openai/gpt-6-astra |
| `arya` | Gab AI | — | — | 1048576 | 65536 | y | y | y | coding,agents | google/gemini-3.5-flash-lite |
| `auto` | gab-ai | — | — | 200000 | 8192 | y | y | y | routing,agents,coding | gab/auto |
| `gemini-3-1-flash-lite` | Google | — | — | 1048576 | 65536 | y | y | y | coding,agents | gemini-3.1-flash-lite |

Cost bands as Gab's own docs group them (docs/credits, 2026-09-18): 1–2 (DeepSeek V4 / Qwen 3.7 Flash / MiniMax M3) · 3 (Kimi K2.6 / Haiku 4.5) · 5 (GLM 5.2) · 6 (o3) · 8 (Sonnet 5 / Gemini 3.6 Flash / Kimi K3 / GPT-5.6 Terra) · 15 (GPT-5.5) · 16 (Opus 4.8) · 18 (Gemini 3.1 Pro — **not in the live API list**) · 22 (GPT-5.6 Sol) · 25 (Opus 5).

### B.3 The `auto` router — what is documented

From docs/api (2026-09-08), docs/models (2026-08-08), docs/credits (2026-09-18), the `auto` model `description`, and the Claude Code / Cursor pages:

- **Classifier:** "the same Intent Engine as the Gab AI app classifies the prompt and picks the model." Intents named: coding (**quick / standard / hard**), "hard reasoning → a reasoner", "live-fact questions → Arya with web search", "political or theological questions → Arya". In-app, the same engine also routes to image/video/music tools and web search; "Fast Mode" bypasses it (saves 1–3 s, same model).
- **Stickiness:** "In Cursor, Claude Code, Codex, or OpenCode the selected model sticks for the tool loop — mid-loop tool results do not re-run the classifier, and Gab does not inject search or political tools when you already sent `tools[]`." Kickoff-only inputs: `routing.coding_tier`, `routing.session_id` (or `X-Gab-Coding-Tier`, `X-Gab-Session-Id`).
- **Observability:** response `model` = slug that ran; headers `X-Gab-Selected-Model`, `X-Gab-Routed-Model`, `X-Gab-Router-Intent`, `X-Gab-Router-Coding-Tier` (all present in the live CORS `expose-headers` list). "Those headers are the live source of truth."
- **Tier → slug mapping: undisclosed on purpose.** "The slug mapped to each coding tier is configurable and can change — it is not a stable API contract." Claude Code docs refer to "the admin quick default". Enumerated values of `X-Gab-Router-Coding-Tier` are only inferable from the prose (`quick|standard|hard`); never observed here (no key).
- **Pricing of the decision:** none — "`auto` has no price of its own. You are billed for the resolved slug."
- **Scope limits:** chat endpoints only; `auto` must not be sent to images/audio/embeddings/video; `count_tokens` accepts it without creating route state; omitting `model` defaults to `arya`, not `auto`.

### B.4 Model-page descriptions and the user-facing "comparison" tool

- `/docs/models` (2026-08-08) gives each text model one line and three "Strengths" tags (e.g., GLM 5.2 "Long-horizon planning, Coding, Execution"; GPT-5.6 Terra "Everyday coding, Reasoning, Price-performance"; Kimi K3 "Complex coding, Multimodal reasoning, Long context"; Arya 3 "General conversation, Writing assistance, Value-aligned responses"). These read as vendor marketing summaries, not measurements, and the page lists models (Hermes 4 405B, Kimi K2 Thinking, Sonar, Gemini 3.1 Pro, Claude Sonnet 4.6) that the live API does **not** serve.
- `gab.ai/tools/model-comparison` (fetched via search index; page itself 502 at fetch time): "run the same prompt through 2–5 models in parallel … add explicit evaluation criteria — accuracy, tone, depth, cost, latency, brevity … Summarize Differences to get a structured verdict … Run the same comparison 2–3 times [because of temperature] … Re-run comparisons as new models ship." Its listed model roster (GPT-4 Turbo, Gemini 1.5 Pro, Mixtral, Llama 3) is years stale. **The method is sound; the page is unmaintained.**

### B.5 What Torba / Gab have said about *why* they pick models

| Statement | Source | Date | What it tells us |
|-----------|--------|------|------------------|
| "Gab doesn't have tens of millions of dollars to train our own in-house core AI model so instead we take multiple open source models and build layers on top of them … We will continue using the best open-source models available, adding our own layers on top" | https://news.gab.com/2026/06/washington-post-tested-gab-ai-heres-what-they-missed/ | 2026-06-29 | Selection criterion = **cost + steerability**. "Best" is asserted, not measured. Contradicted in detail by `arya`'s Gemini alias (not open source). |
| "Our developer API is intentionally designed to give builders a more neutral, blank-slate AI model experience. It does not include the same steering layers" | same | 2026-06-29 | The API is a pass-through router; in-app Arya = system-prompt/steering layer. Relevant: what we evaluate through the API is the upstream model, not "Arya". |
| WaPo replication: "Using their own methodology, the result was clear: 25 right-leaning answers, 5 left, 0 both." | same | 2026-06-29 | The **only** published "evaluation" Gab has run on its own product is a 30-question political-lean test — not capability, not coding. |
| "Arya 3.0 … Powered by a new intent engine … understands what you're trying to accomplish and executes automatically" | https://news.gab.ai/introducing-arya-3-0-by-gab-ai/ (host now 404) | 2026-01-29 | Router framed as product feature; no evaluation numbers. |
| Model descriptions ("Anthropic's most capable…", "Google's most powerful agentic and vibe-coding model") | https://gab.ai/docs/models | 2026-08-08 | Vendor copy; no Gab-run benchmark. |
| SEC annual report: "Gab AI offers users access to all of the top AI models in the world in one dashboard" | EDGAR CIK 1709244 | 2026 | Aggregation is the business model; no R&D/eval spend disclosed. Five employees. |
| Data-centre / "AI for normal people" posts | https://news.gab.com/2026/08/the-datacenter-discussion/ · /2026/09/faith-in-the-age-of-ai · /2026/09/why-they-want-you-to-fear-ai | 2026-08/09 | Positioning only; nothing on model selection or evaluation. |

**Benchmark numbers published by Gab for any model: none found.** No SWE-bench, HumanEval, tool-calling accuracy, latency or cost-per-task data, no model cards, no eval repo, no changelog of router-tier remaps.

### B.6 What is reusable for our `hedge` lane and `eval` pipeline — as process

Adopt as **method**, not ported code:

1. **Catalog-as-contract.** Publish/ingest one machine-readable row per model with `capabilities.*` booleans, a cost tier (`base_cost`, `context_threshold`), `context_window`, `max_output_tokens`, `aliases`, and a *derived* flag like `recommended_for` — and have every harness plan consume it live with an offline fixture fallback (exactly what the Pi plugin does). Our `data/toolsets.json` / hedge inputs should carry the same fields for local engines (ADR-0014 detector) so the hedge compares like with like.
2. **Classify once at kickoff, then pin.** Task class ∈ {quick, standard, hard} for coding plus non-coding intents; select the cheapest tier whose capability flags satisfy the request (tools required? images? context > threshold?); **stick** that model for the whole tool loop; never re-route on tool results. This is ADR-0017 §4's `bulk|hard|interactive` made concrete: `bulk→quick-tier local`, `interactive→standard`, `hard→hard-tier cloud if budget`.
3. **Escalate on failure, not on hunch.** Gab does not document escalation; we should: a `hard` retry is triggered only by an explicit signal (failed golden check, `unsupported_tool_calling`, truncation at `max_output_tokens`, N consecutive tool errors), logged as a new kickoff with its own receipt.
4. **Hold vs settle receipts.** Every cloud call records a pre-call *hold estimate* (`base_cost × (1 + prompt_tokens // context_threshold)`) and a post-call *settled* cost (`usage.credits_used`), plus the *resolved* model (`response.model` / `X-Gab-Routed-Model`) and rate-limit remaining. The ledger reconciles the two; estimates are never reported as costs.
5. **Two-model harness pattern.** Main agent may be routed/`auto`; side-calls (compaction, titles, tab-complete, summarisation) are **pinned** to an explicit cheap model (Gab: `ANTHROPIC_SMALL_FAST_MODEL=arya`). Our `toolset plan` should emit both slots for every harness that has them.
6. **Golden-run protocol for the model lane** (from the comparison tool): same real prompt → 2–5 candidates → explicit criteria (correctness, cost, latency, brevity) → repeat 2–3× for variance → structured verdict → re-run when the catalog changes (ETag). Gab supplies **no golden tasks**; ours must come from `examples/eval-harness/` and the T-0122 receipts.

**Opaque / not reusable:** the classifier itself (no weights, no prompts, no thresholds), the tier→slug table, any quality data behind "best", the in-app steering layer, the reasons a model is added or removed (Hermes 4 405B silently gone).

## C. Billing and rate limits — what the hedge ledger needs (trimmed)

- **Unit:** Gab credits (integer); ≈ $0.010–0.0143 each (packs 700/$10, 2,200/$25, 5,000/$50). Plus: $20/mo, 2,000 credits/mo, 10,000 API req/day. Plus Premium: $99/mo, 12,000 credits, 50,000 req/day. Free tier: 150 credits, **no API**. API always bills, 1-credit floor; in-app free Arya does not apply.
- **Per call:** `usage.credits_used`, `prompt_tokens`, `completion_tokens`, `prompt_tokens_details.cached_tokens`; `response.model`; headers `X-Gab-Routed-Model`, `X-Gab-Router-Coding-Tier`, `X-RateLimit-Remaining/Reset`, `X-Request-ID`. Text settles at **provider cost + margin floor**; listed `base_cost` is the **pre-authorisation hold** (assumes 16,384 output tokens if `max_tokens` omitted → always send `max_tokens`). Undelivered responses are not billed.
- **Balance:** `GET /v1/credits` → `monthly_remaining` (expires at `resets_at`; treat as sunk once subscribed) and `purchased_credits` (real money; `PFY_CLOUD_BUDGET` should cap this pool). Near `resets_at`, unspent monthly credits are use-or-lose → the hedge may legitimately route more `hard` work to Gab late in a cycle.
- **Requests:** each tool turn = 1 request against the daily cap; keep a reserve. Unverified: whether `/v1/responses` tool turns are billed differently from `/v1/chat/completions` (agent-setup note vs docs).
- **Timeouts:** 120–210 s read timeout, `stream: true` for thinking models; retry 504 with backoff. **Availability:** a single-origin outage (Cloudflare 502 on every path) was observed for ~20 min during this research — the hedge must treat Gab as a lane that can vanish and fall back to local, never block.
- **Errors to map:** 401 `invalid_api_key`/`missing_api_key`, 402 `insufficient_credits`, 403 key revoked, 429 rate limit, `plus_required`, `insufficient_credit_authorization`, `invalid_model`, `unsupported_tool_calling`.

## D. ToS points that bind an agent backend (trimmed)

- API automation is explicitly supported (Cursor/Claude Code/Codex/OpenCode/Pi docs) → **authorised** with your own key. ToS bans scraping/automation "for prohibited purposes … without authorization" and (Terms of Sale) "access other than by means authorized by Gab".
- **No competing-model use of Output** (ToS) → never distil Gab responses into local model training or a Gab-equivalent router. Whether internal routing *evaluation* counts is untested → P2 open question (for the parent to file).
- Output rights transfer to the user; business/commercial use OK; **no key sharing** (mint per-operator keys via `/v1/api-keys`); 18+; Pennsylvania law, AAA arbitration (30-day opt-out). No weights → no weight licence; Ollama pulls are governed by upstream licences only.
- Sources: https://gab.ai/terms-of-service · https://gab.ai/terms-of-sale (no visible `Last Updated` date in the fetched text).

## E. Repo assumptions vs findings (`pfy_gab_228.py`, gab-228 docs)

| Repo assumption | Verdict | Evidence |
|-----------------|---------|----------|
| `GAB_BASE = https://gab.ai/v1`; `/v1/models` public; docs URLs | **Correct** | §C, A4 |
| `GAB_API_KEY` primary; `GABAI_API_KEY` fallback | **Partly**: Gab uses `GAB_API_KEY` and `GAB_AI_API_KEY`; `GABAI_API_KEY` is a hobby project's name (A8) | A1, A8 |
| `model=auto` default = "cloud best" | **True but unsafe for a hedge**: cost-unbounded; tier→slug undisclosed | B.3 |
| "Plus/max plan required" copy | **Wrong**: Free / Plus / Plus Premium / Enterprise | §C |
| HTTP 403 → "plus required" | **Wrong**: 403 = key revoked; `plus_required` is an `error.code` | §C |
| `lane: "cloud/subscription"` | **Incomplete**: subscription + metered credits; nothing reads `credits_used` or `/v1/credits` | §C |
| `LOCAL_CODER_MODEL = <gab slug>` in `apply_cloud_env` | **Wrong**: overwrites the local-worker variable with a cloud slug | ADR-0011/0017 |
| "Gab does NOT host GGUF / local weights" | **Correct**, understated: no weights of any kind, anywhere | A10–A11 |
| `PROPRIETARY` contains `arya` | **In effect correct**; `arya`/`arya-agent` are opaque aliases onto third-party slugs that move | B.1 |
| `is_open_weight()` marks `qwen-*-max/-plus/-flash` as open-weight family | **Misleading**: API-only Qwen ids; family ≠ model | B.2 |
| `kimi → qwen2.5:14b` labelled `gab-open-weight→ollama` | Stand-in, mislabelled | code |
| Fixture = "offline Gab `/models` JSON" | **Stale**: 24 of 59 text ids; `arya` alias moved; no `captured_at`/ETag | B.1 |
| `recommended_for` used as a signal (`recommended_for` copied into rows) | **Weak**: blanket `coding,agents` on 52/59; carries no ranking information | B.1 |
| No use of `/v1/agent-setup`, `X-Gab-*`, `max_tokens`, `/v1/credits` | **Gaps** | A3, §C |
| Handoff "Attach Gab cloud with `auto` works under Plus key" | **Unverified** (no key); `--selftest` passes offline | — |

## F. Recommended changes (list only — not applied)

`scripts/pfy_gab_228.py`

1. Env: `GAB_API_KEY` then `GAB_AI_API_KEY`; drop/demote `GABAI_API_KEY`.
2. Stop writing `LOCAL_CODER_MODEL` from the cloud lane; use `PFY_GAB_MODEL` / `PFY_CLOUD_MODEL`.
3. Map `error.code` (`invalid_api_key`, `missing_api_key`, `insufficient_credits`, `plus_required`, `invalid_model`, `unsupported_tool_calling`, `insufficient_credit_authorization`, 429 + `X-RateLimit-Reset`); remove "403 → plus required".
4. Default model by **rule**, not literal: cheapest `base_cost` among text models with `function_calling: true`, `streaming: true`, `max_output_tokens ≥ 32k`; `auto` only on explicit `--model auto` (for `hard`); always emit `max_tokens`. Do not use `recommended_for` as a ranking input.
5. Add `credits()` (`GET /v1/credits`) and a per-call ledger hook recording hold-estimate, `credits_used`, resolved model, `X-Gab-Router-Coding-Tier`, `X-RateLimit-Remaining` into `$PFY_STATE_DIR/hedge-ledger.json` (unit `gab_credit`).
6. Add `agent_setup(client)` for `opencode|claude-code|cursor|openclaw` (call once with no `client` to get the 4-in-1 bundle) and use it in `toolset plan(gab, h)`; treat model lists as **partial** (8–12-slug alphabetical prefix, verified on all four) and merge with `/v1/models`; take per-slug wire protocol from the `cursor` payload's `protocol` field. Claude Code cell: `ANTHROPIC_BASE_URL=https://gab.ai` (no `/v1`) + `ANTHROPIC_SMALL_FAST_MODEL` pinned cheap. Codex cell: env only. Grok/Hermes/Gemini cells: honest `stub` until a recipe exists.
7. Fixture: re-capture `/v1/models?type=text` with `captured_at` + ETag; `--refresh-fixture`; selftest asserts `arya` alias is not trusted.
8. `is_open_weight()` by **id allow-list** (`gemma-4-26b`, `kimi-k2-6`, `kimi-k3`, `glm-*`, `deepseek-v4*`, `minimax-m*`, `qwen-3-5-397b*`); exclude `qwen-*-max/-plus/-flash`; label stand-ins `source: stand-in`.
9. Lane string `cloud/credits (Plus)`; remove "Plus/max" and the HOLD/#76/Env-tab liturgy (ADR-0017 §6).
10. Availability: on any 5xx from gab.ai, `hedge decide` must return `local` with `next_step`, never wait.

`docs/ops/gab-228.md` · `docs/modules/gab-228.md` · `docs/design/GAB-228-DEVBOT-HANDOFF.md`

11. Replace billing prose with §C; state "cloud-only lane; local sync = informational family hint"; `arya` = moving alias.
12. Add "ToS for agents" box (§D) and link this file; add to `docs/ops/local-cloud-split.md`.

`examples/eval-harness/` / `pfylib/hedge.py` (process, per §B.6)

13. Encode the six-step process (catalog-as-contract → classify-once-and-pin → escalate-on-signal → hold/settle receipts → two-model slots → golden-run protocol) as the hedge's documented method; the tier→model table is **ours** and versioned, since Gab's is opaque.

Process items for the parent: P2 OQ on ToS "competing service" vs internal routing evals; T-0122 measurements (settle vs hold on 1-credit slugs; `/v1/responses` vs `/v1/chat/completions` tool-turn billing; `X-Gab-Router-Coding-Tier` observed values).

## G. Catalog Stage 0 gate + provisional row (not written to TOOLS.md / data/tools.json)

**Candidate:** Gab AI API Router (`https://gab.ai/v1`) · **Primary category:** Proxy & Routing (hosted). Published-code angle does not change the verdict: the only code is a client plugin for a harness we do not run.

| Stage 0 gate | Result | Note |
|--------------|--------|------|
| Self-hostable <5 min | **FAIL** | SaaS; the plugin (A1) is a client, not the service. |
| Licence | **PASS** with ToS caveats | Output usable commercially; no weights; no competing-model use; no key sharing. |
| Hello-world | **PASS** | `curl /v1/chat/completions`; public `/v1/models`. |

| Stage | Score | Reasoning |
|-------|------:|-----------|
| S1 agent compat | 80 | OpenAI tools/streaming/strict schema across providers; Responses + Anthropic shapes; kickoff-sticky router. Deductions: `auto` opaque, provider-dependent `json_schema` 400s, plugin's own compat flags disclaim `reasoning_effort`/strict mode. |
| S2 perf | N/A (cloud) | 1-credit (~$0.01) coding calls with 1M context are cheap; single-origin outage observed. |
| S3 integration | 70 | `agent-setup` adapters for 4 clients, `/v1/credits`, `/v1/api-keys`, standard SDKs; payload partial; docs drift; `openapi.json`/`llms-full.txt` 404. |
| S4 ecosystem | 40 | Five-person company; one MIT plugin (11 weekly downloads, no tests shipped); GitLab not public; no AI code on GitHub/HF; no evals; catalog churn without changelog. |
| **Overall** | **≈63** | |

**Provisional tier: C (niche cloud-lane provider; Stage 0 self-host FAIL).**

Proposed `TOOLS.md` row:

```
| **Gab AI API Router** | Proxy & Routing | https://gab.ai/docs/api (SaaS; client plugin npm `@gabai/pi-gab-ai`, MIT) | 80 | N/A | 70 | 40 | 63 | C | #openai-shim #tool-calling #structured-output #cloud #credits #litellm-ready | **Cloud lane only (hedge, ADR-0017).** Plus required; every API call bills credits (1-credit floor; hold vs settle). Meter via `usage.credits_used` + `GET /v1/credits`; 10k req/day. `auto` = kickoff-sticky router, tier→slug undisclosed — pin a `base_cost:1` coding slug by rule. **Published code = one Pi client plugin; no weights, no evals, no router source; `arya` is a moving alias onto third-party slugs.** Harness adapters via `GET /v1/agent-setup?client=cursor|opencode|openclaw|claude-code`. Stage 0: self-host FAIL. Eval: [docs/evaluation/gab-ai-cloud-lane-2026-09.md](docs/evaluation/gab-ai-cloud-lane-2026-09.md). |
```

Proposed `data/tools.json` entry (slim, ADR-0015):

```json
{
  "name": "Gab AI API Router",
  "primary_category": "Proxy & Routing",
  "github": null,
  "url": "https://gab.ai/docs/api",
  "scores": {"s1": 80, "s2": null, "s3": 70, "s4": 40, "overall": 63},
  "tier": "C",
  "tags": ["openai-shim", "tool-calling", "structured-output", "cloud", "credits", "litellm-ready"],
  "notes": "Cloud-only credit lane for the hedge. Stage 0 self-host FAIL (SaaS). Published code = MIT Pi client plugin only; no weights/evals/router source. arya is a moving alias. Adapters: GET /v1/agent-setup?client=cursor|opencode|openclaw|claude-code.",
  "integration_stage": "I1",
  "implementation": {"toolset": "gab", "stage": "I1"},
  "evaluation": "docs/evaluation/gab-ai-cloud-lane-2026-09.md"
}
```

## H. What could not be verified (explicit)

- **Outage:** gab.ai returned 502 on every path ~06:00–06:20 UTC. API endpoints (`/v1/models`, all `agent-setup` variants, `openapi.json`, `llms-full.txt`) were re-verified afterwards; `/docs/cursor-ide`, `/docs/claude-code`, `/docs/codex-cli`, `/tools/model-comparison` were **not** re-fetched — their content above comes from the 05:5x docs captures or search-index excerpts.
- Anything requiring a key: real `credits_used`, hold vs settle, `/v1/responses` vs `/v1/chat/completions` tool-turn billing, observed `X-Gab-Router-Coding-Tier` values, whether `plus_required` fires on Free keys.
- Whether Gab hosts **any** model itself; what `arya` is beyond its alias; how the Intent Engine is built (prompted classifier? small model? rules?).
- Public availability of `gitlab.com/GabAIInc/pi-gab-ai`; whether tests exist upstream.
- Why `agent-setup` model lists stop at an alphabetical prefix (12 for cursor/opencode, 8 for openclaw) — deliberate cap or a bug; no pagination parameter is documented.
- ToS `Last Updated` date; Ollama tag-level existence (`gemma4:26b`, `gpt-oss:120b`) — only library names verified.
- Any independent 2026 technical review of the Gab API; the only third-party artifact found is a hobby client.

## Appendix — verified facts (rev. 1 table, retained; F-numbers cited above)

Confidence: **high** = primary Gab artifact with a date stamp or a live API response; **med** = primary statement without corroboration or third-party report of a reproducible artifact; **low** = inference.

| # | Claim | Source | Date | Conf. |
|---|-------|--------|------|-------|
| F1 | Base `https://gab.ai/v1`; `/chat/completions`, `/responses`, `/messages` (Claude Code uses `ANTHROPIC_BASE_URL=https://gab.ai`) | docs/api · docs/api-endpoints | 2026-09-08 / 2026-08-20 | high |
| F2 | Bearer auth; keys `gab_`+32hex / `gab-`+64hex; env `GAB_API_KEY` (+ `GAB_AI_API_KEY`) | docs/api-auth · docs/api | 2026-09-08 | high |
| F3 | `GET /v1/models` public; 134 ids / 59 text; `?type=text` works; fields as in §B.1 | live fetch | 2026-09-20 05:52 UTC | high |
| F4 | API requires Plus; every request bills credits; 1-credit floor | pricing · docs/api | 2026-09-08 | high |
| F5 | Free 150 · Plus $20/mo 2,000 cr 10k req/day · Plus Premium $99/mo 12,000 cr 50k req/day · Enterprise; no "max" | pricing · docs/pricing-guide · docs/api-auth | 2026-09-20 | high |
| F6 | Packs 700/$10, 2,200/$25, 5,000/$50; monthly expire, purchased never, purchased consumed after monthly | docs/credits | 2026-09-18 | high |
| F7 | `usage.credits_used` on every response; `GET /v1/credits` fields | docs/api-endpoints | 2026-08-20 | high |
| F8 | Settle = provider cost + margin floor; tariff = hold; hold assumes 16,384 out tokens; `insufficient_credit_authorization` / `insufficient_credits`; undelivered not billed | docs/api-endpoints · docs/api | 2026-08-20 / 09-08 | high |
| F9 | Context multiplier per `context_threshold` | docs/credits · live `credit_cost` | 2026-09-18 / 09-20 | high |
| F10 | `auto`: no price, billed for resolved slug, kickoff-sticky, tier→slug unstable, `X-Gab-*` headers, `routing.coding_tier`, omit `model` → `arya` | docs/api · docs/models · live CORS headers | 2026-09-08 / 08-08 / 09-20 | high |
| F11 | 10k req/day Plus (50k Premium), `X-RateLimit-*`, 429; each tool turn = 1 request | docs/api-auth · docs/credits | 2026-09-08 / 09-18 | high |
| F12 | OpenAI `tools`/`tool_choice` translated per provider; streaming deltas; `response_format` json_object / strict json_schema; `reasoning_effort`; `unsupported_tool_calling` | docs/api-endpoints · llms.txt | 2026-08-20 | high |
| F13 | Error codes 401/402/403(key revoked)/429; `plus_required`, `invalid_model` | docs/api-auth · docs/api-endpoints | 2026-09-08 | high |
| F14 | Live `arya` alias `google/gemini-3.5-flash-lite`; fixture alias `google/gemini-3.8-flash` | live vs fixture | 2026-09-20 | high |
| F15 | Live `arya-agent` alias `deepseek/deepseek-v4.1-flash`, base 1, out 384k, created ≈2026-09-17 | live | 2026-09-20 | high |
| F16 | Cheapest tool-capable slugs (base 1): `glm-5-3-flash`, `qwen-3-7-flash`, `qwen-3-8-flash`, `minimax-m2-5`, `arya-agent`, `gemini-35-flash-lite`; frontier 15–60 | live | 2026-09-20 | high |
| F17 | `agent-setup`: exactly 4 clients (server-declared bundle for any other value); opencode `@ai-sdk/openai` 12 models + billing note (docs page says `openai-compatible`); cursor 12 models with per-slug `protocol`; openclaw YAML 8 slugs; claude-code env only | live × 22 probes · docs/opencode | 2026-09-20 05:5x + 06:2x | high / med (billing note) |
| F18 | npm `@gabai/pi-gab-ai` MIT 0.1.0–0.3.0, last 2026-08-14; GitLab repo not verifiably public; no `test/` in tarball | registry.npmjs.org · tarball | 2026-08-14 | high / low |
| F19 | GitHub `gab-ai-inc`: 7 Dissenter repos, last push 2024-06-09; `GabOpenSource`: `gab-social` AGPL zip (2026-06-08), `Hoist` empty (2026-05-16); HF: nothing | GitHub/HF APIs | 2026-09-20 | high |
| F20 | Gab AI Inc.: PA, five employees, Reg A filer; own servers for gab.com; full independence "a plan" | SEC EDGAR CIK 1709244 | 2026 | high |
| F21 | Torba 2026-06-29: API = blank-slate without steering; "take multiple open source models and build layers on top"; WaPo replication 25/5/0 | news.gab.com | 2026-06-29 | high (statement) |
| F22 | Third-party model requests proxied and anonymised | gab.ai/models · gab.ai | 2026-09-20 | high (statement) |
| F23 | gab.ai behind Cloudflare; Express; ~20 min full 502 outage observed (06:00–06:20 UTC) | live headers | 2026-09-20 | high |
| F24 | ToS clauses as in §D | terms-of-service · terms-of-sale | date not shown | high (text) |
| F25 | Arya 3.0 announced 2026-01-29; Arya 2.0 July 2025 | news.gab.ai (now 404) · substack repost | 2026-01 / 2025-07 | med |
| F26 | 2024 in-app Arya system-prompt leak; WIRED: base model unclear | wired.com · HN | 2024-04 | med |
| F27 | All 14 Ollama library names in `OLLAMA_MAP` resolve (tags unchecked) | ollama.com | 2026-09-20 | high / unverified |
| F28 | All 24 fixture ids still live; live text = 59; only diff = `arya` alias | fixture vs live | 2026-09-20 | high |
| F29 | Pi plugin bundle (2026-08-14) vs live: `hermes-4-405b` removed; 17 live text ids not bundled | tarball vs live | 2026-09-20 | high |
| F30 | `recommended_for` = `["coding","agents"]` on 52/59 text ids; `[]` on 6; `web_search: true` on all | live | 2026-09-20 | high |
| F31 | `openapi.json`, `llms-full.txt` 404 (pre-outage) | live | 2026-09-20 05:5x | high |
| F32 | Documented and server-declared `agent-setup` clients: `cursor|opencode|openclaw|claude-code`; Codex/Pi via env/package; `openapi.json` and `llms-full.txt` still 404 after recovery | docs/api-endpoints · live | 2026-08-20 / 2026-09-20 | high |

## Agent section

- **Invariants:** Gab = `cloud` lane only; published code = one MIT Pi plugin (cite, don't catalog); harness adapters = `agent-setup` payloads (consume, merge with `/v1/models`); metering unit `gab_credit`, source of truth `usage.credits_used`; `arya`/`auto` are not stable engines — log `response.model`; `recommended_for` is not a ranking.
- **Do not:** claim Gab publishes weights, evals or router code; default the hedge to `auto`; write `LOCAL_CODER_MODEL` from the Gab lane; share keys; distil Gab Output into local models; block on gab.ai availability.
- **Re-verify when:** `/v1/models` ETag changes; a new `@gabai/*` npm version appears; `agent-setup` gains clients; `openapi.json` starts serving; a Gab HF org appears; T-0122 receipts land.
- **Links:** ADR-0017 · ADR-0014 · ADR-0015 · `docs/ops/gab-228.md` · `docs/ops/local-cloud-split.md` · CATEGORIZATION.md §3–4 · `examples/eval-harness/`.
