# OQ-0005: Grok participation in agent-cage

- **Priority:** P1
- **Status:** answered
- **Created:** 2026-07-12
- **Updated:** 2026-07-12
- **Blocks:** —
- **Blocked-by:** —
- **Related-ADR:** ADR-0002 (Grok primary)
- **Related-code:** `harness/agent-cage/`, `harness/agent-cage/overlays/grok/`
- **Feature/runbook:** harness-integration · [DEPLOY.md](../ops/DEPLOY.md) · [overlays/grok/README.md](../../harness/agent-cage/overlays/grok/README.md)
- **Related-TODO:** T-0020, T-0021, T-0022 (all done)

**Question:** How should Grok CLI interact with the PNNL agent-cage sandbox?

**Context:** Upstream agent-cage is harness-agnostic but docs emphasize Claude/Cline/LangGraph. We already have Grok as primary operator on the host. Need a default so integration tests are consistent.

**Options:**

1. **Host-Grok + cage workspace** — Grok on host; untrusted installs/MCP/network-sensitive work inside cage; mount/sync workspace
2. **Grok installed inside agent image** — custom Dockerfile overlay; API key via env; full in-cage sessions
3. **Claude/Cline inside cage for adversarial tests only; Grok stays host** — dual-harness
4. **Defer** — use cage for policy/MCP/network tests without a coding agent until later

**Recommendation (historical):** Start with **(1)** for speed; add **(2)** as optional versioned overlay.

## Resolution

**Answered (2026-07-12): both (1) and (2)** — dual path, not exclusive.

| Path | Role | How |
|------|------|-----|
| **(1) Host-Grok** | Default for catalog, docs, `/one-shot`, operator work | Host `grok`; cage for untrusted installs / MCP / network-sensitive lab |
| **(2) Grok-in-image** | Optional full in-cage Grok sessions under policy | `overlays/grok/` + `make cage-grok-*` |

**Rejected as default:** pure **(3)** dual-harness (Claude-in-cage only) and pure **(4)** defer — cage already has a coding-agent path with Grok; other harnesses stay **T-0040** (P3).

**Shipped artifacts (T-0022):**

- Overlay: `harness/agent-cage/overlays/grok/` (Dockerfile, compose override, `coding-agent-grok` policy)
- Targets: `make cage-grok-install` · `cage-grok-auth-import` · `cage-grok-build` · `cage-grok-up` · `cage-grok-smoke`
- Auth: host OIDC `auth.json` import (preferred); device login in-cage; `XAI_API_KEY` fallback only

## Resolution notes

- **2026-07-12 (early):** Operator chose to pursue **(2)** after cage baseline green. Scaffold on `feature/agent-cage-grok-image`. Host-Grok remained valid for catalog work. Left **open** until smoke green under `coding-agent-grok`.
- **2026-07-12 (close):** **T-0022 done** (merged main). Overlay README documents auth pitfalls (compose override, mount only `auth.json`, chown uid 1001). Operator smoke path: `make cage-grok-smoke` (`grok --version` + auth present). **OQ-0005 → answered.** No new ADR — operational dual path under ADR-0002; details live in overlay + DEPLOY.
