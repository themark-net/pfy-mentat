# Autonomous decisions: pfy-local-build fix round 1 (2026-10-26)

Format: choice | alternatives | why

Worktree `tmp/mvp-local-build`, branch `bot/mvp-local-build`. The drop-in said decide and record. No question was sent.

## D1: One worktree, lead implements

Choice: edit B1 through B4 in this worktree, serially. | Alternative: one worktree or subagent per blocker. | All four blockers share `scripts/pfy_build_local.py`. Parallel editors would collide. The launch forbids any other checkout and forbids touching `~/DEVELOP/pfy-mentat`.

## D2: Bubblewrap plus a loopback bridge

Choice: when bwrap works, run the agent under it. Loopback Ollama is reached by an AF_UNIX socket that a host thread splices to TCP. `--share-net` is used only when the endpoint is not loopback, and the git lockdown still applies. Missing bwrap is `BLOCKED` `no-sandbox` (exit 4) unless `--unsafe-no-sandbox`. That flag does not turn off a working bwrap. | Alternatives: more bash globs; `unshare -Urn` as the only boundary; a second Linux user (not available without sudo); landlock. | The gate showed the permission denylist does not stop `git -c`, `/usr/bin/git`, `sh -c`, `env git`, or `python` `open()`. bwrap 0.11.1 works on this box. The black-box tests ran here and did not skip.

## D3: Short socket path, inode stays in the worktree

Choice: the socket inode is `worktree/tmp/ollama.sock`. `bind` and `connect` use a symlink `pfy-lb-<pid>-<stamp>` under `XDG_RUNTIME_DIR` or `/run/user/$UID`, because `sun_path` is 108 bytes and this worktree path is longer. The symlink is removed when the sandbox closes. Broken `pfy-lb-*` links are swept. `/run` stays a read-only bind so the agent cannot replace the link. | Alternative: put the socket in `/tmp`. | The drop-in forbids `/tmp`. The short name is a kernel limit, not a scratch directory.

## D4: Listener is a daemon thread, not a fork

Choice: the entry script starts `serve()` on a daemon thread, waits until the port is bound, then `subprocess.call`s the agent and exits with that code. | Alternative: `os.fork` a listener and `os.execvp` the agent. | The fork left a child that kept bwrap alive after the HTTP response, then got reparented to the user systemd when bwrap was killed. Daemon threads die with the wrapper, so bwrap exits.

## D5: Do not edit the caller's git config

Choice: while the agent runs, a linked worktree's `.git` file points at `worktree/tmp/git-sandbox`. That dir is seeded with `git add -A -- . :!tmp` and an empty commit only after `rev-parse --absolute-git-dir` shows the sandbox. No remotes. `pushurl` is `file:///pfy-local-build-push-blocked`. `core.hooksPath` is an empty directory. `credential.helper` is empty. The original `.git` bytes are restored before the real commit. `GIT_CONFIG_NOSYSTEM`, `GIT_CONFIG_GLOBAL`, and `GIT_CONFIG_KEY_*` are on the agent env only. If `.git` is not a file, the swap is skipped and the read-only filesystem is the boundary. | Alternative: edit the common git config of the parent repo. | That would change the operator's remotes and credential helper.

## D6: Ancestor hides keep a mount path

Choice: if a hidden directory is an ancestor of the worktree, pass `--tmpfs` for it and `--dir` for each component from that ancestor through the worktree, then `--bind` the worktree. | Alternative: `--tmpfs` the ancestor and hope the bind still lands. | bwrap will not bind onto a path a parent tmpfs removed.

## D7: Opencode home is under the worktree and is deleted

Choice: `HOME` is `worktree/tmp/opencode.home` plus `/home`, so the old "parent name ends with .home" check still holds. `finish()` deletes that directory, the lock, and the pid file even when the worktree is kept. On PASS the worktree goes first. `opencode.json` is copied into the receipt dir before the home is deleted. | Alternative: a home under the real `~` or under `/tmp`. | Both are forbidden. A leftover home after a run was a should-fix.

## D8: Hash only after the count and skip judge

Choice: an explicit `--protect` hit is `protected-path-changed` before tests. Then `judge_tests`: a new skip or xfail is `tests-failed`, a lower count is `tests-regressed`. The content hash runs only when that judge returns nothing, and a mismatch is `tests-tampered`. `--writable-test` globs are excluded from the hash. | Alternative: hash first, so a skip that also rewrites the file is reported as tamper. | The drop-in asks for both gates. The judge names the skip. The hash catches a rewrite that keeps the count, which is what `assertTrue(True)` does. A skip-gaming test passes `--writable-test tests/*` so the hash cannot be the thing that fails it.

## D9: Reap is conservative

