# Architecture doc checklist

Use when writing or auditing `docs/ARCHITECTURE.md` (or project equivalent).

## Must include

- [ ] One-line vision / purpose
- [ ] Current data-flow diagram (text is fine) reflecting **delivered** code
- [ ] Layering: UI/CLI → domain → persistence → integrations → external systems
- [ ] Explicit **delivered** vs **out of scope / future** lists (no false "future" for shipped features)
- [ ] Pointers to ADR / DECISIONS log as authority for *why*
- [ ] MVP or current milestone boundary if the project has one
- [ ] External systems and ownership boundaries (what this repo must not mutate)

## Must not include

- [ ] Secrets or live credentials
- [ ] Claims contradicted by the package layout or CLI
- [ ] Undated "current state" that is months stale without an update pass

## After a major decision

1. Accept ADR first (or same PR).
2. Update architecture diagram and layer bullets.
3. Update module docs for moved code.
4. Point AGENTS.md at the updated files if the mandatory read list changes.
