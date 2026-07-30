# OQ-0008: OK to download colibri model weights?

- **Priority:** P2
- **Status:** answered
- **Created:** 2026-07-12
- **Updated:** 2026-07-30
- **Blocks:** — (was T-0016)
- **Blocked-by:** —
- **Related-ADR:** ADR-0003 (no weights in catalog repo)
- **Related-code:** TOOLS.md colibri; `docs/ops/local-model-storage-and-eval.md`; `data/golden-tasks/`
- **Feature/runbook:** colibri-eval / local-model-pool
- **Related-TODO:** T-0016 (eval when ready under pool policy)
- **GitHub issue:** [#20](https://github.com/themark-net/pfy-mentat/issues/20)

**Question:** May we download large colibri/GLM int4 weights onto this machine (disk + RAM ~25GB class) for serve benchmarks?

**Context:** Engine is pinned in catalog; weights are large and tok/s is expected low. Ollama already covers day-to-day local models.

**Options:**

1. **No / park** — keep catalog pin only (recommended default)
2. **Yes, under explicit path** — e.g. external disk; document location; never commit weights
3. **Yes, later in agent-cage only** — isolate experiment

**Recommendation:** (1) until operator confirms disk budget and interest in flagship-MoE-on-laptop path.

**Resolution notes:**

- **2026-07-30 — Models are interesting; controlled download OK.** Not a blanket “no.”
  - **Total local weights pool ≤ 250 GB**; concurrent mini models required alongside larger experiments.
  - **Before large download:** scan existing external evals for suitability; **X-post / catalog-forwarded models** with compelling arguments may proceed to direct lab eval faster.
  - **Do not rely only on external sources:** score models on **proximity** to tasks already accomplished building this repo (golden tasks + implement/structural lanes).
  - **Sample** human requests + agent task decompositions (not every turn) under `data/golden-tasks/`.
  - Document capture tooling and queue full automation; seed GT-0001 immediately.
  - Colibri-class weights: **allowed within budget** after suitability ladder; never commit to git.
  - Canonical: [docs/ops/local-model-storage-and-eval.md](../ops/local-model-storage-and-eval.md).
