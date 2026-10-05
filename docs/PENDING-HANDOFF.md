# Pending handoff

Git plus this file is the handoff when another checkout may be open. Do not commit, reset, or stash on an open founder Build branch.

## 2026-10-05 — Dogfood D3 trimmed build preamble (#263)

- **Branch:** `bot/dogfood-d3-263` (from `cbda54a`). Worktree `/home/mark/DEVELOP/pfy-mentat/tmp/dogfood-d3-263`.
- **Landed:** trimmed `./pfy build -p` preamble + isolated child GROK_HOME; `PFY_BUILD_FULL_PREAMBLE=1`; receipt preamble size fields; tests; [docs/dogfood/D3-RESULTS.md](dogfood/D3-RESULTS.md).
- **Live trimmed measure:** ~6s, 1 turn / 1 call, **14 959** total tokens vs D2 **623 246**; route escalate exit 3; preamble_tokens_est **87**.
- **Out of scope:** GUI, catalog HOLD 70–75, Feature GO, merge.
- **Verify:** `make catalog-check` · `make eval-structural` · `python3 -m unittest tests.test_pfy_build_p tests.test_jev_decision_skill`
- **Next:** optional symlink real `bundled/` into isolated GROK_HOME (see D3-RESULTS trim suggestion).

## 2026-10-05 — Dogfood D2 bot lane (`./pfy build -p` real implement)

