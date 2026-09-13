# Module: Recommend / try local models (`scripts/pfy_recommend_models_207.py`)

**Purpose:** Ranked host-fit local models beyond already-pulled, plus one try/pull on the FreeToken-first live runtime. Cite #207.

## Human operator

- What: Engine + `./pfy models recommend` list what fits this machine and is not pulled; **Try** pulls one.
- How: [docs/ops/recommend-models.md](../ops/recommend-models.md)
- Failures: no engine / llama no-pull / unknown VRAM+RAM / none fit → FAIL + next, empty list.
- Recovery: `Launch env or ./pfy up`; llama: set `PFY_LLAMA_MODEL`.

## Agent

- Entry: `scripts/pfy_recommend_models_207.py` (`--selftest` / `--recommend` / `--try [NAME]`).
- Callers: `./pfy models recommend|try` payload; board `recommend_models` / `try_recommended_model`; `POST /models/recommend` `/models/try`; Engine HTML+tk.
- Invariants: reuse `pull_model` / `./pfy models pull`; no fake best list; no paint lie; catalog HOLD; do not reopen #76.
- Issue **#207** only.

## Architecture link

Operator-stack layer (board/gui + `./pfy` models), not catalog product surface.
