# Plan: Integrate mobile-seeded tools (Entries 001–010)

**Created:** 2026-07-12  
**Status:** Proposed (awaiting priority answers)  
**Design authority:** [DESIGN.md](../DESIGN.md), ADR-0002/0003/0004  
**Queue:** [TODO.md](../TODO.md)

## 1. Confirmation (recent seed wave)

| Check | Result |
|-------|--------|
| X seed entries in `sources/x-posts.md` | **10** (Entry 001–010) |
| Most recent commit | `797d023` Entry 010 gstack @ **2026-07-11 22:49:30 -0700** (~12–15 min before this analysis) |
| Wave window | Entries 003–010 committed ~20:24–22:49 local (-0700) same day — mobile Grok session wave |
| `data/tools.json` | Had **invalid JSON** (broken `tags` arrays); repaired to 10 tools; only **colibri** among new external seeds was in JSON |
| `TOOLS.md` table | **Does not list** marketing-skills, Antigravity-Manager, repowise, gstack, mattpocock/skills, etc. — **catalog drift** vs x-posts claims |

**Confirmed:** ≥10 seed entries exist and the latest were added minutes/hours ago. Full rubric rows were **not** fully synced for 004–010.

---

## 2. Deeper analysis of Entries 001–010

### Classification

| Entry | Artifact | Type | Local-first fit | Overlap | Catalog sync | Env status |
|-------|----------|------|-----------------|---------|--------------|------------|
| 001 ATG | paper + `themark-net/atg-framework` | methodology / prototype | High (DAG agents) | LangGraph/DSPy | In TOOLS (paper row); sibling repo | Prototype clone exists; not production |
| 002 ADR process | project-process + skills | process kit | High | — | Implemented first-party | **Working** (skills + docs) |
| 003 colibri | JustVugg/colibri | inference engine | High (extreme low-RAM MoE) | Ollama/llama.cpp | In tools.json only | **Not installed**; no weights |
| 004 marketing-skills | coreyhaines31/marketingskills | skill pack (council pattern) | Medium (prompts portable; Claude-native origin) | gstack roles, our skills | x-posts only | **Not installed** |
| 005 Antigravity-Manager | lbjlaq/Antigravity-Manager | account switcher + local API relay | High for multi-account hybrid | LiteLLM | x-posts only | **Not installed** |
| 006 repowise | repowise-dev/repowise | context/token efficiency layer | High | codebase-memory-mcp | x-posts only | **Not pip-installed** |
| 007 Jamon setup | workflow checklist | process patterns | High | AGENTS/project-process | Partial → AGENTS.md enhanced | **Partially absorbed** into AGENTS.md |
| 008 mattpocock/skills | skill library | composable skills | High | our skills, gstack | x-posts only | **Not installed** |
| 009 Ruben hacks | efficiency playbook | practices | Medium–high (principles) | repowise, AGENTS | x-posts only | **N/A (doc patterns)** |
| 010 gstack | garrytan/gstack | multi-specialist skills + tools | High as pattern; Claude-oriented install | 004, 007, 008 | x-posts only | **Not installed** |

### Value clusters (for integration sequencing)

1. **Catalog hygiene (P0)** — sync TOOLS.md + tools.json for all 10 seeds; fix process so future mobile adds cannot claim “cataloged” without both files.
2. **Already working operator stack** — keep/maintain; don’t reinvent.
3. **Skill/pattern ports** — marketing-council, mattpocock subset, gstack role patterns → Grok skills under bootstrap (small, SUBTREES-friendly as snapshots).
4. **Efficiency layer** — repowise empirical test vs codebase-memory-mcp (complement, not replace).
5. **Routing** — LiteLLM install + optional Antigravity relay for multi-backend.
6. **Inference experiments** — colibri (heavy weights / slow tok/s) only if operator wants flagship-MoE-on-laptop path.
7. **Eval harness** — still OQ-0002; needed to score empirical wins.

---

## 3. Already implemented & working in **this** environment

| Component | Evidence | Notes |
|-----------|----------|--------|
| **Grok CLI** | `grok 0.2.93` | Primary interface (ADR-0002) |
| **Grok process skills** | `~/.grok/skills/{adr,docs,open-questions,project-process,karpathy-guidelines}` | Replayable via bootstrap |
| **ponytail skills path** | config `skills.paths` | Snapshot + DEVELOP clone |
| **codebase-memory-mcp** | `0.9.0` + `grok mcp list` | Working MCP |
| **project-process + DESIGN/ADR/TODO/OQ** | this repo `docs/` | Working process |
| **Ollama** | `0.30.8` + many models (gemma4, qwen, codestral, etc.) | Strong local inference already |
| **Docker / Podman** | present | For later compose stacks |
| **DSPy + LiteLLM (gom-jobbar venv)** | dspy 3.2.1; litellm importable in that venv | Not global CLI; available in project venv |
| **ATG prototype repo** | `/home/mark/DEVELOP/atg-framework` | Sibling experiment |
| **AGENTS advanced workflows** | Entry 007 synthesis committed | Partial implementation of Jamon patterns |

**Not working / not present here:** colibri binary+weights, Antigravity-Manager, repowise package, marketingskills/gstack/mattpocock skill installs, global `litellm` CLI, `aider`/`continue` CLIs, full TOOLS.md rows for 004–010.

---

## 4. Documented design constraints (must follow)

