# Full-repo gap scan — automation & development work

**Date:** 2026-07-30  
**Scope:** All tracked files (~365, excl. pipelines / venv / git)  
**Method:** Structure inventory + TODO/FIXME/deferred grep + examples↔Make mapping + tools.json stages + DESIGN “later” + ops “Not yet”  
**Human decisions held:** #34–#37 (and any HD) — not expanded here  
**Already open (skip re-file):** #24 colibri · #25 Laguna smoke · #30 ATG reminder


## GitHub issues filed (automation only)

| GAP | Issue |
|-----|-------|
| GAP-01 CI G0 | [#38](https://github.com/themark-net/pfy-mentat/issues/38) |
| GAP-02 integration_stage bulk | [#39](https://github.com/themark-net/pfy-mentat/issues/39) |
| GAP-03 triple-write check | [#40](https://github.com/themark-net/pfy-mentat/issues/40) |
| GAP-04 scoring dashboard | [#41](https://github.com/themark-net/pfy-mentat/issues/41) |
| GAP-05+25 smoke contract | [#42](https://github.com/themark-net/pfy-mentat/issues/42) |
| GAP-06 golden draft hook | [#43](https://github.com/themark-net/pfy-mentat/issues/43) |
| GAP-08+34 surface sync | [#44](https://github.com/themark-net/pfy-mentat/issues/44) |
| GAP-09 dual-sided product smoke | [#45](https://github.com/themark-net/pfy-mentat/issues/45) |
| GAP-12 implement tasks expand | [#46](https://github.com/themark-net/pfy-mentat/issues/46) |
| GAP-16 pool inventory soft | [#47](https://github.com/themark-net/pfy-mentat/issues/47) |
| GAP-17 voice memory | [#48](https://github.com/themark-net/pfy-mentat/issues/48) |
| GAP-19 worker brief | [#49](https://github.com/themark-net/pfy-mentat/issues/49) |
| GAP-23+26 cage wrap / umbrella | [#50](https://github.com/themark-net/pfy-mentat/issues/50) |
| GAP-28 external skills verify | [#51](https://github.com/themark-net/pfy-mentat/issues/51) |
| GAP-33 TODO sync helper | [#52](https://github.com/themark-net/pfy-mentat/issues/52) |

Not filed (lower / research / held): GAP-07 UAT eligibility scorer · GAP-10/11 deploy docs · GAP-13–15 model recipes/DSPy/ngram · GAP-18 OpenCode-as-MCP · GAP-20 ticket→PR · GAP-21 TTS recipe · GAP-22 duplex · GAP-24 cage memory · GAP-27 agenc archive · GAP-29–32 catalog depth · GAP-35 module docs. See tables above.

## Inventory snapshot

| Area | Count / state |
|------|----------------|
| Top dirs | examples 91 · docs 86 · bootstrap 80 · harness 27 · sources 14 · scripts 6 · data 5 |
| Make targets | ~79 |
| tools.json | v0.4.10 · **48** tools · **0** with `smoke`/`make_target` fields |
| tool_integration_stages.json | **11** entries (most tools still unstaged) |
| eval tasks | 001–010 (structural + implement) |
| golden-tasks | **1** card (GT-0001) |
| ADRs | 0013 |
| Open OQs | **0** active |
| CI (`.github/`) | **absent** |
| First-party skills | 12 (verify green) |

## Themes of missed work

### A. Meta-platform automation (high leverage)

| ID | Opportunity | Why it was missed | Effort |
|----|-------------|-------------------|--------|
| GAP-01 | **GitHub Actions CI** for `eval-structural` + `eval-golden` (+ optional deploy-ready) | No `.github/`; all gates local | M |
| GAP-02 | **tools.json bulk `integration_stage`** (default I0/I1) + schema check in structural | Only 11/48 in stages registry; 45 lack field | S–M |
| GAP-03 | **Catalog triple-write CI/check** (sources entry ↔ TOOLS.md ↔ tools.json) | Mentioned in plan-mobile-seed; never automated | M |
| GAP-04 | **Scoring dashboard** (static HTML/MD from tools.json tiers) | DESIGN § later; no ticket | M |
| GAP-05 | **Smoke contract linter** — `pipelines/smoke/*` or examples must match harness-integration-framework | Framework docs only | S |
| GAP-06 | **Golden corpus growth automation** — prompt to draft cards on issue close | Only GT-0001; draft script exists, not hooked | S |
| GAP-07 | **G2 UAT eligibility checker** (structural) — DoD blocks human test until deploy-simple flags | Gate policy new; no scorer | S |
| GAP-08 | **Stale surface sync** — README Current Status / DESIGN near-term / TODO GitHub map drift | README still lists T-0021 as next; voice “test edit” | S |

### B. Product deploy spine (G1 standards)

| ID | Opportunity | Notes | Effort |
|----|-------------|-------|--------|
| GAP-09 | **env-stage dual-sided proof** — smoke that `project-onboard` into tmp dir then stage | Product levers exist; no automated dual-client proof | M |
| GAP-10 | **product-ship dry-run** receipt always under pipelines/ | partial | S |
| GAP-11 | **DEPLOY.md ↔ product levers** cross-link + profile recipes as scored matrix | docs drift | S |

### C. Eval / models (non-HD)

| ID | Opportunity | Notes | Effort |
|----|-------------|-------|--------|
| GAP-12 | **Implement-lane tasks expansion** (003+ code tasks beyond palindrome/sum) | only 2 implement tasks | M |
| GAP-13 | **Hybrid local model routing recipes** as scored docs/scripts | DESIGN later | M |
| GAP-14 | **DSPy + MCP scored tier scaffold** (no full DSPy yet) | deferred since OQ-0002 | L |
| GAP-15 | **ngram-mod / llama.cpp perf note → smoke probe** | scoring-summary S-tier; no automation | S–M |
| GAP-16 | **Model pool inventory script** (list GB; warn >250) | policy exists; HD #35 held — **script still valuable as P3 soft** | S |

### D. Voice / worker automation

| ID | Opportunity | Notes | Effort |
|----|-------------|-------|--------|
| GAP-17 | **Cross-turn voice memory** (transcript ring beyond session_id) | orchestrator “Not yet”; session sticky only | M |
| GAP-18 | **Grok MCP tool to spawn OpenCode** as first-class tool | voice-orchestrator Not yet | L |
| GAP-19 | **Worker-monitor auto brief from git/CI** | worker-monitor Not yet | M |
| GAP-20 | **Ticket → worker → PR without supervisor** (bounded) | explicit non-goal today; research only | L |
| GAP-21 | **TTS synthesis soft path** (piper install recipe) | probe only today | S |
| GAP-22 | **True VoIP / duplex** | ADR-0012 deferred; keep I0 | — |

### E. Cage / harness

| ID | Opportunity | Notes | Effort |
|----|-------------|-------|--------|
| GAP-23 | **OpenCode full cage wrap** (not only soft host skip) | soft smoke exists | M |
| GAP-24 | **Cage cross-session memory/** dir from design | cage-session-resumption optional later | M |
| GAP-25 | **examples/* ↔ Make index** — codebase-memory/repowise/write-guard only via harness; add thin smoke.sh wrappers for discoverability | mapping gap | S |
| GAP-26 | **smoke-integration** umbrella target (harness roadmap item 3) | host+context tools bundle | S |
| GAP-27 | **integration/agenc archive banner** — demoted content still present | ADR-0010 | S |

### F. Catalog / skills / research ports

| ID | Opportunity | Notes | Effort |
|----|-------------|-------|--------|
| GAP-28 | **External skills structural check** (mattpocock/ponytail paths pack exists) | verify_skills first-party only | S |
| GAP-29 | **LEANN/Memvid I2 probe criteria** (no embed) | patterns done; probe criteria missing | S |
| GAP-30 | **Hyperframes / Continue.dev** catalog depth (S-tier Continue without smoke field) | catalog hygiene | S |
| GAP-31 | **Night-shift / proactive loop skill** (loop types) | agent-loops docs; no event trigger | M |
| GAP-32 | **sources/entries hygiene** — unprocessed or status-only rows | x-posts processed; aggregates? | S |

### G. Docs hygiene (automation-friendly)

| ID | Opportunity | Notes | Effort |
|----|-------------|-------|--------|
| GAP-33 | **TODO.md sync bot** from GitHub issue state | map stale after batch closes | S |
| GAP-34 | **DESIGN delivered vs near-term rewrite** | write-guard “implement next” stale | S |
| GAP-35 | **Module docs for voice / eval-harness / opencode** under docs/modules | only 5 modules | S |

## Explicitly NOT new HDs

Held per operator: #34 PRODUCT_REMOTE · #35 inventory priority · #36 golden LLM replay · #37 asm adopt.

## Recommended next automation batch (no human)

1. GAP-01 CI structural  
2. GAP-02 + GAP-03 catalog schema automation  
3. GAP-08 + GAP-34 doc drift (quick)  
4. GAP-05 + GAP-25 smoke contract  
5. GAP-06 golden growth hook  
6. GAP-09 dual-sided product onboard smoke  

## Files that most often hide work

| Path | Signal |
|------|--------|
| `docs/DESIGN.md` § later / near-term | research backlog |
| `docs/ops/*` “Not yet” sections | product depth |
| `data/tools.json` vs `tool_integration_stages.json` | incomplete staging |
| `examples/*` without `smoke.sh` | discoverability |
| Missing `.github/workflows` | no CI gate |
| `data/golden-tasks/` size | eval thinness |
| `examples/eval-harness/tasks/001-002` only implement | model ladder thin |
| `README.md` Current Status | operator confusion |

## Progress 2026-07-30 evening

| Issue | Status |
|-------|--------|
| #38 CI G0 | **done** — `.github/workflows/eval-structural.yml` |
| #39 integration_stage bulk | **done** — all 48 tools + structural required |
| #40 triple-write S-tier | **done** — `catalog_check` + structural check |
| #41 dashboard | **done** — `make catalog-dashboard` |
| #42 smoke contract | **done** — lint + thin smoke.sh wrappers |
| #43 golden hook | **docs** — capture doc agent hook |
| #44 surface sync | **partial** — DESIGN later + write-guard stale fixed |
| #45 product levers smoke | **done** — `make smoke-product-levers` (+ init.sh portable fix) |
| #47 pool inventory | **done** — `make model-pool-inventory` soft |
| #51 external skills | **done** — structural `external_skills_paths` |
| #52 TODO sync helper | **done** — `scripts/sync_todo_status.py` |
