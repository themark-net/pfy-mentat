# Critical review — premise, product, code, process (2026-09-20)

**Status:** Delivered (this PR) · **Type:** review + worksheet (AGENTS.md “traces/worksheets”)  
**Ask:** “critically analyze the premise and the current version of this repo and product; improve it and drive forward; ask only for critical architecture decisions.”  
**Owner decisions requested:** [OQ-0011](../open-questions/OQ-0011-product-primacy.md) product primacy · [OQ-0012](../open-questions/OQ-0012-feature-freeze-until-t0090.md) feature freeze · [OQ-0013](../open-questions/OQ-0013-code-layout-pfy-package.md) code layout · [OQ-0014](../open-questions/OQ-0014-why-was-source-sharded.md) why source was sharded  
**Fixes shipped with this review:** de-shard `scripts/pfy`, `pfy-board.py`, `pfy-gui.py`, `pfy_enterable_162_b.py`; G0 gate `scripts/check_no_encoded_payloads.py`; TODO/README/OQ hygiene (see §7 trace).

Blunt by request. Every claim below has a file, a command, or a commit next to it.

---

## 1. Premise — is “scored catalog + operator stack + process framework” coherent?

**Stated premise** (README ¶1–3, DESIGN §1): a scored, receipt-backed catalog of local-first LLM tools **and** a reproducible operator stack (`./pfy`) **and** a portable agent-process framework (DESIGN/ADR/TODO/OQ + skills). DESIGN §1 declares the operator stack is *the* product; the catalog is “how we choose pieces”.

**Verdict:** the three parts are individually coherent and mutually *useful*, but the repo does not behave as if any one of them is primary. Effort since 2026-08-25 (54 issue-tagged feature commits) went almost entirely into (b) the operator GUI, while the README still leads with (a) and the ADR/OQ discipline of (c) is the part that has actually held up. The premise is not wrong; it is **undecided**, and the undecidedness shows up as the contradictions below.

### 1.1 Internal contradictions (with evidence)

