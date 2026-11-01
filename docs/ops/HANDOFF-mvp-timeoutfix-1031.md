# Handoff: mvp-timeoutfix-1031

Exit: lane empty. The last new cloud-runner finding was the selfhost2 kolibri recheck at 2026-11-01T00:29Z. Polls at 00:49Z, 01:09Z, and 01:29Z found no newer cloud-runner finding, so the 60 quiet minutes elapsed. Wall cap 2026-11-01T08:00:55Z was not reached. Host pressure did not fire (at 01:29Z MemAvailable was about 67 GiB and load was about 3.6 on 32 cores). No merge to main, no PR, no tag.

Launch: 2026-11-01T00:00:55Z. Stop: 2026-11-01T01:29Z. Branch `bot/mvp-timeoutfix-1031`. Worktree `~/DEVELOP/pfy-mentat/tmp/mvp-timeoutfix-1031`. Base merged: `origin/bot/mvp-integrate-1031` at `dd1db3b`, then `origin/bot/mvp-cloudfix-1031` (tip `10b4f5b`).

## Items done

| Item | SHA | Result |
|------|-----|--------|
| Exit card before any code | d743bf855f40d19b3699ffa324b97443f90eb7f1 | PASS, docs only |
| Merge origin/bot/mvp-integrate-1031 | 30767626c7fed72f093c5272b2fad2e7ee15c544 | PASS, clean merge, no rebase. Baseline after the merge: tests.test_pfy_build_cloud tests.test_pfy_build_p, 77 OK, skipped 1 |
| Merge origin/bot/mvp-cloudfix-1031 | e84a9cea6bf905d898a1415216705c29f9d4b173 and later c9bef6cf11f3bc9b38b4348f15cfd8177187789e | PASS, clean. Second merge was their handoff docs only |
| dogfood2 row 07 review-reject timeout | dd807fc4a848a8af1022be96c333165d60c54323 | PASS, 79 OK, skipped 1, 24.679s |
| dogfood2 F2 review.truncated | a450f5b6be6f5caa7140a0bf18c3522070000fff | PASS, 80 OK, skipped 1, 24.776s |
| dogfood2 F3 rejected diff on the receipt | 270f75f1f23a039ee464b0dcb755039288205d08 | PASS, 81 OK, skipped 1, 24.849s |
| selfhost2 kolibri recheck git walk | ff6b8559c66be74154f0a716a072919dcf576384 | PASS. New test red first (exit 1, commit-recheck-failed), then green. Helper recheck test stayed green. Both modules exited 0 |

Already on the integrate tip, confirmed and not reimplemented: dogfood2 F1 (commit subject ends on a word), gom wave 5 #2 (default unittest import failure is gate-unusable), #3 (resolve_base asks for --base when HEAD and origin/main differ), #4 (short lowercase fixture values stay readable), #5 (gate env denylist), #6 (same commit subject as F1).

## Skipped

- Gom wave 5 #1 remainder. Base tests stay hashed, and a new test file may reach the gate. A usage note when "the task should have added a test" needs a rule for which tasks must add one. OQ draft below. Not a runner guess.
- Gate env allowlist. The gate already drops TOKEN, SECRET, PASSWORD, PASSWD, CREDENTIAL, AUTHORIZATION, and KEY names. An allowlist of only PATH and TMPDIR would drop VIRTUAL_ENV and PYTHONPATH and break gom's venv gates. OQ draft below.
- docs/modules/pfy-build.md and docs/ops/pfy-build-daily.md. mvp-surface owns them. Cross-lane request below. Not a third skip of a runner item.

Two skips, then the poll continued. The no-progress exit (three skips in a row) did not fire.

## Test evidence

Targeted, niced, fake grok, scratch under this worktree's `tmp/`:

`export TMPDIR="$PWD/tmp" && nice -n 19 python3 -m unittest tests.test_pfy_build_cloud tests.test_pfy_build_p`

Counts above are that command. The skipped test is the existing dogfood module line about grok not on PATH. Lines that print `FAIL: <reason>` during the suite are the recovery-walk test writing receipts, not failures.

The row 07 test was red before the patch (exit 3, reason timeout, recovery asked for a larger --timeout) and green after (exit 1, reason review-rejected). The kolibri recheck test was red before the patch (exit 1, commit-recheck-failed) and green after.

