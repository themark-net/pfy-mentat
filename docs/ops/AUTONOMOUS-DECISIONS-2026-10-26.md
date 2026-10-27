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
