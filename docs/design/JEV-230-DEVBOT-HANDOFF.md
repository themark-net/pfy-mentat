# #230 DevBot handoff — Jev-style decision layer (compaction + routing)

**Design PASS (light DoD):** 2026-09-18 PT  
**Cite:** GitHub **#230** only. Do not reopen **#76**. Catalog **70–75 HOLD** (HOLD exception = this slice only).  
**Additive lock:** primary local attach is **CUA-S1-FORMS** (`JEV-230-CUA-S1-FORMS-LOCK.md`). mini-jev is teaching fallback. TypeSafe remains optional cloud.  
**Implement against:** `DESKTOP-SPEC.md` + this file. Prefer Grok Build on nimo (`machineId` `5c5c138b-c5f6-4ba5-a8d0-fe204735e5cc`).  
**Do not** implement from Design Bot. **Do not** scrape private HTML. **Do not** Mark drip for default smoke. **No Env tab.**

---

## Founder locks

- ATTACH-USABLE CANDIDATE. HOLD exception this slice only; catalog 70–75 stay HOLD.
- Jev = **decision API** (typed Choice/Score), **not chat**.
- Confidence = calibrated **margin**; threshold per use — never paint as “% correct.”
- Core value = coding-session **context compaction** + **model/tool choice middleware** — not browser-use / Ultrafast demo as core.
- Attach: (a) optional TypeSafe key; (b) local **CUA-S1-FORMS** FreeToken-first on nimo (preferred Mark-free smoke). mini-jev teaching fallback only.
- **Additive (2026-09-19):** primary local attach for forms/decision smoke = **CUA-S1-FORMS** (trycua/cua); TypeSafe Jev remains optional cloud compaction/routing. Mini-jev/FreeToken-first still valid offline path.
- Honesty: `decision ≠ gab auto ≠ local recommend`.
- FreeToken-first local spine **unchanged** unless mini-jev is explicitly FreeToken-first.
- Product copy only. Operate-or-FAIL. Prefer Grok Build on nimo after Design PASS.

---

## DoD (must all PASS)

1. **Decision API UX** — Loop wizard + Attach paint decision layer as typed Choice/Score (compaction + routing middleware), not a chat pane.
2. **Confidence honesty** — chip/one-liner: margin ≠ correctness; below threshold → escalate / FAIL visible — no silent auto-act.
3. **Attach paths**
   - (a) TypeSafe key **optional**: when present → compaction/routing via TypeSafe; when toggled without key → FAIL + next (or fall back to local CUA-S1-FORMS)
   - (b) **local CUA-S1-FORMS** FreeToken-first on nimo operates without Mark (mini-jev teaching fallback)
4. **Core value paint** — compaction + model/tool middleware visible in wizard/Engine; browser-use not primary story
5. **Wizard clarity** — control/chip shows decision active vs Gab/Grok cloud vs local
6. **Smoke** — CUA-S1-FORMS Choice on nimo **without Mark ops** (mini-jev teaching fallback)
7. **Holds** — #225 Launch session intact; #228 Gab lane + local sync role intact; no Env tab; catalog 70–75 HOLD; #76 stays closed; FreeToken-first spine hold

---

## Wireframe paints (product)

### Loop — decision local (preferred smoke)

```
lane       local
decision   ● local CUA-S1-FORMS · FreeToken-first
chip       decision · typed Choice · conf ok
chip       decision ≠ gab auto ≠ local
[ Launch session ]
```

### Loop — decision TypeSafe optional

```
decision   ● TypeSafe · compaction/routing
key        set | FAIL optional-missing · next docs | use local CUA-S1-FORMS
chip       typesafe key optional
chip       decision · conf margin
```

### Loop — Gab cloud with decision off (contrast)

```
lane       cloud/subscription
endpoint   Gab · https://gab.ai/v1
model      ● auto
decision   ○ off
chip       gab auto · cloud router
```

### FAIL+next map

| Condition | Paint | Next |
|-----------|-------|------|
| Decision on, TypeSafe path, no key | FAIL key missing (optional) | set TypeSafe key **or** switch local CUA-S1-FORMS |
| conf low on auto-act | FAIL / escalate · conf low | raise threshold bar, confirm, or fallback model |
| mini-jev runtime missing | FAIL decision | install/pull FreeToken-first local path |
| Equated decision with gab auto in copy | FAIL honesty | chip `decision ≠ gab auto ≠ local` |
| Smoke needs Mark | FAIL process | local CUA-S1-FORMS Mark-free path |

---

## Non-goals

- Chat UI for Jev
- Browser-use / Ultrafast as core product story
- Confidence as correctness %
- Equate decision with Gab Intent Engine `auto` or local recommend order
- Mark drip for default smoke
- Reopen #76; lift catalog 70–75; Env tab
- Change FreeToken-first spine (except explicit mini-jev FreeToken-first)
- Private HTML scrape

---

## Refs (public only)

- https://typesafe.ai/ — decisions not chat; calibrated confidence
- https://github.com/tamaratran/fast-jev-compaction — compaction pattern
- https://github.com/r-ms/mini-jev — local logit Choice teaching path
- https://github.com/browser-use/jev-ultrafast — ref only, not core

---

## Suggested build order

1. Wizard decision toggle: off | local CUA-S1-FORMS | TypeSafe optional | mini-jev fallback  
2. Honesty chips: `decision · typed Choice`, `conf ok|low`, `decision ≠ gab auto ≠ local`  
3. Local CUA-S1-FORMS Choice on nimo (Mark-free smoke); mini-jev teaching fallback  
4. Optional TypeSafe client when key present (compaction/routing)  
5. Middleware: session context compaction → Choice model/tool with confidence gate  
6. Tester smoke on nimo without Mark  

---

## Success check (founder)

Decision layer attaches as typed API beside Gab/local. Compaction + routing middleware helps coding sessions. Confidence chips honest. Local CUA-S1-FORMS smokes on nimo without Mark. Window never paints Jev as chat or equates decision with Gab auto or local recommend.
