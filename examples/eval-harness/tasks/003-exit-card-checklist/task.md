# Task 003 — Agent loop exit card (structural)

**Goal:** Given a multi-step automation request, produce an **exit card** covering the eight mandatory exits (Entry 068 / `/agent-loops`).

**Success criteria (scorer):**

1. Output includes a section titled roughly `EXIT` or `LOOP EXIT` or lists exits 1–8.
2. Mentions at least **five** of: goal, turn, budget, wall clock / wallclock, no-progress / no progress, human, error, external.
3. Does **not** claim Hermes Agent or AgenC must be installed.
4. Includes a concrete **goal** line (observable DoD, not only “looks good”).

**Prompt to model:**

```text
You are designing a goal-based agent loop for: "make smoke-grok-skills green on this machine."
Write a LOOP EXIT CARD with all eight exits filled (goal met, turn cap, budget, wall clock,
no-progress, human interrupt, error threshold, external event). Be concise. No tooling install.
```

**Notes:** Fits T-0060. Prefer deterministic keyword scorer in `score.py` (no LLM judge).
