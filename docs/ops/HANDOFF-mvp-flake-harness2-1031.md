# Handoff: mvp-flake-harness2-1031

Exit: lane empty at 2026-11-01T06:00Z. The flake goal is met. Wall stop for new items was 2026-11-01T09:45:36Z. Branch `bot/mvp-flake-harness2-1031`. Base `origin/bot/mvp-integrate-1031` (`1dee0b91`). Do not merge.

## Done

| Item | SHA | What |
|---|---|---|
| A / item 1 | `af1c104` | Harness2 stage tests snapshot a private HOME and `UV_CACHE_DIR` under the test scratch. They no longer hash the operator `~/.cache/uv`. |
| B | `a0885ed` | Docs hygiene uses `skipTest("shallow clone: old main SHAs not present")` when old main blobs are absent. |
| C | `b8ec41d` | `scripts/pregate.sh` exits 3 while a runner worker is up. `--wait-runner SECONDS` waits, then still exits 3. |
| item 2 | `871075c` | The structural runner prints the failing unittest traceback on stdout, which pregate stores as `eval-structural.log`. |
| item 3 | `c5d225f` | Three discovers had no intermittent failures. The four steady image-pin failures were `pgrep -f` matching a shell that only quotes `Runner.Worker`. Pregate now uses `pgrep -x` (process name). |

Docs on this branch: `47c93eb`, `1f1129d`, `928911d`, `8ffce35`, `63336e8`, plus this handoff.

## Skipped

No named item was skipped. After item 3, TODO has no further suite-flake row that fits this lane. No open OQ was turned into an ADR.

## Test evidence

- A: under `flock ~/DEVELOP/pfy-mentat/tmp/heavy-1030.lock`, `TMPDIR=$PWD/tmp`, nice 19. `tests.test_harness2_local_stage` 12 OK in 4.232s (lock acquired 04:05:30Z). Then 20/20 of `test_stub_tools_see_state_caches_and_home_stays` with 4 CPU burners, done 04:05:49Z.
- B: `tests.test_docs_hygiene` 3 OK in 0.067s.
- C first cut: `tests.test_pregate_runner_gate` 2 OK (the early-exit behavior, still using `pgrep -f`).
- Item 2: `tests.test_eval_structural_trace` passed. Detail contained `Traceback`, `AssertionError`, and `operator cache changed`. A passing run had no `Traceback`.
- Item 3 discovers, one flock, in-repo `TMPDIR`, nice 19, 1250 tests, 16 skipped, exit 1 every time: 816.184s, 817.017s, 818.493s. Unittest failures in every run, and in no run alone: `test_failing_image_pin_lint_fails_pregate`, `test_path_python_without_yaml_fails_closed_for_both_call_sites`, `test_root_path_at_the_limit_passes_the_guard`, `test_root_path_over_the_limit_is_refused`. Stderr was the runner-busy line. Not red on the base. Introduced by `b8ec41d`.
- After `c5d225f`, G0 idle (`pgrep -x 'Runner[.]Worker'` empty at 05:57:15Z): runner gate 3 OK in 3.287s; those four image-pin tests OK in 19.037s. `bash -n scripts/pregate.sh` ok.

## How it fails and how it recovers

- Private cache (`af1c104`). Fail: a stand-in for the operator `~/.cache/uv` changes while the test runs. The private snapshot stays empty, so tearDown passes. A mode `0555` stand-in makes an in-process write raise `PermissionError`, and a stage stub pointed at that path makes the stage nonzero with `PermissionError` on stderr. Recover: mode back to `0755`, a write into the private uv cache succeeds, and a clean stage rerun meets the cache contract with the private home unchanged. A stub that writes `$HOME/.npm` still gets `BLOCKED: home-write`, and the next clean run passes.
- Traceback (`871075c`). Fail: a unittest whose assertion is `[] == [".cache/uv"]` puts the traceback and the assertion text in the structural detail (the bytes pregate writes to `eval-structural.log`). Recover: a passing unittest is one `OK` line and has no traceback.
- Shallow clone (`a0885ed`). Fail: a full clone missing `deadbeef:rel` raises `AssertionError`. Recover: a `file://` depth-1 clone raises `SkipTest` with `shallow clone: old main SHAs not present` instead of returning, which would have been a pass.
- Runner gate (`b8ec41d`, `c5d225f`). Fail: a live process whose name matches the pattern makes pregate exit 3 with `not starting`, and it does not reach the unknown-ref check. A shell that only quotes the name does not do that (that shell is what failed the image-pin tests). A `--wait-runner 1` against a process that lives 60s exits 3 with `still running`. Recover: after that process is gone, the same bad ref exits 2 with `unknown ref`. A `--wait-runner 8` that outlasts a 1s process also exits 2. The fake worker sets its name with `prctl` and is reparented so a finished sleeper is not still visible to `pgrep -x` as a zombie.

## Cross-lane

`origin/bot/backlog-catalog-1030` at `47dcd66` still returns silently from the shallow-clone branch of `tests/test_docs_hygiene.py`. This branch uses `skipTest`. When that lane merges, keep the skipTest. Do not edit that worktree from here.

`scripts/pregate.sh` and the harness2 stage test were this lane's files. The image-pin tests were not edited. Their failures were the pregate gate matching the wrong process.

## Gate

- `scripts/pregate.sh` (`b8ec41d`, `c5d225f`) is runtime. Gate: Tester plus Reviewer.
- `examples/eval-harness/run_structural.py` (`871075c`) is eval. The other code commits are test-only. Gate: pregate plus Reviewer.
- pregate not run: the lane drop-in says do not run `scripts/pregate.sh`. At 2026-11-01T05:57:15Z no process was named `Runner.Worker`, MemAvailable was about 62 GiB, and load was about 2.9 on 32 cores. That is not host busy.

## Next

Hand this branch to Reviewer. Do not merge. The operator text for item C said `pgrep -f`. This lane narrowed the check to `pgrep -x` after three discovers showed `-f` matches shells that only quote the name. A real `Runner.Worker` (process name, as on the actions-runner binary) still exits 3.
