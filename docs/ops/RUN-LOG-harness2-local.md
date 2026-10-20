# RUN-LOG harness2-local

Start: 2026-10-20T03:31:50-07:00
Worktree: `~/DEVELOP/pfy-mentat/tmp/h1-harness2`
Branch: `bot/h1-harness2`
HEAD at start: `aed526d080114f83fbd9ad329b4c9e5b62baf64c`
`origin/main`: `aed526d080114f83fbd9ad329b4c9e5b62baf64c` (equal; `git fetch origin` done)
Drop-in: `git diff origin/main -- docs/build-dropins/harness2-local.md` empty. **ALREADY-DONE** (no commit).
STOP file: absent.
Clock: no new item after 09:31 local. Stop by 11:01. Live item only if started by about 07:46.

## Host

- python3 3.14.4. No `/usr/bin/python3.12` or `python3.13`.
- `PY312` realpath: `/home/mark/.local/share/uv/python/cpython-3.12.12-linux-x86_64-gnu/bin/python3.12` (present, read-only).
- uv 0.9.26, node v22.23.0, npm 11.12.1, bwrap 0.11.1.
- `/etc/opencode` absent.
- merged-usr: `/bin`, `/sbin`, `/lib`, `/lib64`, `/lib32` resolve under `/usr`. `/usr/lib32` exists. `/var/run` → `/run`.
- `chmod -P` is present (uutils coreutils: "do not traverse any symbolic links (default)").
- MemAvailable at start: 65733240 kB (about 62.7 GiB). `ollama ps`: no model loaded.

## Baseline

`python3 -m unittest discover -s tests -t .` → Ran 459 tests in 139.175s, OK (skipped=4), exit 0.

`test_hedge.DetectorTests.test_detector_runs_offline` and `test_pfylib_tmp_cleanup` are not allow-listed. The suite exit was 0, and a direct run of `test_module_run_leaves_no_new_tmp_dirs` was ok. Anything new that fails is a real failure.

## Plan

Overview: Pin harness2 and OpenCode locally, run every OpenCode process in a one-port bwrap sandbox, drive the 48-case decision set through the upstream core loop, and land a proposal only on `bot/h2-proposal-*` when the held-out gate passes.

Phases:

- item 0 drop-in | `docs/build-dropins/harness2-local.md` | diff against origin/main empty | none | already done
- item 1 stage | `examples/harness2-local/env.sh`, `stage.sh`, `check.py`, `env.local.example`, `common.py`, `tests/test_harness2_local_stage.py` | `python3 -m unittest tests.test_harness2_local_stage` green, RED lines logged | item 0 | general
- item 2 sandbox | `examples/harness2-local/sandbox.py`, `sbun`, tests | sandbox behavior tests green and RED lines logged | item 1 | general
- item 2b fixes | sandbox, spec, README citation | one commit per sub-item, each with a failing mutant | item 2 | general
- item 3 adapter | `pfy_adapter.py`, `drive.py`, `split.v0.json`, tests | stub `drive.py --k 1` green | items 1-2 | general
- item 4 surface | `surface.py`, tests | map out and back, guardrail and path rejects | item 3 | general
- item 5 propose | `propose.py`, tests | bare-repo gate tests green, no merge | item 4 | general
- item 6 live | receipt under `pipelines/dogfood/harness2-local/` | honest receipt or a named BLOCKED gate | items 3-5 and clock | general
- item 7 docs | `examples/harness2-local/README.md`, drop-in README row, Entry 136 | docs match what landed | item 6 status | general
- item N nimo checks | run log only | each check PASS, FAIL, or BLOCKED with the command | as each item allows | general
- handoff | `docs/ops/HANDOFF-harness2-local-2026-10-19.md` | written on every exit | all | general

Risks:

- HOME writes during `uv` / `npm` / `bun` → stage stops with BLOCKED: home-write (D1 fingerprint).
- Unlisted network host during stage → stop that step and record the host.
- Live run starts after 07:46 → BLOCKED: no-time-for-live, items 1-5 still push.
- bwrap or user namespaces fail → exit 2, never unsandboxed.

