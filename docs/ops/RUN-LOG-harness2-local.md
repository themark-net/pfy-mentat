# RUN-LOG harness2-local

Start: 2026-10-20T03:31:50-07:00
Worktree: `~/DEVELOP/pfy-mentat/tmp/h1-harness2`
Branch: `bot/h1-harness2`
HEAD at start: `aed526d080114f83fbd9ad329b4c9e5b62baf64c`
`origin/main`: `aed526d080114f83fbd9ad329b4c9e5b62baf64c` (equal; `git fetch origin` done)
Drop-in: `git diff origin/main -- docs/build-dropins/harness2-local.md` empty. **ALREADY-DONE** (no commit).
STOP file: absent.
Clock (first session): no new item after 09:31 local. Stop by 11:01. Live item only if started by about 07:46.

## Resume (H1b)

START: 2026-10-20T11:21:42-07:00
HEAD: `902e04f47eaf7c7083b80062235a056c63352f63` (equals `origin/bot/h1-harness2`). Not rewritten.
`git status --short` at resume: `M docs/ops/RUN-LOG-harness2-local.md`, untracked `examples/harness2-local/{cases.py,leaks.py,split.v0.json}`, `tests/test_harness2_local_cases.py`.
STOP file: absent.
This session's clock (replaces 09:31 / 11:01): no new item after 2026-10-20T17:21:42-07:00. Stop by 2026-10-20T18:51:42-07:00. Live item 6 starts only if begun by 2026-10-20T15:36:42-07:00.
Suite on the current tree: `python3 -m unittest discover -s tests -t .` → Ran 498 tests in 337.619s, OK (skipped=4), exit 0. The 498 include the uncommitted `test_harness2_local_cases` (3). Nothing else is red. Not BLOCKED: red-base.
At resume, item 3 attempt 1 was in progress (not a failure). It finished in this session. See Item 3.

## Resume (H1c)

START: 2026-10-20T12:23:06-07:00
HEAD: `e240d5b47024f5102ba0c6939f3fc9e9472434ce` (equals `origin/bot/h1-harness2`). Not rewritten.
`git status --short` at resume: empty.
STOP file: absent. The H1b stop-file was removed before this session. That stop is not a failure and not a skip.
This session's clock (replaces the H1b limits): no new item after 2026-10-20T18:23:06-07:00. Stop by 2026-10-20T19:53:06-07:00. Live item 6 starts only if begun by 2026-10-20T16:38:06-07:00.
Suite on the current tree before item 2c edits: `python3 -m unittest discover -s tests -t .` → Ran 508 tests in 377.550s, OK (skipped=4), exit 0. Nothing else is red. Not BLOCKED: red-base.
Items 0-4 are DONE. Item 2c (Tester FAIL of `902e04f`) is first, then item 5.

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

### Item 0: drop-in

state: ALREADY-DONE | tests: `git diff origin/main -- docs/build-dropins/harness2-local.md` empty | files: 0 | err: none

### Item 1: pinned local stage

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

### Item 2: sandbox

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

### Item 2b: should-fixes

2b.1 DONE. Commit `da6d56a9ea711b3825ba406ca5f49cabe326b55d`. Sweeps list `$RUNS/tmp` with `os.scandir` and `os.lstat` and touch only real directories. Symlinks and other non-directories are skipped and logged. Commands stay `chmod -R -P u+rwX -- <ws>` and `find -P <ws> -xdev -type s -delete`. `chmod --version` is `chmod (uutils coreutils) 0.10.0`; `-P` is accepted ("do not traverse any symbolic links (default)").

Test: `python3 -m unittest tests.test_harness2_local_sandbox` → Ran 27 tests in 45.204s, OK. The new case is `test_sweep_skips_symlinks_and_leaves_the_target`: a symlink under `$RUNS/tmp` and one inside a finished workspace and the live workspace all point at a host-only dir (mode 600 file, mode 700 subdir, a unix socket). After both sweeps the target modes, contents, and socket are unchanged, the real workspace is swept, the log names the skipped symlink and the skipped regular file, and the chmod/find argv record does not name the symlink.

