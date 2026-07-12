# AgenC Bootstrap & Launch Wrapper

**AgenC is the primary host agent runtime** for this project (daemon-backed coding agent).  
**agent-cage** remains the high-isolation **container lab** for untrusted workloads.

| Layer | Tool | Role |
|-------|------|------|
| Host agent runtime | **AgenC** (`agenc`) | Day-to-day daemon + TUI / `--print` / plugins |
| Isolation lab | **agent-cage** | Docker sandbox + network policy + MCP smokes |

Upstream: [tetsuo-ai/agenc-core](https://github.com/tetsuo-ai/agenc-core) · site [agenc.ag](https://agenc.ag) · install docs in upstream `docs/install.md`.

## Official install

```bash
# One-liner (macOS/Linux) — requires Node.js >= 25
curl -fsSL https://get.agenc.ag/install.sh | sh

# Or npm launcher (same runtime contract)
npm install -g @tetsuo-ai/agenc

# Via this repo (bootstraps Node 25 user-local if needed)
make agenc-install
```

State lives under `AGENC_HOME` (default `~/.agenc`). Wrapper install prefix default `~/.local/bin`.

## Primary entry point

Use `agenc-launch` (recommended) instead of calling `agenc` directly:

```bash
chmod +x bootstrap/agenc/agenc-launch
# optional alias
alias agenc="$PWD/bootstrap/agenc/agenc-launch"

./bootstrap/agenc/agenc-launch --help
./bootstrap/agenc/agenc-launch daemon status
```

It adds:

- Non-blocking (configurable) **`agenc update`** on launch  
- Offline/caching resilience (`AGENC_OFFLINE=1`)  
- Daemon health verification  
- Clean hand-off to the real `agenc` binary  

## Smoke test

```bash
make agenc-install   # once
make agenc-smoke     # wrapper + help + daemon (+ doctor if available)

# optional LLM one-shot (needs provider keys / onboard)
AGENC_SMOKE_LLM=1 make agenc-smoke
```

| Exit | Meaning |
|------|---------|
| 0 | Pass |
| 1 | Fail |
| 2 | Skip — `agenc` not installed |

## Environment variables

| Variable | Default | Effect |
|----------|---------|--------|
| `AGENC_UPDATE_CHECK` | `1` | Set `0` to skip update check |
| `AGENC_UPDATE_MODE` | `nonblocking` | `blocking` or `nonblocking` |
| `AGENC_DAEMON_AUTOSTART` | `1` | Set `0` to skip daemon health check |
| `AGENC_NO_UPDATE` | `0` | Kill-switch for all update checks |
| `AGENC_OFFLINE` | `0` | `1` = skip network updates (local cache) |
| `AGENC_HOME` | `~/.agenc` | Runtime state root |
| `AGENC_INSTALL_METHOD` | `official` | `official` (get.agenc.ag) or `npm` |
| `AGENC_INSTALL_DAEMON` | `0` | `1` to install user systemd/launchd service |
| `AGENC_BOOTSTRAP_NODE` | `1` | Fetch user-local Node 25+ if system Node too old |
| `AGENC_SMOKE_LLM` | `0` | `1` to run headless print in smoke |

## Requirements

- **Node.js ≥ 25** (upstream). `make agenc-install` can bootstrap Node under `~/.local/share/pfy-mentat/node`.
- **ripgrep (`rg`)** recommended (`agenc doctor` reports it).
- Provider for real model calls: default **xAI** (`XAI_API_KEY` / Grok OAuth). See upstream providers docs.

## Related

- `integration/agenc/` — augmentation skills (loop-engineering pack)
- `harness/agent-cage/` — container lab (complement, not replacement)
- Upstream update: `agenc update` (not `runtime update`)
