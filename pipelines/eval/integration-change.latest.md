# Integration self-mod eval

date: 2026-07-31T03:47Z
reason: ingest exo self-mod patterns + catalog pin
outcome: **adopt**

| ID | Gate | Hard | Result | Detail |
|----|------|:----:|:------:|--------|
| S1 | structural_G0 | Y | PASS | PASS  skills_manifest: PASS: all first-party skill checks ok |
| S2 | golden_cards | Y | PASS | wrote /tmp/pfy-mentat/pipelines/eval/golden.latest.md |
| S3 | catalog_schema | Y | PASS | ok n=50 v=0.4.12 |
| S4 | triple_write_S_tier | n | PASS | PASS catalog-check S-tier ok n=50 |
| S5 | smoke_contract | n | PASS | PASS smoke contract 7 example dirs |
| S6 | size_policy_no_weights | Y | PASS | ok no weights |
| S7 | paths_pack_integrity | n | PASS | claude-unified-agents=16, mattpocock=3, ponytail=6 |
| S8 | diff_blast_radius | n | PASS | dirty=10 catalog=3 eval=1 docs=3 other=3 |
| S0 | intent | n | PASS | ingest exo self-mod patterns + catalog pin |

## Exo mapping

- Before: intent + optional branch (snapshot)
- Validate: this script (S1–S7)
- Adopt/hold/rollback: outcome above
- Memory: this receipt under pipelines/eval/

