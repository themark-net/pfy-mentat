### Entry 123: HarnessRouter Community Edition — one self-hosted API in front of many agent harnesses (Unified Harness Protocol)

- **URL**: https://github.com/HarnessRouter/harnessrouter (Apache-2.0, Python, about 3,050 stars at this read; release v0.34.2, image `harnessrouter/harnessrouter` 0.34.2, digest `sha256:db412234…9ad5`)
- **Date**: 2026-10-16 (daily X intake)
- **Source / Poster**: @_avichawla, https://x.com/_avichawla/status/2110993106594316306
- **Summary / Key Claims** (upstream README at v0.34.2): one Docker container (Console, Gateway, Runner) that runs harnesses such as Codex, Claude Code, Hermes and Pi behind one OpenAI Responses-compatible API, implementing the Unified Harness Protocol (UHP, https://unifiedharnessprotocol.org): persistent sessions, streaming progress, files, artifacts, cancellation and structured failures. Switching harness becomes a routing choice instead of a rewrite. Secrets passed through `env`/`vault:` references are redacted from responses, traces and stored records. No HarnessRouter account needed for Community Edition; a managed cloud exists but is optional.
- **Why it matters here**: the org runs several harnesses (Grok Build, Cursor, OpenCode, Grok CLI forks) and compares them by hand. UHP is a candidate common contract for running the same pfy-mentat task through different harnesses and comparing results, and for a future "harness choice as a routing decision" step next to Entry 122. Reference design only for now.
- **Fit on nimo**: Not yet. It ships only as a Docker image (Docker is unconfirmed on nimo; installing it is a system change that needs Mark), needs about 4 GB of disk, and the README requires a **provider API key** added in the Console. We have no paid keys, and the README does not say whether a local OpenAI-compatible endpoint (Ollama) can act as the provider, so treat it as catalog-only until that is confirmed.
- **Verified on the Grok Bot box**: nothing ran; there is no Docker on the box. Read the README at v0.34.2 and the Docker Hub tag list only. The smoke's no-docker path exits 2 as intended. **Happy path has not run anywhere.**
- **Finding**: the Console starts with a default password that the README says to change before exposing it; keep the port on loopback. CE issues its own API key, shown once; it must go straight into a secret store. The named volume keeps the database, installed harness CLIs and workspaces, so `docker rm` alone does not clear state (the smoke also removes its volume). Image tags move daily; the smoke pins the digest.
- **Extracted Repos / Tools**: https://github.com/HarnessRouter/harnessrouter · https://hub.docker.com/r/harnessrouter/harnessrouter · https://unifiedharnessprotocol.org · https://github.com/aenawi/uhp-go (third-party Go UHP server, 4 stars, not evaluated)
- **TOOLS.md Link**: None yet. I0 awareness, catalog only. No TOOLS.md row, no `data/tools.json` row.
- **Smoke**: `python3 examples/x-intake-local/smoke_122_124.py --entry harnessrouter`. Needs docker; runs the digest-pinned image on `127.0.0.1:$HR_SMOKE_PORT` (default 3917), waits for the Console, checks that a keyless `POST /api/harness/v1/responses` is refused (401/403), then removes the container and volume. No provider key, no CE key, no task. Receipt: `pipelines/smoke/harnessrouter/latest.json`.
- **Non-goals**: No provider key added, no harness run, no cloud upload, nothing exposed beyond loopback.
- **How this fails / how we recover**:

| Risk | How it fails | Recovery |
|------|----------------|----------|
| No Docker on nimo | Smoke exits 2 forever | Leave catalog-only; ask Mark before installing Docker |
| Needs a paid provider key | Can't run a task locally | Stay catalog-only unless a local endpoint is confirmed as a provider |
| Default Console password exposed | Anyone on the network can sign in | Loopback bind only; change the password on first start |
| Smoke happy path untested | First Docker run fails on a smoke bug (endpoint path, status code) | Treat the first run as the real test; fix the smoke in a follow-up |
