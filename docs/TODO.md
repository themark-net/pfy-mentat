# TODO — next steps

**Purpose:** Single ordered work queue for humans and agents.  
**Design:** [DESIGN.md](DESIGN.md) · **ADRs:** [adr/](adr/README.md) · **Open questions:** [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md)

## Qualification model

| Field | Values | Meaning |
|-------|--------|---------|
| **Priority** | `P0` / `P1` / `P2` / `P3` | P0 = blocks current critical path · P1 = next milestone · P2 = important not blocking · P3 = someday |
| **Status** | `todo` \| `doing` \| `blocked` \| `done` \| `cancelled` | Active work only in **Active** table; finished rows move to **Done** |
| **Open questions** | `OQ-NNNN` or `—` | **Required** if Status is `blocked` or if work needs a human decision before P0/P1 can finish |
| **Depends** | T-IDs | Optional ordering edges |

**Rules**

1. Every `blocked` row **must** cite an OQ (or external blocker named in Notes).
2. Every OQ that blocks work should appear in at least one Active TODO’s **Open questions** column.
3. Do not invent architecture in a TODO — settle with `/adr`.
4. Never delete history; move finished rows to **Done**.
5. New tool integrations: register env vars in `bootstrap/env/REGISTRY.md`; prefer smokes **inside agent-cage**.

---

## Active (sorted P0 → P3)

**Session (2026-07-26):** **T-0093** tools-model probe + tool-split docs. Host: `make eval-select-tools-model` after Ollama up.

### Active — design / coding + local path (agent may pick freely)

| ID | Priority | Status | Item | Open questions | Depends | Notes |
|----|----------|--------|------|----------------|---------|-------|

| T-0090 | P0 | todo | **Minimal product levers audit**: collapse end-user surface to onboard / stage / ship; cap public Make targets | — | — | [product-operator-surface.md](ops/product-operator-surface.md); platform targets stay advanced |
| T-0091 | P1 | doing | **Voice local path** (half-duplex) polish | — | T-0085, ADR-0012 | 4b + T-0092 + T-0093 shipped |
| T-0092 | P1 | done | **Voice auto-agent default → opencode** (`1`/`opencode` local; `grok` escalate) | — | T-0091 4b | `make smoke-voice-agent`; Ollama HTTP fallback if no opencode CLI |
| T-0093 | P1 | done | **Tools-capable Ollama select + tool-split** | — | T-0080 | `make eval-select-tools-model` · `smoke-tools-model` · [local-tools-split.md](ops/local-tools-split.md) |
| T-0094 | P3 | todo | Optional short **local TTS** status (not duplex) | — | T-0092 | Kokoro/piper after local agent path green |
| T-0095 | P3 | todo | Catalog Stage 0: Pipecat / LiveKit / freeapp (ref only) | — | ADR-0012 | No primary install |

| T-0070 | P1 | doing | Grow design/coding **skills + structural eval** (more text scorers) | — | T-0065 | Keep `eval-structural` green |
| T-0074 | P1 | doing | Implement-lane via `make eval-auto` (fit-select + candidates) | — | — | deepseek-coder:6.7b lab-proven; StarCoder demoted |
| T-0075 | P2 | todo | More structural scorers: ADR shape, open-question row shape | — | T-0070 | |
| T-0076 | P2 | todo | Wire mattpocock to-spec/tdd checklist into structural or skill cross-links | — | — | paths pack already installed |
| T-0081 | P2 | todo | Optional OpenCode-in-cage smoke | — | T-0080 | After host smoke green |
| T-0040 | P2 | todo | Broader multi-CLI parity notes (Claude Code) | — | T-0080 | OpenCode first |

### Active — parked (env / not this track)

