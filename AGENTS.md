# AGENTS.md — local-llm-dev-tools

Instructions for coding agents working in this repository.

## Mandatory reads (before non-trivial design or multi-step work)

1. [docs/DESIGN.md](docs/DESIGN.md) — goals, shape, non-goals, process model  
2. [docs/adr/README.md](docs/adr/README.md) — decision index (open full ADRs that touch your area)  
3. [docs/TODO.md](docs/TODO.md) — next steps  
4. [docs/OPEN_QUESTIONS.md](docs/OPEN_QUESTIONS.md) — do not silently “solve” P0/P1 OQs  

Also use as needed: `CATEGORIZATION.md`, `SUBTREES.md`, `TOOLS.md`, `bootstrap/grok-cli/README.md`.

## Process rules

| Situation | Action |
|-----------|--------|
| Architecture pivot / hard-to-reverse choice | Write **ADR** under `docs/adr/` with **rejected alternatives** (`/adr`) |
| Uncertain / can wait / needs human | **Open question** in central index; optional detail file or in-context note citing `OQ-NNNN` (`/open-questions`) |
| Implementation work item | Update **TODO** row; link OQs when blocked |
| Non-trivial module or bootstrap change | Operator + agent docs (`/docs`) |
| New catalog tool | Score with rubric; update TOOLS.md + data/tools.json + sources log |

## Do not

- Re-propose designs rejected in ADRs without a superseding ADR and new context  
- Leave P0–P2 questions only in chat  
- Embed large upstream repos without meeting `SUBTREES.md` (see ADR-0003)  
- Commit secrets, API keys, or `auth.json`  
- Create a second decision log outside `docs/adr/`  

## Bootstrap environment

```bash
./bootstrap/grok-cli/install.sh
# optional: --with-codebase-memory
```

Portable skills: `adr`, `docs`, `open-questions`, `karpathy-guidelines`, `project-process`, ponytail (via skills path).

### Scaffold process into another repo

```bash
./bootstrap/project-process/init.sh /path/to/repo --name <name> --vision "..."
# or: /project-process init <path>
```
