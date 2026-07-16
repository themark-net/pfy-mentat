# Evaluation Framework for Local LLM Dev Tools Catalog

**Status**: v1.1 — July 2026 (Updated with full pipeline + implementation step)
**Purpose**: Provide a consistent, rigorous, and actionable process for triaging, evaluating, scoring, and ultimately **implementing** high-value tools/patterns into our active development environment.

## Full Evaluation Pipeline (Mandatory Flow for New Entries)

Every new item must progress through these phases. The process is designed to be repeatable and leads to concrete implementation.

### Phase 0: Triage & Relevance Gate
- Quick filter (< 5 min).
- Criteria: Local/self-hosted value, open source/reproducible, not pure red-team/offensive unless notable for awareness.
- Decision: Accept → Phase 1, Defer, or Reject.

### Phase 1: Initial Cataloging
- Add to `sources/x-posts.md` with structured entry.
- Create/update row in `TOOLS.md`.
- Add to `data/tools.json` (if applicable).
- Capture initial attributes (Relevance, Integration Ease, etc.).

### Phase 2: Full Attribute Scoring
- Apply the rubric below to produce scores.
- Identify overlaps/complementarity with existing entries.
- Update relevant matrices (Loop Engineering, Memory Systems, Skills, etc.).

### Phase 3: Integration Feasibility Assessment
- Determine specific integration points (new skill? evaluator pattern? memory backend? inference optimization? safety guard? deployment script?).
- Estimate effort and assign priority tier.

### Phase 4: Implementation & Environment Integration (Final Mandatory Step)
- **This is the critical final component**.
- High-priority items must result in concrete changes to our development environment.
- This is handled via the **Centralized Idempotent Environment Setup Script** (see below).
- Examples of implementation:
  - Adding a new skill or pattern to the Loop Engineering pack.
  - Updating the `agenc-launch` wrapper or caching logic.
  - Incorporating a memory backend or RAG optimization.
  - Adding safety guards or inference optimizations to the baseline setup.
  - Updating documentation or AGENTS.md with new patterns.

## Evaluation Rubric (v1.1)

Scored on four dimensions + overall priority.

### 1. Relevance to Local Agent Workflows & Our Goals
- **Very High (5)**: Core to loop engineering, self-improving systems, memory/context, safety, or inference performance.
- **High (4)**: Strong complement or valuable production-validated pattern.
- **Moderate (3)**: Useful in specific niches or as reference.
- **Lower (2)**: Tangential or primarily awareness/red-team value.

### 2. Integration Ease with AgenC + Loop Engineering + Skills Layer
- **Very High (5)**: Minimal adaptation; clear path via skills, MCP, evaluators, or launch wrapper.
- **High (4)**: Moderate work but clear integration points.
- **Moderate (3)**: Significant adaptation or new infrastructure needed.
- **Lower (2)**: High friction or poor architectural fit.

### 3. Reproducibility
- **Very High (5)**: Excellent docs, easy install, active maintenance, clear examples.
- **High (4)**: Good docs + open source; minor friction acceptable.
- **Moderate (3)**: Open source but incomplete docs or complex setup.
- **Lower (2)**: Poor docs, heavy dependencies, or unclear path.

### 4. Redundancy vs. Unique/Complementary Value
- **Low Redundancy / High Unique Value (5)**: Fills clear gap or offers meaningfully superior approach.
- **Low-to-Moderate (4)**: Some overlap but adds important scale, nuance, or validation.
- **Moderate (3)**: Notable overlap; still valuable for comparison.
- **High Redundancy (2)**: Largely duplicates existing entry without clear differentiator.

### Overall Priority Tier
- **S-Tier (Priority 1)**: Must integrate or deeply study in current sprint.
- **A-Tier (Priority 2)**: Strong addition — plan integration or testing soon.
- **B-Tier (Priority 3)**: Useful reference — catalog with lighter follow-up.
- **C-Tier (Awareness)**: Log for completeness; minimal active work.

## Pipeline Process for New Entries (Repeatable Workflow)

1. New X post or candidate identified.
2. Run Phase 0 triage.
3. If accepted → Create structured entry in `sources/x-posts.md` (Phase 1).
4. Apply full rubric scoring (Phase 2) and note overlaps.
5. Determine integration points and priority (Phase 3).
6. **Execute implementation** via the centralized idempotent setup script or targeted updates (Phase 4).
7. Update relevant docs (AGENTS.md, evaluation notes, skill pack READMEs).
8. (Optional but recommended for S/A-Tier) Perform hands-on testing and document results.

This pipeline ensures we don't just catalog — we **build** with the best components.

## Implementation Component: Centralized Idempotent Development Environment

**Location**: `bootstrap/setup-local-agent-env.py` (or equivalent in `tools/`)

**Goal**: A single, idempotent Python script (or small package) that sets up or updates a complete, reproducible local agent development environment incorporating the highest-value components we've evaluated.

**Core Principles**:
- Idempotent (safe to re-run).
- Modular (easy to extend with new high-scoring items).
- Incorporates AgenC as primary runtime + our augmentation layer.
- Includes key patterns from Loop Engineering, Memory/Context, Safety, Inference optimizations, and Skills.

**Planned / In-Progress Components** (to be expanded based on scoring):
- AgenC installation + `agenc-launch` wrapper with update checks and offline mode.
- Loop Engineering skill pack (4-tier autonomy + 14-step roadmap + feedback loops from Hermes patterns).
- Core memory/context tools (e.g., integration points for Memvid-style versioning or LEANN-style compression where applicable).
- Safety guards (e.g., destructive command protection patterns).
- Inference optimizations (e.g., ngram-mod speculative decoding configuration).
- Baseline skills and AGENTS.md enhancements from high-scoring org-chart and skill library patterns.
- Documentation sync (update relevant READMEs and AGENTS.md).

This script will become the canonical way to bootstrap or refresh our environment with the best-evaluated components.

## Current Category Taxonomy (Reviewed July 2026)

(unchanged from v1.0 — see previous version for full list)

## Alignment & Scoring Summary (High-Level)

Recent high-signal clusters:
- **Loop Engineering & Self-Improving Systems**: Very strong (Hermes feedback loops, Spec Kit command flow, eval loops, N-gram optimization).
- **Memory & Context Systems**: Very strong (Memvid, LEANN compression, auto-memory patterns, persistent memory tools).
- **Skills & Org Structures**: Strong (large curated libraries, pre-built company templates).
- **Inference Performance**: Strong (speculative decoding, extreme quantization).
- **Safety**: Good (guardrails and isolation patterns).

Detailed per-entry scoring will be maintained in a separate scoring log or expanded in future updates to this document / TOOLS.md.

## Next Actions
- Implement `bootstrap/setup-local-agent-env.py` as the Phase 4 implementation vehicle.
- Begin systematic scoring of recent high-priority clusters.
- Expand the idempotent script with modules for the top-scoring components.
