# Laya trial results — Entry 086 eval-auto vs CUA-S1-FORMS (#230 / ADR-0016)

**Cite:** Entry 086 · [#230](https://github.com/themark-net/pfy-mentat/issues/230) · [ADR-0016](../adr/0016-jev-decision-layer.md)  
**Branch / worktree:** `bot/laya-trial` · `/home/mark/DEVELOP/pfy-mentat/tmp/laya-trial`  
**Host:** nimo (CPU). Started `2026-10-06T02:47:20Z`, finished `2026-10-06T02:50:55Z`.  
**Receipt:** [`pipelines/dogfood/laya-trial/receipt.json`](../../pipelines/dogfood/laya-trial/receipt.json)  
**Cases:** [`data/decision-gates/laya-trial.cases.v0.json`](../../data/decision-gates/laya-trial.cases.v0.json) (48 labeled Choice cases; labels written `2026-10-06T00:00:00Z`, **before** either model ran)  
**Gate:** `PFY_JEV_CONF_GATE` **0.85** (margin chip, never percent-correct). Below gate → escalate. No silent auto-act.  
**Verdict:** **RAN**. Catalog **HOLD 70–75**. No GUI. No default-lane change. **Not a Feature GO.**

Laya was reached only by pointing the optional TypeSafe lane at a local `laya-serve` (`PFY_JEV_TYPESAFE_URL=http://127.0.0.1:8765/v1/systemone`). Product default `https://api.typesafe.ai/v1/systemone` and `PRIMARY_LOCAL=cua-s1-forms` stayed unchanged. Receipt `default_lane_unchanged: true`.

## Headline numbers

| Lane | Accuracy | Escalate | Wrong-but-confident | Warm p50 | Peak RSS |
|------|----------|----------|---------------------|----------|----------|
| **CUA-S1-FORMS** (default) | **56.3%** (27/48) | **22.9%** (11/48) | **16** | near-instant (`warm_p50` 0.0 s) | **~26 MB** (`peak_rss_kb` **25988**) |
| **laya:english** | **62.5%** (30/48) | **100%** (48/48; never cleared 0.85) | **0** | **0.204 s** | **~4.57 GB** (`laya_hwm_kb` **4568580**) |
| **laya:typed-decisions** | **56.3%** (27/48) | **100%** (48/48) | **0** | 0.1946 s | same Laya process HWM |

**Wire contract:** **PASS** (HTTP **200**, `parser_ok`). Extra answer key vs strict Jev contract: `type`. ADR-0016 typesafe parser is lenient (`answers` + `confidence`); it still got choice + confidence.

**Recommendation:** **keep CUA-S1-FORMS as default** — Laya had no measured win on this set (higher raw accuracy on english but never held a decision at the gate).

## CUA failure mode (call out)

CUA-S1-FORMS is **confidently wrong on 16 of 48** (`wrong_but_confident`). That is the main CUA failure mode on this set.

Held 37/48 at/above 0.85 (`conf ok`). Of those, 21 were correct and **16 were wrong**. The 16 IDs:

`ph-03-ci-red`, `ph-04-known-red`, `ph-05-kronos-busy`, `ph-06-red-busy`, `ph-07-waived-busy`, `ph-08-missing-ci`, `ph-09-unknown-ci`, `ph-10-unknown-kronos`, `wz-07-toolset-jev`, `hd-11-fits-skill-path`, `fm-04-skip-decision-off`, `fm-06-skip-launch-empty`, `fm-08-skip-already-filled`, `cp-02-drop-stale`, `cp-05-drop-old-models-list`, `cp-06-truncate-readme-dump`.

CUA is a form-fill specialist (~706K). On this labeled coding-session Choice set it often locks `push` / `keep` / `check` with a high margin when the label is `hold` / `escalate` / `skip`. Confidence is a margin, not correctness — these 16 cases show the chip can read `conf ok` on a wrong choice.

## Laya on this set

Both Laya checkpoints ran all 48 cases with 0 errors. Confidence never reached the 0.85 gate:

| Checkpoint | Conf min | Conf max | Held at 0.85 |
|------------|----------|----------|--------------|
| english | 0.0231 | 0.6553 | **0 / 48** |
| typed-decisions | 0.0048 | 0.3197 | **0 / 48** |

So Laya **always self-escalates** here. Raw choice accuracy (english 30/48, typed-decisions 27/48) is not a held decision. A bot that required `conf ok` before acting would never auto-act on Laya's output from this trial.

Serve: `laya-serve` on `127.0.0.1:8765`, `LAYA_DEVICE=cpu`, `LAYA_MODELS=english,typed-decisions`, `LAYA_JEV_STRICT=1`. Health in **195.11 s**. Device `cpu`. Revisions `7b928d828b7b0e022f929d9bd2e44165aa270148` for both loaded checkpoints. Trial process `laya_peak_rss_kb` 3844044; high-water **4568580 KB**.

## Next test (proposal only — NOT implemented)

Idea Mark liked: use Laya as a **shadow second opinion** that flags CUA confident-wrong answers. Rule: when CUA is held (at/above 0.85 / not escalate) but Laya's **choice disagrees**, escalate (do not auto-act).

This slice does **not** implement that rule. Numbers below are a **measured replay** of this receipt's per-case `cases` (choice disagreement only; Laya always self-escalates on confidence).

CUA held-correct on this set: **21**. CUA wrong-but-confident: **16**.

| Shadow lane | Catch (disagree on CUA wbc) | Miss (agree on CUA wbc) | False-escalate (disagree on CUA held-correct) |
|-------------|-----------------------------|-------------------------|-----------------------------------------------|
| **laya:english** | **9 / 16** | 7 / 16 | **4 / 21** |
| **laya:typed-decisions** | **7 / 16** | 9 / 16 | **5 / 21** |

Replay IDs (english): catch `ph-03`, `ph-06`, `ph-07`, `ph-08`, `ph-09`, `ph-10`, `wz-07`, `cp-02`, `cp-05`; miss `ph-04`, `ph-05`, `hd-11`, `fm-04`, `fm-06`, `fm-08`, `cp-06`; false-escalate `wz-09`, `hd-01`, `hd-10`, `cp-03`.

Replay IDs (typed-decisions): catch `ph-03`, `ph-06`, `ph-08`, `wz-07`, `hd-11`, `cp-02`, `cp-05`; miss `ph-04`, `ph-05`, `ph-07`, `ph-09`, `ph-10`, `fm-04`, `fm-06`, `fm-08`, `cp-06`; false-escalate `wz-09`, `hd-01`, `hd-06`, `hd-10`, `cp-03`.

english would catch 9 of CUA's 16 confident-wrongs and would also escalate 4 of 21 held-correct answers. typed-decisions is weaker on this replay (7 catch, 5 collateral). Neither checkpoint held a decision of its own.

A follow-up may implement the shadow rule behind a flag. It is **not** a default-lane swap and **not** a Feature GO.

## Locks respected

- Decision API, not chat. Cite **#230** only. Do not reopen #76.
- Catalog **HOLD 70–75**.
- Confidence = margin (`conf ok` / `conf low`). Gate ~0.85. No silent auto-act.
- CUA-S1-FORMS stays primary local. TypeSafe cloud remains optional and unkeyed; this trial used a local URL override only.
- No GUI. No TOOLS.md / `data/tools.json` row. Entry 086 stays off I3 / default smoke.
