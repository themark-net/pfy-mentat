# #243 DevBot handoff — Loop UX (catalog modules + live local/cloud hedge)

**Design PASS (DoD):** 2026-09-24 PT  
**Cite (primary for PM):** this file — `/home/mark/DEVELOP/pfy-mentat/docs/design/LOOP-243-DEVBOT-HANDOFF.md`  
**Also cite:** `LOOP-243-JOURNEY.md` · `LOOP-243-IA.md` · `LOOP-243-WIREFRAMES.md` · `LOOP-243-NON-GOALS.md` · PR body **#243**  
**PR draft:** https://github.com/themark-net/pfy-mentat/pull/243  
**Head verified:** `3cb788a6ed5f76c13da356b6cd9ece3b9945d15d` on `cursor/pr11-loop-local-cloud-ux-055e`  
**Base tip for work:** `main` @ `e797151c47e10e2667cf72b6bcaca0d1ea1c521d`  
**Canonical checkout:** `/home/mark/DEVELOP/pfy-mentat` on nimo (`machineId` `5c5c138b-c5f6-4ba5-a8d0-fe204735e5cc`)  
**T:** T-0125  

**Do not** merge #243 from Design. **Do not** contact Mark. **Do not** reopen #76. Catalog **#70–#75** stay out. Prefer Grok Build on nimo after Design PASS. Design does **not** implement product code.

---

## Founder / product locks (CEO RELEASE + PR #243 body — do not invent beyond)

1. **Loop** = product front door for **gathered tools** — **not** a harness picker.
2. **Pane explains itself:** job, numbered steps, **why-line** on controls.
3. **Where work runs:** **Local compute** (this machine) vs **Cloud orchestration** (credits). Lane words **ON / STANDBY / SPENDING / OFF** defined on the pane (local ON|OFF; cloud STANDBY|SPENDING|OFF).
4. **How hard:** **Bulk** stays local; **Interactive** local-first; **Hard** may spend a cloud credit.
5. **MODULES:** catalog tools; paint **wired / partial / not wired**; **stub cannot enable**.
6. **Launch session** opens **grok** or **OpenCode** with enabled modules (**the proof**). **Launch env** only starts the local model.
7. **Live sentence:** where *this* session will run, or the next step if it cannot.
8. **Other tabs:** one-line lede only — Engine = local model; Attach = open a TUI without composing modules; Tools = skills/catalog (does not start a session). Stage may keep a one-line honesty lede; no Stage redesign.
9. **Code touchpoints:** `pfylib/loop_paint.py` `story()`; HTML + tk Loop; board `POST /module` + `POST /loop/task`; Launch applies enabled modules first.

---

## Design Bot pfy gates (must hold in chrome)

