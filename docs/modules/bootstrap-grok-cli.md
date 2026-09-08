# Module: bootstrap/grok-cli

**Purpose:** Replayable **operator environment** for Grok CLI — skills, MCP wiring, config fragment — so a new machine matches this catalog’s agent process.


**Attach usable (#201):** HTML+tk **Attach grok** (and `python3 scripts/pfy-board.py --start grok`) re-probes FreeToken-first (`:1919`), sets child `LOCAL_OPENAI_BASE_URL` / `OPENAI_BASE_URL` to the live detect base, then proves models list + one smoke (`pfy_attach_usable_201.prove_developer_usable`, same bar as Hermes #196 / OpenCode #193) before `ok:True` / READY / “attached”. Failures: `usable:false`, session/attach state cleared, FAIL + next (`Launch env or ./pfy up`). No false attached paint.

CLI `./pfy start grok` uses the same honesty: no live engine → FAIL + next (does not exec); prove (`python3 scripts/pfy_attach_usable_201.py --prove $LOCAL_OPENAI_BASE_URL`) must pass before exec. Inspect equivalent: `./pfy models` (list) + Test model / `--prove` (smoke).
## Operator: how to run

```bash
# Grok CLI installed first (see https://x.ai/cli or project README)
./bootstrap/grok-cli/install.sh
# optional binary for code graph MCP:
./bootstrap/grok-cli/install.sh --with-codebase-memory
# then:
grok login   # OIDC → ~/.grok/auth.json (preferred over API key alone)
```

| Flag / path | Meaning |
|-------------|---------|
| `install.sh` | Idempotent install of first-party skills + merge config fragment |
| `--with-codebase-memory` | Fetch `codebase-memory-mcp` via upstream install.sh `--skip-config` |
| `--mcp-only` | Config/MCP only (see install help) |
| `skills/` | First-party skills (catalog-docs, one-shot, adr, docs, …) |
| `skills-external/ponytail` | External pack registered via `skills.paths` |
| `config/config.fragment.toml` | Fragment merged into `~/.grok/config.toml` |

Package README: [bootstrap/grok-cli/README.md](../../bootstrap/grok-cli/README.md)

## Where variables live

| Variable / file | Role |
|-----------------|------|
| `~/.grok/auth.json` | Primary OIDC session (not committed) |
| `XAI_API_KEY` | Optional API fallback (CI / no session) — [REGISTRY](../../bootstrap/env/REGISTRY.md) |
| `~/.grok/config.toml` | MCP servers, skills paths (owned by bootstrap merge) |
| `~/.local/bin/codebase-memory-mcp` | Optional MCP binary on PATH |

## Agent map

| Concern | Detail |
|---------|--------|
| **Invariants** | Skills source of truth under repo `.grok/skills/` + bootstrap copy; triple-write catalog skill is **catalog-docs** |
| **Do not** | Mount whole `~/.grok` into cage (hides binary); bake secrets into images |
| **ADR** | ADR-0002 (Grok primary), ADR-0004 (bootstrap) |
| **Related** | [docs/modules/harness-agent-cage.md](harness-agent-cage.md) for Grok-in-cage overlay |

## Verify

```bash
./bootstrap/grok-cli/install.sh --dry-run  # if supported
ls ~/.grok/skills/
# optional: grok mcp list
```

## Not yet

- Replacing Grok’s binary, auth, or marketplace
- Aborting `./pfy start` when grok is missing/unauth (env continues; next ready adapter may attach)

