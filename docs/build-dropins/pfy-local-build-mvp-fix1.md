# pfy local build MVP, fix round 1 (gate FAIL at e63a95b2)

Context: branch bot/mvp-local-build at e63a95b2 failed Tester and Reviewer. Work on this same branch with new commits on top. No rebase, no force-push, no PR. First run `git merge origin/main` (main moved to 2f2b20e, catalog-only), resolve nothing by hand beyond trivial conflicts, then fix. Do not touch the main checkout of pfy-mentat, never push, never use /tmp (use this worktree's tmp/). No em dashes anywhere in docs or code comments. Never print secrets.

Verdict evidence is on the box, not nimo; the findings are quoted below so you do not need it.

## Blockers to fix (all must be closed with a test that fails without the fix)

B1 Test-gate cheating. Default --protect is none and the gate only compares test counts. A model that rewrites tests with assertTrue(True) gets PASS and a commit. Fix: by default hash every test file present at base (and the test command's own config) and FAIL if any is modified, deleted or newly skipped, unless the task explicitly lists writable test paths. Count skipped/xfail as not passing (judge_tests must treat a new skip as FAIL). Fix `_protected` (about lines 501-513): `lstrip("./")` strips leading dots so `.github/*` never matches and `./tests/...` never matches; normalise paths with os.path.normpath / removeprefix("./") and match with fnmatch on the normalised relative path. Give the 5 eval tasks with protect [] real protect lists. Add a stub-agent test that rewrites asserts to assertTrue(True) and must now score FAIL on t01, t04, t08; add a test that adding @unittest.skip to the failing test is FAIL.

B2 Orphans. `_kill_group` and `run_bounded` return early when the group leader has exited, leaving children (TERM-ignoring child, background child, TERM-ignoring grandchild). Fix: always signal the whole process group (TERM, short grace, then SIGKILL) regardless of leader state, also after normal agent exit and after test timeouts; the run must not block 70s when the agent exits leaving a background child. SIGKILL of the runner itself cannot be handled, so: write a pid/pgid file at start and have the next run (and `pfy build --local --reap`) kill stale groups and unload the model; document it, and write a minimal "ABORTED" receipt on the next start for any run dir with no receipt. Tests for all four orphan cases.

B3 CI red on ubuntu-latest. tests.test_pfy_build_local.CloudBuildUnchangedTests.test_help_and_dry_run_stay_the_same needs `grok` on PATH and a host-specific golden (argparse help differs on py3.12 vs 3.13). Fix: skip when grok is missing, drop the host-specific golden (assert on stable substrings and exit codes instead), and make sure it writes no receipts under pipelines/dogfood/build/. Run the suite under both python3.12 and python3.13 if available.

B4 Confinement is a denylist over an allowed bash tool. Proven escapes with real opencode 1.18.31: `git -c k=v push`, `/usr/bin/git push`, `sh -c 'git push ...'`, `env git push`, python subprocess push, and python open() writing into the main checkout, all ending PASS + commit. curl via bash is allowed. Fix with real confinement, not more globs:
 1. Run the agent under bubblewrap (bwrap) when available: read-only bind of the filesystem, read-write bind of only the worktree (and its tmp), --unshare-net except loopback access to the local Ollama (use --share-net only if loopback-to-Ollama cannot otherwise work, and then ALSO do 2 and 3), main checkout and ~/.ssh, ~/.config/gh, ~/.grok not mounted. If bwrap is unavailable, REFUSE to run (exit BLOCKED) unless `--unsafe-no-sandbox` is passed, and record the sandbox mode in the receipt.
 2. In the worktree, remove all remotes and set `remote.origin.pushurl` to an invalid value, set `core.hooksPath` to an empty dir, and unset credential helpers for the run.
 3. Keep the opencode permission config as defence in depth but stop treating it as the boundary.
 Add black-box tests that run the five push forms and the python-open-into-main escape through the real sandbox wrapper (use a bare local remote and a scratch "main" dir under tmp/) and assert nothing leaks. If bwrap is not usable on nimo (check `bwrap --version` and try a trivial run; nimo may restrict unprivileged user namespaces), say so loudly in the handoff and implement the best alternative that works without sudo (for example a separate Linux user is not available, so consider running with a minimal env, `unshare -Urn` if permitted, or a landlock-based wrapper); do not claim confinement you did not demonstrate.

## Should-fix (do these too, they are cheap)
- Redaction misses `password: x` (about lines 100-110): extend patterns and test.
- Stop appending to main repo .git/info/exclude (about lines 536-555); use the worktree's own info/exclude only.
- Do not leave lock file and .home in tmp/ after a run.
- B5 busy-host guard fails open when /api/ps returns 500 or errors: fail closed (BLOCKED) with a test.
- F4 `pfy eval-local-build` must exit non-zero when pass < total.
- Make the no-model exit code consistent (BLOCKED code) and document it.
- Fix the assertion near tests/test_pfy_local_build_eval.py:233 that asserts nothing if its condition is false; add tests for the permission config, the memory watchdog, the leader-dead orphan, dotfile protect, and skip-gaming.
- Optionally rerun a failing-then-passing test once to detect flaky tests before committing (a single pass that fails on a second run is FAIL), if cheap.
- Handoff docs/ops/HANDOFF-pfy-local-build-mvp.md: list known gaps honestly (confinement limits, SIGKILL, egress control, the ubuntu CI history) and the live 8/8 caveat: the 8/8 was scored before B1 was fixed, so rerun the live eval on qwen3.6:35b after the fixes and record the receipts (commit the summary receipt under docs/ or eval/, not just tmp/).

## Done means
- All new tests fail on the old code and pass on the new (show mutant evidence: remove the fix, test goes red).
- Full suite green under python3.12 and 3.13 as far as the box allows, except failures that already exist on main (test_hedge detector, test_lab_stage x2 when ollama is down); list them.
- Live eval rerun on nimo with the local model, receipts summarised in the handoff, with the stub-cheater scoring 0.
- ./pfy and scripts/pfy stay mode 100755, cloud `./pfy build` unchanged, no GUI/catalog/runtime changes.
- Append a RUN-LOG entry, push the branch (git push origin <branch>) and report the new head SHA. Do not merge to main.