| ID | Priority | Status | Item | Open questions | Depends | Notes |
|----|----------|--------|------|----------------|---------|-------|
| T-0064 | P3 | todo | Auth file-mount EBUSY (grok-home dir) | — | T-0045 | Env polish; not design/coding |
| T-0043 | P3 | todo | Write-guard mcp-host wiring | — | T-0031 | Parked |
| T-0062 | P3 | todo | Laguna local model DoD | — | — | Hardware-gated; catalog only for now |
| T-0046 | P3 | todo | Re-evaluate AgenC | [ADR-0010](adr/0010-reject-agenc-as-primary-runtime.md) | T-0044 | |

| T-0007 | P3 | todo | adr-tools companion docs | — | — | |
| T-0002 | P3 | todo | Aggregate synthesis | — | — | |

### Active — blocked (batch OQs only — do not ask ad hoc)

| ID | Priority | Status | Item | Open questions | Depends | Notes |
|----|----------|--------|------|----------------|---------|-------|
| T-0015 | P2 | blocked | Antigravity-Manager eval | [OQ-0007](open-questions/OQ-0007-antigravity-need.md) | — | OQ-BATCH |
| T-0016 | P2 | blocked | colibri build+serve | [OQ-0008](open-questions/OQ-0008-colibri-weights-ok.md) | — | OQ-BATCH |
| T-0004 | P2 | blocked | ATG prototype coupling | [OQ-0004](open-questions/OQ-0004-atg-prototype-relationship.md) | — | OQ-BATCH |
| T-0005 | P2 | blocked | First subtree | [OQ-0003](open-questions/OQ-0003-first-subtree-candidate.md) | — | OQ-BATCH |

---

## Done

