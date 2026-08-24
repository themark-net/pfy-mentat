# Module docs (operators + agents)

Short structural maps for first-party packages in this repo. Deep design stays in ADRs; runbooks in `docs/ops/`.

| Module | Path | Doc |
|--------|------|-----|
| Consultant eval pack | `docs/ops/consultant-eval.md` | [consultant-eval.md](../ops/consultant-eval.md) |
| `./pfy` simple surface | `scripts/pfy` | [pfy.md](pfy.md) |
| Local runtime detector | `scripts/detect-local-runtime.sh` | [detect-local-runtime.md](detect-local-runtime.md) |
| Product env-stage | `scripts/env-stage.sh` | [env-stage.md](env-stage.md) |
| Grok CLI bootstrap | `bootstrap/grok-cli/` | [bootstrap-grok-cli.md](bootstrap-grok-cli.md) |
| OpenCode host adapter | `bootstrap/opencode/` | [opencode-adapter.md](opencode-adapter.md) |
| Hermes runtime adapter | `hermes` / `hermes-agent` | [hermes-adapter.md](hermes-adapter.md) |
| project-process scaffold | `bootstrap/project-process/` | [bootstrap-project-process.md](bootstrap-project-process.md) |
| agent-cage lab | `harness/agent-cage/` | [harness-agent-cage.md](harness-agent-cage.md) |
| write-guard MCP | `harness/write-guard-mcp/` | [write-guard-mcp.md](write-guard-mcp.md) |
| In-cage tool smokes | `examples/` + `pipelines/smoke/` | [examples-smokes.md](examples-smokes.md) |

**Related ops (not a package):** [gstack role recipes](../ops/gstack-role-recipes.md) (T-0014) · [gstack skill port comparison](../ops/gstack-skill-port-comparison.md) (attributes + single-skill recommendation).

**Catalog (not modules):** [TOOLS.md](../../TOOLS.md) · [data/tools.json](../../data/tools.json) · [sources/x-posts.md](../../sources/x-posts.md)  
**Deploy map:** [docs/ops/DEPLOY.md](../ops/DEPLOY.md)
