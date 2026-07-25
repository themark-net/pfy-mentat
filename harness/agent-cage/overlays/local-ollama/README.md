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

## Failure modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `JSONDecodeError` / mitm **502** | HTML from proxy; DNS/policy | `make local-ollama-up`; policy allows host |
| `Could not resolve host.docker.internal` | No extra_hosts | smoke now applies local-ollama fragment |
| DNS → **172.17.0.1** but **connection refused** | Docker `host-gateway` = docker0; cage is on **172.30.0.0/24** | smoke rewrites host to **bridge .1** (e.g. `172.30.0.1`) |
| Gateway running; host `curl :11435` OK; cage fail | Wrong host IP from container | Use cage-bridge host IP, not 172.17.0.1 |

`make smoke-litellm-ollama` now: overlay-install → local-ollama-up → detect cage-bridge host IP → patch `/etc/hosts` → smoke via that IP:11435 (NO_PROXY).
