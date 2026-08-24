# Architecture snapshot

**Last updated:** 2026-08-24  
**Design authority:** [DESIGN.md](DESIGN.md)  
**Decision authority:** [adr/](adr/README.md)

Keep this file short. If layering or boundaries change, accept an ADR and update both this snapshot and DESIGN section 4.

## Purpose

Catalog + integration track for local-first LLM tooling, with a **hybrid operator environment**: Grok (primary/subscription **monitor**) + OpenCode (or any OpenAI client) as **worker** against a **pluggable OpenAI-compat** inference adapter (Shimmy | llama-swap+llama-server | Ollama) — ADR-0011 + ADR-0014.

## Data flow (delivered)

```text
sources (X / aggregates / papers)
    -> scoring (CATEGORIZATION rubric)
    -> TOOLS.md + data/tools.json
    -> bootstrap/grok-cli (skills SoT) + bootstrap/opencode (adapter)
    -> operator: Grok (monitor) and/or OpenCode (worker)
         -> OpenAI-compat (Shimmy | llama-swap+llama-server | Ollama)
         -> optional cloud per DEPLOY_PROFILE
```

## Layout map

| Area | Path | Notes |
|------|------|--------|
| Process | `docs/` | Design, ADR, TODO, OQ |
| Catalog | `TOOLS.md`, `data/`, `sources/` | Source of truth for scores |
| Bootstrap Grok | `bootstrap/grok-cli/` | Skills SoT + MCP + config merge |
| Bootstrap OpenCode | `bootstrap/opencode/` | Thin adapter; no forked skills |
| **Simple launch** | `./pfy`, `data/harnesses.json` | G8 / ADR-0012 multi-harness surface |
| Inference adapters | `PFY_INFERENCE`, `docs/ops/openai-compat-worker.md` | Shimmy / llama-swap / Ollama; do not vendor |
| Inference recipes | `config/litellm/`, `examples/litellm-ollama/` | Profile routers + cage smoke |
| Harness | `harness/agent-cage/` | Lab + Grok-in-cage |
| Eval | `examples/eval-harness/`, `pipelines/eval/` | Structural + implement lanes |

## Delivered vs not

| Delivered | Not yet |
|-----------|---------|
| Methodology + catalog + Grok bootstrap | OpenCode host smoke script (T-0080) |
| LiteLLM profiles + Ollama cage smoke | Default always-on LiteLLM daemon |
| Process docs + structural eval | Automated dashboard from JSON |
| Hybrid ADR-0011 + pluggable inference ADR-0014 | Full Shimmy/llama-swap serve recipes |
| `./pfy` MVP + harness stubs | Full Hermes/Codex/Gemini adapters |

## Extension points

- New tool -> score -> `TOOLS.md` + `data/tools.json` + source log
- New integration package -> under `bootstrap/` or `pipelines/` with ADR if it changes stack defaults
- New process rule -> ADR + update DESIGN/AGENTS.md
- New inference engine -> adapter row in `data/harnesses.json` + OpenAI-compat URL; **never vendor** (ADR-0003)

## Forbidden without ADR

- Second parallel decision log outside `docs/adr/`
- Embedding large upstream histories without meeting `SUBTREES.md`
- Putting secrets in catalog or docs
- Making Grok the bulk local worker or Ollama the only inference spine
