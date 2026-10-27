# Gate notes for fix round 2 (Reviewer FAIL at 42fcc229)

Reviewer holds only on these two; both overlap fix2 blockers 3 and 1.
- R1 (same as fix2 item 3): run_tests (scripts/pfy_build_local.py ~577-604, callers ~1976, ~2052, ~2064) runs agent-written code on the host outside bwrap while the receipt says bwrap-unshare-net. A stub that writes src/__init__.py got PASS plus commit, and during the test run it wrote into the main checkout, created a branch in the main repo, pushed to the bare origin and connected to 1.1.1.1:53. Run the test command in the same bwrap profile and add a test that a src/__init__.py side effect cannot touch main, refs or network. List this nowhere as a "known gap"; it must be closed.
- R2 (tip CI red): eval-structural ubuntu job fails at step "pfylib toolset x harness + hedge" (full unittest discover, exit 1) while nimo is green and main was green. Fixing the SIGTERM race may not be the whole cause. Find every test that fails on ubuntu-latest but not on nimo (missing grok on PATH, TMPDIR, /run/user, bwrap not installed or unprivileged userns disabled on GitHub runners, python version). Tests that need bwrap must skip with a clear reason when bwrap is unusable. Pre-existing failures on main (test_hedge detector, test_lab_stage x2, test_local_bench relative outdir when ollama is down) must be skipped honestly or not hit on CI. After pushing, trigger eval-structural.yml on the branch (user-GitHub actions_run_trigger is not available on nimo; instead run `gh run list` if gh exists, otherwise just state the tip must be re-run by the caller) and report the failing test names you could reproduce.

Follow-ups worth doing in the same round if cheap:
- A test that pins --die-with-parent (mutant removing it currently survives), and verify the agent dies after a runner SIGKILL.
- --reap must write ABORTED receipts under a custom --receipt-dir too.
- Handoff Status section is stale (says item 4, base 7b716e8, 842 tests, Python 3.13 absent): update it.
- Sandbox needs XDG_RUNTIME_DIR or /run/user/UID else BLOCKED; make the BLOCKED reason say so and consider a fallback runtime dir under the worktree tmp/ (not /tmp).
- Hash sitecustomize.py and conftest.py (already in fix2 item 2); product code that patches unittest.TestCase (src/__init__.py) is a documented known gap unless the gate runs the tests from a pristine copy of the test files and a clean interpreter flag (-I and -S where possible); do what is cheap, document the rest.
- Commit the raw live receipt summary and note that raw receipts are gitignored.

## Tester addendum (no new blockers)
- CI root cause confirmed: test_sigterm_interrupts_and_releases_the_lock sends SIGTERM when the pfy-agent-started marker appears (tests ~448-457, ~575-598), possibly before the stub writes orphan-child.pid (stub ~72, ~96-106). Wait for BOTH pid files before sending SIGTERM.
- Test gap: stripping the push remote (pushurl config and GIT_CONFIG_VALUE_0) leaves all 63 tests green. Add a test that a push from the agent phase fails because the remote is blocked.
- With no XDG_RUNTIME_DIR and no /run/user/UID, 36 of 63 tests fail with BLOCKED no-sandbox. Make the tests provision a short runtime dir (under the worktree tmp/, not /tmp) or skip. BLOCKED message must name the cause (bwrap missing vs no runtime dir).
- Redaction gaps: passwd=, Authorization: Basic ..., AKIA key ids, PEM private key blocks. --unsafe-no-sandbox must print a stderr warning.
- Py3.12 and 3.13 pass with an external TMPDIR; the TMPDIR failures are environment-only, document that.
