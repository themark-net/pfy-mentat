# OpenCode-in-cage smoke (T-0081)

Optional isolation of OpenCode worker inside agent-cage.

| Mode | Command |
|------|---------|
| Soft smoke | `make smoke-opencode-cage` |
| Host path (required first) | `make smoke-opencode-ollama` |

Soft-SKIP when docker/podman or `opencode` CLI missing. Full cage wrap is optional after host path green.
