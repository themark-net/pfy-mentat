# ADR-0014: Pluggable local inference runtime (OpenAI-compat)

- **Date:** 2026-08-24
- **Status:** Accepted
- **Deciders:** operator (direction); agent (write-up)

## Context

Local bulk work should not burn a Grok subscription (ADR-0011 worker/monitor split). Today `./pfy` treats **Ollama** as the inference spine (T-0101 / #54). That is too narrow:

- **Shimmy** is a lightweight single-binary OpenAI-compatible server (likely X-name candidate; “free forever”).
- **llama.cpp `llama-server`** behind **llama-swap** is the tok/s + on-demand model-swap path.
- **Ollama** remains valuable and already in the harness registry.

Vendoring any of those engines would violate ADR-0003 (pin, do not embed histories) and the DESIGN non-goal of not becoming an inference distro. Grok stays the **monitor / default harness** (ADR-0002, ADR-0011). Cloud Agent is not an implementer runtime on the current operator plan.

## Decision

1. **Local worker talks to an OpenAI-compatible HTTP endpoint.** Configure with `OPENAI_BASE_URL` and/or `PFY_INFERENCE_URL`. Recipe: `docs/ops/openai-compat-worker.md`.
2. **Inference engines are pluggable adapters**, not a monopoly spine. Candidates:
   - **Shimmy** — https://github.com/Michael-A-Kuykendall/shimmy — lightweight OpenAI server; default `http://127.0.0.1:11435/v1`; likely X-name candidate. Registry id=`shimmy`.
   - **llama-swap + llama.cpp llama-server** — https://github.com/mostlygeek/llama-swap + https://github.com/ggml-org/llama.cpp — on-demand swap / tok/s; default `http://127.0.0.1:8080/v1`. Registry id=`llama-swap`.
   - **Ollama** — remains an **adapter** (T-0101 completeness, not monopoly) at `:11434` (`/api/tags` or `/v1/models`). Do **not** remove. Default `PFY_INFERENCE=ollama`.
3. **Select at runtime:** `PFY_INFERENCE=ollama|shimmy|llama-swap` and optional `PFY_INFERENCE_URL`.
4. **Do not vendor engines** (ADR-0003). Pin + detect binaries only. `./pfy` must not exec engines that are not on PATH; missing adapters are honest notes + issue pointers, never fake **ready**.
5. **Grok = monitor / default harness.** Local worker = OpenAI-compat client (OpenCode or any OpenAI SDK). `make worker-stage` unchanged in spirit.

## Rationale

- One HTTP dialect (OpenAI `/v1/models`, `/v1/chat/completions`) lets the worker stay engine-agnostic.
- Adapter registry matches G8 / ADR-0012 (`data/harnesses.json` + `./pfy`) without exploding Make.
- T-0101 health (API actually responds) still applies; it is completeness for Ollama, not a claim that Ollama is the only spine.

Rejected alternatives:

1. **Vendor llama.cpp / Shimmy / Ollama into this repo** — ADR-0003 bloat; DESIGN non-goal (we are a catalog + operator surface, not an inference distro).
2. **Ollama-only forever** — blocks the Shimmy / llama-swap tok/s path; T-0101 is adapter completeness, not monopoly.
3. **Make Grok the local worker** — burns subscription on bulk; ADR-0011 already split worker vs monitor.
4. **Cloud Agent as implementer runtime** — not on the current Cursor plan; local OpenAI-compat worker remains the bulk path.
5. **Hermes Agent / AgenC as inference spine** — ADR-0010 / 0011 / 0013; those are harness/TUI surfaces, not engines.

## Consequences

- `data/harnesses.json` grows inference adapters (`shimmy`, `llama-swap`); `inference_default` stays `ollama`.
- `./pfy start` health-checks the selected OpenAI-compat URL (`/v1/models`) and, for Ollama, `/api/tags`. Bounded retries (not unbounded). If still down, report error and continue for cloud harnesses.
- `./pfy status` shows live inference backend; Ollama is **ready** only when an API responds.
- Catalog: Shimmy, llama-swap, llama.cpp llama-server rows in `TOOLS.md` + `data/tools.json` (v0.4.14). Stage 0 conceptual scores; integration_stage I0/I1 until smoke.
- Topology docs (`ARCHITECTURE.md`, `docs/ops/local-cloud-split.md`) show pluggable OpenAI-compat under the worker; Grok monitor unchanged.
- Layers on ADR-0002 / 0003 / 0011 / 0012 (G8 launcher). Does not renumber duplicate ADR-0012 files.

## References

- ADR-0002, ADR-0003, ADR-0010, ADR-0011, ADR-0012 (voice) / `0012-simple-harness-agnostic-launch.md` (G8 launcher; duplicate ID, not renumbered), ADR-0013
- `data/harnesses.json`, `scripts/pfy`, `docs/ops/openai-compat-worker.md`, `docs/ops/simple-launch.md`
- TODO T-0101, T-0110 · issues #53 #54
