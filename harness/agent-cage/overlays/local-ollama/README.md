# Overlay: local Ollama (host) for agent-cage

Allows the **agent** container to reach **host Ollama** for LiteLLM / OpenAI-compatible smokes.

## Why a gateway?

Stock Ollama systemd often listens on **`127.0.0.1:11434` only**. Containers (and the cage proxy) cannot connect to that address on the host. Rebinding Ollama to `0.0.0.0` needs sudo; instead we run a **user-space TCP forwarder** on port **11435**.

## Install + smoke

From catalog root:

```bash
# 1) Host forwarder (no sudo)
./examples/litellm-ollama/host-ollama-gateway.sh start

# 2) Overlay + policy into ~/.agentcage
make local-ollama-overlay-install

# 3) Bring cage up with local policy + compose fragment
make local-ollama-up

# 4) In-cage LiteLLM → Ollama completion
make smoke-litellm-ollama
```

Policy name: `coding-agent-local`  
URL from cage: `http://host.docker.internal:11435` (and `/v1` for OpenAI shim).

## Failure: JSONDecodeError / mitm 502 on preflight

| Symptom | Cause | Fix |
|---------|-------|-----|
| `JSONDecodeError` on `/api/tags` | Response is HTML 502 from mitmproxy | DNS/policy: host not resolved or not whitelisted |
| `Could not resolve host: host.docker.internal` | Agent recreated by `cage-grok` **without** local-ollama `extra_hosts` | `make local-ollama-up` (smoke now does this automatically) |
| Gateway “already running” but tags fail | Ollama down on host, or gateway stale | `host-ollama-gateway.sh restart`; `curl http://127.0.0.1:11434/api/tags` |

`make smoke-litellm-ollama` now runs **overlay-install + local-ollama-up** first so `extra_hosts` and `coding-agent-local` are applied.
