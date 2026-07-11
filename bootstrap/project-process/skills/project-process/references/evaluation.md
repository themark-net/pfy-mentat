# Evaluation: process framework vs external tools (2026-07-11)

Research summary for whether the light DESIGN/ADR/TODO/OQ framework should be replaced by heavier tools.

## What we ship

1. **Design** — master goals doc  
2. **ADR** — multi-file decisions with rejected paths  
3. **TODO + Open questions** — execution queue + parking lot  

Delivered as: markdown templates + `init.sh` + Grok skills (`project-process`, `adr`, `open-questions`, `docs`).

## Signals from X / community

| Theme | Signal | Implication |
|-------|--------|-------------|
| In-repo ADRs for agents | Strong consensus: agents should read/write ADRs during architecture chats; multi-session alignment improves (e.g. practitioners documenting ADRs for Codex/Claude) | Markdown-in-repo is the right default |
| ADR template | Fowler / Nygard-style: Context, Decision, Consequences, Alternatives | Our template matches industry standard |
| Lightweight over SaaS | Teams use repo files so agents and PRs see the same source | Avoid requiring Linear/Confluence for core process |
| Optional tooling | `adr-tools` (CLI numbering), template catalogs, experimental “ADR enforcement for AI” (e.g. Mneme, Decision Guardian) | Nice-to-have, not required for MVP |
| Open-question / parking lot products | No dominant agent-native product; people use issues or markdown | Our OQ log fills a real gap without new infra |
| Spec-driven / OpenSpec | Emerging pairing of ADR with richer specs | Complementary later; not a replacement for ADR+TODO |

## Comparable tools

| Tool | Role | Vs our framework |
|------|------|------------------|
| [adr-tools](https://github.com/npryce/adr-tools) | CLI create/supersede ADR files | Optional accelerator for numbering; **does not** replace DESIGN/TODO/OQ or agent skills |
| [architecture-decision-record](https://github.com/joelparkerhenderson/architecture-decision-record) templates | Rich template library | We stay Nygard-simple; can adopt a template if a project needs MADR/etc. |
| [log4brains](https://github.com/thomvaill/log4brains) | Static site for ADR browsing | Overkill for small agent-driven repos |
| Mneme / Decision Guardian (emerging) | Enforce ADRs for AI agents | Watch list if soft docs prove insufficient |
| GitHub Issues / Linear | Work tracking | Fine as **mirrors**; filesystem TODO/OQ stays agent-readable offline |
| Claude/Cursor skills (community ADR skills) | Same idea as our skills | We package scaffold + three-process triad as one bootstrap |

## Verdict

**Keep the light framework as the default.** It is sufficient and aligned with how agent practitioners actually work in 2026:

- No new runtime dependency  
- PR-reviewable  
- Covers the three user requirements (design goals, ADR with rejected paths, TODO linked to open questions)  
- Deployable to any new environment via `init.sh` + skill install  

**Do not replace** with a heavy platform unless empirical pain appears (e.g. teams ignore docs → then evaluate enforcement tools).

**Optional upgrades later (not blocking):**

1. Document `adr-tools` as optional companion in TOOLS.md  
2. Revisit Mneme-class enforcement if agents repeatedly violate Accepted ADRs  
3. Issue-tracker sync scripts only if humans demand them  

## Catalog implication

Score **project-process bootstrap** as S-tier pipeline/process component for this catalog; list adr-tools as A-tier optional CLI utility (pin, do not embed).