- **Branch:** `bot/dogfood-d2-0310654` (from main after #261). Worktree `/home/mark/DEVELOP/pfy-mentat/tmp/dogfood-d2`.
- **Landed:** jev-decision skill prefers `./pfy build -p` + route exit **3**=escalate; project mirror `.grok/skills/jev-decision/`; `tests/test_jev_decision_skill.py`; modules Failure-modes ESCALATE wording; [docs/dogfood/D2-RESULTS.md](dogfood/D2-RESULTS.md) + `pipelines/dogfood/build/20261005T071051Z/` receipt.
- **Path:** one `./pfy build -p` run completed implement (~203s, 1 turn / 13 model calls). TypeSafe tokens **0**.
- **Out of scope:** GUI, #258/#256, catalog HOLD 70–75, live TypeSafe, Feature GO, merge.
- **Verify:** `make catalog-check` · `make eval-structural` · `python3 -m unittest tests.test_jev_decision_skill tests.test_pfy_build_p`
- **Next:** Review D2; optional live `push_hold` dual-run shadow; human D1-dev lane still open.

## 2026-10-05 — D1 friction fixes (`./pfy build -p` + route escalate exit)

- **Branch:** `fix/d1-friction-pfy-build-p` (from main `682aa20`). Worktree `/home/mark/DEVELOP/pfy-mentat/tmp/d1-friction-fix-20261005`.
- **Landed:** `scripts/pfy_build_p.py` + `./pfy build -p`; route conf-low → exit **3** / `verdict: escalate`; docs follow-up in [docs/dogfood/D1-RESULTS.md](dogfood/D1-RESULTS.md); tests `tests/test_pfy_build_p.py`.
- **Closes:** D1 friction (plain output-format wrap, escalate≠broken, real receipt.jsonl). Empty D1 `pipelines/dogfood/d1/receipt.jsonl` left historical.
- **Out of scope:** GUI, #258, TypeSafe spend, Feature GO, merge.
- **Verify:** `make catalog-check` · `make eval-structural` · `make smoke-product-levers` · `python3 -m unittest tests.test_pfy_build_p`
- **Next:** merge when checks green; optional bot skill to prefer `./pfy build -p` over bare `grok -p`.

## 2026-10-05 — Dogfood D1 bot lane (jev toolset + wrapped grok -p)

- **Branch:** `dogfood/d1-jev-pfy-wrap` (from main `29b74ac`). Worktree `/home/mark/DEVELOP/pfy-mentat/tmp/dogfood-d1-20261004`.
- **Landed:** `data/decision-gates/` (README + `push_hold.shadow.v0.json`), ops/handoff cross-links, [docs/dogfood/D1-RESULTS.md](dogfood/D1-RESULTS.md) + `pipelines/dogfood/d1/` receipt.
- **Path:** `./pfy toolset apply jev --harness grok --lane local` → smoke/selftest READY → `./pfy decision route` conf-low (shadow escalate, no auto-act) → `grok -p` body (~125s, 1 turn). TypeSafe tokens **0**.
- **Out of scope:** D1 human-dev lane (Mark at keyboard), #258, Kolibri, catalog HOLD 70–75, live TypeSafe, Feature GO, merge.
- **Next:** Review D1 results; optional live shadow dual-run for `push_hold`.

## 2026-10-04 — Jev decision layer × org bots × pfy dogfood plan

- **Branch:** `docs/jev-decision-layer-and-pfy-dogfood` (from main `c0d9072`). Worktree `/home/mark/DEVELOP/pfy-mentat/tmp/jev-dogfood-plan-20261004`.
- **Ask:** Figure out existing Jev/TypeSafe usage; plan integration with Grok Bot org + Grok Build on nimo and pfy-mentat; dogfood whether `./pfy` can replace/augment bare `grok -p` for bots and a human (Mark / Bleeping Blank).
- **Landed (docs-only):** [docs/design/JEV-DECISION-LAYER-AND-PFY-DOGFOOD.md](design/JEV-DECISION-LAYER-AND-PFY-DOGFOOD.md) — inventory, decision table (keep-in-code vs Jev-style vs LLM), catalog posture (`jev` toolset stays `catalog_tool: null` per ADR-0016; no TOOLS.md row in this PR), thin-adapter notes, dogfood slice **D1**, blockers (no `TYPESAFE_API_KEY`).
- **Already wired (not new code):** `#230` / ADR-0016 / `scripts/pfy_jev_230.py` / `./pfy decision` / toolset `jev`. Local smoke READY; TypeSafe cloud optional and **unkeyed** on nimo. Org side: `themark-net/org-spinny-decide` + box skill `org-spinny-decide` (Ollama, explicitly not cloud TypeSafe).
- **Out of scope:** live TypeSafe calls, new TypeSafe account/spend, catalog HOLD 70–75, PR #256 Loop agent-picker split, eval-auto `NameError: re` fix branches, Feature GO, merging.
- **Next:** (1) Done — plan merged as #259 @ `29b74ac`. (2) D1 bot lane ran — stub in `data/decision-gates/` + [docs/dogfood/D1-RESULTS.md](dogfood/D1-RESULTS.md). (3) Shadow-log bridge for `push_hold` (live dual-run) still next. (4) T-0123 if/when catalog re-score for TypeSafe cloud is wanted.

## 2026-10-04 — PR #256 follow-up: split Loop picker + harness extract fix

- **PR #256 branch:** `build/pfy-cli-catalog-cards-0925` — CLI/catalog/eval only (no `gui/`, no `pfy-gui.py`, no `loop_paint.py`).
- **Split-off (draft PR #258):** `build/loop-agent-picker-0925` — Sep 25 Loop agent-picker / compose-from-Loop / "Open … with …" CTA. Conflicts with LOOP-243 design lock on main. Needs a Design pack before review.
- **Harness bug:** `extract_python` dropped leading `import re` before `def` → live `NameError: re` on 012-slugify (pre-existing on main). Fixed + `tests/test_extract_python.py`.
- **ensure_compose_defaults:** stayed with the picker branch (tied to Loop agent selection / GUI).
- **Eval-auto:** WIP kept; passes with gate `deepseek-coder:6.7b` after extract fix.

## 2026-10-04 — land Sep 25 Grok Build: CLI catalog cards + eval-auto

- **Branch:** `build/pfy-cli-catalog-cards-0925` (rebased onto current `origin/main`)
- **Backup:** `backup/main-local-20261004` @ pre-rebase `3afd13b`; WIP snapshot `backup/wip-uncommitted-20261004`
- **What the Build session did (Sep 25) — kept here:**
  1. **pfy CLI harness polish** — short product help; shimmy last after ollama; ollama start health + default model; share Hermes/Claude/Codex installers between CLI and Attach; read Gemini/Exo installers from registry; Continue recipe names direct vs cage filesystem.
  2. **Catalog stage cards** — every TOOLS.md row must have an integration-stage card; handoff cards for stage rows.
  3. **Eval-auto** — `scripts/eval_auto_candidates.py` + `eval-auto.sh` candidate loop + receipt (T-0074); `013-stage-card` structural scorer (T-0070).
- **Moved out:** Loop/GUI agent-picker → draft PR #258.
- **Verify:** `make catalog-check` · `make eval-structural` · `make smoke-product-levers` · `EVAL_AUTO_REQUIRE_OLLAMA=1 make eval-auto`.
- **Next:** merge when checks green. Do not auto-lift catalog HOLD entries 70–75.

## 2026-10-04 — Kolibri-1 catalog + local smoke lab (Entry 085)

- **Branch:** `bot/kolibri-1` (from main `53b24ec`). Worktree `/home/mark/DEVELOP/pfy-mentat/tmp/kolibri-1`. Operator ask: "Add to pfy-mentat. Pull it and test." (X post 2106306843052052616)
- **Landed:** `sources/entries/085-kolibri-1.md` (084 is taken by open PR #254), a TOOLS.md row (B, 72, public-docs scores), a `data/tools.json` row + `data/tool_integration_stages.json` (I0), `examples/kolibri1-llamacpp/` (build/download/serve/smoke), `make smoke-kolibri1`, and the receipt `pipelines/smoke/kolibri1/latest.json`.
- **Paths checked:** (a) Community GGUFs exist, but every one needs a llama.cpp source patch; stock llama.cpp and Ollama have no `kolibri1` (llama.cpp#29922 open). The smallest is `Eliasfpv28/Kolibri-1-Q3_K_S-GGUF` at 33.87 GB. (b) The only other registered machine, GROKBOT-WIN, is offline; nimo is AMD Strix Halo (Radeon 8060S, 64 GiB VRAM carve-out, 61 GiB RAM, no NVIDIA). (c) Kolibri is not on OpenRouter and has no HF inference-provider mapping. No Aleph Alpha, OpenRouter, or HF key names are in nimo env or `.env`.
- **Done on nimo:** Patched llama.cpp CPU backend built under `tmp/kolibri-runtime/build-cpu`. GGUF download was started then **stopped and deleted** (too big for nimo). Meta-only under `tmp/models/Kolibri-1-meta/`. Smoke at PR time: `FAIL_NO_BACKEND` (honest).
- **Next:** Kolibri-1 stays **watch-only at I0**. Mark: too big for nimo; watching for newer/smaller models. No Vulkan build; do not re-download weights or promote to I1.
- **Out of scope:** catalog 70–75 HOLD, other open PRs, Feature GO.

## 2026-09-28 — founder standings into portable skills SoT

- **Branch:** `bot/skills-port-standings-20260928` (from main `bd35bad`)
- **Prior:** stalled `bot/skills-port-standings-20260925` @ `d262300` cherry-picked here. That branch was never a PR. Do not force-push `main`.
- **Landed:** `prefer-behavior-and-fail-recover-tests`, `ui-is-the-app-design-in-loop`, `best-effort-and-bot-budget-build-max`
- **SoT:** `bootstrap/grok-cli/skills/<name>/` (org bot skills stay pointers). Project mirror: `.grok/skills/`.
- **Out of scope:** catalog 70–75 HOLD, LIVE_HARD_OFF, product UI, Feature GO.
- **Verify:** `make smoke-grok-skills`
- **Next:** merge the docs/skills PR when checks are green. Pattern: [port-bot-doctrine-to-pfy-sot.md](ops/port-bot-doctrine-to-pfy-sot.md).