RED: `find -P` → `find -L` in `_sweep_one` → `test_sweep_skips_symlinks_and_leaves_the_target` FAILED (`sock_path.exists()` is false). Restored. Green again inside the same script (rc 0).

RED: drop the lstat skip → same test FAILED. The argv record contained the symlink path and `note.txt`. Target modes were unchanged because the commands were still `-P`. Restored.

PASS-BY-ACCIDENT: `chmod -R -P` → `chmod -R -L` → same test stayed green (rc 0). The fixture modes were 600 and 700, which `u+rwX` cannot change on any chmod. The cause was the fixture, not uutils. See D8 and D13.

2b.2 DONE. Commit `31c326743010d3e1fb11036f287d5ac0b65521bc`. Every sandboxed call takes an exclusive nonblocking `fcntl.flock` on `$W/tmp/host-only/call.lock` before the pre-launch sweep and holds it until the after-call sweep finishes (the fd stays open across that sweep; closing it releases the lock). A second call exits 2 `BLOCKED: call in progress` and does not start a child. `drive.py` does not exist yet. Item 3 will run executors and editors through this same sandbox path, so the lock is the concurrency gate, and the upstream arguments recorded then are `propose_workers=1` and `rollout_workers=1`.

Test: `python3 -m unittest tests.test_harness2_local_sandbox` → Ran 28 tests in 51.530s, OK. `test_second_call_is_blocked_until_the_first_finishes`: A sleeps 5s inside the sandbox against a stub server; B, with its own state dir, exits 2 `BLOCKED: call in progress` within 1s, writes no marker, and adds no POST. A then exits 0 with one POST. C after A exits 0 with a second POST.

RED: `_acquire_call_lock` opens the file and does not flock → `test_second_call_is_blocked_until_the_first_finishes` FAILED (`0 != 2`). B finished in 1.175s, so its child ran. Restored. Green again in the same script (6.836s, rc 0).

2b.3 ALREADY-DONE in item 2. `test_preflight_and_real_bwrap_argv_match` diffs the argv and env captured from the preflight and the real `Popen`, not the builder's return value. RED: `--setenv X 1` on the real call only → argv prefixes differ. No new commit.

2b.4 ALREADY-DONE in item 2. `test_preflight_cap_records_the_stub_before_the_next_launch` reads the stub `find` record right after the BLOCKED exit, then removes it. RED: launching the next call first stayed green (PASS-BY-ACCIDENT). The record is a regular file in that workspace, and the sweep deletes sockets only. The test keeps the check first. No new commit.

2b.5 ALREADY-DONE in item 2. `OPENCODE_TEST_MANAGED_CONFIG_DIR` is in the always-dropped set. `test_env_allow_list_drops_secrets_and_open_code_overrides` sets it and asserts it is absent, along with `OPENCODE_CONFIG_DIR`, `OPENCODE_CONFIG_CONTENT`, and `OPENCODE_FOO`. RED: matching `OPENCODE_` as a prefix → `OPENCODE_CONFIG_DIR` arrives. No new commit.

2b.6 DONE. Commit `931b2030846d892daa15c884013cc97695483cc6`. Re-read at the OpenCode pin `23fb5e05`: `packages/opencode/src/config/managed.ts:30` returns `/etc/opencode` on Linux. `managedConfigDir()` at line 35 returns `process.env.OPENCODE_TEST_MANAGED_CONFIG_DIR || systemManagedConfigDir()`. `packages/opencode/src/config/config.ts:619-623` merges `opencode.json` and `opencode.jsonc` from that directory when it exists. The drop-in now cites `managed.ts:30` next to `config.ts:619-623`. `examples/harness2-local/README.md` cites the same lines. No runtime mutant: this sub-item is the citation. The drop of `OPENCODE_TEST_MANAGED_CONFIG_DIR` stays covered by the 2b.5 env test.

### Item 3: adapter

state: DONE | tests: `python3 -m unittest tests.test_harness2_local_cases tests.test_harness2_local_drive` → Ran 8 tests in 62.360s, OK | files: cases, leaks, split, pfy_adapter, drive, sbun, both test modules | err: none | commit: `3260e0228cee5344578bfad2a26076ef43bb03ec`

