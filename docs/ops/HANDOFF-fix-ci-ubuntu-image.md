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

All at the gated code SHA `603c2c3` (this results note is a docs-only follow-up commit).

| Check | Id | Result |
|-------|----|--------|
| eval-structural (dispatch), G0 (ubuntu-latest) job, runner label `ubuntu-24.04`, image 24.04.5 | run 41003223935, job 123892193920 | success (ripgrep step ok; Structural + golden ok) |
| eval-structural, G0 (self-hosted nimo) job | run 41003223935, job 123892194072 | success |
| operator-launch-filemode (push) | run 41003167991 | success |
| pregate full, nimo, runner idle | `603c2c3-20261030T051106Z-352430` | OVERALL=PASS wall=1062s pass=6 fail=0 skip=1 (suite skipped by design: eval-structural and ubuntu-parity already ran discover) |
| pregate `--only lint` with this branch's script on main `6b04ba8` | `6b04ba8-20261030T042938Z-103650` | FAIL as intended: 3 unpinned `runs-on: ubuntu-latest` lines and no ripgrep install |

Baseline: the failing run on the old image was 41000777422 (40 failures in `tests.test_harness2_local_sandbox`, rg missing on ubuntu 26.04).

## Known gaps

- 24.04 will also be retired eventually. When the pin moves, the harness2 sandbox tests will run on the hosted runner with bwrap; ripgrep is already installed for that case, but other missing tools may surface.
- The job display name still says "ubuntu-latest". Renaming it needs a matching branch-protection update.

## Next (no-PR flow)

Reviewer gates the pinned SHA with the pregate summary and CI run ids. When it PASSes, bots fast-forward `main` to the pinned SHA.
