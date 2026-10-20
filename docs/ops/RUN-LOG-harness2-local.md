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

state: pending

### Item 2b — should-fixes

state: pending

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