| Gate | Rule |
|------|------|
| Operate-or-FAIL | Every visible control runs its action or shows **FAIL**/**STUB** in-window with a next step. Silent no-op = FAIL. |
| Operator copy only | No design notes, ADR theology, adapter lectures, nimo-runner banners, honest-state dumps, or localhost board URLs as window identity. |
| Honesty | Missing ≠ unknown; no fake green; stub ≠ ready. |
| Native path | Native operator window (`./pfy` / `./pfy board`); do not bounce to Mark. |

---

## DoD — acceptance checklist (all must PASS before merge)

### A. Front door

- [ ] **A1** Loop is default/primary; copy = gathered catalog tools + Launch session proof — not harness picking.
- [ ] **A2** Numbered how-to: where → work class → modules → Launch session; Launch env = model only.
- [ ] **A3** Compose wizard (#225) may run under Launch; it is **not** Loop front-door chrome.

### B. Where work runs

- [ ] **B1** Split panes Local compute | Cloud orchestration, each with why-line.
- [ ] **B2** Local hero **ON** when a model answers, else **OFF**; status uses ready|partial|missing|skip|FAIL — never `unknown`.
- [ ] **B3** Cloud hero **STANDBY** | **SPENDING** | **OFF** per `story()`.
- [ ] **B4** Meanings from `pfylib.loop_paint.story()` on **both** HTML and tk.

### C. How hard

- [ ] **C1** Bulk / Interactive / Hard with operator why-lines (`TASK_HELP`).
- [ ] **C2** `POST /loop/task` persists task; hedge route updates live sentence.
- [ ] **C3** Bad task → FAIL + next (`bulk|interactive|hard`).

### D. MODULES

- [ ] **D1** Every toolset from `data/toolsets.json` listed.
- [ ] **D2** Operator labels **wired** / **partial** / **not wired** on HTML **and** tk (no raw `implemented` as operator chrome).
- [ ] **D3** Click toggles include; stub cannot enable → STUB + next; stub not persisted on.
- [ ] **D4** `POST /module` wired; Launch session `apply_enabled` before enterable TUI.

### E. Launch + live sentence

- [ ] **E1** Live route: where *this* session runs, or next if not ok.
- [ ] **E2** Launch session = proof (grok/OpenCode + modules). Launch env = local model only.
- [ ] **E3** Launch fail → FAIL in-window + next.

### F. Other tabs + holds

- [ ] **F1** Engine / Attach / Tools one-line ledes per locks; no redesign beyond ledes.
- [ ] **F2** Catalog #70–#75 untouched; #76 closed; no Mark ops in default smoke.
- [ ] **F3** `python3 -m unittest discover -s tests` and `python3 scripts/pfy-gui.py --selftest` green on head.

### G. Out of scope regression

- [ ] **G1** No Env nav tab.
- [ ] **G2** #228 Gab honesty and #230 decision honesty on Engine not stripped.
- [ ] **G3** Wizard lane/harness/decision buttons (if still in tk) are **not** packed on Loop view.

---

## Gaps flagged at Design skim (head `3cb788a`)

| ID | Severity | Gap | DevBot action |
|----|----------|-----|---------------|
| G-1 | **Must-fix before merge** | HTML maps `implemented`→**wired**, `stub`→**not wired**; tk chips/body still paint raw `implemented`/`partial`/`stub`. Lock requires operator labels on both surfaces. | Same mapping as HTML `paintModules` in tk chip + `loop_text` MODULES lines. |
| G-2 | Observe / hold | tk still constructs wizard lane/harness/decision buttons; Loop `pack_acts` omits them. | Keep off Loop front door. |
| G-3 | Observe | Compose wizard under Launch (#225) allowed. | Do not promote wizard chrome onto Loop lede/how-to. |

No lock-contradiction FAIL vs CEO locks / PR body. Critical UX is defined. **Design verdict: PASS** with G-1 as DevBot merge blocker inside this DoD.

---

## FAIL+next map

| Condition | Paint | Next |
|-----------|-------|------|
| Local OFF + cloud OFF | Not ready · FAIL | Launch env or set `PFY_CLOUD_BUDGET` |
| Stub module enable | STUB | how from toolset cell |
| Unknown module | FAIL module | pick listed id |
| Bad task | FAIL task | bulk|interactive|hard |
| Launch session cannot run | FAIL Launch session | Launch env / budget / wire module |
| Missing loop_paint | FAIL | install/import pfylib |

---

## Implementation pointers (Design does not code)

| Area | Path |
|------|------|
| Story + fields + toggle/task/apply | `pfylib/loop_paint.py` |
| Hedge decide | `pfylib/hedge.py` |
| HTML Loop | `gui/operator/frontend/index.html` · `app-core-2.js` (`paintHedge`/`paintModules`) · `app-ui.js` |
| tk Loop | `scripts/pfy-gui.py` (`loop_text`, module chips, task buttons) |
| Board routes | `scripts/pfy-board.py` — `POST /module` (+`/modules`), `POST /loop/task` (+`/hedge/task`), launch applies enabled modules |
| Tests | `tests/test_loop_paint.py`, `tests/test_hedge.py` |

---

## Smoke (Mark-free on nimo)

```bash
cd /home/mark/DEVELOP/pfy-mentat
git fetch origin pull/243/head:pr-243-head
git checkout 3cb788a6ed5f76c13da356b6cd9ece3b9945d15d
python3 -m unittest discover -s tests
python3 scripts/pfy-gui.py --selftest
# Manual: ./pfy setup && ./pfy  → Loop steps → toggle module → Launch session
```

---

## Non-goals

See `LOOP-243-NON-GOALS.md`. No catalog 70–75, no #76, no Mark ops, no Engine/Attach redesign beyond ledes, no Design implementation, no merge from Design.
