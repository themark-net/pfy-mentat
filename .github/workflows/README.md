# GitHub Actions (self-hosted first)

Runner label required: **`pfy-mentat`** (plus `self-hosted`).

| Workflow | Purpose | Default trigger |
|----------|---------|-----------------|
| `voice-clean.yml` | **Primary goal:** clean voice interface (STT wiring + agent + long-task mock + optional remote) | push on voice paths, dispatch |
| `eval-structural.yml` | Deterministic structural gates (no LLM) | path push, dispatch |
| `eval-long.yml` | Operator ladder (structural / skills / eval-auto / voice-agent-mock / full) | dispatch only |

## Operator loop

1. Runner installed as a service on the Strix Halo host (see `bootstrap/github-runner/`).
2. **Actions → voice-clean → Run workflow** after voice changes — or push to `examples/voice-stt-edge/`.
3. Receipts land as artifacts + `pipelines/smoke/voice-clean/results.latest.md`.
4. Use `eval-long` for longer unsupervised ladders (up to 6h).

## Citizenship

- Self-hosted only for these jobs (no burning GitHub-hosted minutes for local stack work).
- `concurrency` cancels superseded voice-clean runs on the same ref.
- Required voice steps need no mic and no cloud.
- Do not attach self-hosted runners to untrusted fork PRs.

## Related

- `make smoke-voice-stt` / `make smoke-voice-agent` / `make smoke-voice-remote`
- `docs/ops/self-hosted-runner.md`
