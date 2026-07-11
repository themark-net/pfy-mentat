# Design: {{PROJECT_NAME}}

**Status:** Active  
**Last updated:** {{DATE}}  
**Authority for *why*:** [docs/adr/](adr/README.md)  
**Next work:** [docs/TODO.md](TODO.md) · open items [docs/OPEN_QUESTIONS.md](OPEN_QUESTIONS.md)

Master design document: primary goals, intended shape, and boundaries. Settled choices live in ADRs; day-to-day work lives in TODO + open questions.

---

## 1. Vision

{{VISION_ONE_LINER}}

---

## 2. Primary goals

| # | Goal | Success looks like |
|---|------|--------------------|
| G1 | {{GOAL_1}} | |
| G2 | {{GOAL_2}} | |
| G3 | {{GOAL_3}} | |

*(Replace placeholders; add rows as needed.)*

---

## 3. Non-goals (current horizon)

- {{NON_GOAL_1}}
- {{NON_GOAL_2}}

---

## 4. System shape

```text
{{SYSTEM_DIAGRAM_OR_LAYERS}}
```

| Layer | Location | Role |
|-------|----------|------|
| Process | `docs/` | Design, ADR, TODO, open questions |
| Application | *(fill in)* | |
| Integrations | *(fill in)* | |

---

## 5. Delivered vs future

### Delivered

- Process docs layout (DESIGN, ADR, TODO, OQ, AGENTS.md)

### Near-term

- See [TODO.md](TODO.md)

### Later

- *(park research items; link OQs)*

---

## 6. Process model (mandatory for agents)

| Artifact | Path | Holds |
|----------|------|--------|
| **Design** | `docs/DESIGN.md` | Goals, shape, boundaries |
| **Architecture map** | `docs/ARCHITECTURE.md` | Current structural snapshot |
| **ADR** | `docs/adr/` | Settled *why*, including **rejected** alternatives |
| **TODO** | `docs/TODO.md` | Ordered next steps; links to OQs |
| **Open questions** | `docs/OPEN_QUESTIONS.md` + optional detail files | Unsettled TBDs |
| **Module/ops docs** | `docs/modules/`, `docs/ops/` | How to run / navigate code |

### Rules

1. **Read before design changes:** DESIGN + open ADRs + relevant OQs.
2. **Architecture pivots → ADR** with paths decided against.
3. **Work items → TODO**; link OQ IDs when blocked or uncertain.
4. **Uncertainty → Open Question** (central index required). In-context notes may cite `OQ-NNNN`.
5. **Answered architectural OQs → promote to ADR**.

---

## 7. External ownership boundaries

| System | This project may | This project must not |
|--------|------------------|------------------------|
| *(fill)* | | Commit secrets; break external contracts without ADR |

---

## 8. Related documents

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [adr/README.md](adr/README.md)
- [TODO.md](TODO.md)
- [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md)
- Root: `README.md`, `AGENTS.md`