Choice: the pid file records the runner pid, its group, and the agent group. The next lock holder and `--reap` kill a dead pid's group only. A live recorded pid is left alone, because the pid may have been recycled, and the pid file is still removed. The model is unloaded only when `loaded_by_run` is set. ABORTED receipts are written for `build-local` directories that have no `receipt.json`. Reap runs after the lock is held and before the new receipt directory is created. `--reap` with no task exits 0. `--reap` while the lock is held returns `BLOCKED` `another run` (exit 4). | Alternative: kill every recorded pid, including a live one. | A recycled pid could be an unrelated process.

## D10: Exit codes

Choice: no-model is `BLOCKED` exit 4. no-opencode stays exit 2. Eval exit 0 only when every scored task passed or the run is a named skip. Eval exit 1 when pass is below passed+failed+blocked, or the runner broke. Eval exit 2 when `--require-live` and a skip fired. | Alternative: keep no-model at exit 2 and eval exit 0 on a low pass rate. | The drop-in says both of those were wrong. The old handoff's exit-0 eval contract is superseded.

## D11: CI without bwrap stays green without weakening this box

Choice: behavior tests append `--unsafe-no-sandbox` only when `bwrap_works()` is false in the test process. `SandboxEscapeTests` call `skipTest` only in that same case. Eval forwards the flag only when `PFY_LOCAL_BUILD_UNSAFE_NO_SANDBOX=1`. The product never auto-selects unsafe mode. | Alternative: always pass the unsafe flag, or apt-install bwrap in CI. | This box has bwrap, so the escape tests run. Ubuntu without bwrap must not become a new red, and the product must still refuse a real run.

## D12: Interpreters

Choice: run the suite on system Python 3.14.4 and on `~/.local/share/uv/python/cpython-3.12.12-linux-x86_64-gnu/bin/python3.12`. Do not install Python 3.13. | Alternative: apt-install 3.13. | The drop-in says as far as the box allows, and this session must not install system packages.

## D13: Live load waits for a green suite and a quiet host

Choice: load `qwen3.6:35b` only after the suites are acceptable and `MemAvailable+SwapFree` is at least 32 GiB and `ollama ps` is empty. Do not unload a model this run did not load. The stamp `20261026T072940388555Z` (8/8) was scored before B1 and is not reused. The stub cheater is the offline test, not a live model. | Alternative: quote the old 8/8 as the post-fix rate. | The drop-in says that number is stale.

## D14: Ship path

Choice: new commits on `bot/mvp-local-build`, then `git push origin HEAD:bot/mvp-local-build`. | Alternative: a bare `git push` or a PR. | The branch tracks `origin/main`, so a bare push can update main. No PR. No merge to main. No rebase. No force-push.

## D15: Bridge timeout is the handshake only

Choice: `create_connection(..., timeout=3)` then `settimeout(None)` before splicing. A regression test sleeps 4 seconds before the upstream writes a body. | Alternative: raise the timeout to a few minutes and leave it on the socket. | A model load sends no bytes for longer than 3 seconds. The first live rerun (`20261027T030049105086Z`) failed three tasks at about 83 seconds with `Cannot connect to API` and an empty `ollama ps`. After the clear, a sandboxed `opencode run` returned `pong`.

# Fix round 2 (2026-10-27)

Tester FAIL at `42fcc229`. Reviewer notes in `docs/ops/GATE-NOTES-fix2.md` are included. Same worktree and branch. No question was sent.

## D16: One lead, same files

Choice: implement blockers 1 through 6 in this worktree, serially. | Alternative: one subagent per blocker. | All six share `scripts/pfy_build_local.py` and `tests/test_pfy_build_local.py`. Parallel editors would collide. The launch forbids any other checkout.

## D17: The test gate uses the agent profile with no Ollama bridge

Choice: `tests_before`, `tests_after`, the repeat run, and the archive recheck call `prepare_sandbox(..., endpoint=None)`. That is `--unshare-net`, a read-only root, no push remote, and a scrubbed env. The agent still gets the loopback splice. | Alternative: a second, weaker profile for tests, or leave tests on the host. | GATE-NOTES R1 showed `src/__init__.py` writing the main checkout, creating a branch, pushing, and opening TCP during the gate. The receipt said `bwrap-unshare-net` while the tests were not in bwrap.

## D18: Pid, ipc, and uts on every sandbox

Choice: after `--unshare-net` or `--share-net`, always add `--unshare-pid`, `--unshare-ipc`, and `--unshare-uts`. `--die-with-parent` stays the second bwrap argument. `bwrap_works()` probes those flags. Liveness of a daemon is a heartbeat file inside the worktree, not `kill` of a namespace pid. `tearDown` SIGKILLs only processes whose cmdline contains that case's tmp path, and never pid 1. | Alternative: `killpg` only, or host-kill the pid printed inside the namespace. | `setsid` and a double fork survive `killpg`. A namespace pid is not a host pid. Signalling it can hit an unrelated host process.

