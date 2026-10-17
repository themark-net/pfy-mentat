# Autonomous decisions 2026-10-16

- PR #298 (X intake 122-124): fixed Tester FAIL B1 at 5a68459. smoke_122_124.py watches the real ~/.llm-router, ~/.local/state/squadra and ~/.cache/squadra in a finally (FAIL on change, also on timeout); harnessrouter refuses a pre-existing pfy-hr-smoke container/volume, keeps the first failure reason, always runs volume rm, WARNs on $HR_IMAGE; added tests/test_x_intake_smoke_122_124.py. Pushed to the same branch, not merged.
