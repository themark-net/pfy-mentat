# Autonomous decisions 2026-10-16

- PR #298 (X intake 122-124): fixed Tester FAIL B1 at 5a68459. smoke_122_124.py watches the real ~/.llm-router, ~/.local/state/squadra and ~/.cache/squadra in a finally (FAIL on change, also on timeout); harnessrouter refuses a pre-existing pfy-hr-smoke container/volume, keeps the first failure reason, always runs volume rm, WARNs on $HR_IMAGE; added tests/test_x_intake_smoke_122_124.py. Pushed to the same branch, not merged.
- PR #298 Reviewer B1 at a3cab83: a failed Squadra step raised KeyError on _ok_reason, so no receipt was written. Fixed with r.pop('_ok_reason', '') plus a catch-all in main() that writes a FAIL receipt; added a test over the four steps that pre-seeds a stale receipt.
