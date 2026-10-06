# ATG coupling (Atomic Task Graph prototype)

**Status:** I1 refreshed 2026-10-06. The 2026-08-06 snapshot below is superseded.  
**Prototype:** https://github.com/themark-net/atg-framework  
**Paper:** Zhang, Chen, Huang, Cui, Ji, and Wang (2026), arXiv:2607.01942. This repo is an independent reimplementation. It is not official ATG code and it does not claim the paper's benchmark numbers.  
**Pinned checkout:** branch `build/atg-finish` @ `86d1b8905116fb7ec954ee5c4fe0d18f763b7e16` (this host: `/tmp/atg-finish`). Do not score `~/DEVELOP/atg-framework`.  
**Integration stage:** **I1**. Not I2. Submodule later stays an intent, not an instruction.  
**Reviews:** 2026-08-06 → issue #30 (stay I1). 2026-10-06 → card refresh, still I1.

## 2026-10-06 snapshot

Called by path from `examples/atg-compile/bench.py`. Not vendored. Not on the eval-harness or cage default path. Default model stays `qwen3.6:35b` on Ollama. `qwen3-coder-next` is opt-in via the `llamacpp-nommap` lane.

### Offline checks (this session)

Worktree was dirty (`examples/poc_suite.py`, `docs/ops/RUN-LOG-atg-finish.md`). HEAD matched the pin.

| Command | Result |
|---------|--------|
| `.venv/bin/python -m pytest -q -m "not integration"` | **40 passed, 1 deselected** (2.43 s) |
| `.venv/bin/python examples/toy_parallel.py` | `mock total={'value': 25} waves=2 parallel=2` exit 0 |
| Live compile | **Not run.** Parent session held `qwen3.6:35b`. Absence is not a pass. |

### Gate table

| Gate | Reading | Counts? |
|------|---------|---------|
| Gap fill | Explicit compile, parallel tool waves, freeze, and localized repair. pfy's primary loop does not ship this library. LangGraph overlaps "run a DAG". The distinct piece is repair and freeze for a small local model. No first-party skill does that. | Partial |
| Operator leverage | Offline `run_task` is one import. The new bench is a measurement, not a shorter default pipeline. | No |
| Evidence | Offline toy and unit suite exit 0 on the pin. Live toy was not re-measured. | Offline yes. Live no. |
| Blast radius | MIT. No model weights. Safe while it stays off primary orchestration and off the default cage and eval-harness. | Yes, with those constraints |

Modularity, if a later session copies or imports the repo: one Python package, entry `run_task`, reversible by deleting the pin. That is small. It does not satisfy I3. I2 stays closed until a live atg-compile exits 0.

**Chosen stage:** I1 refresh.

### Non-goals (repeated)

- Do not call ATG from eval-harness or the cage by default.
- Do not treat ATG as primary orchestration (Grok, OpenCode, and skills stay primary).
- Do not vendor `src/atg` or add a submodule in this change.
- Do not claim pfy reproduced ALFWorld, WebShop, or a GPT-4 comparison.

## Relationship to pfy-mentat

| Concern | Policy |
|---------|--------|
| Catalog | List ATG as research/prototype; link atg-framework |
| Code coupling today | Bench calls the pinned checkout by path. No pipeline hard dependency. No Make smoke and no eval-harness import require ATG |
| Future embed | **Submodule (I4)** only after I3 value+modularity gates ([integration-stages.md](integration-stages.md)) |
| Weights / large assets | N/A (code/method, not model weights) |

## Non-goals (now)

- Do not force symbolic submodule while prototype is still in development.  
- Do not call ATG from eval-harness or cage by default.  
- Do not treat ATG as primary orchestration (Grok + OpenCode + skills remain primary).

## Uses / features / potential (I1 card)

| Field | Content |
|-------|---------|
| **Uses** | Compile, parallel tool waves, freeze, and localized repair. Independent reimplementation of Zhang et al. (2026). |
| **Features** | DAG compile, localized repair, OpenAI-compatible client |
| **Potential** | Ambiguous until a live atg-compile exits 0 |
| **Non-goals** | Primary runtime; I2 before that live pass; immediate I4 |

## 2026-08-06 maturity snapshot (issue #30) — superseded

The paragraph below described a tree with no `src/atg/`. That is no longer true. It stays as history. Do not use it as the current maturity statement.

- atg-framework remains **docs-only**: ARCHITECTURE, DECISIONS 0001–0010, OPEN_QUESTIONS, TODO, attribution. No `src/atg/`, no pyproject, no tests, no examples.
- Phase 0 complete; Phase 1 skeleton (graph/types/history/validation + green pytest) **not started**.
- Working tree size trivial (≪ 50 MB). No open issues on the prototype repo.
- **Decision:** stay **I1**. I2 probe has nothing executable to probe. Value + modularity gates for I3 unmet. Do not plan I4.
- **Next trigger:** after Phase-1 runnable skeleton lands, or explicit re-request. No calendar auto-reminder required.