From DESIGN + ADRs:

| Rule | Implication for this plan |
|------|---------------------------|
| Grok-first (ADR-0002) | Prefer skill ports and OpenAI-compatible endpoints over Claude-only install paths |
| Pin default, rare subtree (ADR-0003) | Shallow clone + pin; vendor only small skill snapshots into bootstrap |
| Bootstrap for operator env (ADR-0004) | New skills go through `bootstrap/grok-cli` or `project-process` patterns |
| Lean non-goals | Do not embed Ollama/colibri weights or huge UIs in this repo |
| Intake path | X → x-posts → rubric → TOOLS.md **and** tools.json |
| Near-term DESIGN goals | Seed intake, real pins, eval harness prototype |

---

## 5. Implementation plan (phased)

### Phase 0 — Catalog integrity (do first, ~1 session)

1. Keep `data/tools.json` valid (repaired).
2. Add TOOLS.md rows + tools.json entries for Entries 004–010 with honest scores and `x_post_id`.
3. Mark x-posts status accurately (`processed` only when both catalog files updated).
4. Add a short CONTRIBUTING/checklist bullet: **triple-write** (x-posts + TOOLS.md + tools.json) or fail CI later.
5. Close/update T-0001 if Entry 001/003 content supersedes pure placeholder (ATG + colibri already real seeds).

### Phase 1 — Skill ports (highest leverage, small surface)

Order by stack fit and size:

| Step | Work | Design method |
|------|------|----------------|
| 1.1 | Vendor **minimal** subset of mattpocock skills most aligned with our process (plan/review/TDD) into `bootstrap/grok-cli/skills-external/mattpocock/` or selective first-party adaptations | pin + skills.paths (like ponytail) |
| 1.2 | Port **marketing-council** pattern as Grok skill (single skill + advisor refs subset) under `bootstrap/grok-cli/skills/` or `examples/skills/` | snapshot SKILL.md; no full 47-skill pack unless asked |
| 1.3 | Extract **gstack** role patterns (CEO/QA/security review chain) into 1–3 Grok skills or document as AGENTS router recipes — **do not** full-clone 121k-star tree into repo | pin URL + optional skill adapters |
| 1.4 | Fold Ruben **efficiency principles** into AGENTS.md or a small `context-budget` skill | docs-only first |

### Phase 2 — Efficiency & memory

| Step | Work |
|------|------|
| 2.1 | `pip install repowise` in a dedicated venv or operator tools venv; run published harness or a small repo smoke |
| 2.2 | Compare: baseline Grok vs repowise-assisted context vs codebase-memory alone on same task |
| 2.3 | Document result in TOOLS notes; adjust scores |

### Phase 3 — Routing / hybrid stack

| Step | Work |
|------|------|
| 3.1 | Install LiteLLM globally or document uvx/docker one-liner in `examples/integration-patterns/` |
| 3.2 | Config recipe: Ollama (local) + Grok (remote) via LiteLLM |
| 3.3 | **Optional:** evaluate Antigravity-Manager Tauri binary if multi-account web-session tools are in use (GUI machine) |
| 3.4 | Wire OpenAI-compatible base URLs for agents |

### Phase 4 — Inference experiments (optional / hardware-gated)

| Step | Work |
|------|------|
| 4.1 | Decide whether colibri is worth disk+RAM (weights large; tok/s low) |
| 4.2 | If yes: shallow clone pin `5198fee…`, build, `serve`, point LiteLLM at it |
| 4.3 | Benchmark tok/s and agent usability; update scores |

### Phase 5 — Eval harness (DESIGN near-term)

| Step | Work |
|------|------|
| 5.1 | Resolve OQ-0002 (recommend: LiteLLM + Ollama smoke + one coding task) |
| 5.2 | Scaffold `examples/eval-harness/` or `pipelines/smoke/` |
| 5.3 | Use harness to re-score repowise, skill ports, colibri if adopted |

### Phase 6 — ATG coupling

| Step | Work |
|------|------|
| 6.1 | Resolve OQ-0004 (recommend: sibling only until harness needs DAG) |
| 6.2 | Link ATG prototype in catalog only; no submodule unless SUBTREES criteria met |

---

## 6. Suggested priority order (default if no answers)

1. Phase 0 catalog sync (P0)  
2. Phase 1.1–1.2 skill ports (P1)  
3. Phase 3.1–3.2 LiteLLM + Ollama recipe (P1)  
4. Phase 2 repowise smoke (P1)  
5. Phase 5 eval harness MVP (P1)  
6. Phase 1.3 gstack patterns (P2)  
7. Phase 3.3 Antigravity (P2, only if multi-account pain)  
8. Phase 4 colibri (P2/P3, hardware/time gated)  

---

## 7. Out of scope (this plan)

- Embedding full gstack / marketingskills / Ollama histories  
- Replacing codebase-memory with repowise  
- Making Claude Code the primary interface (violates ADR-0002)  
- Downloading multi-10GB weights without explicit operator OK  

---

## 8. Success criteria

- All 10 seeds have consistent x-posts + TOOLS.md + tools.json rows  
- Operator can reinstall skills via bootstrap  
- At least one new skill port usable in Grok (`/marketing-council` or mattpocock subset)  
- LiteLLM+Ollama recipe documented and smoke-tested  
- OQ-0002 either answered or harness scaffolded with a chosen option  
