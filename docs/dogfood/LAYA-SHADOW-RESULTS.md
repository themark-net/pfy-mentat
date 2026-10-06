# Laya shadow second-opinion — Entry 086 follow-up (#230 / ADR-0016)

**Cite:** Entry 086 · [#230](https://github.com/themark-net/pfy-mentat/issues/230) · [ADR-0016](../adr/0016-jev-decision-layer.md)  
**Branch / worktree:** `bot/laya-shadow` · `/home/mark/DEVELOP/pfy-mentat/tmp/laya-shadow`  
**Host:** nimo (CPU). Started `2026-10-06T03:25:39Z`, finished `2026-10-06T03:27:06Z`.  
**Receipt:** [`pipelines/dogfood/laya-shadow/receipt.json`](../../pipelines/dogfood/laya-shadow/receipt.json)  
**Cases:** same 48 as [`data/decision-gates/laya-trial.cases.v0.json`](../../data/decision-gates/laya-trial.cases.v0.json)  
**Gate:** `PFY_JEV_CONF_GATE` **0.85**. Flag: `PFY_JEV_LAYA_SHADOW=1` (default unset).  
**Verdict:** **RAN**. Catalog **HOLD 70–75**. No GUI. No default-lane change. **Not a Feature GO.** Flag stays **off**.

CUA-S1-FORMS stays `PRIMARY_LOCAL`. Laya **english** runs only when the opt-in flag is on **and** CUA would auto-act (`conf ok` / `auto_act`). Choice disagreement or Laya error → escalate (exit 3). No silent auto-act. Cloud TypeSafe is refused.

## Headline numbers (measured)

| | Count |
|--|------:|
| CUA held at 0.85 | 37 / 48 |
| CUA wrong-but-confident | **16** |
| CUA held-correct | **21** |
| **Catch** (Laya disagrees on CUA wbc) | **9 / 16** |
| **Miss** (Laya agrees on CUA wbc) | **7 / 16** |
| **False-escalate** (Laya disagrees on CUA held-correct) | **4 / 21** |
| Shadow errors | **0** |
| Shadow-call latency | p50 **0.185 s**, p95 **0.260 s** (n=37) |
| Laya process RAM | peak RSS **2142456 KB** (~2.14 GB), HWM **2867668 KB** (~2.87 GB) |

Serve: `laya-serve` on `127.0.0.1:8765`, `LAYA_MODELS=english`, CPU, health in **80.06 s**. Weights from `/home/mark/DEVELOP/pfy-mentat/tmp/laya-trial/.hf-cache` (not copied into this worktree). Revision `7b928d828b7b0e022f929d9bd2e44165aa270148`.

Catch IDs: `ph-03-ci-red`, `ph-06-red-busy`, `ph-07-waived-busy`, `ph-08-missing-ci`, `ph-09-unknown-ci`, `ph-10-unknown-kronos`, `wz-07-toolset-jev`, `cp-02-drop-stale`, `cp-05-drop-old-models-list`.

Miss IDs: `ph-04-known-red`, `ph-05-kronos-busy`, `hd-11-fits-skill-path`, `fm-04-skip-decision-off`, `fm-06-skip-launch-empty`, `fm-08-skip-already-filled`, `cp-06-truncate-readme-dump`.

False-escalate IDs: `wz-09-local-not-tool`, `hd-01-optional-tool-skip`, `hd-10-phase0-not-assist`, `cp-03-truncate-bulky`.

These match the Entry 086 trial **replay** projection for english (9/16 catch, 4/21 false-escalate). This run applied the live helper, not a receipt replay.

## Verdict on keeping the flag

Catch **9** vs collateral **4** is a net save of auto-acts on this set, and added latency is small (~0.2 s p50). It is **not** catch ≫ collateral: 7 of 16 confident-wrongs still pass, and 4 of 21 held-correct answers get escalated.

**Keep the flag off by default.** Useful as an opt-in brake on CUA `conf ok` mistakes when an operator already runs local `laya-serve`. Not a default-lane swap. Not a Feature GO. RAM for english-only is ~2.9 GB HWM (the dual-checkpoint trial was ~4.6 GB).

## How it is wired

- Helper: `maybe_laya_shadow` in `scripts/pfy_jev_230.py`, after a CUA Choice that would auto-act.
- Call sites: `cua_s1_forms_plan`, `route_model_tool` (CUA path), `compact_session`. `decide_choice` stays local.
- Flag off: identity. No shadow key, no network.
- Flag on + disagree or Laya unreachable: `ok=False`, `auto_act=False`, `usable=False`, `classify_decision` → **escalate** (exit **3**).
- Env: `PFY_JEV_LAYA_SHADOW=1`, `PFY_JEV_TYPESAFE_URL=http://127.0.0.1:8765/v1/systemone`. Unset `PFY_JEV_MODEL` → shadow model `english`. Cloud TypeSafe URL is refused.

## Locks respected

- Decision API, not chat. Cite **#230** only. Do not reopen #76.
- Catalog **HOLD 70–75**.
- Confidence = margin. Gate ~0.85. No silent auto-act.
- CUA-S1-FORMS stays primary local. TypeSafe cloud remains optional and unkeyed.
- No GUI. No TOOLS.md / `data/tools.json` row. Entry 086 stays trial-ran / no promotion.
