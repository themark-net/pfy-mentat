# pfy-mentat

**pfy-mentat — Your PFY, a Mentat. It gets sent out, finds the tools, applies the standards, and reports back with receipts.**

pfy-mentat is both a high-standard catalog of local LLM development tools *and* an orientation toward building the software that actually deploys and runs them reliably.

The system (the PFY) is sent out to discover candidates, apply strict local-first standards, reject what doesn’t meet them, and deliver only the components that are worth using. The goal is not merely “tools that exist,” but tooling that helps people ship working local LLM systems instead of fighting endless “it works on my machine” problems — both for the tools themselves and for the products built with them.

Repository: https://github.com/themark-net/pfy-mentat

## Simple path

One command starts the detected local runtime if it is only partial, then list what it is serving:

```bash
./pfy up        # start FreeToken / Ollama / … if partial; print engine, base_url, models
./pfy models    # live GET /v1/models (and Ollama /api/tags); usage if the engine exposes it
```

`./pfy start` with no harness named does the same as `./pfy up`. FreeToken model env: **`PFY_FT_MODEL`** (then `LOCAL_CODER_MODEL` or `FREETOKEN_MODEL`).

## What it is

- A living, gate-checked catalog of local LLM dev tools, frameworks, patterns, and methods.
- An operator posture (the PFY) for discovery on X and elsewhere: apply non-negotiable criteria, log every decision with receipts, and keep the catalog current.
- A deliberate focus on **reproducibility and deployment**, not just “it builds” — components and patterns that support shipping working systems.
- Practical operator stack: **Grok CLI**, custom agents, **MCP** code memory, LiteLLM routing, **containerized harnesses** (agent-cage), and process docs so multi-session agents stay aligned.

## Core principles

- **Local first, always.** Tools must be self-hostable and runnable on normal developer hardware with minimal ceremony.
- **Permissive and embeddable.** Licenses must allow real use and modification.
- **Receipts over vibes.** Every inclusion or rejection is logged with explicit reasoning in [`sources/x-posts.md`](sources/x-posts.md) (and related sources).
- **Beyond “it builds.”** While many projects struggle to even compile successfully, pfy-mentat orients toward components and practices that support working, deployable results — for the tools themselves and for the systems people build with them.

We recognize that perfect reproducibility is impossible in computing (just as Ansible’s idempotency guarantees can be broken by the environment). The intent is still to raise the baseline: tools and patterns that are more likely to result in something that actually runs and keeps running, rather than another local-only prototype.

## Stage 0 gate

Items must satisfy all of the following before catalog consideration (full rubric: [CATEGORIZATION.md](CATEGORIZATION.md)):

- Runnable self-hosted path under ~5 minutes on a clean Ubuntu or macOS system (or a documented one-liner).
- Permissive open-source license suitable for embedding and modification.
- Working hello-world or quickstart that demonstrates the core capability.

Rejections are logged with short, explicit reasons. There is no silent ignoring of candidates.

## Goals

- Maintain a living, versioned catalog of the best local-first LLM tools.
- Apply consistent, multi-stage evaluation criteria for compatibility, performance, agentic capability, and pipeline readiness.
- Identify synergies for a unified local development stack (inference + agents + memory + orchestration + CI/CD).
- Enable rapid prototyping and deployment of custom pipelines using the highest-ranked components.
- Support Grok CLI as primary interface initially, with fallback/hybrid to other identified toolsets based on task requirements.
- Provide selective, reproducible copies of critical tools via pinned commits (rare subtree) while keeping the tracking repo lean.
- Test integrations in **versioned container sandboxes** (agent-cage) so host systems stay clean and results are reproducible.

## Using the catalog

| Consume | Path |
|---------|------|
| Human catalog | [TOOLS.md](TOOLS.md) — categories, scores, tiers, notes |
| Machine catalog | [data/tools.json](data/tools.json) — structured, must stay valid JSON |
| Decision receipts | [sources/x-posts.md](sources/x-posts.md) — examined posts and decisions |
| Taxonomy & rubric | [CATEGORIZATION.md](CATEGORIZATION.md) — Stage 0 + weighted stages → 0–100 → S/A/B/C |
| Work queue | [docs/TODO.md](docs/TODO.md) — deeper eval and integration work |

**Default tracking:** pinned commit + shallow clone (`data/tools.json`). Rare subtree only if [SUBTREES.md](SUBTREES.md) criteria are met.

**Catalog triple-write rule:** every processed tool seed must update `sources/x-posts.md` (if social/paper) **and** `TOOLS.md` **and** `data/tools.json` (JSON must parse). `/catalog-docs seed` or `/catalog-docs audit` enforces this.

### Automation (the PFY)

Discovery is not a slowly rotting list: candidates from X (and related monitors such as [@tom_doerr](docs/automation/tom-doer-monitor.md)) are triaged against the gate and relevance rules, with traceable entries for what was examined. Catalog updates happen only when justified. Full daily unattended PFY automation is evolving; until then, operators and agents run the same receipt-backed process by hand or on demand.

### Philosophy on deployment and working results

pfy-mentat does not treat “it builds on my machine” as success. While we cannot eliminate all environment-specific failures, selection criteria and patterns here prioritize components that support reproducible builds *and* working deployments. People using this catalog should spend less time debugging why something only works for the original author and more time shipping functional local LLM systems.

## Process docs (agents & humans)

| Artifact | Path | Role |
|----------|------|------|
| **Design** | [docs/DESIGN.md](docs/DESIGN.md) | Master goals, system shape, non-goals |
| **Architecture** | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Short structural snapshot |
| **ADR** | [docs/adr/](docs/adr/README.md) | Settled decisions + **rejected alternatives** |
| **TODO** | [docs/TODO.md](docs/TODO.md) | Ordered next steps (links to OQs) |
| **Open questions** | [docs/OPEN_QUESTIONS.md](docs/OPEN_QUESTIONS.md) | TBDs; detail may live next to work citing `OQ-NNNN` |
| **Agent entry** | [AGENTS.md](AGENTS.md) | Mandatory read list + do-nots |
| **Contributing** | [CONTRIBUTING.md](CONTRIBUTING.md) | How to add seeds/tools |
| **Catalog docs skill** | `/catalog-docs` | Keep README, triple-write catalog, harness docs consistent |
| **Module docs** | [docs/modules/](docs/modules/README.md) | Operator + agent maps for bootstrap, cage, write-guard, smokes |

When architecture pivots: `/adr`. When something is unsettled: `/open-questions`. When documenting this repo: **`/catalog-docs`**. Work queue: `docs.TODO.md`.
