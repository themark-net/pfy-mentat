# Handoff: pin the GitHub-hosted CI image to ubuntu-24.04

## Status

Branch `fix/ci-ubuntu-image`, cut from `origin/main` `6b04ba8`. CI-config only (plus a pregate lint check). Gated by pregate plus Reviewer under Mark's 2026-10-29 rule. Not merged by the implementer. Results are under "Verify".

## Problem

`main` went red: eval-structural run 41000777422, job "G0 (ubuntu-latest)", 40 failures, all in `tests.test_harness2_local_sandbox` (for example "AssertionError: 2 != 0 : rg missing"). GitHub moved `ubuntu-latest` from 24.04 to 26.04. On 26.04 bwrap works, so the bwrap-gated tests run (skipped dropped from 93 to 20), and ripgrep is not installed, so they fail.

## Change

- `.github/workflows/eval-structural.yml`: the GitHub-hosted G0 job runs on `ubuntu-24.04`. The job name stays "G0 (ubuntu-latest)" so required status checks keep matching; a comment says why. A new step installs ripgrep when `rg` is missing, so a later image bump does not fail on `rg missing`.
- `.github/workflows/filemode-operator-scripts.yml`: both jobs pinned to `ubuntu-24.04`.
- Self-hosted workflows (`local-lab`, `nightly-models`, `post-merge-brief`, the nimo G0 job) are unchanged.
- `scripts/pregate.sh` lint (Reviewer follow-up 8): FAILs if any workflow uses `runs-on: ubuntu-latest` or if `eval-structural.yml` stops installing ripgrep. The ubuntu-parity detail says it mirrors the pinned `ubuntu-24.04` job. `docs/ops/PREGATE.md` updated to match.

## Verify

RESULTS_PLACEHOLDER

## Known gaps

- 24.04 will also be retired eventually. When the pin moves, the harness2 sandbox tests will run on the hosted runner with bwrap; ripgrep is already installed for that case, but other missing tools may surface.
- The job display name still says "ubuntu-latest". Renaming it needs a matching branch-protection update.

## Next (no-PR flow)

Reviewer gates the pinned SHA with the pregate summary and CI run ids. When it PASSes, Mark fast-forwards `main`.