## How each change fails and recovers

- Row 07. Fail: a review reject whose next grok call hits the cap was TIMEOUT exit 3, the reject reasons were dropped, and the recovery told Mark to raise --timeout. There was no run-level deadline, so each implement call, review call, and gate could spend a full --timeout (row 07 wall was 2942s). Recover: the run budget is --timeout times the attempt count from the start of execute. An ordinary call still uses at most one --timeout. A review-reject retry may use the time still left. If that retry still times out, the receipt is FAIL review-rejected exit 1, the reject reasons stay, the timed-out attempt is also recorded TIMEOUT, and the recovery says to change the task or the patch and rerun. A first timeout with no prior reject stays exit 3 and still says to rerun or pass a larger --timeout. A hung gate stays TIMEOUT. The worktree is still removed on failure.
- F2. Fail: the review prompt cuts the diff at 12000 characters and the receipt never said whether that happened, so a 60 to 250 line patch could not prove the cap. Recover: `review.truncated` is true when the redacted diff is past the cap and false when the reviewer saw the whole diff. The prompt still carries the `...[diff truncated]` marker when it cuts. A run that never builds a review prompt reports truncated false.
- F3. Fail: finish() removes the worktree, so a reject followed by a timeout left prose tails and no patch (row 07 attempt 2). Recover: record() stores the redacted unified diff on the review-rejected attempt while the worktree still exists. The diff is not cut at the review cap. The worktree is still removed, and no branch is kept. The operator can reapply the diff from the receipt. Other attempt reasons do not get a diff field.
- Kolibri recheck. Fail: `git archive` has no .git, so a gate that runs git walked up into the caller repo. Review could accept and the recheck still failed with no SHA (selfhost2 item 02, attempts 1 and 3). Recover: recheck_sha builds a nested repo whose index is the archived tree, with commit hooks and gpg turned off, then runs the gate. Git's toplevel is the extract. Gitignored files are still absent from the archive, so a helper that exists only in the worktree still fails recheck and a clean retry can land. The nested repo and the empty hooks dir are removed in the finally block.

## Cross-lane requests

- mvp-surface: docs/modules/pfy-build.md and docs/ops/pfy-build-daily.md still describe --timeout as both "seconds for one grok call" and "bound the run." After row 07, one ordinary grok call or gate stays at --timeout, and the run budget is --timeout times the attempt count. This lane did not edit those files.
- mvp-integrate-1031: merge `bot/mvp-timeoutfix-1031` (merge, not rebase) when collecting pass 3. Do not rebase this branch.

## OQ drafts

- OQ draft, test-file usage note. When should `./pfy build` refuse to start because the task was supposed to add a test and the tree has no new test file? Gom wave 5 #1 asked for a usage note instead of pre-committing a red test the model must not edit. Today a path absent from the base test hash may reach the gate, and an edit or delete of a base test is tests-tampered unless `--writable-test` names it. A sentence heuristic would mis-fire. Needs a human rule before any runner change.
- OQ draft, gate env allowlist. Should the product gate start from an allowlist instead of the current denylist? Wave 5 receipts had no AKIA, PEM, sk_, ghp_, or xai- markers after the denylist. A short allowlist that keeps only PATH and TMPDIR drops VIRTUAL_ENV and PYTHONPATH and breaks the venv gates gom runs. Needs a named allowlist before any runner change. Grok itself must keep child_env(), because the operator login lives there.

## Gate

Tester plus Reviewer. This branch changes the cloud runner (`scripts/pfy_build_cloud.py`) and `tests/test_pfy_build_cloud.py`.

Pregate not run: this lane's drop-in says do not run scripts/pregate.sh. At 2026-11-01T01:29Z `Runner.Worker` was idle and `~/DEVELOP/pfy-mentat/tmp/heavy-1030.lock` was free, so this was not "host busy."

## Next step

Leave this branch unmerged. The integrate lane merges `bot/mvp-timeoutfix-1031` after `origin/bot/mvp-cloudfix-1031`. Review the four runner commits above. No further timeoutfix item is waiting unless a later dogfood branch names a new cloud-runner finding.
