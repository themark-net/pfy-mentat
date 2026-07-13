# AgenC bootstrap (reference only — not primary)

**Status:** Demoted. **[ADR-0010](../../docs/adr/0010-reject-agenc-as-primary-runtime.md)** — do **not** use as jump-off / primary runtime.

**Primary operator:** Grok CLI ([ADR-0002](../../docs/adr/0002-grok-cli-primary-interface.md))  
**Primary lab:** agent-cage (`harness/agent-cage/`, including Grok-in-image overlay)

AgenC was installed and smoked (T-0044), then **uninstalled** after operator trial: TUI approval UX unfit vs Grok Build / Claude Code / OpenCode. Scripts remain for **optional re-evaluation** only.

## Interesting gaps to watch / re-create later

| AgenC idea | Why interesting | Our path |
|------------|-----------------|----------|
| Web console | Remote visibility | Optional later; not blocking |
| Marketplace-style jobs | External job intake | Catalog watch only |
| Daemon + gateway | Always-on agent | Prefer cage + Makefile smokes first |
| ACP → Grok Build composer | Nested Grok Build | Prefer **Grok CLI primary**, not wrap |

## Optional re-install (not recommended)

```bash
# Requires Node ≥ 25; official installer
./bootstrap/agenc/install.sh
make agenc-smoke   # only if intentionally re-evaluating
# uninstall: agenc daemon stop; rm -f ~/.local/bin/agenc; rm -rf ~/.agenc
```

## Related

- ADR-0010, ADR-0002  
- Catalog row in `TOOLS.md` / `data/tools.json` (reference tier)  
- Success path: **Grok Build inside agent-cage** + filesystem MCP workspace + Makefile pipeline  