Attempt 1 (the interrupted slice) finished. One commit on top of `902e04f`. The driver runs the upstream chain through `recursion.run_parallel` with `propose_workers=1` and `rollout_workers=1`. Labels are `base1` and `agg1`. `H_{t+1}` is `agg1` when its train `n_correct` and `parse_ok` are at least `base1`'s, otherwise the log says `kept H_t: agg1 regressed`. Held-out scoring uses the chain's final tree. A chain that keeps the base is `negative_finding: chain-kept-base` and does not rerun held-out. Receipt status stays `draft`.

`sbun` no longer execs the sandbox, so an opt-in `HARNESS2_BUN_TRACE` can record start and end. It passes `--heldout` or `--runs`. Stdin stays closed with `</dev/null`. `config.BUN` is a `Path` of `sbun`.

Split: seed 230, 32 train / 16 held-out, four tasks of 8, committed as `examples/harness2-local/split.v0.json`. Opaque ids are `t01`..`t48` after `random.Random(230).shuffle` of the sorted real ids. Criteria keys are sorted, then shuffled with `random.Random(f"230:{real_id}")`. Pinned shuffle: label is first in 12 of 48 and last in 22 of 48. The order-preserving stripped sha256 (D11) is `ab0ee29bbe75b46d33248729f9c4dd61376ec357275c8debf6efdb4d296e1b7e`. The sort_keys digest `6d6c09cf6467a7fbd72c5d7800be86794867e483c5aa2e26c7c35a38658b57bb` is not the pin.

Fail/recover: stopping the stub server makes `drive.py` exit 2 with `endpoint down` and no receipt (`test_endpoint_down_writes_no_receipt`). The later stub runs complete.

RED (each mutant restored; the tree matched the pre-mutant bytes afterward):

- `strip_case` id is the real id → `test_stripped_file_hash_and_key_order` (`'local' unexpectedly found in 'wz-01-local-30b'`). Re-run after the assert reorder.
- `shuffled_criteria` returns `dict(criteria)` → same test (`first=24 last=9`). Re-run after the assert reorder.
- criteria keys reversed → same test (`first=9 last=24`). Re-run after the assert reorder.
- `sorted(criteria)` only, no shuffle → same test (`eb00a397` != `ab0ee29b`, first=20 last=12, band still true).
- drop comma and bare-space joiners → `test_pair_controls` (`[] is not true : hd-03 hold`).
- copy unstripped cases into the train batch → `test_real_bank_hides_labels_and_heldout` (verbatim note in the leak walk).
- write `train-scores.json` under the runs dir → same test (host-boundary hook, open outside host-only).
- id map via default-dir `NamedTemporaryFile` plus `os.replace` → same test (rename source outside host-only).
- train batch includes one held-out id → same test (isolation match `t33`).
- `PROPOSE_WORKERS=2` → same test (trace overlap `2 != 1`).
- roll an extra `base2` at k=1 → same test (`BudgetError: R=5 (want 4)`).
- `FINAL_LABEL="c1"` → same test (`KeyError: 'c1'`).
- every task re-reads the base harness → `test_improve_chain_adopts_and_scores_heldout` (task 2 base sha != task 1 agg sha).

### Item 4: surface

state: DONE | tests: `python3 -m unittest tests.test_harness2_local_surface` → Ran 5 tests in 0.426s, OK. Drive and case tests re-run after `write_base` became live: Ran 8 tests in 62.413s, OK | files: surface.py, trial.py `decision_prompt`, surface tests | err: none | commit: `475f34ddc8736969db253e3ed654fd85f8bbaea1`

Skills mapped: `jev-decision` only (`.grok/skills/jev-decision/SKILL.md`). That is the #230 Choice skill the decision task uses (D12).

`systemprompt.md` is the return string of `decision_prompt()` in `examples/typed-decisions-local/trial.py`. `guardrails.md` is the `## Do not` block of `AGENTS.md` plus the Feature-GO gate line, read-only. `tool_descriptions/tool_guidance.md` is the `### Custom Scripts, Tools & Automation` section. `write_base` also writes `scripts/pfy_jev_230.py` so upstream accepts the skill's `python3 scripts/pfy_jev_230.py` line. Adopt ignores that stub when it is unchanged.

