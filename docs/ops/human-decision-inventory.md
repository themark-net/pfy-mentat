# Human decision inventory (minimize per-item questions)

**Purpose:** Map branching decisions so agents **batch** operator input and build automation loops instead of asking one question at a time.  
**Rule:** Prefer defaults + reversible experiments. Only escalate when blast radius is high or OQ is P0/P1.

## Pending decisions (estimate)

| Bucket | Count | Automation loop (instead of N chats) |
|--------|------:|--------------------------------------|
| **Blocked OQs (P2)** | **4** | Single “OQ batch” form: subtree / ATG / Antigravity / colibri weights |
| **Optional tool adopt** (MUE-X, LEANN, Memvid, Laguna weights, Bumblebee install) | **0 now** — defaults below | Default = **pattern/docs + structural eval only**; promote only if structural green + smoke exists |
| **Cage/env polish** (auth dir mount, write-guard mcp-host) | **0 for this track** | Parked; not design/coding assist focus |
| **Product forks needing ADR** | **0 open P1** | None until architecture pivot |
| **Hybrid surfaces (ADR-0011)** | **0** | Defaults: Grok primary hard tasks; OpenCode+Ollama bulk; no Hermes runtime |
| **Total decisions needed from you this week (design/coding track)** | **0 required** | Optional: fill OQ batch when ready (**4 checkboxes**) |

**Bottom line:** You can ignore human input for the design/coding assist track; agents should keep shipping skills, structural evals, and pattern docs. **4 deferred P2 OQs** remain when you want a single batch review.

---

## Branch maps

### B1 — Optional catalog tool (coding assist)

```text
Phase0 gate: open-source + local + coding/design assist?
  NO → catalog C/awareness only; stop
  YES → Structural lane green? (make eval-structural)
          NO → fix structural; stop
          YES → Fits existing skill/smoke path?
                  YES → implement skill or smoke; no human
                  NO → Default: docs/pattern extract + B-tier catalog
                       Need runtime install/weights/subtree?
                         YES → add OQ row (batch later); do not ask ad hoc
                         NO → done without human
```

**Human decisions if runtime needed:** 1 (allow install/weights?) — add to OQ batch, not chat.

### B2 — New process skill (design/coding)

```text
Complex procedure ≥ threshold?
  NO → hermes memory / TODO only
  YES → first-party skill under bootstrap + manifest + eval-structural
        Pass? ship. Fail? fix until green. No human.
```

### B3 — Implement-lane model eval (needs Ollama)

```text
Ollama + gate model present?
  NO → record SKIP (exit 2); structural still PASS; no human
  YES → make eval-suite; fail → model/prompt fix loop (agent); no human unless infra missing on purpose
```

### B4 — Blocked OQ batch (4 items — single operator pass)

| ID | Question | Default if unanswered | Reversible? |
|----|----------|----------------------|-------------|
| OQ-0003 | First subtree? | **No subtree** (ADR-0003 pins) | Yes |
| OQ-0004 | ATG prototype relationship? | **Catalog link only** | Yes |
| OQ-0007 | Antigravity multi-account? | **No** (single account / LiteLLM) | Yes |
| OQ-0008 | Colibri weights download OK? | **No download** | Yes |

**Automation loop:** Agent never asks these individually. When you want them answered, reply once:

```text
OQ-BATCH: 0003=no 0004=catalog 0007=no 0008=no
```

---

## Defaults (agent may apply without asking)

| Topic | Default |
|-------|---------|
| Primary code memory | codebase-memory-mcp |
| Graphify / LEANN / Memvid | docs/reference until smoke |
| MUE-X | pattern extract only; no evolve in lab without pin+safety note |
| Laguna | catalog + DoD only; no weights in-repo |
| Bumblebee | design note; optional smoke when Go binary easy |
| AgenC | stay demoted (ADR-0010) |
| Write-guard mode | audit (OQ-0009 answered) |
| Eval without Ollama | structural PASS required; implement SKIP |

---

## Automation loops to build next

1. **`make eval-structural`** in every design/coding PR (this repo).  
2. **OQ-BATCH parser** — one message closes N OQs.  
3. **Eval SKIP vs FAIL policy** — missing model = 2, not 1 (already for matrix cells).  
4. **Night-shift TODO** — only pick rows with Open questions = `—`.
