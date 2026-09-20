# Evaluation: Gab AI as a cloud lane (hedge) — research 2026-09

**Status:** research note, read-only · **Date:** 2026-09-20 · **Scope:** #228 lane vs. what Gab AI actually offers as of Sep 2026 · **Related:** [ADR-0017](../adr/0017-product-catalog-evaluation-handoff-harness.md) (hedge policy), [ADR-0014](../adr/0014-pluggable-local-inference-spine.md), [gab-228.md](../ops/gab-228.md), `scripts/pfy_gab_228.py`, `scripts/fixtures/gab_models_v1.json`.
**Method:** primary sources only where marked *high* (gab.ai docs pages with `Last updated` stamps, a live `GET https://gab.ai/v1/models` pulled 2026-09-20 05:52 UTC, `GET /v1/agent-setup?client=opencode`, Gab's own news posts, the Gab AI Inc. SEC Reg A annual report, npm registry, GitHub/GitLab/Hugging Face API probes). No authenticated calls were made; nothing below about billing was observed on a real invoice.

## Summary (5 lines)

1. Gab AI's developer offering is a **hosted OpenAI-compatible router** at `https://gab.ai/v1` (`/chat/completions`, `/responses`, Anthropic-style `/messages`), 134 model ids (59 text) from OpenAI/Anthropic/Google/DeepSeek/Alibaba/Z.ai/Moonshot/MiniMax plus Gab-branded `auto`, `arya`, `arya-agent`. API requires a **Plus** subscription and **every** API request bills credits (1-credit floor).
2. **There is no local path.** Gab publishes no weights, no model card, no Hugging Face org, no AI code on GitHub; the API's `arya` id carries alias `google/gemini-3.5-flash-lite` today (fixture captured earlier: `google/gemini-3.8-flash`), `arya-agent` aliases `deepseek/deepseek-v4.1-flash`, and Torba wrote in June 2026 that Gab "take[s] multiple open source models and build[s] layers on top". "Local/sovereign" claims are about gab.com's social-network servers, not about model hosting. Gab cannot be a local lane; it is a cloud lane only.
3. **Credits are the metering unit** and the API tells you exactly what to log: `usage.credits_used` on every response, `GET /v1/credits` for monthly (expiring) vs purchased (non-expiring) pools, `X-RateLimit-*` for the 10,000 req/day (Plus) / 50,000 (Plus Premium) cap. Published per-model `base_cost` is only a pre-authorisation hold; settlement is provider cost + margin floor.
4. The repo's #228 assumptions are **mostly right on shape** (base URL, `GAB_API_KEY`, `model=auto`, public `/v1/models`, "Gab does not host GGUF") and **wrong on detail**: no "max" plan exists, 403 ≠ plus-required, `LOCAL_CODER_MODEL` is overwritten with a cloud slug, `auto` as default is cost-unbounded for a hedge, nothing reads `credits_used`, and the fixture is 24 of 59 text ids.
5. Catalog verdict: Stage 0 gate **fails on self-hostability** (SaaS), passes license/hello-world. Provisional **C-tier (niche, cloud-lane provider)**, ~62 overall, category *Proxy & Routing*; track, do not promote, do not build a "Gab local" story.

## 1. Verified facts

Confidence: **high** = primary Gab artifact fetched by me with a date stamp, or a live API response; **med** = primary Gab statement without independent corroboration, or third-party report of a reproducible artifact; **low** = inference from artifacts.

| # | Claim | Source | Date | Conf. |
|---|-------|--------|------|-------|
| F1 | Base URL `https://gab.ai/v1`; OpenAI-compatible `/v1/chat/completions`; also `/v1/responses` (Codex-style) and `/v1/messages` (Anthropic-style; Claude Code uses `ANTHROPIC_BASE_URL=https://gab.ai` **without** `/v1`) | https://gab.ai/docs/api · https://gab.ai/docs/api-endpoints | docs "Last updated 2026-09-08" / "Updated August 20, 2026" | high |
| F2 | Auth: `Authorization: Bearer <key>`; keys are `gab_`+32 hex (UI) or `gab-`+64 hex (`/v1/api-keys`); env var in Gab's own examples is `GAB_API_KEY`; Pi package also accepts `GAB_AI_API_KEY` | https://gab.ai/docs/api-auth · https://gab.ai/docs/api (Pi section) | 2026-09-08 | high |
| F3 | `GET /v1/models` is **public** (no key); returns `aliases`, `context_window`, `max_output_tokens`, `capabilities.function_calling`, `recommended_for`, `credit_cost {base_cost, context_threshold}`, `is_plus_only`; `?type=text` filter works | live fetch, HTTP 200, 134 ids / 59 text | 2026-09-20 05:52 UTC | high |
| F4 | API access requires **Plus**; every API request draws credits with a **one-credit floor**; free in-app default-model messages do **not** apply to the API | https://gab.ai/pricing · https://gab.ai/docs/api | 2026-09-08 | high |
| F5 | Plans: Free (150 credits, no card) · Plus $20/mo or $200/yr, 2,000 credits/mo, 10,000 API req/day · **Plus Premium** $99/mo or $999/yr, 12,000 credits/mo, 50,000 API req/day, web only · Enterprise custom. No plan called "max" | https://gab.ai/pricing · https://gab.ai/docs/pricing-guide · https://gab.ai/docs/api-auth | fetched 2026-09-20 | high |
| F6 | Credit packs: 700/$10 ($0.0143), 2,200/$25 ($0.0114), 5,000/$50 ($0.010). Monthly credits reset and do not roll over; purchased credits never expire and are consumed **after** monthly | https://gab.ai/docs/credits | "Last updated: 2026-09-18" | high |
| F7 | Every response carries `usage.credits_used` (plus `prompt_tokens_details.cached_tokens` on cache hits). `GET /v1/credits` returns `monthly_credits / monthly_used / monthly_remaining / purchased_credits / total_available / resets_at` | https://gab.ai/docs/api-endpoints | 2026-08-20 | high |
| F8 | Billing model for text: **settle at provider token cost + margin floor**, not the listed tariff; the listed `base_cost` is a pre-authorisation **hold**; hold assumes 16,384 output tokens when `max_tokens` omitted; errors `insufficient_credit_authorization` (hold > balance) and `insufficient_credits` (settle > balance, not billed); undelivered responses are not billed | https://gab.ai/docs/api-endpoints · https://gab.ai/docs/api | 2026-08-20 / 2026-09-08 | high |
| F9 | Context multiplier: for most models each additional `context_threshold` (~20k tokens; 50–60k on some) of history adds another base charge | https://gab.ai/docs/credits · `credit_cost.context_threshold` in live `/v1/models` | 2026-09-18 / 2026-09-20 | high |
| F10 | `model="auto"` is a router id with **no price of its own**; billed for the resolved slug; coding classified quick/standard/hard; kickoff model sticks for the tool loop; destination slugs are configurable and "not a stable API contract"; inspect `X-Gab-Routed-Model`, `X-Gab-Selected-Model`, `X-Gab-Router-Intent`, `X-Gab-Router-Coding-Tier`; optional `routing.coding_tier` / `X-Gab-Coding-Tier` at kickoff; omitting `model` defaults to `arya` | https://gab.ai/docs/api · https://gab.ai/docs/models · live CORS `access-control-expose-headers` lists those headers | 2026-09-08 / 2026-08-08 / 2026-09-20 | high |
| F11 | Rate limits: 10,000 req/day Plus (50,000 Premium), reset midnight UTC, headers `X-RateLimit-Limit/Remaining/Reset`, 429 on excess; **each tool-loop turn is one request** | https://gab.ai/docs/api-auth · https://gab.ai/docs/credits | 2026-09-08 / 2026-09-18 | high |
| F12 | Tool/function calling: OpenAI `tools`/`tool_choice` shape translated to each provider; streaming tool-call deltas; `response_format` `json_object` / strict `json_schema`; `reasoning_effort`; `unsupported_tool_calling` error if model has `function_calling: false` | https://gab.ai/docs/api-endpoints · https://gab.ai/llms.txt | 2026-08-20 | high |
| F13 | Error codes documented: 401 `invalid_api_key` / `missing_api_key`, 402 insufficient credits, 403 **key revoked**, 429 rate limited, `plus_required` (model requires Plus), 400 `invalid_model` | https://gab.ai/docs/api-auth · https://gab.ai/docs/api-endpoints | 2026-09-08 | high |
| F14 | Live `arya`: `owned_by: "Gab AI"`, `aliases: ["google/gemini-3.5-flash-lite"]`, ctx 1,048,576, out 65,536, `credit_cost: null`, `is_plus_only: false`. Repo fixture (earlier capture) had alias `google/gemini-3.8-flash` for the same id — the alias **moved** between captures | live `/v1/models` vs `scripts/fixtures/gab_models_v1.json` | 2026-09-20 | high (artifact) |
| F15 | Live `arya-agent` (new, created 1789712064 ≈ 2026-09-17): `aliases: ["deepseek/deepseek-v4.1-flash"]`, `base_cost 1`, out 384,000, `recommended_for: coding, agents` | live `/v1/models` | 2026-09-20 | high (artifact) |
| F16 | Cheapest coding-capable text slugs live today (`base_cost` 1, `function_calling: true`): `glm-5-3-flash`, `qwen-3-7-flash`, `qwen-3-8-flash`, `minimax-m2-5` (no streaming/thinking), `arya-agent`, `gemini-35-flash-lite`; `base_cost` 2: `deepseek-v4-flash`, `deepseek-v4-1-flash`, `qwen-3-5-397b(-thinking)`, `qwen-3-7-plus`, `minimax-m3`. Frontier: `gpt-5-5` 15, `claude-opus-5` 25, `claude-fable-5(-1)` 46, `gpt-6-astra` 60 | live `/v1/models` | 2026-09-20 | high |
| F17 | `GET /v1/agent-setup?client=opencode|cursor|openclaw|claude-code` returns a generated client config from the live catalog (public, HTTP 200). The live OpenCode payload says use `@ai-sdk/openai` and notes: "The openai package sends tool turns to /v1/responses (1 credit each, with context-window usage). The compatible package uses /v1/chat/completions and bills every tool turn at the model base_cost." The `/docs/opencode` page still says `@ai-sdk/openai-compatible` — **docs drift** | live fetch · https://gab.ai/docs/opencode ("2026-09-08") | 2026-09-20 | high (payload) / med (billing semantics) |
| F18 | Official client package: npm `@gabai/pi-gab-ai` (Pi provider + Gab tools), **MIT**, versions 0.1.0–0.3.0, last modified 2026-08-14, repo `gitlab.com/GabAIInc/pi-gab-ai` (GitLab web returns 302 → not verifiably public; GitLab API 404 for the group) | https://registry.npmjs.org/@gabai%2Fpi-gab-ai · https://gab.ai/docs/pi-cli | 2026-08-14 | high (npm) / low (repo public) |
| F19 | GitHub org `gab-ai-inc` exists with 7 repos, all Dissenter-browser era (MPL-2.0/Apache-2.0), last push 2024-06-09; **no AI/model repos**. Hugging Face API: no models for author `GabAI`, no search hits for "gab arya" | GitHub API · HF API probes | 2026-09-20 | high |
| F20 | Gab AI Inc. is a Pennsylvania company with **five employees** (software engineering, support, ops…), files Reg A/Reg CF reports with the SEC; report states Gab "has our own servers, our own payment processor" and a plan for "our own infrastructure at every level of the tech stack" (i.e., not complete) | SEC EDGAR CIK 1709244, 2026 annual report (`gabar.pdf`) | filed 2026 | high (filing) |
| F21 | Torba, 2026-06-29: "The Washington Post used our developer API … intentionally designed to give builders a more neutral, blank-slate AI model experience. It does not include the same steering layers we use in the main Gab AI product." and "Gab doesn't have tens of millions of dollars to train our own in-house core AI model so instead we take multiple open source models and build layers on top of them" | https://news.gab.com/2026/06/washington-post-tested-gab-ai-heres-what-they-missed/ | 2026-06-29 | high (statement) |
| F22 | Gab states third-party model requests are proxied and **anonymised** ("requests to third-party providers are anonymized so those providers never learn who you are") — i.e., upstream inference for named vendors is third-party API, not Gab GPUs | https://gab.ai/models · https://gab.ai/ | fetched 2026-09-20 | high (statement) |
| F23 | gab.ai is fronted by **Cloudflare** (`server: cloudflare`, `cf-ray`), app is Node/Express (`x-powered-by: Express`) | live response headers | 2026-09-20 | high |
| F24 | ToS: prohibits "using the Service or any Output to develop models or services that compete with Gab AI", robots/scraping "for prohibited purposes … without authorization", reverse engineering; **18+**; Gab transfers its rights in Output to the user; Terms of Sale allow personal **and business** use and commercial use of Output, forbid resale/sharing of access and "access other than by means authorized by Gab"; Pennsylvania law, AAA arbitration (30-day opt-out), Scranton venue; liability cap greater of 6-month fees or $100 | https://gab.ai/terms-of-service · https://gab.ai/terms-of-sale | page shows no visible `Last Updated` date in fetched text | high (text) / unknown (date) |
| F25 | Arya 3.0 announced 2026-01-29 with an "intent engine"; Arya 2.0 announced July 2025 | https://news.gab.ai/introducing-arya-3-0-by-gab-ai/ · Torba post reproduced at acbailey2.substack.com/p/introducing-arya | 2026-01 / 2025-07 | med |
| F26 | 2024 reporting (WIRED, HN, reproductions) of the in-app Arya **system prompt**; WIRED: "It's unclear which large language model Gab's chatbots are trained on" | https://www.wired.com/story/gab-ai-chatbot-racist-holocaust/ · https://news.ycombinator.com/item?id=40009307 | 2024-04 | med (historical; app, not API) |
| F27 | Every Ollama library name used in `OLLAMA_MAP` (`gemma4`, `gemma2`, `qwen3-coder`, `qwen2.5-coder`, `qwen2.5`, `deepseek-coder`, `glm-4.7-flash`, `glm4`, `gpt-oss`, `llama3.1/3.2/3.3`, `mistral`, `phi3`) resolves on ollama.com (HTTP 200); specific tags (`:26b` etc.) not checked | ollama.com/library/* | 2026-09-20 | high (names) / unverified (tags) |
| F28 | All 24 fixture ids still exist live; only diff is the `arya` alias (F14). Live text catalog is 59 ids; fixture lacks 35 of them | fixture vs live diff | 2026-09-20 | high |

## 2. Unverified or marketing claims (be blunt)

| Claim | Where it appears | Why it is not verified |
|-------|------------------|------------------------|
| "Arya is Gab's own model … not a wrapper" | gab.ai/right-wing-ai, gab.ai/models, llms.txt, ToS §1 | No weights, no model card, no training report, no parameter count anywhere. The only machine-readable artifact (`/v1/models`) shows `arya` aliased to a Google Gemini slug and `arya-agent` to a DeepSeek slug. Torba's own June 2026 post says Gab layers on top of "open source models" — which contradicts a Gemini alias (Gemini is not open source). Best reading: **Arya = brand + steering/system layer over a swappable upstream**, and on the API the steering layer is largely absent (F21). |
| "100+ models … Grok, Llama" on the API | gab.ai/api | Live `/v1/models` has 134 ids total but **no** `grok*`, `llama*`, `hermes*`, `gpt-oss*`, `mistral*`, `phi*`, `sonar*` ids. `/docs/models` lists Hermes 4 405B, Kimi K2 Thinking, Sonar — not in the live API list. Marketing/catalog drift. |
| "Own servers, own data centers, independent from Big Tech" | develop.gab.com FAQ, SEC report, news.gab.com | Plausible for gab.com social hosting (long-standing, SEC-stated). **Not shown for AI inference**: named vendor models are proxied to third-party APIs (F22), the site sits behind Cloudflare (F23), and the filing itself says full independence is a plan (F20). No GPU counts, no model-hosting claims, no location. |
| "Uses the best open-source models, adding our own layers" | Torba 2026-06-29 | Consistent with `gemma-4-26b`, `qwen-*`, `glm-*`, `kimi-*`, `deepseek-*`, `minimax-*` appearing in the catalog, but no evidence Gab **hosts** any of them itself versus reselling a provider's API. Unknown; assume reseller. |
| "Privacy — your API calls are not used for training", "identity masked" | docs/api, gab.ai | Policy statements only; not auditable from outside. ToS §"Content" grants Gab a processing licence and says model-improvement uses are "subject to … Privacy Policy" — not an unconditional no-training promise. |
| Tool-turn billing difference between `/v1/responses` (1 credit each) and `/v1/chat/completions` (base_cost each) | live `agent-setup` note (F17) | Conflicts with F8 ("settle at provider cost + margin floor" for text). Could be true for the hold, false for the settlement, or a stale note. **Must be measured** with a real key before the hedge relies on it. |
| Owner's framing: Gab is "'local' focused on their cloud competing with the very large providers" | conversation | Not supported. Gab competes with **routers/resellers** (OpenRouter-class), not with providers, and offers nothing runnable locally. The "local" vocabulary in Gab's material means jurisdiction/hosting independence for the social network, not on-device or self-hosted inference. |
| `is_plus_only: false` on `auto`/`arya` | live `/v1/models` | Field is misleading for the API: F4 says all API access requires Plus. Treat `is_plus_only` as an in-app flag. |

## 3. Implications for the hedge lane (ADR-0017 §4)

### 3.1 Gab is a cloud lane only — no "Gab local"

- There is no open-weights path, so Gab **cannot** be both a local and a cloud lane. The existing "local sync" in `pfy_gab_228.py` is really *"open-weight families Gab happens to list → Ollama"*. That signal is weak (the same families are visible directly in the Ollama library and in `pfy_recommend_models_207.py`) and it mislabels proprietary Qwen Max/Plus as "open-weight family". Keep it, if at all, as an **informational** hint, not as a lane; the honesty chips (`gab auto ≠ local ranking`, `Gab does not host GGUF`) are correct and should stay.
- Local lane stays ADR-0014 (FreeToken → llama-swap → Ollama). Gab enters only as one `cloud` provider next to Grok.

### 3.2 How to meter credits

- **Unit:** Gab credits (integer). Nominal value ≈ $0.010 (Plus allotment or 5k pack) to $0.0143 (700 pack). Record the unit as `gab_credit`, not dollars.
- **Per call (append-only ledger row):** `credits_used` from `usage`, `prompt_tokens`, `completion_tokens`, `cached_tokens`, `response.model` (resolved slug), `X-Gab-Routed-Model`, `X-Gab-Router-Coding-Tier`, `X-RateLimit-Remaining`, `X-Request-ID`. This is exact; never estimate when the response is present.
- **Pre-call estimate (for `hedge decide`):** `hold ≈ base_cost × (1 + floor(prompt_tokens / context_threshold))`; treat it as an **upper bound** on the hold, not the cost. Always send `max_tokens` (Gab assumes 16,384 for the hold otherwise) — this is the single biggest lever on `insufficient_credit_authorization`.
- **Two pools, two prices:** `GET /v1/credits` → `monthly_remaining` (expires at `resets_at`, sunk cost) and `purchased_credits` (real money, never expires). The hedge should value monthly credits at **zero marginal cost** once the subscription exists and purchased credits at pack price. Practical policy: `PFY_CLOUD_BUDGET` caps **purchased**-pool spend; monthly pool is spendable freely for `hard` tasks, and as `resets_at` approaches, unspent monthly credits become "use-or-lose" — the hedge may legitimately route more `hard`/`interactive` work to Gab in the last days of a cycle.
- **Request budget is separate from credit budget:** 10,000 req/day (Plus). An agent loop is one request per turn; a 40-turn loop is 40 requests. Track `X-RateLimit-Remaining` and refuse cloud when it is below a reserve.
- **Unknowns to measure with a real key (T-0122):** actual settlement vs hold for 1-credit models; whether `/v1/responses` tool turns are cheaper than `/v1/chat/completions` (F17); cache-hit savings.

### 3.3 Which model to default

- `auto` is honest ("billed for the resolved slug") but **cost-unbounded**: a "hard" classification can land on a 15–60 credit model. For a hedge whose whole point is bounded cloud spend, `auto` should be opt-in for `hard` tasks, not the default.
- Recommended default pin for the Gab lane: a `base_cost: 1`, `function_calling: true`, streaming slug with a large output ceiling — today `qwen-3-8-flash` (1M ctx, 131k out) or `glm-5-3-flash`; `arya-agent` (DeepSeek V4.1 Flash alias, 384k out) is also 1 credit but its alias can move (F14/F15). Re-read `/v1/models` at attach time and pick by rule (`min base_cost` among `recommended_for ∋ coding`), do not hard-code the slug.
- If `auto` is used, send `routing.coding_tier: "quick"` for `bulk`, unset for `hard`, and always `max_tokens`.
- Client timeouts: 120–210 s read timeout and `stream: true` for thinking models (Gab's own guidance).

### 3.4 Harness wiring differences the toolset plan must know

| Harness | Gab env | Endpoint |
|---------|---------|----------|
| OpenCode | `opencode.json` provider block; fetch from `GET /v1/agent-setup?client=opencode`; OpenCode ignores `OPENAI_BASE_URL` | `/v1/chat/completions` or `/v1/responses` depending on `npm` package (F17) |
| Codex | `OPENAI_BASE_URL=https://gab.ai/v1`, `OPENAI_API_KEY=$GAB_API_KEY` | `/v1/responses` |
| Claude Code | `ANTHROPIC_BASE_URL=https://gab.ai` (**no** `/v1`), `ANTHROPIC_AUTH_TOKEN=$GAB_API_KEY` | `/v1/messages` |
| Grok CLI | not documented by Gab; would need an OpenAI-compatible provider entry | `/v1/chat/completions` |
| Pi | `pi install npm:@gabai/pi-gab-ai`; `GAB_API_KEY` or `GAB_AI_API_KEY` | via package |

### 3.5 ToS points that bind the harness

- API use in agent loops is explicitly supported (Cursor/Claude Code/Codex/OpenCode docs) → **automation is authorised** when it goes through the API with your own key.
- **Do not** fine-tune, distil, or build a competing model/service from Gab Output (ToS). For this repo: never feed Gab responses into local model training or into a "Gab-equivalent" router product. Evaluation/benchmarking for internal routing is not obviously prohibited but is untested; record as an open question rather than assume.
- One key per operator; no shared/team keys (Terms of Sale: no sharing access). Use `/v1/api-keys` to mint per-box keys.
- Output rights transfer to the user; business use permitted. 18+ only. PA law/arbitration.
- Weights licensing: **not applicable** — Gab ships no weights. Licences that matter for the Ollama pulls are the upstream ones (Gemma Terms of Use, Qwen/Apache-2.0, DeepSeek MIT, GLM MIT, Kimi modified-MIT, …) and are unaffected by Gab.

## 4. Repo assumptions vs findings (`pfy_gab_228.py`, `docs/ops/gab-228.md`, `docs/design/GAB-228-DEVBOT-HANDOFF.md`)

| Repo assumption | Verdict | Evidence |
|-----------------|---------|----------|
| `GAB_BASE = https://gab.ai/v1`, `/v1/models`, docs URLs | **Correct** | F1–F3 |
| `GAB_API_KEY` primary; `GABAI_API_KEY` fallback | **Partly**: Gab uses `GAB_API_KEY` and `GAB_AI_API_KEY`; `GABAI_API_KEY` is a third-party project's (indyfive11/gabagent) variable, not Gab's | F2, F18 |
| `model=auto` default = "cloud best" | **True but unsafe for a hedge** (cost-unbounded, slug not stable) | F10, §3.3 |
| "Plus/max plan required" copy | **Wrong**: plans are Free / Plus / Plus Premium / Enterprise; there is no "max" | F5 |
| HTTP 403 → "plus required" | **Wrong**: 403 is documented as *key revoked*; `plus_required` is an `error.code`; 402 = insufficient credits | F13 |
| `GET /v1/models` "auth optional" | **Correct** (public) | F3 |
| `lane: "cloud/subscription"` | **Incomplete**: subscription **plus metered credits**; the lane never reads `credits_used` or `/v1/credits` | F4, F7 |
| `LOCAL_CODER_MODEL = <gab slug>` in `apply_cloud_env` | **Wrong**: overwrites the local worker model variable with a cloud slug, blurring the lane the hedge is supposed to keep separate (AGENTS.md: `LOCAL_CODER_MODEL` = local worker) | ADR-0011/0017 |
| "Gab does NOT host GGUF / local weights" | **Correct**; stronger than stated — Gab hosts no weights of any kind | F19, §2 |
| `PROPRIETARY` contains `arya` | **Correct** in effect; but `arya`/`arya-agent` are aliases to third-party slugs, so they are neither Gab-proprietary nor open — treat as "opaque alias, price 1–floor" | F14, F15 |
| `is_open_weight()` marks `qwen-3-7-max`, `qwen-3-8-max`, `qwen-3-7-plus` as open-weight family | **Misleading**: Qwen Max/Plus are API-only models; the *family* has open siblings but the listed id does not. Mapping to `qwen2.5-coder:32b` is a stand-in, not a sync | live catalog |
| `kimi → qwen2.5:14b` "closest common local stand-in" | **Not a sync**; honest comment, dishonest row label (`source: gab-open-weight→ollama`) | code |
| Fixture = "offline Gab `/models` JSON" | **Stale**: 24 ids vs 59 live text ids; `arya` alias moved; no capture date/ETag recorded | F14, F28 |
| Timeout 12 s for `/v1/models` | fine; **no** guidance for chat (Gab: 120–210 s, stream) | docs/api |
| No handling of `X-RateLimit-*`, `X-Gab-Routed-Model`, `max_tokens`, `/v1/credits`, `/v1/agent-setup` | **Gaps** for a hedge lane | F7, F10, F11, F17 |
| DevBot handoff: "Attach Gab cloud with `auto` works under Plus key" | **Unverified** in this pass (no key used); `--selftest` passes offline | selftest run 2026-09-20 |

## 5. Recommended changes (list only — not applied)

`scripts/pfy_gab_228.py`

1. Env: accept `GAB_API_KEY` then `GAB_AI_API_KEY`; drop or demote `GABAI_API_KEY` (third-party name).
2. Stop writing `LOCAL_CODER_MODEL` in `apply_cloud_env`/`cloud_lane.env`; use `PFY_GAB_MODEL` (and `PFY_CLOUD_MODEL`) only.
3. Error mapping: parse `error.code` — `invalid_api_key`/`missing_api_key` (401), `insufficient_credits` (402), key revoked (403), `plus_required`, `invalid_model` (400), `unsupported_tool_calling`, 429 with `X-RateLimit-Reset`. Remove "403 → plus required".
4. Default model: replace hard-coded `auto` with a rule — cheapest `base_cost` among live/fixture text models with `function_calling: true` and `recommended_for ∋ "coding"`; keep `auto` as explicit `--model auto` for `hard`. Always set `max_tokens` (e.g. 8k) in any generated request config.
5. Add `credits()` → `GET /v1/credits` (auth) returning `monthly_remaining`, `purchased_credits`, `resets_at`; surface in `snapshot_fields` and in `./pfy hedge ledger`.
6. Add a per-call ledger hook that records `usage.credits_used`, resolved `model`, `X-Gab-Routed-Model`, `X-RateLimit-Remaining` into `$PFY_STATE_DIR/hedge-ledger.json` (unit `gab_credit`). Estimator: `base_cost × (1 + prompt_tokens // context_threshold)` labelled `hold_estimate`, never `cost`.
7. Add `agent_setup(client)` → `GET /v1/agent-setup?client=opencode|claude-code|cursor` and use it for the OpenCode/Claude Code cells of the toolset × harness matrix (ADR-0017) instead of hand-built env; Claude Code needs `ANTHROPIC_BASE_URL=https://gab.ai` (no `/v1`).
8. Fixture: re-capture from live `/v1/models?type=text`, store `captured_at` and the `etag` (`W/"131f4-..."` today) beside `data`; add a `--refresh-fixture` verb; extend selftest to assert `arya`'s alias is *not* trusted (it moves).
9. `is_open_weight()`: match on **model id**, not family token — allow `gemma-4-26b`, `kimi-k2-6`/`kimi-k3`, `glm-*`, `deepseek-v4*`, `minimax-m*`, `qwen-3-5-397b*`; exclude `qwen-*-max`/`-plus`/`-flash` API-only ids. Label stand-ins (`kimi → qwen2.5:14b`) as `source: stand-in`, not `gab-open-weight→ollama`.
10. Rename lane string `cloud/subscription` → `cloud/credits (Plus)`; docstring: remove "Plus/max".
11. Chat guidance constants: `GAB_READ_TIMEOUT_S = 210`, `stream: true` for thinking models; expose in `env`.
12. Remove "Catalog 70–75 HOLD / do not reopen #76 / No Env tab" liturgy from the docstring per ADR-0017 §6.

`docs/ops/gab-228.md` / `docs/modules/gab-228.md` / `docs/design/GAB-228-DEVBOT-HANDOFF.md`

13. Replace "Plus/max" with "Plus (or Plus Premium)"; add the credits model (1-credit floor, hold vs settle, two pools, 10k req/day) and the `hedge` interaction.
14. State plainly: Gab is a **cloud-only** lane; the "local sync" is an informational family hint, not a Gab local path; `arya` on the API is an alias to a third-party slug that changes.
15. Add a "ToS for agents" box: API automation OK; no distillation/competing-model use of Output; one key per operator; 18+.
16. Add this file to the module page's links and to `docs/ops/local-cloud-split.md` as the Gab pricing reference.

Process items (for the parent to file, not done here): an OQ on whether internal routing evals count as "developing a competing service" under Gab's ToS (P2); T-0122 live ledger should include the two Gab measurements in §3.2.

## 6. Catalog Stage 0 gate + provisional row (CATEGORIZATION.md; not written to TOOLS.md / data/tools.json)

**Candidate:** Gab AI API Router (`https://gab.ai/v1`) · **Primary category:** Proxy & Routing (hosted).

| Stage 0 gate | Result | Note |
|--------------|--------|------|
| Self-hostable, <5 min on fresh Ubuntu/Mac | **FAIL** | SaaS; nothing to install. Client setup (key + base URL) is <5 min, but that is not self-hosting. |
| Licence allows commercial/research use, no copyleft for embedding | **PASS (with ToS caveats)** | Output usable commercially; no weights so no weight licence; ToS bars competing-model use of Output and sharing keys. |
| Clear runnable hello-world | **PASS** | `curl https://gab.ai/v1/chat/completions` with Bearer key; public `/v1/models`. |

Gate fails on one criterion → per rubric, track as **niche** with the failure documented.

| Stage | Score | Reasoning |
|-------|------:|-----------|
| S1 Core LLM & agent compat | 80 | OpenAI tools/streaming/strict JSON schema across many models, Responses + Anthropic shapes, tool-call translation; deductions for `auto` non-determinism and provider-dependent `json_schema` 400s. |
| S2 Performance & resource | N/A (cloud) | Rubric measures local tok/s and VRAM. If scored on cost-efficiency: 1-credit (~$0.01) coding calls with 1M context are cheap; unmetered latency. |
| S3 Pipeline integration | 70 | `agent-setup` configs for OpenCode/Claude Code/Cursor, `/v1/credits`, `/v1/api-keys`, standard SDKs; no Docker (n/a), docs drift (F17), no Grok CLI recipe, Cloudflare/504 retry burden. |
| S4 Ecosystem | 40 | Five-person company; one official client package (MIT, 11 weekly downloads); GitLab repo not verifiably public; no AI code on GitHub/HF; docs decent but self-contradicting on catalog. |
| **Overall (S1,S3,S4 mean)** | **≈63** | |

**Provisional tier: C (niche, cloud-lane provider; Stage 0 self-host gate FAIL).** Interesting for the hedge as a cheap multi-vendor credit pool with exact per-call metering; not infrastructure, not local, small-vendor risk.

Proposed `TOOLS.md` row (do not paste without owner review):

```
| **Gab AI API Router** | Proxy & Routing | https://gab.ai/docs/api (SaaS; client pkg npm `@gabai/pi-gab-ai`, MIT) | 80 | N/A | 70 | 40 | 63 | C | #openai-shim #tool-calling #structured-output #cloud #credits #litellm-ready | **Cloud lane only (hedge, ADR-0017).** Plus required; every API call bills credits (1-credit floor; hold vs settle). Meter via `usage.credits_used` + `GET /v1/credits`; 10k req/day. `auto` = router, billed for resolved slug — pin a `base_cost:1` coding slug by rule. **No weights, no local path; `arya` is an alias to third-party slugs.** Stage 0: self-host FAIL. Eval: [docs/evaluation/gab-ai-cloud-lane-2026-09.md](docs/evaluation/gab-ai-cloud-lane-2026-09.md). |
```

Proposed `data/tools.json` entry (slim subset, ADR-0015):

```json
{
  "name": "Gab AI API Router",
  "primary_category": "Proxy & Routing",
  "github": null,
  "url": "https://gab.ai/docs/api",
  "scores": {"s1": 80, "s2": null, "s3": 70, "s4": 40, "overall": 63},
  "tier": "C",
  "tags": ["openai-shim", "tool-calling", "structured-output", "cloud", "credits", "litellm-ready"],
  "notes": "Cloud-only credit lane for the hedge. Stage 0 self-host gate FAIL (SaaS). No weights; arya is an alias to third-party slugs. Meter usage.credits_used + /v1/credits.",
  "integration_stage": "I1",
  "implementation": {"toolset": "gab", "stage": "I1"},
  "evaluation": "docs/evaluation/gab-ai-cloud-lane-2026-09.md"
}
```

## 7. What could not be verified (explicit)

- Anything requiring an authenticated call: real `credits_used` per model, hold vs settle behaviour, `/v1/responses` vs `/v1/chat/completions` tool-turn billing, cache-hit discounts, actual `X-Gab-*` header values, whether `plus_required` fires for a Free-tier key.
- Whether Gab hosts **any** model on its own hardware (no statement, no artifact either way).
- What `arya` is beyond its alias; parameter count; training; whether the in-app steering layer exists on the API in any form (Torba says no; not tested).
- Public availability of `gitlab.com/GabAIInc/pi-gab-ai` (302 redirect; group API 404).
- ToS `Last Updated` date (not present in fetched text).
- Ollama tag-level existence (`gemma4:26b`, `glm-4.7-flash` default tag, `gpt-oss:120b`) — only library names were checked.
- Any independent (non-Gab) technical review of the API in 2026; the only third-party artifact found is a hobby client (`indyfive11/gabagent`).

## Agent section

- **Invariants:** Gab = `cloud` lane only; metering unit `gab_credit`; source of truth per call is `usage.credits_used`, never the tariff; `arya`/`auto` slugs are not stable engines — log `response.model`.
- **Do not:** claim Gab hosts weights; default to `auto` in the hedge; write `LOCAL_CODER_MODEL` from the Gab lane; share keys across operators; use Gab Output to train local models.
- **Re-verify when:** `/v1/models` ETag changes; pricing page changes; a Gab weights release appears on HF (search author `GabAI`, `Gab AI Inc`); T-0122 live ledger lands.
- **Links:** ADR-0017 · ADR-0014 · ADR-0015 · `docs/ops/gab-228.md` · `docs/ops/local-cloud-split.md` · CATEGORIZATION.md §3–4.