## Items

### Item 0 — drop-in

state: ALREADY-DONE | tests: `git diff origin/main -- docs/build-dropins/harness2-local.md` empty | files: 0 | err: none

### Item 1 — pinned local stage

state: DONE | tests: `python3 -m unittest tests.test_harness2_local_stage` → Ran 8 tests in 132.068s, OK (exit 0), after the check.py re-exec fix | files: examples/harness2-local/{env.sh,stage.sh,check.py,common.py,env.local.example}, tests/test_harness2_local_stage.py | err: first real stage attempt exited 2 (`cannot import OpencodeSubstrate: No module named 'harness2'`); fixed by re-exec into the venv Python 3.12 plus `site.addsitedir` for the editable `.pth`. Second run: `stage: ok`.

RED: unset `npm_config_cache` in env.sh → `test_stub_tools_see_state_caches_and_home_stays` (`git npm_config_cache=None`). Restored.
RED: `version_output_ok` requires `1.14.18` only → `test_stub_stage_exits_0_without_preflight_module_or_harness2_check` (`check: opencode --version printed 'local'`). Restored. The source run prints `local`; bare `bun --version` prints `1.3.11` and is only required to exit 0.
RED: drop the vertex value guard → `test_vertex_model_exits_2` (exit 0, `check: ok`). Restored.

Real stage (2026-10-20, `$W/tmp/state/stage-rerun.log`, exit 0):

- harness2 `git rev-parse HEAD` = `1cfe254e8d25b15f37048c3730134686abe60335`
- OpenCode `git rev-parse HEAD` = `23fb5e0516c99ac04a1aa46c193efda2e1b9bb24`; `packages/opencode/package.json` `"version": "1.14.18"`; `@ai-sdk/openai-compatible` `2.0.41`; `src/provider/provider.ts:101` lists it in `BUNDLED_PROVIDERS` (`createOpenAICompatible`). No provider package is fetched at run time.
- `check.py`: `check: ok`. `/etc/opencode` absent (re-checked).
- `.env`: first run logged `env: written from env.local.example`. Re-run logged `env: kept existing .env`.
- HOME fingerprint: `tmp/state/home.diff` is 0 bytes after the re-run. No BLOCKED: home-write.
- uv log: `Resolved 1 package in 1ms`, built harness2 0.1.0 from the local tree. No PyPI URL in the stage log. `UV_PYTHON_DOWNLOADS=never`. No `releases.astral.sh`.
- Hosts named in the stage log: `https://github.com/google-research/harness2`, `https://github.com/anomalyco/opencode.git`. `npm install bun@1.3.11` and `bun install --frozen-lockfile` are the registry.npmjs.org step (npm printed "added 5 packages" on the first run, "up to date" on the re-run; bun "Checked 2419 installs"). A `/proc/net/tcp` sampler wrote `tmp/state/hosts-seen.txt` with unrelated LAN and public sockets. That file is not the stage process tree and is not allow-list evidence.
- `$W/tmp/state` path length on this host: 55 bytes (the drop-in said 65). `$W/tmp/state/r/<name>` still fits `sun_path` (107).
- Node warning only: `NO_COLOR` ignored because `FORCE_COLOR` is set.

### Item 2 — sandbox

state: DONE | commit: `96408480a0fcfa29e6bff0963aa6f7ff58c313e6` | tests: `python3 -m unittest tests.test_harness2_local_sandbox` → Ran 26 tests in 46.054s, OK | files: `examples/harness2-local/sandbox.py`, `examples/harness2-local/sbun`, `tests/test_harness2_local_sandbox.py`, D7 sentence in `docs/build-dropins/harness2-local.md` | err: none

Real OpenCode at the pin, through the sandbox, against a stub server: one `POST /v1/chat/completions` with `model=qwen3.6-35b`, relay log `temperature: 0` and `seed: 230`, no `PLANT-CANARY`. A host plant at `$RUNS/opencode.json` then exits 2 `BLOCKED: opencode-plant` before the child, with no later POST.

