# TODO — next steps

**Purpose:** Single ordered work queue for humans and agents.  
**Design:** [DESIGN.md](DESIGN.md) · **ADRs:** [adr/](adr/README.md) · **Open questions:** [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md)


## G8 — Simple harness-agnostic launch (2026-07-31)

| ID | Item | Status |
|----|------|--------|
| T-0100 | Epic: `./pfy` simple surface + harness registry | **done** (MVP) · [#53](https://github.com/themark-net/pfy-mentat/issues/53) |
| T-0101 | Ollama adapter complete in `pfy start` (health, default model) | open · [#54](https://github.com/themark-net/pfy-mentat/issues/54) |
| T-0102 | OpenCode host adapter (skill path + Ollama base_url) | open · [#55](https://github.com/themark-net/pfy-mentat/issues/55) |
| T-0103 | Hermes integrated installer adapter | open · [#56](https://github.com/themark-net/pfy-mentat/issues/56) |
| T-0104 | Claude Code adapter | open · [#57](https://github.com/themark-net/pfy-mentat/issues/57) |
| T-0105 | Codex adapter | open · [#58](https://github.com/themark-net/pfy-mentat/issues/58) |
| T-0106 | Gemini / Google harness adapter | open · [#59](https://github.com/themark-net/pfy-mentat/issues/59) |
| T-0107 | Exo optional lab path | open · [#60](https://github.com/themark-net/pfy-mentat/issues/60) |
| T-0108 | Continue + Ollama recipe | open · [#61](https://github.com/themark-net/pfy-mentat/issues/61) |
| T-0109 | Fold agent-cage into `pfy stage --lab` | open · [#62](https://github.com/themark-net/pfy-mentat/issues/62) |
| T-0110 | Pluggable local inference (ADR-0014 + Shimmy/llama-swap adapters) | **doing** · [#53](https://github.com/themark-net/pfy-mentat/issues/53) [#54](https://github.com/themark-net/pfy-mentat/issues/54) |

Authority: ADR-0012 · ADR-0014 · issues labeled `harness-adapter`. T-0090 remains documented MVP (do not mark done here if GitHub #1 already closed).

## GitHub issues (synced 2026-07-30)

Active work is also tracked as issues: https://github.com/themark-net/pfy-mentat/issues

See remaining tables on `main` for issue sync, qualification model, parked, follow-ups, and Done. Active design/coding table includes T-0110 P1 doing (pluggable local inference) immediately after T-0090. T-0090 stays todo / documented MVP.

### Active — design / coding + local path (agent may pick freely)

| ID | Priority | Status | Item | Open questions | Depends | Notes |
|----|----------|--------|------|----------------|---------|-------|
| T-0090 | P0 | todo | **Minimal product levers audit**: collapse end-user surface to onboard / stage / ship; cap public Make targets | — | — | [#1](https://github.com/themark-net/pfy-mentat/issues/1) · [product-operator-surface.md](ops/product-operator-surface.md) |
| T-0110 | P1 | doing | **Pluggable local inference** ADR-0014 + Shimmy/llama-swap/Ollama adapters; OpenAI-compat worker | — | T-0101 | [#53](https://github.com/themark-net/pfy-mentat/issues/53) · [#54](https://github.com/themark-net/pfy-mentat/issues/54) · [openai-compat-worker.md](ops/openai-compat-worker.md) |
