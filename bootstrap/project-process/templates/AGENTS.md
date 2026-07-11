# AGENTS.md — {{PROJECT_NAME}}

Instructions for coding agents working in this repository.

## Mandatory reads (before non-trivial design or multi-step work)

1. [docs/DESIGN.md](docs/DESIGN.md) — goals, shape, non-goals, process model
2. [docs/adr/README.md](docs/adr/README.md) — decision index (open ADRs that touch your area)
3. [docs/TODO.md](docs/TODO.md) — next steps
4. [docs/OPEN_QUESTIONS.md](docs/OPEN_QUESTIONS.md) — do not silently “solve” P0/P1 OQs

## Process rules

| Situation | Action |
|-----------|--------|
| Architecture pivot / hard-to-reverse choice | Write **ADR** under `docs/adr/` with **rejected alternatives** (`/adr`) |
| Uncertain / can wait / needs human | **Open question** in central index; optional detail or in-context note citing `OQ-NNNN` (`/open-questions`) |
| Implementation work item | Update **TODO** row; link OQs when blocked |
| Non-trivial module change | Operator + agent docs (`/docs`) |

## Do not

- Re-propose designs rejected in ADRs without a superseding ADR and new context
- Leave P0–P2 questions only in chat
- Commit secrets, API keys, or credentials
- Create a second decision log outside `docs/adr/`

## Skills (install via local-llm-dev-tools bootstrap)

- `/adr` — Architecture Decision Records
- `/open-questions` / `/oq` — TBD parking lot
- `/docs` — operator + agent module documentation
- `/project-process` — re-scaffold or audit this layout
