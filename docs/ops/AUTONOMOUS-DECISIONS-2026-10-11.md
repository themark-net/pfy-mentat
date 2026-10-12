# Autonomous decisions — orch-fixes-1011

One line per choice. Format: choice | alternatives | why

- Stay on `a5c0362`, which equals `origin/main`, instead of resetting to the named base `27c2d3b` | reset `build/orch-fixes-1011` to `27c2d3b` | `a5c0362` is already on `origin/main` and is the current branch tip; resetting would drop a merged catalog commit
- No extra git worktrees; workstreams share this tree on disjoint paths and do not commit | one `build/<phase>` worktree per phase | the request allows only `/home/mark/DEVELOP/pfy-mentat/tmp/orch-fixes-1011`, and `git worktree add` mutates the shared git dir
- The lead commits after each green gate | each agent commits on the shared branch | four agents on one index would race
- Code agents start only after the baseline unittest line is in the run log | spawn them in parallel with the suite | an edit during the suite would make the baseline count untrustworthy
- Shared timeout text is `{tag} timeout` from `smoke.timeout_reason` | keep each smoke's current sentence | `smoke_109_111.py` already uses that shape; one function is the single format
- Sha receipts use the shipped `pinned()` shape `expected.<VAR>.{value,source,pin}` plus stderr `WARN: $VAR=… overrides the pinned …` | top-level `expected_sha` and `source` fields | Entries 109–111 already record overrides that way
- Gitignore only `pipelines/smoke/{rulora,har,cassmemory,bugpatrol,graphjin,antislop}/` | ignore all of `pipelines/smoke/` | `pipelines/smoke/kolibri1/latest.json` is tracked and must stay tracked
- Do not bulk-delete the pre-existing `/tmp/pfylib-*` directories | delete all of them now | this run did not create them; the check is that a full test run leaves no new ones
- Decisions file is `docs/ops/AUTONOMOUS-DECISIONS-2026-10-11.md` | name it for UTC 2026-10-12 | the request names the 2026-10-11 file
- Doc edits get no unit test that only searches the markdown | add a test that asserts the new sentence exists | that test cannot fail for a behavior reason
- Har work-dir check uses `Path.is_relative_to` on resolved paths | keep `str.startswith` | `startswith` treats `/tmp/foo-evil` as inside `/tmp/foo`
- The `git add -f` sentence goes on every x-intake handoff from 2026-10-05 through 2026-10-11 that tells the operator to commit a nimo receipt | only the 2026-10-11 handoff | the request says handoff docs, plural
- The atg worktree note goes on `docs/ops/HANDOFF-orch-decisions-1009-2026-10-09.md` | a new doc, or `docs/ops/atg-coupling.md` | that handoff is the one that recorded the detached atg pin e2e
- Do not delete `/tmp/atg-*` logs or the `atg-eval` and `build-local-lane` worktrees | remove them so the sentence is about this run | the pin worktree is already gone; those other paths are not this run's
- Stage A spec edits are two `python3` blocks in the agent-substrate handoff (root path read-only, then `process.terminal=false`) | `jq`, or one combined script | `python3` is already required; the request asks for a command block per spec edit
- Host swap is partly used (about 6.7 GiB of 8 GiB) with about 66 GiB RAM available, so the run continues and loads nothing | stop for host memory | swap is not full and the suite is small
- Replace only existing timeout reason strings with `timeout_reason` | also catch timeouts in qwen38flash and foremerge | those two smokes do not record a timeout reason today, and the request does not add new failure paths there