## D19: No summary is a failed gate

Choice: `judge_tests` returns `tests-failed` when the command did not start, the exit is not 0, or either side has no counts. A higher skip, xfail, deselect, error, or failed count is `tests-failed`. A lower passed or ran count is `tests-regressed`. Unittest, a pytest summary line, and junit xml are the parsers. There is no `None` fallthrough on exit 0. | Alternative: keep treating an unknown runner as a pass. | That is how `os._exit(0)`, a conftest that exits 0, and `pytest -q` without a summary became PASS. Pytest is not installed for the default Python here. The deselect proof is `tools/fake_pytest.py` plus the parser. Nothing was apt-installed.

## D20: Gate filenames are hashed wherever they appear

Choice: hash `conftest.py`, `pytest.ini`, `tox.ini`, `setup.cfg`, `pyproject.toml`, `sitecustomize.py`, `usercustomize.py`, `.gitignore`, and `.gitattributes`, including files the agent creates. A change or a new file is `tests-tampered` after the count judge. | Alternative: hash only paths that existed before the run, or only the repo root. | A new `conftest.py` was outside `snapshot_tests`. Unittest does not load `conftest.py`, so the hash is what stops it. An eval task that also lists those names in `--protect` can still report `protected-path-changed` first. The product default has an empty protect list, so the hash is the gate that matters there.

## D21: Force-add, then recheck the commit

Choice: `git add -A -f` with path excludes for `tmp`, `__pycache__`, `*.pyc`, and `.pytest_cache`. The commit env is the scrubbed git env and does not carry the lockdown `GIT_CONFIG_*` values. Then `git archive` of that SHA is extracted under `<repo>/tmp/recheck-<sha12>` and the test command runs in the sandbox against `tests_before`. On failure, `git reset --hard HEAD~1` runs before the `local/<slug>-<stamp>` branch is created, and the reason is `commit-recheck-failed`. An interrupt during the recheck rolls back to `interrupted`. | Alternative: `git add -A` without `-f`, or trust the worktree tests. | A helper listed in `.gitignore` is skipped by `git add -A`. Removing `-f` on this box failed `test_ignored_helper_is_in_the_commit` with `commit-failed` (exit 1), not a silent PASS. The force add is what puts `src/helper.py` in the commit. The archive recheck is the second gate. Do not use `/tmp` for the recheck tree.

## D22: Rehash immediately before git add

Choice: take `tree_digest` right after the flaky judge, return if the agent had already timed out, then take a second digest. A mismatch is `worktree-changed-after-gate`. The digest ignores `tmp`, `.git`, `__pycache__`, `.pytest_cache`, names ending in `.home`, `*.pyc`, `*.pyo`, and paths under `tmp/`. | Alternative: only the namespace, or only a late test run. | The two hashes sit next to each other on purpose. `test_setsid_daemon_cannot_rewrite_after_the_gate` proves the namespace dies (the run finishes in under 20 seconds and the committed blob is the fix). A mutant that deletes only the second hash and keeps `--unshare-pid` still passes that test. Say that in the handoff.

## D23: Runtime dir reasons, and a short worktree socket only when XDG is unset

Choice: if `XDG_RUNTIME_DIR` is set and the path is under `/tmp` or `/var/tmp`, reason `runtime-dir-in-tmp`. If it is set but missing or not writable, reason `no-runtime-dir`, with no fallback. The same checks apply to `/run/user/$UID` when XDG is unset. The direct socket `worktree/tmp/ollama.sock` is used only when that fallback reason is `no-runtime-dir`, XDG is empty, and the path is shorter than 108 bytes. Otherwise a too-long symlink path is reason `socket-path`. | Alternative: always fall back to the worktree socket, or accept a runtime dir under `/tmp`. | The sandbox tmpfs-hides `/tmp`, so a socket there does not reach the host listener. An explicit bad XDG must not silently change paths. A typical fixture worktree socket is 109 bytes and must stay `no-runtime-dir`. The successful fallback test uses a short tree `tmp/s/w` (73 bytes). This box has `/run/user/1000`, so production runs still use the short symlink.

## D24: Resolve the test command on the host

Choice: if `argv[0]` is not an executable file and is not on `PATH`, record `started=False` before bwrap. | Alternative: let bwrap report the missing binary. | bwrap hides `FileNotFoundError`, so the reason became `tests-failed` instead of `test-cmd-failed-to-start`.

## D25: Reap writes the pid file's receipt dir

