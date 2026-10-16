# Autonomous decisions 2026-10-15

- PR #296 (X intake 119-121): fixed Tester FAIL B1 at 6d6962b. smoke_119_121.py now checks the real HOME (~/.agentdescent, ~/.tsa, ~/.cache/tree-sitter-analyzer, ~/.local/state/kenfold, ~/.cache/kenfold) in a finally that also runs on timeout, keeps partial checks, stops a down timeout overwriting the failure reason, pins Kenfold to commit dfc18f9f; added tests/test_x_intake_smoke_119_121.py and fixed Entry 119's risk-table claim. Pushed to the same branch, not merged.