Fail/recover: delete `.grok/skills/jev-decision/SKILL.md` and export exits 2 naming it; restore the file and export plus adopt leave the repo byte-identical (`test_missing_skill_recovers`).

RED (restored; surface tests green afterward):

- `rule_edits` returns `[]` immediately → `test_guardrail_edit_is_rejected` (`0 != 2`).
- `enforce_path_allow` returns `[]` immediately → `test_disallowed_paths_are_named` (`0 != 2`).

Upstream `validate` on the mapped tree: 1386 always-on chars, 1 skill, 1 script, no error.

### Item 2c: Tester FAIL of 902e04f

state: DONE | attempt 1 | commit: `a785c27e88945791de0e9a658dd6f2bdfa53f308` | tests: `python3 -m unittest discover -s tests -t .` → Ran 520 tests in 424.657s, OK (skipped=4), exit 0. Sandbox module is 40 tests. Stage module stays 8. Baseline at resume was 508.

Fixes the two blockers and the should-fixes from the Tester FAIL of `902e04f`, before item 5. One commit. Decisions D13-D20.

2c.1 Relay idle is 600 s on both splice sides (`RELAY_IDLE_S`). A stub that answers `/health` and stays silent for 35 s on POST then answers: child rc 0, body contains `pong-slow`, relay log `bytes_out` is not 0. RED: `RELAY_IDLE_S = 30.0` → `test_silent_post_survives_35s` FAILED (`RemoteDisconnected`). Restored. Green again.

2c.2 `env.sh` sets `XDG_DATA_HOME` and `XDG_STATE_HOME` only when unset. `sbun` passes `--expose` and `--allow` from `HARNESS2_RELAY_PORT` and exits 2 `BLOCKED: relay port unknown` when the port is missing or not an integer from 1 to 65535. A real OpenCode call through `sbun` (not a stub bun), with upstream Proposer's per-workspace XDG dirs, `OPENCODE_*` vars, and `run ... --dir ... --model ... --format json`, against a stub that speaks SSE: rc 0 in 3.2 s, 2 POSTs, relay log `temperature: 0` and `seed: 230`, stdout contains `pong`. The old "answered pong in 4 s" line was not true for the previous sbun (EROFS on the state XDG dir, and no relay route). The drop-in and the README say what is true now.

RED: `env.sh` forces the state XDG dirs → `test_caller_xdg_survives_env_sh` FAILED (`Read-only file system`). Restored. Green again.