`config.BUN` is `examples/harness2-local/sbun` as a `pathlib.Path`. `OpencodeSubstrate().preflight()` passes that way. The sbun stdin test leaves the parent pipe open (`communicate()` closes stdin, and the first RED missed because of that).

RED (each mutant restored; the suite above is the restored tree):

- canary control binds of `canary.txt` and `.ssh` → `test_canary_home_is_unreadable` (token read twice, child rc 0)
- bind the worktree instead of `$W/tmp/harness2` → `test_answer_files_and_id_map_are_absent_inside` (cases file visible)
- write the id map into `$W/tmp/state` → same test (map visible)
- skip the socket preflight → `test_socket_in_runs_blocks_before_child` (child rc 0)
- unpruned `find` on every mount → `test_unreadable_dir_and_clean_etc_layout` (`BLOCKED: sandbox-socket rc=1 mount=/usr`)
- prune every mount without the owner rule → `test_owned_000_blocks_then_recovers` (launch rc 0)
- allow sockets anywhere under state → `test_socket_outside_state_r_blocks` (launch rc 0)
- remove the plant walk → `test_host_plants_block_and_shell_cannot_plant_runs` (launch rc 0)
- walk the host view → `test_nimo_shaped_home_hides_host_agents` (`BLOCKED: opencode-plant .../wt/.opencode`)
- remove the workspace sweep → `test_sweep_lets_the_next_call_run` (mode stays `000`)
- remove the preflight cap → `test_preflight_cap_records_the_stub_before_the_next_launch` (error at the test's 20s timeout)
- match `OPENCODE_` as a prefix → `test_env_allow_list_drops_secrets_and_open_code_overrides` (`OPENCODE_CONFIG_DIR` arrives)
- remove the relay watchdog → `test_relay_kill_ends_the_call_and_the_next_call_runs` (call did not end)
- bind state read-write → `test_writes_outside_workspace_are_erofs` (write to `opencode.json` succeeds)
- drop `</dev/null` from sbun → `test_sbun_closes_stdin` (blocked on the open pipe)
- bind the runs parent during training → `test_heldout_runs_are_not_visible_to_training` (`seen` is `yes`)
- drop `/run` tmpfs and `--hide-dir` → `test_hidden_unix_sockets_and_live_paths` (preflight blocks the stub socket; the child does not start)
- relay ignores `--allow` → `test_allow_list_forwards_only_A` (B returns 200)
- drop `--unshare-net` → same test (C opens, and `1.1.1.1:443` opens)
- `--setenv X 1` on the real call only → `test_preflight_and_real_bwrap_argv_match` (argv prefixes differ)
- fake HOME under the state bind → `test_canary_home_is_unreadable` (token read twice). A first try was invalid: the stand-in `~/.opencode` was visible and the plant check blocked before the read.
- launch the next call before the cap-stub check → PASS-BY-ACCIDENT. The record is a regular file in the same workspace, and the sweep deletes sockets only, so the reversed order still passed. The test keeps the check before the next launch.

Re-read at the OpenCode pin: `packages/opencode/src/config/managed.ts:30` returns `/etc/opencode` on Linux; `managedConfigDir()` at line 35 uses `OPENCODE_TEST_MANAGED_CONFIG_DIR` or that path. `config.ts:619-623` merges `opencode.json` and `opencode.jsonc` from that directory. The spec citation is item 2b.6.

### Item N checks recorded with item 2

N1 PASS. Command: `python3 /tmp/h2-nimo.py` (real harness, real runs, real state, real `PY312`, real HOME). Child `test -e` was false for `$W/AGENTS.md`, `$W/.opencode`, the founder checkout `AGENTS.md`, `~/.opencode`, `~/.config/opencode`, `/etc/opencode`, and the cases file. Walk inside, then `PREFLIGHT_OK`: `$RUNS/tmp`, `$RUNS`, `$W/tmp`, `$W`, `.../tmp`, `.../DEVELOP`, `/home/mark`, `/home`, `/`, then `/etc/opencode`, `/home/mark/.opencode`, `/home/mark/.config/opencode`. Planted `$RUNS/tmp/AGENTS.md` → exit 2 `BLOCKED: opencode-plant` naming that path, marker absent. Plant removed.

N2 PASS. `bwrap --version` is `bubblewrap 0.11.1`. Captured argv (preflight and the real call, same flags): `--ro-bind /usr /usr`, symlinks for `/bin` `/sbin` `/lib` `/lib64` and `/lib32` (`/usr/lib32` exists), `--ro-bind /etc /etc`, `--tmpfs /home/mark`, read-only `PY312` (`cpython-3.12.12-linux-x86_64-gnu`), read-only harness, read-only runs, writable workspace, read-only state, `--tmpfs /tmp`, `--tmpfs /run`, `--dev /dev`, `--proc /proc`, `--unshare-net`, `--unshare-pid`, `--die-with-parent`. Relay socket `$W/tmp/state/r/s` was a socket inside the child (`SOCK yes`). Child stderr was empty: no AppArmor denial text. `dmesg` was not used.

N5 PASS. The same find the preflight uses, inside the real sandbox, total 1.151s (outer call 3.79s). Slowest mounts: harness 0.405s, `/usr` 0.400s, state 0.302s (the one allowed relay socket). Every mount rc 0. No socket outside `$W/tmp/state/r/`. The 120s cap fits. It is not raised.

N3, the held-out half of N4, and N6 wait for items 3 and 6. Layout half of N4, recorded now: `PY312` realpath is the cpython-3.12.12 root above; `/usr/lib32` exists; `/var/run` is a symlink to `/run`.

### Item 2b — should-fixes

2b.1 DONE. Commit `da6d56a9ea711b3825ba406ca5f49cabe326b55d`. Sweeps list `$RUNS/tmp` with `os.scandir` and `os.lstat` and touch only real directories. Symlinks and other non-directories are skipped and logged. Commands stay `chmod -R -P u+rwX -- <ws>` and `find -P <ws> -xdev -type s -delete`. `chmod --version` is `chmod (uutils coreutils) 0.10.0`; `-P` is accepted ("do not traverse any symbolic links (default)").

Test: `python3 -m unittest tests.test_harness2_local_sandbox` → Ran 27 tests in 45.204s, OK. The new case is `test_sweep_skips_symlinks_and_leaves_the_target`: a symlink under `$RUNS/tmp` and one inside a finished workspace and the live workspace all point at a host-only dir (mode 600 file, mode 700 subdir, a unix socket). After both sweeps the target modes, contents, and socket are unchanged, the real workspace is swept, the log names the skipped symlink and the skipped regular file, and the chmod/find argv record does not name the symlink.

RED: `find -P` → `find -L` in `_sweep_one` → `test_sweep_skips_symlinks_and_leaves_the_target` FAILED (`sock_path.exists()` is false). Restored. Green again inside the same script (rc 0).

RED: drop the lstat skip → same test FAILED. The argv record contained the symlink path and `note.txt`. Target modes were unchanged because the commands were still `-P`. Restored.

PASS-BY-ACCIDENT: `chmod -R -P` → `chmod -R -L` → same test stayed green (rc 0). uutils 0.10.0 does not follow a directory symlink. Not treated as a red. See D8.

2b.2 through 2b.6: pending. 2b.3, 2b.4, and 2b.5 were already proven in the item 2 RED list (`--setenv X 1`, cap-stub order, `OPENCODE_TEST_MANAGED_CONFIG_DIR`). They will be logged ALREADY-DONE when that pass is written. No extra commit unless a gap shows up.

### Item 3 — adapter

state: pending

### Item 4 — surface

state: pending

### Item 5 — propose

state: pending

### Item 6 — live

state: pending

### Item 7 — docs

state: pending

### Item N — nimo-only

state: pending
