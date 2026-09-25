---
name: prefer-behavior-and-fail-recover-tests
description: >
  Use this when writing or reviewing tests, drafting a Build or Cursor DoD, or
  when an agent is about to add many unit tests. Ban tautological units, prefer
  integration and E2E, and ask how the change fails and how we recover.
argument-hint: "[review | dod]"
---

# Prefer behavior and fail-recover tests (no tautology)

Use this when writing tests, reviewing a PR’s test suite, drafting a Build/Cursor DoD, or when an agent is about to add a pile of unit tests.

See [PORT.md](PORT.md). Structural check: `make smoke-grok-skills` ([skill-verification.md](../../../../docs/ops/skill-verification.md)).

## Standing rule (2026-09-25)

Prefer the **Testing Trophy**: mostly integration/E2E for product confidence; static analysis for the cheap floor. Unit tests are allowed only when they exercise **shaky or non-obvious** behavior (branching, invariants, recovery) — not to rubber-stamp trivial happy paths.

**Forbidden:** tautological tests (mirror implementation, assert constants just assigned, or mock so heavily the test cannot fail if the bug is present); tests of implementation details (private state, collaborator call choreography as the sole assertion).

Prefer **sociable** tests (real collaborators). Use doubles only at awkward/slow/nondeterministic boundaries; back those doubles with **contract tests** when the boundary is external.

Every non-trivial change must answer: **How could this fail? How do we recover?** Prefer negative-path / failure-mode coverage (and fault injection for resilience-critical paths) over more happy-path unit tests. Coverage % is not a goal; weak assertions that survive obvious mutations are a fail.

Applies to local Grok Build sessions **and** every bot-spawned Build/Cursor session.

## Key terms

| Term | Meaning |
|------|---------|
| **Tautological test** | Restates the implementation; can’t catch a real behavior change. |
| **Implementation-detail test** | Asserts internals (private state, call order) → brittle; often tautological. |
| **Behavioral / structure-insensitive** | Coupled to observable behavior; survives refactors (Kent Beck). |
| **Sociable unit** | Real collaborators; doubles only at awkward boundaries. Prefer over solitary/mockist. |
| **Testing Trophy** | Bias to integration + thin E2E, not a unit-heavy pyramid. |
| **Negative-path / failure-mode** | How could this fail, and how do we recover? |
| **Fault injection / resilience** | Break deps on purpose; assert recovery. |
| **Contract test** | Real external boundary still matches what doubles/consumers expect. |
| **Characterization test** | Locks current legacy behavior before changing it (Feathers). |
| **Mutation testing** | Flips code subtly; surviving mutants = weak assertions. |
| **Property / generative** | Invariants; generator finds counterexamples. |

**PR short lexicon:** tautological · implementation details · sociable · trophy · failure-mode · recoverability.

## Anti-patterns → do instead

| Anti-pattern | Instead |
|--------------|---------|
| Assert constant just assigned / mirror formula | Observable outcomes from realistic inputs |
| Mock wall; `toHaveBeenCalledWith` as the test | Sociable/integration; assert state/UX/API |
| Coverage mandate on getters/wiring | Cover risk: branching, money/auth, retries, permissions |
| Happy-path only | Negative-path + recovery |
| Doubles with no reality check | Contract tests at the boundary |
| Legacy fear → no tests | Characterization first, then change |

## Reviewer / Tester FAIL if any apply

1. **Tautological** — expected value from same logic/constants as SUT, or mocks encode the only “behavior.”
2. **Implementation details** — private state / call order instead of observable result.
3. **Happy-path only** on non-trivial logic — no failure/recovery where failure is plausible.
4. **Mock wall** — mocks away the seam the change depends on, with no sociable/integration/E2E.
5. **Coverage theater** — tests mainly raise %; no stated failure mode.
6. **No recoverability** on resilience-sensitive paths.
7. **Untested external contract** — new dependency double with no plan that the real API matches.

One solid sociable/integration (or E2E) that goes red if the bug shipped beats ten tautological units.

## Build / Cursor DoD line (paste into every implement prompt)

```
Tests: prefer E2E/integration/operate-or-FAIL (Trophy). No tautological or implementation-detail unit sprawl. Unit tests only for shaky behavior; must be able to fail with the bug present (sociable where possible). For each risk: how could this fail + how do we recover.
```

## Sources

- Kent C. Dodds — Write tests. Not too many. Mostly integration. / Testing Implementation Details
- Martin Fowler — UnitTest (solitary vs sociable); Mocks Aren't Stubs; Contract Test
- Kent Beck — Test Desiderata
- Google Testing Blog — Code Coverage Best Practices (coverage ≠ quality)
- Principles of Chaos Engineering — fault/resilience framing
- Michael Feathers — characterization tests (*Working Effectively with Legacy Code*)