| ID | Priority | Status | Item | Notes |
|----|----------|--------|------|-------|
| T-0050 | P2 | done | First-party `/agent-loops` skill (8 exits + 4 types + Finn + rubric) | `bootstrap/grok-cli/skills/agent-loops/`; Entries 024/027/031/032/068; pairs with `/one-shot` |
| T-0048 | P2 | done | Hermes feedback loops as first-party Grok skill | `bootstrap/grok-cli/skills/hermes-feedback/`; Entry 048 pattern port; not Hermes runtime |
| T-0051 | P2 | done | First-party skill structural smoke + verification docs | `make smoke-grok-skills`; `bootstrap/grok-cli/scripts/verify_skills.py`; `docs/ops/skill-verification.md` |
| T-0052 | P2 | done | Cage first-party skills install on `cage-grok` + project `.grok/skills` sync | `grok-skills-install`; workspace-sync mirrors bootstrap skills |
| T-0053 | P2 | done | codebase-memory vs Graphify decision + Graphify B-tier catalog row | `docs/evaluation/codebase-memory-vs-graphify.md`; tools.json v0.4.6 |
| T-0054 | P2 | done | Loop engineering ops map + one-shot DoDs H/I/J | `docs/ops/loop-engineering.md`; one-shot-example-dods |
| T-0055 | P2 | done | Auto-Company pattern extract (no runtime) | `docs/ops/auto-company-patterns.md` |
| T-0060 | P2 | done | 8-exits eval task scaffold + deterministic scorer | `examples/eval-harness/tasks/003-exit-card-checklist/`; fixtures in structural lane |
| T-0065 | P1 | done | Structural eval lane (no LLM) + design-coding rubric + decision inventory | `make eval-structural`; `data/eval-lanes.json`; human-decision-inventory |
| T-0082 | P1 | done | ADR-0011 hybrid Grok/OpenCode/Ollama + local-cloud-split ops + opencode adapter | `docs/adr/0011-…`; `docs/ops/local-cloud-split.md`; `bootstrap/opencode/` |
| T-0080 | P1 | done | OpenCode + Ollama host smoke (skills + config + completion) | `make smoke-opencode-ollama`; `examples/opencode-ollama/`; opencode CLI optional |
| T-0085 | P0 | done | Worker/monitor dual-session recipe | `make worker-stage`; `/worker-monitor` skill; `docs/ops/worker-monitor.md` |
| T-0071 | P2 | done | Bumblebee coding-safety assist docs | `docs/ops/bumblebee-coding-safety.md` |
| T-0072 | P2 | done | MUE-X pattern extract (no evolve) | `docs/ops/mue-x-patterns.md` |
| T-0073 | P2 | done | LEANN/Memvid memory assist patterns | `docs/ops/memory-assist-patterns.md` |
| T-0030 | P0 | done | Env registry + profiles | merged main |
| T-0022 | P1 | done | Grok-in-image overlay | feature/agent-cage-grok-image merged; OIDC auth import |
| T-0000 | — | done | Process docs bootstrap | ADR-0001 |
| T-B001 | — | done | Grok CLI bootstrap | ADR-0004 |
| T-B002 | — | done | project-process scaffold | |
| T-B003 | — | done | `/catalog-docs` skill + README v0.4 | |
| T-0010 | P0 | done | Catalog hygiene Phase 0 | |
| T-0001 | P1 | done | Seed placeholder reconcile | OQ-0001 answered |
| T-0020 | P0 | done | agent-cage lab baseline (up-mcp + policy tests pass) | Operator smoke 2026-07-12; UX on main |
| T-0021 | P1 | done | Cage tool smokes **inside cage** (LiteLLM, MCP memory, repowise) | LiteLLM + codebase-memory + repowise; `make smoke-context-tools` |
| T-0013 | P1 | done | repowise smoke vs codebase-memory (prefer in-cage) | pipelines/smoke/context-tools-compare.md; both smokes green 2026-07-12 |
| T-0031 | P1 | done | **Write-guard MCP implement** (stdio server + cage overlay) | harness/write-guard-mcp v0.1; make smoke-write-guard; OQ-0009 audit default |
| T-0032 | P1 | done | **One-shot skill polish + example DoDs** for cage/tool smokes | docs/ops/one-shot-example-dods.md; skill points at make smoke-* |
| T-0006 | P2 | done | Module docs bootstrap + harness via `/catalog-docs` | docs/modules/* for grok-cli, project-process, agent-cage, write-guard, smokes |
| T-0011 | P1 | done | Phase 1 skill ports: marketing-council first-party + mattpocock paths subset | ADR-0009; council in skills/; mattpocock tdd/code-review/to-spec via paths |
| T-0014 | P2 | done | gstack role-pattern skills / AGENTS recipes (docs-first, not full embed) | docs/ops/gstack-role-recipes.md + AGENTS role router |
| T-0017 | P2 | done | First-party `investigate` RCA skill (gstack method rewrite) | bootstrap/grok-cli/skills/investigate/; not raw snapshot |
| T-0012 | P1 | done | LiteLLM recipes by DEPLOY_PROFILE (local / balanced / max) | config/litellm/{local-only,balanced,max-performance}.yaml + cage smoke |
| T-0003 | P1 | done | Eval harness MVP (OQ-0002 option 5) | tier0 smokes + tier1 scored task; make eval-mvp; DSPy deferred |
| T-0041 | P1 | done | Eval harness v0.2: multi-task suite + multi-model matrix | 002-fix-sum-evens; make eval-suite/matrix/v02; 3×2 matrix green |
| T-0044 | P1 | done | AgenC install experiment + smoke (then demoted) | Trial only; **ADR-0010** rejects as primary; host uninstalled; catalog B/watch |
| T-0045 | P1 | done | Grok Build in agent-cage + filesystem MCP on catalog workspace | `make cage-workspace-sync` / `cage-grok-ready`; project `.grok` → mcp-host filesystem |
| T-0047 | P1 | done | Cage Grok session resumption (persist + host→cage import) | `grok-state/sessions` mount; `cage-grok-sessions-import-host`; `cage-grok-resume` |
| T-0042 | P2 | done | Catalog re-score + absorb S-tier clusters; recover sources 001–055 | TOOLS.md + tools.json v0.4.2; eval-framework Grok-first; setup-local-agent-env rewritten |


## How to use

1. Scan **Open questions**; do not silently answer P0/P1.
2. Pick highest-priority non-blocked Active row.
3. Uncertainty → OQ; set TODO `blocked` if needed.
4. Architecture → `/adr`.
5. Finish → **Done** table.
