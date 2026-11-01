# Handoff: mvp-dogfood6-1031

Branch `bot/mvp-dogfood6-1031`. Worktree `/home/mark/DEVELOP/pfy-mentat/tmp/mvp-dogfood6-1031`. Base `origin/bot/mvp-integrate-1031` at `1dee0b91`. Exit: DONE. The exit card turn cap is 8 cloud builds. All 8 were human-accept. Pass rate 8/8. No reject, so there is no FINDING.

Launch 2026-11-01T02:33:54Z. Stop 2026-11-01T03:20:00Z. Wall cap 2026-11-01T10:33:54Z was not reached. No `--local`. Pregate was not run.

## Eight rows

| n | slug | human | cloud | landed | tests | wall |
| --- | --- | --- | --- | --- | --- | --- |
| 01 | hermes-driver-symlink | accept | b011907ff97eb68a83404d090e3726d5b2589dfb | ebb808d | tests.test_hermes_driver_symlink 4 OK | 131s |
| 02 | attach-session-symlink | accept | ba92aca780cb3d447b8b014159ed8741b649bab1 | 29ee1cc | session + tests.test_attach 38 OK | 167s |
| 03 | attach-pid-symlink | accept | 8d7b20e769e774759cb8a4a23a2338a486bdc9d0 | 3675945 | pid + session + attach 42 OK | 82s |
| 04 | attach-receipt-symlink | accept | 8bce3dbe0cb4bc63550c283e3ac4db82db4c6b9b | 1c100a5 | receipt + pid + session + attach 46 OK | 78s |
| 05 | hermes-arm-symlink | accept | 39069ebd86b568cd2c72818c8e8b1ed4e1335071 | 839ae5e | arm + tests.test_hermes_bakeoff 35 OK (1 skipped) | 95s |
| 06 | opencode-arm-symlink | accept | 1f469327c8a1866442365966d1c3aa73b83af51c | 51ed297 | opencode + bakeoff 35 OK (1 skipped) | 99s |
| 07 | think-proxy-symlink | accept | 49979f196748f86fc730507f8f4706f0ed7a0424 | 4340a72 | think-proxy + bakeoff 35 OK (1 skipped) | 87s |
| 08 | make-tasks-symlink | accept | 1ac3db4d3aa386f1a2192369fff7fbfeeacb5048 | a7008f4 | make-tasks + bakeoff 35 OK (1 skipped) | 109s |

Planned six: 6/6 accept. The two extra slots in the turn cap were the same replace contract on `write_forced_log` and `make_tasks.main`. Overall pass rate: 8/8.

Each product commit keeps author `pfy-cloud-build` and adds a `Built-by` trailer. Receipts, `diff.patch`, `command.txt`, and `notes.md` are under `eval/mvp-1031/dogfood6/`. Docs commits: 7932552, a209e82, f17a47b, f3f2dfe, b4958fd, efb9dee, 8cbc852, d9bc4e3. Item 04 also dropped unused test imports in `5d00715` after the product land.

## How each change fails and recovers

Every accept replaces `Path.write_text` with a temp file in the parent directory and `os.replace`, so a symlink becomes a regular file and the outside bytes stay. A broken symlink does not create the missing name. A regular file still receives the payload.

| n | fail | recover |
| --- | --- | --- |
| 01 | `_write` and `_config` no longer follow a symlink | a regular Hermes driver file and `config.yaml` still receive their bytes |
| 02 | `write_session_reach` no longer follows a symlink; `read_session_reach` returns empty on a symlink | a regular session file still round-trips, trimmed to 80 characters |
| 03 | `write_terminal_pid` no longer follows a symlink; `read_terminal_pid` returns 0 on a symlink | a regular pid file still stores the integer; a non-integer regular file still returns 0 |
| 04 | the spawn receipt write no longer follows a symlink | a regular receipt still gets `exit_code` and `live` FAIL; an unwritable parent still does not raise |
| 05 | Hermes `config.yaml` no longer follows a symlink | a regular yaml still contains the model name and the base URL; home is still not created here |
| 06 | `opencode.json` no longer follows a symlink | a regular JSON file still has `ollama/<model>` and the provider baseURL; both mkdir calls stay |
| 07 | the forced-log path no longer follows a symlink | a regular log still gets one JSON line per row, and an empty row list still writes an empty file |
| 08 | `OUT` no longer follows a symlink | a regular tasks file still gets indent-2 JSON plus a newline; `build` does not write; the committed tasks file was not rewritten |

The gate was red before each build (exit 1) and green after (exit 0). Review accepted attempt 1 on every build. No build edited a test or a second product file.

## Skipped

Recorded before item 01. They do not count as a no-progress streak.

- TODO rows that need a shelf, a local model, docker, a parked env, hardware, an ADR, or an open OQ: T-0091, T-0094, T-0081, T-0064, T-0043, T-0062, T-0046, T-0016, T-0005. `docs/TODO.md` was not edited.
- `scripts/pfy_build_cloud.py` and `scripts/pfy_build_local.py` (mvp-cloud347), including pass3 findings 3, 4, and 7.
- `tests/test_harness2_local_stage.py` and harness2 product files (mvp-flake-harness2).
- Smoke timeout files already built by dogfood3, dogfood4, dogfood5, or pfy-followups-next.
- `pipelines/dogfood/local-bench-5/run_runtime_matrix.sh` (localbench).
- `bootstrap/grok-cli/scripts/merge_config.py`. Replacing a user config symlink is a policy choice this lane does not invent.
- `pfylib/hedge.py`, `pfylib/toolsets.py`, `pfylib/loop_paint.py`, and `pfylib/bot_interface.py`. Other branches already replace those symlink writes.
- `open_session` writes of `active-harness` and the attach base. They sit inside the session opener. This lane did not hand that function to the model.
- `baseline_arm.main`, `hermes_arm.main`, and `opencode_arm.main` result writes. Each write runs only after the arm talks to a model.

## Test evidence

Targeted `nice -n 19 python3 -m unittest` only. No `unittest discover`, no `make eval-*`, no pregate.

`tests.test_hermes_bakeoff` prints `ResourceWarning` for a socket, `/proc/meminfo`, and pipes, and it prints three install hints. Those warnings were already present. The suite still exits OK with 1 skipped. Item 08's `main` prints `wrote <temp> n=27` into the test output. The committed `data/decision-gates/hermes-bakeoff.tasks.v0.json` mtime did not change.

A class scan of receipts found the letters sk- only inside the words `task-id` and `task-file`. Those are not credentials. No receipt contained a key. No written note uses an em dash or an en dash.

## Cross-lane requests

None that ask another lane to change course.

Leave these files to their owners: `scripts/pfy_build_cloud.py`, `scripts/pfy_build_local.py`, `tests/test_harness2_local_stage.py`, and `pipelines/dogfood/local-bench-5/run_runtime_matrix.sh`.

## Gate

Tester plus Reviewer. The product files are runtime code. This lane did not run pregate. The operator runs it when no process has comm `Runner.Worker` and the heavy lock is free.

## OQ draft

Do not file these in `docs/OPEN_QUESTIONS.md` from this lane.

- smoke_149 `home_sig` still reads `.cache/chroma` bodies. A bounded fingerprint needs a size cap written down before anyone implements it.
- harness2 mode 751 sandbox prune needs an allowlist. This lane does not invent one.

## Next step

Review this branch (Tester plus Reviewer). Do not merge, open a PR, or tag from this lane. The integrator lands it. A later lane can take the two `open_session` symlink writes after an ownership check. Do not start another `./pfy build` on this branch. The turn cap is spent.
