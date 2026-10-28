# Autonomous decisions 2026-10-27

MVP2 trial on `bot/mvp2-trial`. No questions asked.

1. Choice: six tasks from still-open follow-ups, not from items that the tree already fixed (Hermes start time, labels stamp, and choice scattershot already have tests). Tasks are t1 stderr-over-cache, t2 content hash in smoke 119, t3 daemon-stop timeout is a fail, t4 timeout text names `new` and `version`, t5 117/119 tests stop writing repo receipts, t6 content hash in the three older tree_sig copies. Alternatives: re-do already-fixed Hermes items, or take catalog HOLD and GUI work. Why: the drop-in wants small test-gated build tasks that are still wrong, at most a few files, and off the hands-off list.

2. Choice: plant the acceptance test as a local commit on a detached worktree of `997d892`, then point `./pfy build --local --base` at that commit. Alternatives: ask the agent to invent the test, or commit the test on `bot/mvp2-trial` and merge it into the run. Why: the local runner treats a missing test summary as a failed gate even after a good fix, and it refuses edits to test files that are not marked writable. The planted test is the gate. It is not merged to main. Patches are diffs against `997d892`, so they include the test and the fix.

3. Choice: run every local arm first, with `--keep-model`, then the cloud arms. Alternatives: alternate L then C per task, or unload after every task. Why: nimo has one GPU and the memory guard. Reloading `qwen3.6:35b` six times spends the same RAM twice. Cloud Build does not load that model. The flag is the tool's own keep switch. The default model, sandbox, and protect-by-default hash stay on.

4. Choice: cloud command is `grok -p <spec> --cwd <worktree> --always-approve --no-alt-screen`, wrapped by a 40 minute timeout. Alternative: omit `--no-alt-screen`. Why: `-p` is the headless switch the drop-in names. `--no-alt-screen` keeps a non-TTY session from sitting on the alternate screen. One retry only when the sandboxed gate does not pass.

5. Choice: record `turnCount` and `modelCalls` from the session usage file, and record only whether `~/.grok/auth.json` is non-empty. Alternative: print `grok usage` or token totals. Why: the weekday percentage is not in that file and `gh` has no token in this environment. Token fields stay out of the report.

6. Choice: the local process wrapper waits 60 minutes, and the agent timeout stays the tool default of 1200 seconds. The cloud wrapper stays 40 minutes. A wrapper timeout is recorded as TIMEOUT and does not abort the other tasks. A cloud retry writes `*-C-retry.patch` and keeps the first attempt inside the result JSON. Why: tests-before plus two test passes can outlive 40 minutes even when the agent itself stops at 1200 seconds, and a timeout must still leave a receipt for the later tasks.
