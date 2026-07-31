# Simple launch surface (`./pfy`)

**Goal G8 · ADR-0012**  
**Feel:** install once → start inference → pick a harness (Ollama then Hermes/OpenCode style).

## New machine (happy path)

```bash
git clone https://github.com/themark-net/pfy-mentat.git
cd pfy-mentat
./pfy setup                 # or: ./pfy setup local-only
./pfy status                # ready | partial | stub
./pfy start                 # default harness = grok
# optional:
./pfy harness use opencode
./pfy start
./pfy models pull deepseek-coder:6.7b
./pfy stage                 # green checks
./pfy eval                  # catalog self-mod gates
./pfy ship                  # product verify
```

Install Grok CLI once if missing: `curl -fsSL https://x.ai/cli/install.sh | bash` then re-run `./pfy setup`.  
Install Ollama for local models: https://ollama.com

## Map to old Make levers

| Simple | Make / script |
|--------|----------------|
| `pfy setup` | `make env-init` + `bootstrap/grok-cli/install.sh` |
| `pfy stage` | `make env-stage` |
| `pfy ship` | `make product-ship` |
| `pfy eval` | `make eval-integration-change` |
| Platform deep dives | `make help` (cage, smokes, matrix) |

## Harness status legend

| Live status | Meaning |
|-------------|---------|
| **ready** | Binary found; start should work |
| **partial** | Installed or documented path incomplete |
| **stub** | Slot reserved; `pfy start` prints setup + issue text |
| **missing** | Not installed |
| **detected-stub** | Binary found but adapter still stub |

Registry: [`data/harnesses.json`](../../data/harnesses.json).

## Stubs (honest)

Hermes, Claude Code, Codex, Gemini/Antigravity-class, Exo full runtime, Continue — **stubbed**. Patterns may already exist as skills/docs; the **unified installer path** does not. Progress tracked on GitHub under label `harness-adapter`.

## Why not Make-only?

Builders keep Make. **New operators** get one verb set so they never need to learn `cage-grok-auth-import` on day one.

## Tracking

| Work | Issue |
|------|------:|
| Epic G8 | [#53](https://github.com/themark-net/pfy-mentat/issues/53) |
| Ollama | [#54](https://github.com/themark-net/pfy-mentat/issues/54) |
| OpenCode | [#55](https://github.com/themark-net/pfy-mentat/issues/55) |
| Hermes | [#56](https://github.com/themark-net/pfy-mentat/issues/56) |
| Claude Code | [#57](https://github.com/themark-net/pfy-mentat/issues/57) |
| Codex | [#58](https://github.com/themark-net/pfy-mentat/issues/58) |
| Gemini | [#59](https://github.com/themark-net/pfy-mentat/issues/59) |
| Exo | [#60](https://github.com/themark-net/pfy-mentat/issues/60) |
| Continue | [#61](https://github.com/themark-net/pfy-mentat/issues/61) |
| agent-cage lab | [#62](https://github.com/themark-net/pfy-mentat/issues/62) |
