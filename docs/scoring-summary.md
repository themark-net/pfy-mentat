# Scoring Summary — Major Clusters (July 2026)

This document provides systematic scoring of high-signal entries using the rubric defined in `docs/evaluation-framework.md` and, for full multi-agent orgs, [evaluation/autonomous-ai-companies-rubric.md](evaluation/autonomous-ai-companies-rubric.md).

**Scoring Scale (standard tools)**:
- Relevance, Integration Ease, Reproducibility, Unique Value: 1–5
- Overall Priority: S-Tier (must act now), A-Tier (plan soon), B-Tier (useful reference), C-Tier (awareness)

**Scoring Scale (AI companies)**: C1–C6 dimensions 1–5 → weighted avg → S/A/B/C (see company rubric).

---

## Cluster 1: Loop Engineering & Self-Improving Systems

**Overall Cluster Assessment**: **Very Strong (S-Tier cluster)**
This is currently one of the highest-value areas. Multiple entries reinforce self-improving, compounding agent behavior with clear implementation paths.

| Entry | Title | Relevance | Integration Ease | Reproducibility | Unique Value | Overall Priority | Key Notes |
|-------|-------|-----------|------------------|-----------------|--------------|------------------|-----------|
| 018 | Getting Started with Loops (4 tiers + 14-step roadmap) | 5 | 5 | 4 | 5 | **S-Tier** | Foundational. Directly informs our Loop Engineering skill pack. |
| 021 | Loop Engineering Guide 2026 | 4 | 4 | 4 | 3 | A-Tier | Good reinforcement of Entry 018; useful for comparison. |
| 024 | Finn Loop (spec/build/review + Linear + Slack approval) | 5 | 5 | 4 | 5 | **S-Tier** | Excellent production example of goal-based + proactive loops with human gate. Strong candidate for adaptation. |
| 027 | Four Types of Agent Loops (turn/goal/time/proactive) | 5 | 5 | 5 | 4 | **S-Tier** | Clean pedagogical breakdown. Directly maps to our 4-tier model. |
| 031 | Iterative Feedback Loop (generate → test → update context) | 5 | 5 | 4 | 5 | **S-Tier** | Powerful self-healing pattern. High value for evaluator design. |
| 032 | Eval Loop (rubric-driven verification) | 5 | 5 | 5 | 4 | **S-Tier** | Practical rubric + layered rigor approach. Easy to port. |
| 048 | HERMES AGENT — Three Feedback Loops (Auto-Memory, Auto-Skill, Curator) | 5 | 5 | 4 | 5 | **S-Tier** | Best real-world self-improving system found. Direct blueprint for our skills + memory layer. |

**Cluster Recommendations**:
- Prioritize integration of Hermes-style feedback loops into Loop Engineering pack.
- Adapt Finn Loop patterns (spec/build/review) as concrete examples.
- Use rubric-driven eval loop (Entry 032) as a template for goal-based evaluators.

---

## Cluster 2: Memory & Context Systems

**Overall Cluster Assessment**: **Very Strong (S-Tier cluster)**
Strong convergence on practical, local-first memory solutions.

| Entry | Title | Relevance | Integration Ease | Reproducibility | Unique Value | Overall Priority | Key Notes |
|-------|-------|-----------|------------------|-----------------|--------------|------------------|-----------|
| 014 | Karpathy Second Brain / Obsidian + Claude | 4 | 5 | 5 | 3 | A-Tier | Solid lightweight pattern; already partially referenced. |
| 020 | Live Obsidian Business Network Graph | 3 | 4 | 4 | 3 | B-Tier | Good real-world scale example but less directly actionable. |
| 044 | Memvid (MP4-based memory with git-like versioning) | 5 | 5 | 4 | 5 | **S-Tier** | Revolutionary approach. High potential for long-term agent memory. |
| 049 | opencode-mem (persistent memory for OpenCode) | 4 | 4 | 5 | 3 | A-Tier | Practical local vector DB solution for coding agents. |
| 052 | LEANN (extreme RAG compression 97% savings) | 5 | 4 | 4 | 5 | **S-Tier** | Game-changing for local RAG feasibility. Must evaluate. |

**Cluster Recommendations**:
- Deeply evaluate Memvid and LEANN for memory layer.
- Consider hybrid approaches (versioned MP4 + compressed indexes).
- Integrate persistent memory patterns into Loop Engineering where relevant.

---

## Cluster 3: Skills & Org Structures

**Overall Cluster Assessment**: **Strong (A-Tier cluster)** — *partially superseded for full-company eval by Cluster 5*
Good production validation of large-scale skill organization. Pure skill packs stay here; full closed-loop companies move to Cluster 5.

| Entry | Title | Relevance | Integration Ease | Reproducibility | Unique Value | Overall Priority | Key Notes |
|-------|-------|-----------|------------------|-----------------|--------------|------------------|-----------|
| 016 | Claude Company Org Chart (42+ skills) | 4 | 4 | 4 | 4 | A-Tier | Early strong signal for org-chart thinking. |
| 037 | Claude as Full Company (122 skills, 7 departments) | 5 | 5 | 5 | 4 | **S-Tier** | Excellent real-world $40k MRR example. High production value. Also scored under Cluster 5 when treated as company. |
| 050 | paperclipai/companies (16 pre-built AI companies) | 4 | 5 | 5 | 4 | A-Tier | Ready-made templates — useful for rapid bootstrapping. Cluster 5 primary. |
| 053 | awesome-hermes-skills (271 curated skills) | 5 | 5 | 5 | 4 | **S-Tier** | Best current curated library. Direct complement to Hermes (Entry 048). |

