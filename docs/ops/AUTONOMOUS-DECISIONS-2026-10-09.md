# Autonomous decisions — 2026-10-09

One line each. Choice | alternatives | why. Pre-authorized batch `orch-decisions-1009`. Smallest reversible option.

- Sponsio probe and repoharness harness subprocesses get a fresh temp `HOME` (opensteps hooks already do) | isolate git only; leave `HOME` inherited | those third-party subprocesses are what can write the operator home
- `TimeoutExpired` in opensteps `hook()` and repoharness `hj()` records a check failure, exit 1, receipt reason contains `timeout` | exit 2 | file contract: 1 = the tool ran but the check failed, 2 = prereq missing; sponsio already returns 1 on timeout
- `PFY_XINTAKE_TIMEOUT` (float seconds) overrides those timeouts; defaults stay 60 (opensteps) and 120 (repoharness and sponsio) | hard-code a 1s production timeout | the regression test needs a tiny timeout without slowing a real smoke
- Pin `68b6a51e40cd8e229f1f056c2aa5ea93de7934f746dcf8dd38e3b7d9dd4ee397` from `https://github.com/hoangnb24/repository-harness/releases/download/harness-v0.1.10/harness-linux-x64.sha256` (curl to `/tmp` only; binary not run). Smoke hashes the local file and exits 2 with a sha256 reason before exec on mismatch | docs-only pin; exit 1 | the entry's truncated `68b6a51e40cd…ee397` was not checked, so a wrong binary still ran
- `HARNESS_SHA256` env, when set, is the expected digest; unset means the release pin | no override | a HOME or timeout stub cannot equal the release digest; the default stays the release pin
- Gitignore only `pipelines/smoke/sponsio/`, `pipelines/smoke/opensteps/`, and `pipelines/smoke/repoharness/` | ignore all of `pipelines/smoke/` | `pipelines/smoke/kolibri1/latest.json` is already tracked and must stay tracked
- `--integration-stage` has no default; absent writes `unscored` (field kept) on the cannot-run JSON and the scored receipt; a passed value is copied; committed receipt files are not rewritten | omit the field; keep hardcoded `I1` | the bench must not claim catalog stage I1; `unscored` is explicit; historical receipts stay evidence
- T-0076 is cross-link lines in `one-shot`, `agent-loops`, and `prefer-behavior-and-fail-recover-tests` to `bootstrap/grok-cli/skills-external/mattpocock/to-spec/SKILL.md` and `.../tdd/SKILL.md` | a new eval-harness scorer | the request says skill cross-links, not new scorers
- T-0040 marked done | leave it doing | the work item is parity notes; the section cites the existing adapter, attach path, and tests and does not claim runtime parity
- GitHub-issues table keeps one row each for T-0075 and T-0007 with status done; the stray top "Done / shipping" bullets move into the Done table; the file starts at `# TODO` | delete the #230 and #228 bullets | the Done table is the status source, and those two bullets exist nowhere else
- Active parked row for T-0007 is removed | leave that row as todo | the Done table already says T-0007 is done, and Active is for unfinished work
