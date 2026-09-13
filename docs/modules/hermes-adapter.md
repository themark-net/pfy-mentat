# Module: Hermes runtime adapter

**Purpose:** Exec `hermes` or `hermes-agent` from `./pfy start hermes`. Inference via `LOCAL_OPENAI_BASE_URL` from the ADR-0014 detector (not Ollama-only). The Grok skill `/hermes-feedback` stays process-only.

## Entry

```bash
./pfy harness use hermes
./pfy start hermes
```

Detect: `hermes` or `hermes-agent` on PATH. When the local runtime is ready, `OPENAI_BASE_URL` defaults to `LOCAL_OPENAI_BASE_URL`.

**Attach usable (#196):** HTML+tk **Attach hermes** (and `python3 scripts/pfy-board.py --start hermes`) re-probes FreeToken-first (`:1919`), sets child `LOCAL_OPENAI_BASE_URL` / `OPENAI_BASE_URL` to the live detect base, then proves models list + one smoke (`pfy_attach_usable_196.prove_developer_usable`, same bar as OpenCode #193) before `ok:True` / READY / “attached”. Failures: `usable:false`, session/attach state cleared, FAIL + next (`Launch env or ./pfy up`). No false attached paint.

CLI `./pfy start hermes` uses the same honesty: no live engine → FAIL + next (does not exec); prove (`python3 scripts/pfy_attach_usable_196.py --prove $LOCAL_OPENAI_BASE_URL`) must pass before exec. Inspect equivalent: `./pfy models` (list) + Test model / `--prove` (smoke).

**OpenContext handoff (#205):** Attach / `./pfy start hermes` inherit `OPENCONTEXT_BIN` / `OPENCONTEXT_CONTEXTS_ROOT` / `OPENCONTEXT_DB_PATH` when `oc` is on PATH. Prove OpenContext with `./pfy context` (operate-or-FAIL). Missing `oc` is a skip on Attach, not a false attached paint. No OpenContext GUI in pfy chrome. Runbook: [opencontext.md](../ops/opencontext.md).

**Attach mode (#208):** `bare` and `orchestration` hand off prompt/env (orchestration also needs `/agent-loops`). `code-graph` is unwired for Hermes (no MCP) → FAIL + next: Attach grok or opencode. [attach-mode.md](../ops/attach-mode.md).

Missing binary: `STUB harness: hermes`, issue #56, installer one-liner, exit 2. No fake ready.

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

Upstream: [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)

## Not yet

- Changing `/hermes-feedback` (process-only pattern port)
- Vendoring Hermes into git
- Other harness adapters
