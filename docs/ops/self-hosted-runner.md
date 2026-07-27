# Ops: self-hosted GitHub Actions runner

**Status:** active (2026-07-26)  
**Goal:** Unsupervised long-running eval/smokes on operator hardware without an interactive shell babysitter.

## Why

- GitHub-hosted runners are ephemeral and wrong for Ollama / agent-cage residency.
- A self-hosted runner on the operator machine (or a VPS you control) picks up jobs continuously.
- Grok operations push code and workflow definitions via the GitHub connector; the runner executes them locally with full local filesystem and optional Docker/Ollama.

## Workflows

| Workflow | File | Runs on | Purpose |
|----------|------|---------|---------|
| eval-structural | `.github/workflows/eval-structural.yml` | self-hosted `pfy-mentat` (push) or `ubuntu-latest` (PR) | No-LLM structural gate |
| eval-long | `.github/workflows/eval-long.yml` | **self-hosted only** | Dispatch lanes up to N minutes |

## Operator install

See [bootstrap/github-runner/README.md](../../bootstrap/github-runner/README.md).

Minimum: register runner with label `pfy-mentat`, install service, confirm idle in repo Settings → Actions → Runners.

## Safe local access model

- Structural and skill verification: unlimited local reads; write only CI receipts under `pipelines/eval/`.
- Long lane may set `contents: write` for optional receipt commits (off by default unless you add a step).
- No fork-PR execution on self-hosted.
- Voice lane in CI uses **mock** mode only (no microphone).

## Long-running tests without supervision

1. Runner service is up (`svc.sh status`).
2. Trigger **eval-long** with `full-local-ladder` or `eval-auto` and `max_minutes=180`.
3. Watch Actions UI or `gh run watch` — no need to keep a TTY open.
4. Download artifacts for receipts.

## Failure modes

| Symptom | Fix |
|---------|-----|
| Job queued forever | Runner offline / missing label `pfy-mentat` |
| structural FAIL on 007 | Missing fail* fixtures — fix catalog, re-run |
| eval-auto skipped | Install Ollama on runner host |
| Permission denied docker | Add runner user to docker group; re-login service |

## Relation to agent-cage

Cage smokes remain available via Makefile on the same host. Future workflow steps can call `make smoke-*` once Docker is confirmed in the runner environment; keep them optional so structural stays green without containers.
