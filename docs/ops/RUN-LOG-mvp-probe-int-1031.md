# RUN LOG mvp-probe-int-1031

Launch: 2026-11-01T01:33:31Z
Wall cap: 2026-11-01T09:33:31Z (8 hours from launch). Sunday 2026-11-02T02:00Z is later, so the 8 hour cap binds.
Handoff buffer: no new probe or fix after 2026-11-01T09:13:31Z.
Branch: `bot/mvp-probe-int-1031`
Base: `origin/bot/mvp-integrate-1031` at `1dee0b91`, plus drop-in `2742345`.
Host at launch: MemAvailable about 66 GiB, load about 3.6 on 32 cores.

## LOOP EXIT CARD

```text
LOOP EXIT CARD
Goal (success criteria):     11 cloud-default probes have a receipt (exit, reason, PASS or FINDING). Each FINDING has a behavior test and the smallest fix in scripts/pfy_build_cloud.py, one commit, pushed. Handoff has the probe table.
1 Goal met:                  probe table complete, findings fixed or recorded, targeted tests green, handoff pushed
2 Turn cap:                  8 fix attempts per finding, then stop that finding
3 Budget cap:                no live Grok spend, no --local, fake grok only, closed port is 127.0.0.1
4 Wall clock:                2026-11-01T09:33:31Z, handoff starts by 2026-11-01T09:13:31Z
5 No-progress:               same failure twice with no new information, or 3 items skipped in a row
6 Human interrupt:           user stop. Do not ask. No force-push, merge, PR, or tag
7 Error threshold:           3 consecutive identical test failures on one item, then stop
8 External event:            if origin/bot/mvp-probe-int-1031 advances under this lane, stop and record. Do not rebase
Loop type:                   goal
Human gate:                  push bot/mvp-probe-int-1031 only. No merge
```

Drop-in exits (same run): wall cap, lane empty, no progress, host pressure (MemAvailable under 16 GiB, or load over 64 for 5 minutes, pause 10 minutes, then stop), red base (record and skip that area, do not stop the lane).

## Plan

Overview: Adversarial probes of `./pfy build` (cloud default, never `--local`) in scratch repos under this worktree `tmp/probe-int/`. Score each probe against the cloud build contract. Fix only FINDINGs, in `scripts/pfy_build_cloud.py` and `tests/test_pfy_build_cloud.py`, one commit each. Do not edit `scripts/pfy_build_local.py`.

Phases:

- contract | `docs/ops/RUN-LOG-mvp-probe-int-1031.md`, `docs/ops/AUTONOMOUS-DECISIONS-mvp-probe-int-1031.md` | exit card on disk before probes | none | general
- probe | `tmp/probe-int/` only | 11 fact receipts | contract | general
- fix | `scripts/pfy_build_cloud.py`, `tests/test_pfy_build_cloud.py` | one green behavior test and push per FINDING | probe | general
- handoff | `docs/ops/HANDOFF-mvp-probe-int-1031.md`, this log | probe table and `state:` line | fix | general

Risks:

- A live `grok` binary would spend and might read auth state. Mitigation: `--grok-cmd` fake, `HOME` and `PFY_STATE_DIR` under `tmp/probe-int/`, network probe connects to `127.0.0.1` only.
- Other lanes share `scripts/pfy_build_cloud.py`. Mitigation: this drop-in assigns the probe fixes here. Do not edit `scripts/pfy_build_local.py` or `pfylib/`.
- A probe could signal the wrong pid. Mitigation: signal only child pids this run starts.

## Expected fail-closed (written before the probes)

- dirty: caller porcelain stays dirty. Those paths are not in the new commit. Caller HEAD unchanged. A valid agent edit may still PASS.
- detached, sha is not `origin/main`: exit 2 before grok. Caller stays detached at the same sha. No `cloud/` branch.
- detached, sha matches `origin/main`: build that sha. Caller stays detached at the same sha.
- detached, no `origin/main`: build HEAD. Caller stays detached at the same sha.
- shell metacharacters in the task: the task is data. No side file is created. The receipt stores the task text. A valid agent edit may PASS.
- unicode path the agent creates: the commit names that path, or the run fails with no branch and the caller unchanged.
- symlink out of scope: an outside target is not modified. A new commit does not add a symlink whose target resolves outside the worktree. Pre-existing escaping link: do not run the agent through it.
- gate rewrites a file: the committed bytes are not the gate rewrite. If the gate changes the tree, no branch.
- hung gate: exit 3, reason `timeout`, no branch, child gone, returns without the outer wait firing.
- review reject then retry: exit 0, one branch, commit is the accepted attempt only.
- network loss (closed port, partial file, non-zero): does not hang, does not PASS, partial file is not committed, caller unchanged. Other non-zero grok exits that are not network, rate-limit, or auth still follow the existing contract and may run the gate.
- SIGTERM during the agent: exit 1, reason `interrupted`, no branch. Signal only this run's child.
- two builds at once: caller unchanged, no cross-contaminated commit. A single pid slot must not drop a live build. Prefer an explicit busy refusal for the second start.

## Items

Scratch receipts are in gitignored `tmp/probe-int/results.json` (first pass, before the fixes). PASS rows have no product commit. Each FINDING is one commit.

- dirty | none | probe only | PASS, exit 0 reason ok, caller porcelain unchanged, dirty paths not in the commit
- detached-mismatch | none | probe only | PASS, exit 2 before grok, no receipt, still detached, no cloud branch
- detached-match | none | probe only | PASS, exit 0 reason ok, still detached, HEAD unchanged
- detached-no-origin | none | probe only | PASS, exit 0 reason ok, still detached, HEAD unchanged
- shell-metacharacters | none | probe only | PASS, exit 0, task stored as data, PWNED not created
- unicode-paths | none | probe only | PASS, exit 0, commit names the unicode paths
- symlink-out-of-scope | e7703bf | nice -n 19 python3 -m unittest tests.test_pfy_build_cloud | FINDING fixed, exit 1 reason symlink-escape
- gate-rewrote | 30b3c3a | nice -n 19 python3 -m unittest tests.test_pfy_build_cloud | FINDING fixed, exit 1 reason gate-rewrote
- hung-gate | none | probe only | PASS, exit 3 reason timeout, no branch, elapsed 4.088s
- review-reject-retry | none | probe only | PASS, exit 0, accepted attempt only
- network-closed-port | 9028d4f | nice -n 19 python3 -m unittest tests.test_pfy_build_cloud | FINDING fixed, exit 1 reason network; other non-zero grok text can still PASS
- sigterm | none | probe only | PASS, exit 1 reason interrupted, no branch
- parallel-build-busy | e2da1d6 | nice -n 19 python3 -m unittest tests.test_pfy_build_cloud | FINDING fixed, exit 1 reason build-busy, live pid kept
- handoff | docs only, with this log | tests already green at e2da1d6 (67 tests, 21.784s, 2026-11-01T01:58Z) | lane empty

state: lane empty | 11 probes scored (detached split into 3, symlink into 2), 4 findings fixed and pushed, sandbox write-through left as an OQ draft, no further item fits this lane
