# Module: Attach mode (`scripts/pfy_attach_mode_208.py`)

**Purpose:** Operator-selected Attach mode `bare` | `orchestration` | `code-graph` with `using: <mode>` paint and operate-or-FAIL handoff into OpenCode | Hermes | Grok. Cite #208.

## Human operator

- What: pick a mode on Attach (HTML+tk), then Attach a harness. Loop/Attach show `using: <mode>`.
- How: [docs/ops/attach-mode.md](../ops/attach-mode.md)
- Failures: unwired mode → FAIL + next (never silent bare).
- Recovery: `bare` always; orchestration needs `./pfy setup`; code-graph needs `codebase-memory-mcp`.

## Agent

- Entry: `scripts/pfy_attach_mode_208.py` (`--selftest` / `--set` / `--prepare` / `--export-env`).
- Callers: `start_sidecar` / `POST /mode` / `POST /start`; Attach 162/196/202 child env; `./pfy start` payload.
- Invariants: one mode at a time; no Env nav tab; do not rewrite repo `AGENTS.md`; catalog HOLD; do not reopen #76.
- Issue **#208** only.

## Architecture link

Operator-stack layer (board/gui + attach child env), not catalog product surface.
