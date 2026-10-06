# Build drop-in: Practice Minder, M3 LockAdapter + emergency unlock (#8 / T-0012)

Paste everything below the line into Grok Build on nimo. **Pasting this is the founder RELEASE for M3 only (#8).**

---
Repo: `~/DEVELOP/practiceminder` (GitHub themark-net/practiceminder). Read AGENTS.md, SPEC.md, docs/PENDING-HANDOFF.md, docs/TODO.md, docs/contracts/lock-adapter.md, ADR-0003/0004/0005/0009 first.
Worktree: `git fetch && git worktree add /tmp/pm-m3 -b build/m3-lock-adapter origin/main`. The nimo checkout is detached with an untracked `docs/M1B-POINTER.md`. Leave it alone.

Goal: M3 only. A real `LockAdapter` behind the existing contract (`src/practiceminder/contracts/lock.py`): soft session lock by default (`loginctl lock-session` or equivalent), strict GDM stop/start opt-in, and an emergency unlock that works offline. Core accumulate and notify must keep working with the no-op adapter.

Hard invariants (frozen):
- **Never lock `nimo`.** Soft and strict both refuse when the target host is nimo, by hostname and by machine-id. Do not lock anything on nimo while testing. All lock calls in tests go through an injected command runner (ADR-0009).
- Locks stay optional (ADR-0004). No agent runtime in the shipping architecture (ADR-0003).
- Strict mode is opt-in and must say that it ends the graphical session (ADR-0005).
- Out of scope: MicIngest capture, smash polish, media (M4), web UI (M5), systemd (M6), cutover (M7).

Definition of done (behavior and fail-and-recover):
- A sociable E2E (fake runner, real daemon / control path, temp SQLite): arm → practice deficit → lock is issued against `maximum` → emergency unlock → the session is back and the event is logged with reason.
- Refusal: a target of `nimo` (or the local host's machine-id) raises the contract's refusal error. No command is executed, and the operator sees why.
- Failure: the lock command exits non-zero or times out. The adapter reports FAIL, the accumulator state is unchanged, and the next tick retries without double-locking.
- Offline emergency unlock: with the network and BLE down, the unlock path still works from the local CLI with the documented code or file.
- `scripts/ci-local.sh` is green. Report the test count. No tautological tests: each test must be able to fail when the behavior breaks.
- `M3_REPORT.md` follows the M2 report shape.

Handoff: update docs/PENDING-HANDOFF.md (M3 landed, SHAs, how Mark tries it on `maximum`, emergency unlock steps) and flip T-0012 in docs/TODO.md to `review`.
PR: push and write the body to `/tmp/pr-pm-m3.md` with `Fixes #8`. Use `gh pr create --body-file` if authenticated, otherwise print `https://github.com/themark-net/practiceminder/compare/main...build/m3-lock-adapter?expand=1`.
Gates: do not merge. Tester and Reviewer gate it. Do not start M4 or later.