RED: delete `extra+=(--expose "$port" --allow "$port")` → `test_sbun_runs_real_opencode_with_proposer_env` FAILED (0 POSTs, the test's own 60 s bound). Restored. Green again.

2c.3 Both watchdog waits use `WATCHDOG_GAP_S` (10 s). One 12 s `/health` blackout during a live call stays rc 0 with the marker (31.1 s). A 6 s stall of a single request does not separate the cadences: under the 0.2 s mutant it stayed green in 22.8 s, because the first probe's 5 s recv timeout uses the stall and the retry is a new request. The 12 s blackout covers two 5 s probes when the gap is 0.2 s. A dead server still ends the call with `relay down`, and the test requires that kill to land between 15 s and 35 s (about 20 s: two 5 s timeouts and one 10 s gap, plus preflight).

RED: miss-path `stop.wait(0.2)` → `test_one_health_stall_does_not_kill_the_call` FAILED (`relay down`). Restored. Green again (31.1 s).

2c.4 One test change per surviving mutant. Each RED was restored and the same test passed again.

RED: drop the second net → `test_env_allow_list_drops_secrets_and_open_code_overrides` FAILED (`UV_PUBLISH_TOKEN` reached the child). M02d.

RED: drop `config.json` from the plant list → `test_host_plants_block_and_shell_cannot_plant_runs` FAILED (the `config.json` plant was not blocked). M03c.

RED: drop `/etc/opencode` from the preflight extras → `test_etc_opencode_plant_blocks` FAILED (`opencode-plant`). The overlay stand-in is `--overlay-src /etc --tmp-overlay /etc --ro-bind standin /etc/opencode --remount-ro /etc`. Local bwrap 0.11.1 has those flags, so the test did not skip. M03h.

RED: `chmod -R -P` → `chmod -R -L` → `test_sweep_skips_symlinks_and_leaves_the_target` FAILED (target mode changed from 400). M05a. The earlier green run was the 600/700 fixture, not uutils. See D13.

RED: default cap 1200 → `test_preflight_defaults_are_120s_and_30s` FAILED (`1200.0 != 120.0`). M09b.

RED: default mount timeout 3000 → same test FAILED (`3000.0 != 30.0`). M10b.

RED: workspace check wrapped in `if False` → `test_workspace_must_sit_directly_under_runs_tmp` FAILED (`workspace is not directly under RUNS/tmp` absent). Outside, nested, missing, and a symlink to outside each give rc 2 and no marker when the check is present. M15.

RED: drop `--unshare-pid` → `test_unshare_pid_hides_the_host_pid` FAILED (`'yes' != 'no'`, the child saw the test PID in `/proc`). M21.

M22 is 2c.1.

2c.5 Stage tests plant their own `cpython-3.12.9` stand-in under a fake HOME and set `HARNESS2_PY312`. `test_existing_env_file_is_kept_byte_identical` asserts stage rc 0 and `env: kept existing .env`. RED: point `HARNESS2_PY312` at `<stand-in>-missing` → that test FAILED (`no-python312`). Restored. Green again.

2c.6 The executor launcher sets `XDG_DATA_HOME` and `XDG_STATE_HOME` to `<workspace>/.ocdata` and `<workspace>/.ocstate`. RED: delete those two assignments → `test_executor_launcher_xdg_is_inside_the_workspace` FAILED (`xdg-data`, the read-only state dir). Restored. Green again.

2c.7 A checkout whose realpath is under `/tmp` or `/run` exits 2 `BLOCKED: checkout under /tmp` (or `/run`) before any mount. The test points `HARNESS2_W` at a symlink. RED: delete `_refuse_ephemeral_checkout(wt)` → `test_checkout_under_tmp_or_run_is_refused` FAILED (`checkout under`). Restored. Green again. No checkout debris was created under `/tmp`.

2c.8 Headings this branch added since `aed526d` used U+2014. The `## D1` through `## D12` headings, the handoff title, and the `### Item N` headings now use a colon. After `a785c27`, `git diff aed526d..HEAD | grep '^+' | grep -c $'\xe2\x80\x94'` is 0.

Cheap nits folded in: the dead `/var/run` `pass` in `build_bwrap` is gone (`/var` is not bound). Handoff status and `docs/TODO.md` no longer say 26 sandbox tests. The handoff Head line is updated in the docs commit that records this item's SHA.

Deferred Tester nits (not in this commit): `_read_http` truncates a chunked body (`body[:0]`); preflight `find` is resolved through PATH with the venv first; `main()` treats `"--mode" in argv[:6]` as an internal mode; `check.py` only requires a venv Python version that contains "3."; the relay startup probe sends a real `GET /health` and it shows in `relay.log`; M03i and M03j (`~/.opencode`, `$XDG_CONFIG_HOME/opencode`) still survive, and the spec keeps them as guards that cannot fire on today's fresh HOME tmpfs; M04c and M04d survive and are equivalent for a non-root user.

### Item 5: propose

state: DONE | tests: `python3 -m unittest tests.test_harness2_local_propose` → Ran 20 tests in 1.962s, OK | files: `propose.py`, `leaks.py` verdict scan, `tests/test_harness2_local_propose.py`, README, D21

`propose.py` is the host-side gate. Tests use a bare repo under `$W/tmp/propose-tests` (H1c: not `/tmp`). `origin/main` is no longer `aed526d` (Hermes eval commits, tip read `24fe672` at 13:16 PDT). This branch was not rebased onto it. D21.

A passing receipt pushes `bot/h2-proposal-<YYYYMMDD>-<12 hex>` and leaves bare `main` where it was. The commit body has the before/after counts. Warn-only lines (`Prefer push only when CI is green.`, `Expected: escalate for the ambiguous Kronos case.`) are under `Leak warnings:`.

Named leak lines, including `label: B correct`, `ph-01-green-idle`, a verbatim note, and `see ph-03`, all block. The receipt stores line numbers and not the matched text. The 28 benign lines block only `case 3 - A`.

RED (each restored, then cases + propose green):
- `GAIN_MIN = 1` → `test_plus_one_gain_writes_no_ref` FAILED (`pushed bot/h2-proposal-20261020-ebc621cc1281`, no gain finding).
- `scan_secrets` returns `[]` → `test_secret_shapes_are_masked_and_write_no_ref` FAILED (rc 0, pushed).
- token regex replaced with `sk-|xai-` → `test_benign_secret_text_pushes` FAILED (rc 1).
- `gh[pousr]_` changed to `ghp_` → `test_gho_token_is_refused` FAILED (rc 0, pushed).
- `_line_leaks` returns `False` → `test_label_b_correct_is_a_negative_finding` FAILED (pushed, no `label-leak`).
- `BLOCK_BARE_LABELS = True` → `test_false_positive_budget_blocks_only_case_3` FAILED (list was not only `case 3 - A`).
- letter class without `(?-i:)` → same test FAILED (`answer: a.` and `case 3 - A`).
- `name_is_protected` returns `False` → `test_target_main_exits_2` FAILED (rc 0, `pushed main-2`).

Full suite after the restore: `python3 -m unittest discover -s tests -t .` → Ran 540 tests in 427.292s, OK (skipped=4).

Commit: `4bd065de7a2366149dac47f4c9cf964e31e65f20`. Pushed fast-forward to `origin/bot/h1-harness2`. `git diff aed526d..HEAD | grep '^+' | grep -c` of U+2014 is 0.

### Item 6: live

state: in progress. Load gates passed at 2026-10-20T13:37 PDT. Item clock starts 2026-10-20T13:42 (own 3h cap, stop this item by about 16:42). Server pid 425470, pgid 425470, port 18111. Not stopped yet.

Quiet host: `ollama ps` printed only the header. No other `llama-server` and no `bench.py`. Port 18080 is monerod (pid 1163482). It was not touched. Our server uses 127.0.0.1:18111.

Memory arithmetic before load: weights file 20.227 GiB (21706498560 bytes) + about 4 GiB KV at 32k + 25 GiB margin = 49.227 GiB. The spec floor is 52 GiB. MemAvailable was 61547860 kB (58.70 GiB), above 52. The lane's own check is file size + 25 GiB (45.227 GiB), also clear. SwapFree was 612 kB. Lowest MemAvailable seen during load: 29777968 kB (28.40 GiB), above the 16 GiB floor. After the N3 generation: 56 to 57 GiB.

Server: `llamacpp-nommap` via `pfylib/hedge.py` `start_llamacpp_nommap`, script flags `--no-mmap -ngl 999 -c 32768 -np 1 -fa on --no-webui`. GGUF is the `qwen3.6:35b` blob `sha256-d372de8e934898a59e6ccfabc3368474711384d8f1fd4d22d87a3f0a45400cdc` (sha256sum matches that name). `GET /health` returned 200 `{"status":"ok"}` at t=20s. `GET /v1/models` lists that blob with `n_ctx` 32768.

N3: during one completion that took 23.8 s, `GET /health` was HTTP 200 in 1.3 ms and `GET /v1/models` was HTTP 200 in 0.4 ms. Idle, both were under 8 ms. `/v1/models` does not queue behind the single slot on this build. The watchdog already probes `GET /health` and treats any bytes back as alive. That probe stays.

Next: held-out base runs `a1` and `a2`, then `drive.py --k 1`.

### Item 7: docs

state: pending

### Item N: nimo-only

state: pending

## Exit

Superseded by the H1c session (START 2026-10-20T12:23:06-07:00). The H1b stop-file below was intentional so item 2c could run first. It is not a failure and not a skip.

STOPPED_EXIT: stop-file. `$W/tmp/STOP` existed (empty file, mtime 2026-10-20 12:13 PDT, owner mark). Seen at 2026-10-20 12:20 PDT, after item 4 was green and before item 5 started. No llama-server was started in that session. Items 5, 6, 7 and checks N3, N4 held-out, N6 did not start. Local CI was not run.
