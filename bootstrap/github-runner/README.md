# Self-hosted GitHub Actions runner (pfy-mentat)

**Purpose:** Run unsupervised structural eval, smokes, and long lanes on *your* machine without babysitting a terminal session.

This is ordinary GitHub Actions self-hosted runner setup, driven by workflows in `.github/workflows/`. The Grok GitHub connector can push workflow changes and trigger work via commits / `workflow_dispatch`; the runner executes on the host where you install it.

## One-time install (Linux / macOS / WSL)

1. Create a runner registration token for this repo:
   - GitHub → **themark-net/pfy-mentat** → **Settings** → **Actions** → **Runners** → **New self-hosted runner**
   - Copy the token shown (expires quickly).

2. On the machine that will run jobs:

```bash
cd /opt   # or any durable directory
mkdir -p actions-runner && cd actions-runner
# Use the download URL GitHub shows for your OS/arch, then:
./config.sh --url https://github.com/themark-net/pfy-mentat \
  --token "${RUNNER_TOKEN}" \
  --labels pfy-mentat \
  --name "$(hostname)-pfy"
```

3. Install as a service (recommended — survives logout):

```bash
sudo ./svc.sh install
sudo ./svc.sh start
sudo ./svc.sh status
```

Or foreground: `./run.sh`

Labels **must** include `pfy-mentat` so `eval-long.yml` can target `[self-hosted, pfy-mentat]`.

## What the runner host should have

| Capability | Required for |
|------------|--------------|
| `python3` 3.10+ | structural, skills |
| `make` | Makefile lanes |
| Docker (optional) | agent-cage smokes |
| Ollama (optional) | `eval-auto` / local models |
| Network to `github.com` | job pickup |

Structural lane needs **no** Ollama and **no** Docker.

## Security rules (non-negotiable)

1. **Never** enable self-hosted runners for untrusted fork PRs. Workflows use GitHub-hosted for `pull_request` where possible; do not add `pull_request` to `eval-long.yml`.
2. Runner process has the same filesystem rights as the install user. Prefer a dedicated user with access only to the repo workdir and tool caches.
3. Do not put cloud API keys in runner env unless required; local-first profile is default.
4. Treat `workflow_dispatch` as privileged — only repo collaborators can trigger it.

## Day-to-day use

- Push to `main` / `heavy-worth-300` touching eval paths → `eval-structural` runs.
- **Actions → eval-long → Run workflow** → choose lane (`structural`, `smoke-skills`, `voice-agent-mock`, `eval-auto`, `full-local-ladder`).
- Artifacts upload receipts under `pipelines/eval/` and voice `.generated/` when present.

## Uninstall

```bash
sudo ./svc.sh stop
sudo ./svc.sh uninstall
./config.sh remove --token "${REMOVE_TOKEN}"
```

## Related

- [docs/ops/self-hosted-runner.md](../../docs/ops/self-hosted-runner.md)
- `make eval-structural`
- ADR local-first stack (agent-cage, Ollama optional)
