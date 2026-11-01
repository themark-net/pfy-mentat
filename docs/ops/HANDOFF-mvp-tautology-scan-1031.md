# HANDOFF mvp-tautology-scan-1031

Lane: `bot/mvp-tautology-scan-1031`
Worktree: `/home/mark/DEVELOP/pfy-mentat/tmp/mvp-tautology-scan-1031`
Base: `origin/bot/mvp-integrate-1031` at `1dee0b91bda11ba1fcda87819423437a3f10f289`
Exit: turn cap. Eight fix items after the scan doc. Wall clock was not the limit (handoff at `2026-11-01T03:06:12Z`, buffer `2026-11-01T10:14:15Z`).

## Items done

| Item | SHA | What changed |
|------|-----|----------------|
| Exit card | `5eb5800`, logged `bd31b3d` | Run log exits before the scan |
| Scan table | `6b05285` | `docs/ops/TAUTOLOGY-SCAN-1031.md` |
| Install stubs | `4587707` | Five missing-binary arms run `exec_harness` |
| Smoke 149 temp dirs | `d591f2b` | Real `main` stays under the caller TMPDIR. Entry count 35 |
| Registry state_dir | `a237265` | Explicit path, tilde, and `PFY_STATE_DIR` |
| Har sibling prefix | `4723705` | Deleted two stdlib asserts. Receipt checks remain |
| Local bench exe name | `9843412` | Deleted the test that never called `is_ollama_runner_proc` |
| Continue stub | `6253b5d` | Runs `stub_harness continue` |
| Shimmy cold start | `c173893` | Stub `ensure_*` order. No engine binary |
| Hermes stamp | `55abd44` | Temp tree. Later ATG `when` moves the stamp |

Production files were mutated only in memory for the proof, then restored. `scripts/pfy`, `examples/local-bench/bench.py`, and `examples/hermes-bakeoff/make_tasks.py` match the parent of each test commit.

## How each change fails and recovers

- Install stubs. Fail: the missing-binary arm prints `WRONG` instead of the registry installer. The five tests exit 1. Recover: print the registry setup line and exit 2. Green rerun: 13 OK.
- Smoke 149. Fail: `bwrap_ok` calls `mkdtemp` with `dir="/tmp"`. A `pfy-smoke-149` path sits outside the caller TMPDIR. Recover: create those dirs under the caller TMPDIR. Green: the module plus `tests.test_entry_149_count`, 36 OK. No probe dir left behind.
- Registry. Fail: `state_dir` returns `Path(".")` and ignores the argument. Recover: `Path(explicit).expanduser()`, and a bare call uses `PFY_STATE_DIR`.
- Har sibling. Fail: the smoke uses `startswith`, so a sibling `home + "-evil"` counts as inside HOME and the receipt says `work_dir_under_temp_home` true. Recover: `is_relative_to` on the resolved paths. The receipt check fails the sibling.
- Local bench delete. Fail: `is_ollama_exe` returns True for every path, including the grok exe and an empty exe. `test_rss_sampler_ignores_grok_exe` and `test_eacces_exe_falls_back_to_argv0_and_recovers_stats` both raise AssertionError. Recover: match `ollama` or `llama-server` in the exe string. Those two tests are the coverage. The deleted test only called `is_ollama_exe`.
- Continue stub. Fail: the continue arm no-ops instead of `write_continue_config`. Exit can still be 2 and the filesystem line can still print, and `continue-config.json` is missing. Recover: write the config and exit 2. Module: 4 OK. PATH in the test is python3 and mkdir only.
- Shimmy order. Fail: the shimmy block runs before ollama and a successful shimmy skips ollama. Recorded order is `shimmy`. Recover: ollama success records only `ollama`. Ollama failure then records `ollama shimmy`. Module: 3 OK. The stubs do not start a binary.
- Hermes stamp. Fail: `labels_written_stamp` drops the ATG receipt. The stamp stays on the older bench time `2026-03-01T00:00:00Z`. Recover: include the ATG `when`. A later ATG time moves the stamp. An older bench time that stays older does not. The committed tasks file still matches `build()`.

## Test evidence

Targeted `nice -n 19 python3 -m unittest ...` only. No `unittest discover`, no `./pfy`, no uv, no `scripts/pregate.sh`. `TMPDIR` was this worktree's `tmp/`.

Each green run was repeated after the mutant was restored. The first local-bench red used a wrong class name and was discarded. The real red is the AssertionError pair above.

## Skipped

- `eval/local-build/fixtures/*/tests/test_keep.py` and t07 `test_live`. Scored fixture anchors. Documented in the scan table. Not rewritten.
- `eval/mvp2/gates/test_mvp2_t6_tree_sig_three.py` unreadable-file assert. The content-hash asserts already fail if hashing ignores bytes. Left as a note.
- `tests/test_hermes_bakeoff.py` `test_rescore_reads_the_committed_receipt_only`. Still takes `n_pass` and the verdict from the input receipt. Cap reached.
- `tests/test_atg_compile_bench.py` `test_no_default_tmp_worktree_literal_in_tests_data_or_bench`. Literal ban. Cap reached.
- `tests/test_attach.py` `test_selftest_passes_for_every_harness`. Banner prefix. Cap reached.
- `tests/test_ollama_adapter.py` `test_named_start_calls_ensure_before_exec`. Source order. Cap reached. A later edit must stub the arm and must not start a model.
- `tests/test_local_bench.py` RSS tail inside `test_eacces_exe_falls_back_to_argv0_and_recovers_stats`. Still mocks `proc_status` and asserts that same number. The argv0 cases in that test are real and were kept.
- `tests/test_pfy_build_p.py` `test_fixture_bundle_under_bound_without_user_skills`. Size assert compares the receipt to `measure_skills_bundle` of the same tree. Cap reached.
- `tests/test_workflow_image_pin.py` `test_pregate_lint_calls_helper`. Three shell strings. Not deleted. This lane must not run `scripts/pregate.sh`. Execing it from a linked worktree writes `tmp/pregate-runs` on the main checkout.
- Live-lane files were not edited: `tests/test_pfy_build_local.py`, `tests/test_pfy_build_local_review.py`, `tests/test_pfy_build_local_review_ci.py`, `tests/test_pfy_build_cloud.py`, `tests/test_harness2_local_stage.py`. The scan notes did not put a tautology row on them.

## Cross-lane requests

None. The worst owned findings were in files this lane could edit. No request for mvp3, mvp-cloud347-1031, or mvp-flake-harness2-1031.

## Gate

Pregate plus Reviewer. Docs and test-only. No product runtime change remains. This lane did not run pregate. Do not merge.

## Next step

A later lane can take the open rows in this order: hermes `--rescore` on a receipt whose rows are forced to pass, then the ollama start arm with the same stub style as the shimmy cold start, then attach selftest when `open_session` returns ok for a missing binary. Leave the workflow image-pin strings until pregate can run somewhere other than the main checkout. Do not rewrite the fixture `test_keep` files.
