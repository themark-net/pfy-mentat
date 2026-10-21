Tue Oct 20 11:41:46 PM PDT 2026

# RUN-LOG hermes-wire

START: 2026-10-20 23:41:46 PT (`date` above).
Worktree: `/home/mark/DEVELOP/pfy-mentat/tmp/hermes-wire`
Branch: `bot/hermes-wire`
HEAD at start: `e9365d545e52dcb7a319377c87edf32e1c7dce0a` (equals `origin/main` and `origin/bot/hermes-wire` after `git fetch`).
STOP file: absent.
Clock: no new item after 2026-10-21 05:41 PT. Stop work by 2026-10-21 07:11 PT. Hard kill 2026-10-21 07:41 PT. Live 27-task re-run only if started by 2026-10-21 04:26 PT.
`~/.hermes` snapshot before: 113616 paths (path, mtime, size) in `tmp/hermes-snapshot-before.json`. Contents not read.
Ollama at start: tags include `qwen3.6:35b`, `ollama ps` empty. bwrap present. System `~/.local/bin/hermes` not used.

## Decisions

- 2026-10-20 23:45 PT: TTFT stamps are UTC ISO-8601 with milliseconds and a Zulu suffix. `parse_ts` rejects a whole-second stamp. Decision: fail closed rather than truncate.
- 2026-10-20 23:45 PT: Hermes wording follows the code. Each task is a new `subprocess` of `hermes_arm.py`. `AIAgent.run_conversation` is the library call inside that process.
- 2026-10-20 23:54 PT: The unittest suite runs with TMPDIR unset. `test_relative_outdir_log_path_safe` treats a temp dir inside the repo as in-tree, so pointing TMPDIR at `$W/tmp` fails that test. Scratch for this run stays under `$W/tmp`. CI-shaped suite uses the default temp dir.

## Item 0

- 2026-10-20 23:45 PT: start R1 R2 R3. STOP absent.
- R1: rewrote the in-process sentence in `docs/eval/HERMES-EVAL-HANDOFF.md`. `git grep -n in-process -- docs/eval examples/hermes-bakeoff pipelines/dogfood/hermes-bakeoff` is empty after the edit.
- R2: summary line in `docs/eval/hermes-vs-current.md` links "much faster" to the not-like-for-like note (thinking off on Hermes only, opencode CLI cold start, RSS excludes the model).
- R3: MCP log stamp and `ttft_s` use millisecond stamps. RED: `stamp_now` forced to `%Y-%m-%dT%H:%M:%SZ` -> `test_ttft_keeps_milliseconds_and_rejects_whole_second_stamps` FAILED (regex). Restored. Same test then OK.
- 2026-10-20 23:59 PT: `env -u TMPDIR python3 -m unittest discover -s tests -t .` -> Ran 618 tests in 375.711s, OK (skipped=14), EXIT 0. An earlier run with `TMPDIR=$W/tmp/tmpdir` failed `test_relative_outdir_log_path_safe` (in-repo temp counted as in-tree) and raced `test_module_run_leaves_no_new_tmp_dirs` against other `/tmp/pfy-*` dirs. Those two tests pass with TMPDIR unset.