| Principle stated | What the repo does | Evidence |
|---|---|---|
| **G8 “≤ 3 levers”** — onboard / stage / ship; “product UX must stay ≤ ~3 levers” (DESIGN §2 G8, §5) | `./pfy` has **21 top-level verbs** and ~24 sub-verbs (`models gab-sync`, `launch lane|toolset|harness|decision|review|compose`, `decision off|cua-s1-forms|typesafe|mini-jev`, …); Makefile has **91 targets** | `./pfy help` (baseline capture); `sed -n '/^main() {/,/^}/p' scripts/pfy`; `grep -cE '^[a-z0-9_.-]+:' Makefile` |
| **T-0090 P0 “collapse surface”** listed as `todo` since 2026-07-30 (TODO.md Active table) | GitHub **#1 was closed COMPLETED on 2026-07-30** with “3 public product targets ≤5” — i.e. the lever count was satisfied *at the Make level* on day one and then the `./pfy` surface grew ~7× on top of it. TODO.md and GitHub disagree about whether the P0 exists. | `gh issue view 1 --json state,stateReason,closedAt` → `CLOSED / COMPLETED / 2026-07-30`; `docs/TODO.md` line “T-0090 · P0 · todo” |
| **“Receipts over vibes”** (README Core principles) | The product entry point was a **9-line stub** that `base64 -d | gzip -dc`’d six opaque shards into `scripts/.pfy.expanded.sh` at every run; `pfy-board.py` / `pfy-gui.py` / `pfy_enterable_162_b.py` `exec(compile("".join(parts)))` byte-split fragments (no individual `_body_NN.py` was valid Python). Nothing about the ~2,000-line launcher was reviewable in a PR diff. | `git show --stat c68aed8` (#161, 2026-09-06: `scripts/pfy 1160 +----` → 6 `.b64` files); `ae5d2d2` (#150) and `b93ef36` (#153) for board/gui; shard sizes ≈ 4,000 B; `scripts/_pfy_board_probe.txt` = `PROBE_5K_OK` |
| **“Honest status; `missing` ≠ `partial`”** (DESIGN G8, README) | `./pfy status` and `./pfy harness list` print **different statuses for the same slots** on the same box: `status` = live detection (all `missing` here), `harness list` = the static `data/harnesses.json` field (`grok ready`, others `partial`). Same column header “STATUS”. | baseline captures `/tmp/baseline/status.out` vs `harness.out`; `cmd_status` uses `detect_status`, `harness list` prints `json_field list` (scripts/pfy ~L830, ~L1895) |
| **“Local first, always”** (README) | Default harness is **Grok (cloud subscription)** (ADR-0002, ADR-0011: “Grok primary + subscription for hard reasoning”). Local is the *worker*; the monitor and the “primary interface” are cloud. | `docs/adr/0002-*`, `docs/adr/0011-*` L11–15; `data/harnesses.json` default `grok` |
| **Catalog is “living”** (README, DESIGN G1) | Catalog is on **“HOLD 70–75”** since mid-August; last `sources/x-posts.md` entries dated **2026-07-31**; `data/tools.json` carries **4 tools** (ADR-0015 slim subset, fine) but `TOOLS.md` hasn’t moved in 7 weeks while ~20 features shipped. | `rg -n '2026-0[89]-' sources/x-posts.md` → none; PR #75 (Axon, 2026-08-14) still OPEN; every Done row since #205 carries `catalog HOLD 70–75` |
| **Non-goal: “not a monorepo of … full IDE products”** (DESIGN §3) | Repo now ships a Tauri 2 desktop app + HTML/JS frontend + tk/webkit fallback GUI + voice orchestrator + Space Invaders (`scripts/pfy_space_invaders.py`, `gui/operator/frontend/space-invaders.js`). | `gui/operator/`, `examples/voice-stt-edge/`, `scripts/pfy_space_invaders.py` |

### 1.2 Is DESIGN §1 (“operator stack is the product”) right?

Arguments **for**: it is where all recent energy went; it has a runnable `./pfy`, a GUI, 15 selftests; the owner clearly wants to *use* it.  
Arguments **against**: the distinctive, defensible idea in this repo is the **scored, receipt-backed catalog** — nobody else has “Stage 0 gate + X-post receipts + tiers” for local LLM tooling. The operator stack, as built, is a personal launcher for one operator’s box (nimo, FreeToken :1919, Grok subscription, Gab lane) — many features are only meaningful with that exact box. A third reading — the **process framework** — is the part other repos actually consume (`bootstrap/project-process/init.sh`, skills SoT) and is the most portable.

This is the one decision that cannot be made by an agent: **[OQ-0011](../open-questions/OQ-0011-product-primacy.md)**.

---

## 2. Product as built — what works on a clean box vs. what is painted

Environment for this review: clean Ubuntu container, Python 3.12, **no** tkinter, Ollama, FreeToken, Grok, Node, Docker, or GitHub token. That is close to “bare clone” — the G8 promise.

| Surface | Result on clean box | Assessment |
|---|---|---|
| `./pfy help`, `./pfy status`, `./pfy harness list` | run, exit 0 | Works. But `status` says every slot `missing` while `harness list` says `grok ready` (see §1.1). |
| `./pfy` / `./pfy up` (bare) | would try FreeToken→llama-swap→llama-server→Ollama, all absent → FAIL + “next: ./pfy up” (correct honesty), then attempt Tauri → webkit → tk; **tk is absent here so the window cannot open** | The “window always opens” claim (README L28, `pfy help`) is false on a box without tkinter or a GUI toolkit. Not tested interactively; inferred from `scripts/pfy-gui.py` (`run_tk` requires `tkinter`) and `python3 scripts/pfy-gui.py --selftest` → exit 1, silent. |
| `python3 scripts/pfy-board.py --snapshot` | exit 0, valid JSON, honest `missing`/`FAIL` fields | Works offline. Good. |
| 15 `--selftest`s (`pfy_*_NNN.py`) | 14/14 runnable ones PASS offline (`PFY_GAB_OFFLINE=1`, `PFY_JEV_OFFLINE=1`); `pfy-gui.py --selftest` exit 1 (no tk) | Selftests are real and offline-capable. But they are **self-referential**: they mostly assert that the module paints FAIL/SKIP/PASS strings and that certain substrings exist in HTML/py sources (e.g. #214 checked for `"queue      "` inside `_pfy_gui_body_08.py`). They are not behavior tests of a session actually attaching. |
| `make eval-structural` / `run_golden.py` | PASS | Real, no-LLM gate. Best thing in CI. |
| GUI (Tauri) | `gui/operator/src-tauri/` present; no build in CI; `README` says primary “when the binary is current” | Painted-primary, effectively optional. |
| Voice orchestrator, dual-tier route | `examples/voice-stt-edge/` + `make smoke-voice-*`; needs Whisper venv + Ollama | Lab-only. Not on the product path. |
| Attach Codex/Claude/Grok/OpenCode/Hermes “usable” sessions (#193/196/202/220/221) | Every path FAILs honestly without the binary; the “usable” claim was proven only on the owner’s box | Five ~90%-identical scripts (see §3.2). |
| Catalog (`TOOLS.md`, `data/tools.json`, `sources/`) | Valid; structural check passes; content frozen since 2026-07-31 | Stalled, not broken. |
| Write-guard MCP (`harness/write-guard-mcp`) | has the **only pytest-style unit tests** in the repo (`tests/test_policy.py`) | Solid small module. |
| agent-cage harness | Make wrappers + docs; requires Docker (absent here) | Unverifiable here; documented honestly. |

**Net:** the honest-FAIL discipline is real and consistent — the product rarely lies about a missing piece. What it does instead is *accumulate*: each missing piece got another verb, another lane, another “paint”. On a clean box, the product is a well-behaved status printer with ~45 verbs and no runnable session.

---

## 3. Code health

### 3.1 Sharding / encoded source (fixed in this PR)

- `scripts/pfy` (stub, 327 B) + `scripts/pfy.payload.b64.00..05` (6 × ~3.6 KB) → decoded **1,924-line** bash. Introduced `c68aed8` (#161, 2026-09-06). Commit message gives no reason.
- `scripts/pfy-board.py` (assembler, 518 B) + `_pfy_board_body_00..14.py` (15 parts, 99,448 chars, byte-split at ~4,000; exact-length check).
- `scripts/pfy-gui.py` (assembler) + `_pfy_gui_body_00..10.py` (11 parts, 72,229 chars).
- `scripts/pfy_enterable_162_b.py` (assembler) + `_p0/_p1a/_p1b` parts.
- Probe artifacts of the same pipeline committed to `main`: `scripts/_pfy_board_probe.txt` (`PROBE_5K_OK`), `scripts/_pfy_board_canary.py`, `gui/operator/frontend/.mcp-probe`, `.pfy-150-paint-note.md`, and `scripts/_pfy_launch_env_paint.py` (stale copy of `launch_env`).
- `.github/workflows/filemode-operator-scripts.yml` header: “**Contents API writes 100644**; this feature-branch job restores 100755 via git.” A whole CI job exists to undo a side-effect of pushing files through the GitHub Contents API.

Conclusion: the repo was being written through a tool with a **~4–5 KB per-file write cap and no file-mode control** (GitHub Contents API / MCP `create_or_update_file`). The workaround was pushed into the repository instead of the pipeline. It is now removed and gated ([OQ-0014](../open-questions/OQ-0014-why-was-source-sharded.md) asks the owner to confirm the constraint is gone).

### 3.2 Issue-number naming and duplication

- **21 scripts** named by GitHub issue (`pfy_attach_usable_193/196/202/220/221.py`, `pfy_enterable_162{,_a,_b}.py`, `pfy_gab_228.py`, `pfy_jev_230.py`, `pfy_launch_wizard_225.py`, `pfy_session_compose_224.py`, `pfy_live_org_queue_214.py`, `pfy_catalog_ask_queue_209.py`, `pfy_code_graph_215.py`, `pfy_orchestration_213.py`, `pfy_recommend_models_207.py`, `pfy_opencontext_205.py`, `pfy_attach_mode_208.py`, `pfy_usage_165.py`, `pfy_verify_159.py`) — **12,868 lines**, 63 % of `scripts/`.
- Duplication (difflib line-similarity, `python3 -c` over pairs): `attach_usable_196 ↔ 202` **91.0 %**, `220 ↔ 221` **90.0 %**, `202 ↔ 220` 83.6 %, `196 ↔ 220` 83.6 %. 14 function names are defined identically in 4 of the 5 files (`fail_not_usable`, `prove_cli`, `inspect_models`, `_probe_freetoken`, `read/write/clear_session_reach`, `_apply_opencontext_env`, `_apply_attach_mode_env`, `_load_193`, `_load_162_a`, …). Each Attach-X issue was solved by copying the previous script and changing the binary name.
- Modules load each other by **path** (`importlib.util.spec_from_file_location("pfy_enterable_162_a_220", …)`) rather than by package import — there is no `pfy/` package, no `__init__.py`, no importable namespace, hence no unit tests.
- Scratch in product dir: `scripts/pfy_space_invaders.py` (9.3 KB) is wired to `POST /space-invaders` in the board.

### 3.3 Tests

- `test_*.py`: **5 files / 171 lines** (write-guard policy + 4 eval-harness task fixtures). Zero tests for `scripts/pfy` (1,924 lines), `pfy-board.py` (2,407), `pfy-gui.py` (1,436), or any `pfy_*_NNN.py`.
- 15 `--selftest` flags: useful smoke, but they assert paint strings and substring presence, and CI runs only **3** of them (#228, #230, #225).
- No `bash -n`, no `shellcheck`, no `py_compile` in CI until this PR.
- **False-confidence scorers:** the repo ships deterministic “shape” scorers for its own process docs (`examples/eval-harness/tasks/006-adr-shape`, `007-oq-shape`) but runs them only against fixtures. Run against the real files: `docs/open-questions/OQ-0010-*.md` FAILs (`missing Question field`), `docs/adr/0014-*.md` and `0015-*.md` FAIL (`missing ## Consequences`). The four OQs added in this PR were written to pass `007-oq-shape`.

### 3.4 Size / ratio

| | Count |
|---|---|
| Code: `scripts/` py+sh | ~20,400 lines (after de-shard, incl. 1,924 bash) |
| Code: `examples/` py | 5,546 |
| Docs: `docs/**/*.md` | **139 files / 9,756 lines** (64 in `docs/ops/`, 26 in `docs/modules/`, 17 ADRs) |
| Root `*.md` | 884 lines |
| Make targets | 91 |
| `./pfy` verbs | 21 top-level + ~24 sub |
| Commits | 367 total; **56 since 2026-09-01** |

Roughly one markdown file per 190 lines of code. The docs are not bad — many are honest — but 64 ops docs for a product with a “≤3 lever” target is itself a symptom.

---

## 4. Process health

### 4.1 P0 starvation vs. GitHub truth

- TODO.md Active: `T-0090 · P0 · todo` (unchanged since 2026-07-30). GitHub #1: **CLOSED COMPLETED 2026-07-30**. The one P0 in the queue was declared done the day it was filed, and the doc that agents are told is authoritative says the opposite. Meanwhile ~20 P1 “done” rows shipped features that widen the very surface T-0090 was meant to shrink.
- T-0110 notes say both “#76 stays OPEN” (Active row) and “#76 CLOSED” (Done rows #214/#215). GitHub: **#76 CLOSED 2026-09-08**. Fixed in this PR.

### 4.2 Cargo-cult notes

Every Done row from #205 to #224 repeats `catalog HOLD 70–75 · #198 parked · do not reopen #76`. The same three phrases are baked into prompt text in `pfy_catalog_ask_queue_209.py` and `pfy_live_org_queue_214.py` and into the #230 selftest (`ok snapshot does not reopen 76`). Constraints became liturgy: nobody re-derived them, one selftest exists to check the liturgy is repeated. Once #76 was closed the phrase kept being copied.

### 4.3 Document drift

- TODO.md had a “Done / shipping” bullet list **above the H1** (fixed).
- Duplicate rows in the issues table: T-0075 and T-0007 appear as both `P2`/`P3` and `done` (fixed).
- Duplicate ADR ID **0012** (`0012-voice-half-duplex-local-first.md` and `0012-simple-harness-agnostic-launch.md`). Acknowledged in the index (“cite this file, do not reuse ID”). **Not renumbered here** — 20+ docs cite `ADR-0012` for the launcher; a rename is a mechanical follow-up once OQ-0011 settles which one is load-bearing.
- README “Current status → Next steps” listed Write-guard (T-0031), skill ports (T-0011), eval harness (T-0003) as next; all three are in the Done table (fixed).
- `docs/OPEN_QUESTIONS.md` said “*No open P0/P1/P2 OQs*” while a P0 product-shape question had been implicitly open for 7 weeks.

### 4.4 What the process did right

The ADR/OQ discipline **worked where it was used**: ADR-0010 rejected AgenC with reasons, ADR-0011/0014 record the local/cloud split and inference spine honestly, OQ-0002..0009 were all answered with dated resolution notes. The failure mode is that the last 7 weeks of product decisions (GUI-primary, Tauri, voice, attach lanes, Gab, Jev) were made in **issue titles and selftests**, not in ADRs/OQs — only ADR-0016 (Jev) came out of that period.

---

## 5. What is genuinely good and must be kept

1. **Structural eval lane** (`examples/eval-harness/run_structural.py`, `run_golden.py`): deterministic, no-LLM, runs on GitHub-hosted *and* self-hosted, uploads receipts. Extended in this PR with the payload gate.
2. **ADR/OQ/TODO discipline as a framework** — the rejected-alternatives rule and “never leave P0–P2 in chat” are the right rules; `bootstrap/project-process/init.sh` makes them portable.
3. **Honest status painting** — `missing ≠ partial ≠ stub`, FAIL + `next:` on every dead end. This is rare and valuable; keep it even if the surface shrinks.
4. **Write-guard MCP** — small, tested, clear policy model (ADR-0007).
5. **Harness registry** (`data/harnesses.json`) — one table of slots with roles and detect commands; a good spine for a thin launcher.
6. **Catalog methodology** (`CATEGORIZATION.md` Stage 0 gate + weighted stages + receipts in `sources/x-posts.md`) — the distinctive idea; frozen, not broken.
7. **Offline selftests** — the habit of `--selftest` with `PFY_*_OFFLINE=1` fixtures is good; it needs to become pytest under a package.

---

## 6. Recommendations (ranked)

| # | Recommendation | Tag |
|---|---|---|
| 1 | **De-shard the entry points; gate against re-sharding.** | **do now — done** (`f90ee19`, `344c2b2`, `f9a6967`, `7baef21`) |
| 2 | **Decide product primacy** (catalog / operator stack / process framework). Everything else in this list depends on it. | **needs owner — [OQ-0011](../open-questions/OQ-0011-product-primacy.md)** |
| 3 | **Feature freeze on new `./pfy` verbs/lanes until T-0090 is actually done** (≤3 levers, measured against `./pfy help`, not `make`). | **needs owner — [OQ-0012](../open-questions/OQ-0012-feature-freeze-until-t0090.md)** |
| 4 | **Move `scripts/pfy_*_NNN.py` into a `pfy/` package named by concept**, one `attach/` module with a harness table instead of five clones, `tests/` + pytest in G0. | **needs owner — [OQ-0013](../open-questions/OQ-0013-code-layout-pfy-package.md)** (layout choice); execution is mechanical after |
| 5 | **Confirm the write-pipeline constraint is gone** (per-file cap, 100644 modes). If not, fix the pipeline (git push, not Contents API). | **needs owner — [OQ-0014](../open-questions/OQ-0014-why-was-source-sharded.md)** (P1) |
| 6 | Reconcile TODO.md with GitHub (#1, #76); remove duplicate rows; stop copying `HOLD/parked/do-not-reopen` into new rows. | **do now — done** (docs commit) |
| 7 | Make `./pfy harness list` show live status or rename its column (`REGISTRY`), so two commands don’t disagree. | later (small; after OQ-0011) |
| 8 | Add `bash -n`, `py_compile`, and all 15 selftests to G0 (only 3 run today). | later (trivial once tests move to pytest) |
| 9 | Decide whether Tauri GUI / voice / Space Invaders are product or lab; move lab to `examples/` behind a flag. | later — falls out of OQ-0011/0012 |
| 10 | Renumber the duplicate ADR-0012 → next free ID with a redirect stub. | later — after OQ-0011 (which ADR is load-bearing) |
| 11 | Lift or formally park the catalog HOLD 70–75 with an ADR (either the catalog is living or it is archived). | later — falls out of OQ-0011 |
| 12 | Delete `scripts/pfy_space_invaders.py` + `/space-invaders` route from the product path. | later (owner may want it; it is wired into the board) |

---

## 7. Session trace (worksheet)

**Branch:** `cursor/critical-review-and-deshard-055e` off `main` @ `e797151`.  
**Env:** clean Ubuntu, Python 3.12, no tkinter/Ollama/FreeToken/Grok/Docker/Node; `gh` read-only.

### 7.1 Baseline (before any change)

| Check | Result |
|---|---|
| `python3 examples/eval-harness/run_structural.py` | PASS (9 checks) |
| `python3 examples/eval-harness/run_golden.py` | PASS (2 cards) |
| `PFY_GAB_OFFLINE=1 pfy_gab_228.py --selftest` | PASS |
| `PFY_JEV_OFFLINE=1 pfy_jev_230.py --selftest` | PASS |
| `pfy_launch_wizard_225.py --selftest` | PASS |
| 11 other `pfy_*_NNN.py --selftest` | all PASS |
| `pfy-gui.py --selftest` | exit 1, silent — **environmental** (no tkinter) |
| `./pfy status` / `help` / `--help` / `harness list` | exit 0; outputs captured for diff |
| `pfy-board.py --snapshot` | exit 0, JSON |
| `bash -n` decoded payload; `py_compile` concatenated bodies | OK |
| `make -n eval-structural` | `python3 examples/eval-harness/run_structural.py --write-md pipelines/eval/structural.latest.md` |
| Side effect noted | running `run_golden.py` modifies tracked `pipelines/eval/golden.latest.md` (timestamp); reverted each time |

### 7.2 Changes

1. `f90ee19` — `scripts/pfy` = decoded source (1,924 lines + 1 header line); deleted 6 shards; 4 ops docs + 2 module docs + 2 prompt strings updated from `gzip -t payload` to `bash -n scripts/pfy`.
2. `344c2b2` — `pfy-board.py` (2,407 lines) and `pfy-gui.py` (1,436 lines) as plain modules; deleted 26 body parts; `pfy_live_org_queue_214.py` selftest reads whole modules; removed 5 dead probe/scratch artifacts.
3. `f9a6967` — `pfy_enterable_162_b.py` de-sharded (3 parts).
4. `7baef21` — `scripts/check_no_encoded_payloads.py` + `--selftest`; wired into `run_structural.py` (`no_encoded_payloads`), `eval-structural.yml` (both jobs), Makefile comment. Negative test: on `main` the gate reports **39 offenders** (4 assemblers by content + 35 shards by name); on the branch, PASS.
5. Docs commit — this review; OQ-0011..0014 (index + detail files); TODO.md hygiene (title first, duplicate rows removed, #76 consistent, T-0090 note reconciled with GitHub, new Active row T-0111); README next-steps fixed.

### 7.3 After (same commands)

| Check | Result | vs baseline |
|---|---|---|
| `run_structural.py` | PASS (10 checks; new `no_encoded_payloads`) | +1 check, no regressions |
| `run_golden.py` | PASS | identical |
| #228 / #230 / #225 selftests | PASS | identical |
| all other `pfy_*_NNN.py --selftest` (11) | PASS | identical |
| `pfy-gui.py --selftest` | exit 1 (no tkinter) | identical (environmental) |
| `./pfy help` / `status` / `harness list` | **byte-identical** to baseline (`diff` empty) | — |
| `pfy-board.py --snapshot` | JSON identical except `ts` and `last_verb.when` | — |
| `bash -n scripts/pfy`; `py_compile pfy-board.py pfy-gui.py pfy_enterable_162_b.py` | OK | — |
| `check_no_encoded_payloads.py` (+ `--selftest`) | PASS / PASS | new |
| `git ls-files -s pfy scripts/pfy scripts/check_no_encoded_payloads.py` | all 100755 | — |

### 7.4 Deliberately not done

- No consolidation of `pfy_*_NNN.py` (layout needs OQ-0013).
- No ADR renumbering (0012 duplicate) — cited by filename in 20+ places.
- No change to product behaviour, verbs, or GUI. No deletion of Space Invaders / voice.
- No PR created (coordinator owns that).