**Cluster Recommendations**:
- Study curation patterns from awesome-hermes-skills and Entry 037.
- Use pre-built company templates (Entry 050) for experimentation.
- Expand our own skill pack using these as references.
- Route full autonomous company runtimes to **Cluster 5**.

---

## Cluster 4: Inference Performance

**Overall Cluster Assessment**: **Strong (A-Tier cluster)**
High practical value for making local agents faster.

| Entry | Title | Relevance | Integration Ease | Reproducibility | Unique Value | Overall Priority | Key Notes |
|-------|-------|-----------|------------------|-----------------|--------------|------------------|-----------|
| 045 | Bonsai 27B (1-bit quantization + browser WebGPU) | 4 | 4 | 4 | 4 | A-Tier | Impressive extreme quantization results. |
| 051 | N-gram Speculative Decoding (ngram-mod in llama.cpp) | 5 | 5 | 5 | 5 | **S-Tier** | Zero-VRAM, high-impact optimization. Immediate integration candidate. |

**Cluster Recommendations**:
- Add ngram-mod configuration to the idempotent setup script (high priority).
- Test Bonsai-style quantization on relevant local models.

---

## Cluster 5: Autonomous AI Companies (NEW — 2026-07-20)

**Overall Cluster Assessment**: **Strong / emerging (S/A mix)**  
Dedicated category + rubric: [evaluation/autonomous-ai-companies-rubric.md](evaluation/autonomous-ai-companies-rubric.md).  
These are full multi-agent orgs (personas, consensus, cycles), not skill packs alone.

| Entry / Tool | C1 Org | C2 Cycle | C3 Memory | C4 Safety | C5 Econ | C6 Local | Weighted | Priority | Key Notes |
|--------------|--------|----------|-----------|-----------|---------|----------|----------|----------|-----------|
| **Auto-Company** (MaxMiksa) Entry 066 | 5 | 5 | 5 | 4 | 4 | 5 | **4.7** | **S** | 14 expert personas (Bezos/Vogels/Munger/DHH…); consensus.md baton; pre-mortem gates; daemon on macOS/Win/Linux; Claude Code + Codex; honest cost caveat. Pattern goldmine. |
| Claude Company 122 skills (037) | 4 | 2 | 3 | 3 | 3 | 4 | 3.2 | B→A | Org chart + skills; weak closed-loop autonomy unless operator builds cycles. |
| paperclipai/companies (050) | 4 | 2 | 3 | 2 | 2 | 4 | 2.9 | B | Templates/import; platform-coupled; good bootstrap reference. |
| Multica (012) | 3 | 4 | 4 | 3 | 3 | 4 | 3.5 | A | Board + agent teammates + skills; closer to PM platform than full company loop. |
| gstack (010) | 4 | 3 | 3 | 4 | 2 | 3 | 3.2 | B | Role skills + workflow; not a 24/7 company daemon. |

**Company-dimension key (1–5):**  
C1 Org Design & Role Fidelity · C2 Autonomy & Cycle Design · C3 Shared Memory & Consensus · C4 Safety & Blast Radius · C5 Economic Realism & Convergence · C6 Local / Operator Fit.

**Cluster Recommendations**:
1. **Extract from Auto-Company first:** consensus.md steer file, Munger pre-mortem gate, named expert personas, squad formation, forbidden-action table → first-party Grok skills / AGENTS.md sections.
2. Do **not** make Auto-Company (or any company daemon) primary operator runtime without ADR.
3. Compare Auto-Company vs Multica board vs gstack roles vs paperclip templates before any deep port.
4. Optional later: pin Auto-Company + document external run; cage only if isolation story is clear.
5. Re-score 037/050 under this rubric when they gain real cycle engines.

---

## Summary of Top Priorities (S-Tier Items)

1. **HERMES feedback loops** (Entry 048) — Core self-improvement architecture.
2. **N-gram speculative decoding** (Entry 051) — Immediate performance win.
3. **Memvid + LEANN** (Entries 044 + 052) — Next-generation memory/context layer.
4. **Finn Loop + Eval Loop patterns** (Entries 024 + 032) — Concrete implementation examples.
5. **awesome-hermes-skills + Company org patterns** (Entries 053 + 037) — Skill scale and organization.
6. **Auto-Company** (Entry 066) — Best full autonomous company blueprint; extract patterns, do not adopt as primary runtime.

These should drive **Grok+cage** ports (skills, eval tasks, optional smokes)—not AgenC (ADR-0010).  
Checker: `python3 bootstrap/setup-local-agent-env.py`. Catalog: T-0042 triple-write.

## Next Steps
- Keep `sources/x-posts.md` append-only (never replace whole file with a single entry).
- Triple-write S-tier tools into TOOLS.md + data/tools.json (T-0042).
- Implement one S-tier pattern as first-party Grok skill or eval harness extension.
- Optional overlap matrices for Loop Engineering and Memory clusters.
- **Company track:** flesh out Auto-Company pattern extraction ticket; keep Multica/gstack/paperclip as comparison set under Cluster 5.
