# Module: OpenCode host adapter

**Purpose:** Secondary operator surface. Skills SoT stays `bootstrap/grok-cli/skills` (`OPENCODE_SKILLS`). Inference via `LOCAL_OPENAI_BASE_URL` from the detector (not Ollama-only).

## Entry

```bash
./pfy harness use opencode
./pfy start opencode
```

Package notes: [bootstrap/opencode/README.md](../../bootstrap/opencode/README.md)

**OpenContext handoff (#205):** Attach / `./pfy start opencode` inherit `OPENCONTEXT_*` when `oc` is on PATH. Prove with `./pfy context`. Optional MCP: `oc mcp`. No OpenContext GUI in pfy chrome. Runbook: [opencontext.md](../ops/opencontext.md).

**Attach mode (#208 / #213 / #215):** session inherits `PFY_ATTACH_MODE` plus skills/prompt for `bare` | `orchestration` | `code-graph`. Orchestration proves a multi-step local loop (not thin inject). Code-graph writes Axon MCP (`axon serve --watch`) when live, else `codebase-memory` into `opencode.json` and paints **not axon**. Unwired → FAIL + next. [attach-mode.md](../ops/attach-mode.md) · [code-graph.md](code-graph.md).

Missing `opencode` / `opencode-cli`: `STUB harness: opencode`, issue #55, exit 2.

## Not yet

- OpenCode-in-cage parity (T-0081)
- Replacing Grok as default harness
- Forking a second skill tree