Choice: when the recorded pid is dead and `receipt_dir` has no `receipt.json`, write `ABORTED` / `no-receipt` there (create the directory if needed), then scan `pipelines/dogfood/build-local/`. | Alternative: scan only the default tree. | `test_sigkill_of_pfy_kills_the_sandbox_and_reap_writes_aborted` uses a receipt dir outside that tree.

## D26: R1 is closed by an `__init__.py` payload

Choice: the sandbox probe writes the side effect in `src/__init__.py` (TCP to the test listener and to `1.1.1.1:53`, write into a scratch main, `git push`, and branch `pwned`) and fixes `src/calc.py` so the tests can pass. The scratch main is under the test tmp, not `~/DEVELOP/pfy-mentat`. | Alternative: put the payload only in `calc.py`, or list R1 as a known gap. | GATE-NOTES says the side effect must be in `src/__init__.py` and must not be listed as a gap.

## D27: Assertion monkeypatch stays a gap

Choice: document that production code can still patch `unittest.TestCase` or `TestResult` from `src`. Close `os._exit(0)` and a new `sitecustomize.py`. Do not add `-I` or `-S` in this round. | Alternative: run the gate under `python -I -S` and a pristine copy of the tests. | That changes the default test command and can break imports. The drop-in says do what is cheap and document the rest.

## D28: Unsafe mode warns, and it also unsandboxes the gate

Choice: print `WARN: --unsafe-no-sandbox is on and bwrap is not usable, so this run is not sandboxed` once, only when the flag is set and `bwrap_works()` is false. A working bwrap still sandboxes the agent and the gate. Document that the flag also leaves `run_tests` unsandboxed. | Alternative: make the flag a no-op for the gate, or warn on every run. | The flag's meaning is "proceed without a sandbox when bwrap is missing". Hiding that the gate follows it would be a new hole. Tests that need bwrap already skip with a reason when it is unusable. `command()` adds the flag only when the test process's own `bwrap_works()` is false.

## D29: Redact the extra secret shapes

Choice: PEM blocks become `[redacted-private-key]` before the other substitutions. `PASSWD` joins the assignment pattern. `Authorization: Basic` and `AKIA` plus 16 alphanumerics are masked like the existing key pattern (length 4 or less becomes `***`, otherwise the first 4 characters plus `***`). | Alternative: drop the whole line. | The existing receipt tests assert the masked form.

## D30: Wait for both pid files before SIGTERM

Choice: `test_sigterm_interrupts_and_releases_the_lock` polls for `orphan-child.pid`, `orphan-parent.pid`, and both heartbeats, then sends SIGTERM. The same wait is used by the other orphan scenarios. | Alternative: sleep a fixed second. | Ubuntu CI failed because the marker arrives before the stub writes the pid file. A local mutant that signalled as soon as the marker appeared still passed here in 2.347 s: the stub won the race on this box. The red evidence is that CI quote plus the waiter. The waiter stays.

## D31: Do not rewrite the pre-existing suite failures

Choice: document them. Python 3.14.4: 916 tests, 612.110 s, failures=1, skipped=16. The failure is `test_relative_outdir_log_path_safe` because `TMPDIR` is `$PWD/tmp/scratch`, inside the repo. Python 3.12.12: 916 tests, 538.420 s, failures=21, skipped=16. Twenty are `tests.test_harness2_local_sandbox` (`FileNotFoundError` on the uv interpreter path, which lives under the home that sandbox hides). The twenty-first is the same outdir case. Python 3.13 is absent. Hedge and lab_stage did not fail (Ollama was up). The local module was 61 tests, OK, 70.965 s. The stub cheater is `EvalRunnerTests.test_cheat_asserts_scores_zero_on_t01_t04_t08` (the class is not `EvalTests`): 1 test, OK, 2.733 s, score 0. | Alternative: point `TMPDIR` at `/tmp`, or edit `tests/test_local_bench.py` and the harness sandbox. | `/tmp` is forbidden. Those failures are not in the fix-2 diff.

## D33: Quote only this run's 8/8

Choice: the fix-2 rate is stamp `20261027T070700973123Z`, eval exit 0, 8/8, 617.949 s, mean 77.244 s, `bwrap-unshare-net` on every task, context 262144 while loaded. t08 `unloaded` is true. | Alternative: reuse the fix-1 stamp `20261027T031008578576Z`. | That run did not have the pid namespace or the sandboxed gate.

## D32: Two small edits after the 61-test run

Choice: if the socket link is `None` (the direct-socket fallback), do not call `unlink` on it when `bind` fails. The module docstring says reap also writes the pid file's receipt dir. | Alternative: leave the `AttributeError` on that rare path. | The long-path test never takes the direct socket, so the bug was not hit. These two lines were not in the 61-test run. Re-run the runtime-dir and socket tests after the live eval, before the commit.
