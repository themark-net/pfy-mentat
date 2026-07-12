# Overlay: Grok CLI inside agent-cage

Versioned agent image with Grok CLI. **Primary auth is the same as host Grok Build:** browser/OIDC login stored in `auth.json` — **not** an API key (though `XAI_API_KEY` remains an optional fallback).

## How Grok Build auth works (host)

| Method | When | Where stored |
|--------|------|----------------|
| **Browser / OIDC login** (`grok` or `grok login`) | Default for subscriptions (opens browser → auth.x.ai) | `~/.grok/auth.json` (mode `oidc`, access + refresh tokens) |
| **Device auth** (`grok login --device-auth`) | Headless / Docker / SSH (URL + code in any browser) | same `auth.json` |
| **`XAI_API_KEY`** | CI / console key from [console.x.ai](https://console.x.ai) | env only — used **only if no active session** in `auth.json` |

You authenticated this environment with the web OAuth flow; that session lives in:

```text
~/.grok/auth.json          # mode 0600, contains OIDC tokens (do not commit)
```

Tokens refresh automatically via `refresh_token` until refresh fails (then re-login).

## Cage auth strategies

### 1) Import host session (recommended)

Copies host `auth.json` into the cage’s isolated Grok home (not a live bind of your whole `~/.grok`):

```bash
make cage-grok-install
make cage-grok-auth-import   # ~/.grok/auth.json → ~/.agentcage/grok-home/auth.json
make cage-grok-build         # rebuild after Dockerfile changes
make cage-grok-up            # MUST use this — not plain cage-up-mcp / agentcage up
make cage-grok-smoke         # expect grok 0.x.x + auth.json present
make cage-shell
# [cage] grok --version
# [cage] grok -p "ping" --always-approve   # uses imported session
```

**Pitfalls fixed in this overlay:**

1. **`agentcage up` ignores compose override** when it passes `-f docker-compose.yaml`. Always use **`make cage-grok-up`** (explicit third `-f` for override).
2. **Do not bind-mount the whole `.grok` tree** — that hid `.grok/downloads/` and broke `grok`. Binary is installed to **`/usr/local/bin/grok`**; only **`auth.json`** is mounted.

Re-import after host re-login if the cage session expires.

### 2) Device login inside cage (separate session)

No host secrets shared:

```bash
make cage-grok-up
make cage-shell
# [cage] grok login --device-auth
# open URL on any browser, enter code
```

Needs policy allow for `auth.x.ai` / `*.x.ai` (included in `coding-agent-grok`).

### 3) Shared mount of host auth.json (advanced)

Higher coupling: host and cage share the same file; concurrent refresh can race.

```bash
GROK_AUTH_MOUNT=1 make cage-grok-install   # generates mount-based override
```

### 4) API key only

```bash
echo 'XAI_API_KEY=xai-...' >> ~/.agentcage/.env
```

Only if you use console API keys; subscription browser users should prefer (1) or (2).

## Prerequisites

1. Base cage green (`make cage-up-mcp` + tests once).
2. Image `agent-cage-agent:latest` exists.
3. Auth: import, device-login, or API key as above.

## Make targets

| Target | Action |
|--------|--------|
| `grok-overlay-install` | Copy Dockerfile, compose override, policy into `~/.agentcage` |
| `grok-auth-import` | Copy host `~/.grok/auth.json` → `~/.agentcage/grok-home/` |
| `grok-overlay-build` | Build `local-llm-dev-tools/agent-cage-grok:0.1.0` |
| `grok-up` | `up --mcp` with `coding-agent-grok` policy |
| `grok-smoke` | `grok --version` in container |
| `grok-overlay-uninstall` | Remove overlay files (not host auth) |

Repo root: `make cage-grok-*`.

## Security

- **Never commit** `auth.json` or cage `grok-home/`.
- Import copies a **credential** into `~/.agentcage/grok-home` — treat that dir like a secret store (`chmod 700`).
- Prefer import or device-auth over mounting full host `~/.grok` (skills/sessions are host-specific).
- Do not bake tokens into the Docker image layer.

## Files

| File | Purpose |
|------|---------|
| `Dockerfile` | FROM `agent-cage-agent:latest` + install Grok CLI binary |
| `docker-compose.override.yaml` | Image + `grok-home` volume + optional key |
| `coding-agent-grok.yaml` | Proxy allowlist including `*.x.ai`, `*.grok.com` |
