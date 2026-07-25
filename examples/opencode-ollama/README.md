# OpenCode + Ollama host smoke (T-0080)

**Zero cage.** Proves the **local worker** path for ADR-0011 / T-0085.

| Check | Required for exit 0 |
|-------|---------------------|
| Ollama OpenAI-compat on host | Yes |
| `LOCAL_CODER_MODEL` present (or close tag) | Yes |
| First-party skills SoT + `.opencode/skills` symlinks | Yes |
| Generated `opencode.json` | Yes |
| Chat completion via `/v1/chat/completions` | Yes |
| `opencode` CLI binary | Optional — smoke still **PASS** with install hint |

## Quick start (host)

```bash
# Ollama + worker model (lab default after eval-select)
ollama serve   # if needed
curl -sS http://127.0.0.1:11434/api/tags | head
# ensure worker tag exists, e.g.:
# ollama pull deepseek-coder:6.7b

export LOCAL_CODER_MODEL=deepseek-coder:6.7b
make smoke-opencode-ollama
# or:
./examples/opencode-ollama/smoke.sh
```

## OpenCode CLI (full check)

```bash
curl -fsSL https://opencode.ai/install | bash   # once
export PATH="$HOME/.opencode/bin:$PATH"         # if needed

export LOCAL_CODER_MODEL=deepseek-coder:6.7b
export OPENCODE_CONFIG="$PWD/examples/opencode-ollama/.generated/opencode.json"
make smoke-opencode-ollama

# interactive worker
opencode   # then /models → ollama/deepseek-coder:6.7b
```

Skills: smoke creates **symlinks** under `.opencode/skills/` → `bootstrap/grok-cli/skills/*` (SoT; not a fork).

## Worker vs monitor

| Role | Tool | Model |
|------|------|--------|
| Worker | OpenCode → Ollama | `LOCAL_CODER_MODEL` |
| Monitor | Grok Build | subscription |

See [docs/ops/local-cloud-split.md](../../docs/ops/local-cloud-split.md) · [product-operator-surface.md](../../docs/ops/product-operator-surface.md).

## Files

| Path | Role |
|------|------|
| `smoke.sh` | Host smoke driver |
| `opencode.json.template` | Documented shape |
| `.generated/opencode.json` | Written by smoke (gitignored) |
| `../../bootstrap/opencode/` | Adapter policy |

## Related

- ADR-0011 hybrid surfaces  
- T-0085 worker/monitor automation next  
