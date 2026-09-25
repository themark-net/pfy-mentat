# Port bot doctrine to pfy SoT

**Purpose:** A locked bot standing is not done until it is portable in this repo for Build, cage, and `install.sh`.  
**Catalog:** HOLD — do not triple-write TOOLS / `data/tools.json` / sources for a doctrine port.  
**Verify:** [skill-verification.md](skill-verification.md).

Chat handoff is temporary. The reusable surface is **see, evaluate, and reuse** (same shape as catalog evaluation for tools). Until a Loop UX owns that inventory, first-party skills plus ops notes are the manual path.

## Source of truth

| Layer | Where | Consumers |
|-------|--------|-----------|
| Org coordination | Grok Bot skills (pointer only) | Bots |
| **Portable SoT** | `bootstrap/grok-cli/skills/` + `docs/ops/` + AGENTS router | Grok Build, cage, `install.sh`, other agents |
| Project mirror | `.grok/skills/` (cwd discovery; refresh from bootstrap) | Sessions opened in this repo |
| Thin product repos | Root `AGENTS.md` one-liner pointing at the principle | Repo agents |

Full skill packs stay in this repo unless that scope is explicitly expanded.

## Port checklist

1. Write a first-party skill under `bootstrap/grok-cli/skills/<name>/SKILL.md` (+ `PORT.md`). Frontmatter `name:` must equal the directory (smoke requirement).
2. Register in `bootstrap/grok-cli/manifest.json` → `first_party_skills.skills`.
3. Row in `bootstrap/grok-cli/README.md` skills table.
4. AGENTS.md router line if it is a process skill.
5. Ops note under `docs/ops/` when verification or DoD matters.
6. `make smoke-grok-skills` green. Install path: `./bootstrap/grok-cli/install.sh --skills-only`.
7. Docs-only / skill PR is BEST_EFFORT even under Feature STAND BY. No Feature GO from the port itself.
8. Org Bot skill keeps a one-line pointer: `SoT: pfy bootstrap/grok-cli/skills/<name>`.
9. Strip bot-only ids and founder personal names. Keep DoD paste lines verbatim.
10. Do not commit `_port_sources/` (gitignored local input).

## Anti-patterns

- Doctrine only in chat or in a bot skill with no port here
- Copying full skill trees into every product repo
- Claiming “ported” without `make smoke-grok-skills` and a manifest row
- A catalog tool row for a prompt pack while catalog is on HOLD
