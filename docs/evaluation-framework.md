# Evaluation Framework for Local LLM Dev Tools Catalog

**Status**: Draft v1.0 — July 2026
**Purpose**: Provide a consistent, rigorous process for triaging, evaluating, and integrating new tools, patterns, and resources into the catalog.

## Evaluation Phases

### Phase 0: Triage & Relevance Gate (Quick Filter)
- **Goal**: Quickly determine if an item warrants deeper evaluation.
- **Criteria**:
  - Does it meaningfully advance local/self-hosted LLM/agent capabilities?
  - Is it open source or have clear reproduction path?
  - Does it overlap significantly with existing high-priority entries (if yes, still consider for comparison notes)?
- **Output**: Accept for Phase 1, Defer, or Reject (with brief reason).
- **Typical Time**: < 5 minutes per item.

### Phase 1: Initial Cataloging
- **Goal**: Log the item and capture high-level attributes.
- **Actions**:
  - Add to `sources/x-posts.md` (or equivalent source log) with summary, extracted repos/tools, and initial notes.
  - Create or update row in `TOOLS.md`.
  - Add to `data/tools.json` if structured data is maintained.
- **Key Attributes Captured**:
  - Relevance to local agent workflows
  - Integration Ease (with existing stack: AgenC, loop engineering, skills, MCP, etc.)
  - Reproducibility (open source? clear install/docs?)
  - Redundancy / Complementarity with existing entries

### Phase 2: Attribute Scoring & Comparison
- **Goal**: Score the item rigorously against the rubric and compare to similar entries.
- **Actions**:
  - Apply full rubric scoring.
  - Identify overlaps, gaps, and unique value.
  - Update overlap/complementarity matrices (especially for clusters like Knowledge Graph/Second Brain, Loop Engineering, Skills).
- **Output**: Scored entry + comparison notes.

### Phase 3: Integration Feasibility & Planning
- **Goal**: Determine how (or if) to integrate the item into our active systems (skills, loops, harness, etc.).
- **Actions**:
  - Identify specific integration points (e.g., new skill, evaluator pattern, memory backend, deployment script).
  - Estimate effort and priority.
  - Document recommended next steps (test, adapt pattern, full integration, reference only).

### Phase 4: Hands-on Testing & Reproduction (Optional but Recommended for High-Priority Items)
- **Goal**: Validate claims through practical testing.
- **Actions**:
  - Set up and test in local environment (or Colab where appropriate).
  - Measure relevant metrics (speed, token usage, accuracy on representative tasks).
  - Document findings, gotchas, and reproduction steps.
- **Output**: Test report / reproduction notes.

## Evaluation Rubric

We score items across four core dimensions (1-5 scale where applicable, or qualitative labels).

### 1. Relevance (to Local Agent Workflows & Our Goals)
- **Very High**: Directly advances loop engineering, skills, memory/context, safety, or core local agent capabilities.
- **High**: Strong complement or useful pattern for our stack.
- **Good/Moderate**: Useful in specific niches or as reference.
- **Lower**: Tangential or primarily offensive/red-team focused (still logged for awareness if notable).

### 2. Integration Ease (with AgenC + Loop Engineering + Skills Layer)
- **Very High**: Drop-in or minimal adaptation required; clear MCP/skill/plugin path.
- **High**: Requires moderate work but clear integration points.
- **Moderate**: Significant adaptation or new infrastructure needed.
- **Lower**: Poor fit or high friction.

### 3. Reproducibility
- **Very High**: Fully open source, excellent docs, easy install, active maintenance.
- **High**: Open source with good docs; minor friction possible.
- **Moderate**: Open source but docs/install are incomplete or complex.
- **Lower**: Closed source, heavy dependencies, or unclear reproduction path.

### 4. Redundancy vs. Unique Value
- **Low Redundancy / High Unique Value**: Fills clear gap or offers meaningfully better approach.
- **Low-to-Moderate**: Some overlap but adds important nuance, scale, or production validation.
- **Moderate**: Notable overlap; still valuable for comparison or specific strengths.
- **High Redundancy**: Largely duplicates existing entry without clear differentiator.

### Overall Priority Scoring (Qualitative)
- **S-Tier / Priority 1**: Core to our direction; integrate or deeply study soon.
- **A-Tier / Priority 2**: Strong addition; catalog + plan integration or testing.
- **B-Tier / Priority 3**: Useful reference or niche value; catalog with lighter notes.
- **C-Tier / Awareness**: Log for completeness or red-teaming context; minimal follow-up.

## Current Category Taxonomy (as of July 2026)

Based on entries added so far, the catalog is organized around these primary categories (with sub-themes):

- **Agent Frameworks & Orchestration** (core multi-agent patterns, role specialization)
- **Autonomous Loops & Agentic Workflows** (loop engineering, feedback loops, self-improvement)
- **Skills & Prompt Engineering** (SKILL.md patterns, large curated libraries, org-chart structures)
- **Context & Memory** (RAG optimization, compression, persistent memory, second brain)
- **Inference & Serving** (local inference optimizations, speculative decoding, extreme quantization, browser inference)
- **Safety & Guardrails** (destructive command prevention, isolation)
- **Visualization & Observability** (real-time agent flow visualization)
- **Structured Workflows** (spec-first approaches like Spec Kit)
- **Pre-built Templates & Company Orgs** (ready-made org charts + skill sets)
- **Local Deployment & Stacks** (one-click local AI servers, hardware-aware tools)
- **MCP & Tooling Ecosystem** (MCP servers, design tools with MCP, etc.)
- **Task Management for Agents** (boards, issue tracking tailored for agents)

## Alignment Notes from Recent Additions (July 2026)

Recent entries (roughly Entries 018–053) show strong clustering around:
- Loop engineering & self-improving feedback loops (Hermes loops, Spec Kit, eval loops, N-gram optimization)
- Memory & context systems (Memvid, LEANN compression, opencode-mem, auto-memory patterns)
- Large-scale skills & org structures (awesome-hermes-skills, pre-built companies, Claude Company patterns)
- Inference performance (N-gram speculative decoding, Bonsai extreme quantization)
- Safety & reliability (destructive_command_guard, verification patterns)

**Key Observation**: There is healthy convergence on *self-improving / compounding agent systems* and *practical local memory/context solutions*. We should prioritize deepening the Loop Engineering skill pack and Memory/Context layer in the next integration sprint.

## Next Steps
- Formalize this rubric in `TOOLS.md` or a dedicated evaluation section.
- Create overlap/complementarity matrices for key clusters (Loop Engineering, Memory Systems, Skills).
- Begin Phase 2/3 scoring on high-priority recent entries.
- Update `AGENTS.md` and integration docs with relevant patterns from high-scoring items.
