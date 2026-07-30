# mattpocock to-spec / tdd wiring (T-0076)

**Paths pack:** `bootstrap/grok-cli/skills-external/mattpocock/`  
**Skills:** `to-spec`, `tdd`, `code-review`

## Operator invoke path

| Intent | How |
|--------|-----|
| Spec before code | Install paths → invoke **to-spec** skill (or open `skills-external/mattpocock/to-spec/SKILL.md`) |
| Red-green-refactor | **tdd** skill + `tdd/tests.md` / `mocking.md` |
| Review | **code-review** skill |

First-party complements: `/one-shot` (DoD), `/agent-loops` (exits), `/investigate` (RCA).

## Structural coverage

Deterministic checklist shape for “to-spec” style output lives as text scorer  
`examples/eval-harness/tasks/008-to-spec-checklist/` (T-0076).

## Non-goals

- Do not rewrite mattpocock content into first-party duplicates unless PORT.md says so.  
