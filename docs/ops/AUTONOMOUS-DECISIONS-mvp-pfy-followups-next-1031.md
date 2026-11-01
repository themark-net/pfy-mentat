# Autonomous decisions mvp-pfy-followups-next-1031

Run on `bot/mvp-pfy-followups-next-1031`. No questions asked. One line per decision.

1. Choice: the lead executes every item in this worktree, in order, and does not spawn implementation sub-agents. Alternatives: parallel sub-agents on `build/<phase>` worktrees, or shared-checkout sub-agents. Why: the request forbids other worktrees and any worktree under `tmp/` besides this one, requires a push of this branch after every item, and the run log and handoff are shared files. A project-map subagent may write only `.project-map/`.

2. Choice: follow `repo-handoff-doc-required` and `write-loop-exits-first` as the drop-in already states them (handoff doc on every exit; exit card in the run log before item work) plus `.grok/skills/agent-loops`. Alternatives: block until those skill files appear. Why: no `SKILL.md` with either name is in this checkout or `~/.grok/skills`. `prefer-behavior-and-fail-recover-tests` is present and is followed.

3. Choice: do not run `scripts/pregate.sh` even if the GitHub runner is idle. Alternatives: run it once at the end under the heavy flock when `Runner.Worker` is absent. Why: this lane's drop-in says "Do not run scripts/pregate.sh". The handoff will record that. The generic pregate sentence in the same drop-in loses to the explicit forbid.

4. Choice: for #300 deferred 4, stderr `Pulling image <ref>` wins when both lines are present, and a stdout cache line is still evidence when stderr has no pull. Alternatives: drop the stdout branch entirely, as the fix2 handoff suggested. Why: mvp2 t1 was reviewed and accepted with the cache-only branch kept, and `test_h_oci_cache_stdout_branch` exists to kill the mutant that ignores stdout. Dropping that branch would make a known-good cache-only run fail.

5. Choice: treat the #303 OpenLore panic note and the "catalog_check was not run" note as already closed on main. Alternatives: add another orient-error check, or re-run a full unittest discover to recreate the 2026-10-17 receipt. Why: the smoke already requires orient to rank applyDiscount, sets a writable TMPDIR, and sets `OPENLORE_NO_UPDATE_NOTIFIER=1`. The 2026-10-17 handoff round 2 records 421 tests OK and catalog_check PASS. This lane still runs catalog_check and the x-intake smoke unit tests. A full discover is a heavy job and is not required to close a note that is already recorded.

6. Choice: skip the live smolvm digest run. Alternatives: download smolvm, or treat `/dev/kvm` being present as enough. Why: the binary `~/DEVELOP/pfy-mentat/tmp/smolvm/smolvm` is absent. The drop-in says item 12's live digest is blocked. No download, no sudo.

7. Choice: after the #300 deferred list, land the unlanded content-hash `tree_sig` from mvp2 t2 and t6 (119, then 112, 115, and 117). Alternatives: stop at lane empty once the deferred list is done, or also rewrite every older smoke. Why: those four still hash size and mtime, so a touch false-fails a real-HOME check and a same-size edit that restores mtime is invisible. The cloud patches were accepted and never merged. Same x-intake smoke area, no model, no sudo. 122 and 128 stay as they are.

8. Choice: stop after that content-hash change. Alternatives: also convert the size-and-mtime signatures in smokes 148 and 149, or start the #303 Harness Score eval-auto trial. Why: 148 and 149 are later intakes outside the accepted mvp2 t2 and t6 set. The #303 recommended next steps need other product repos, a model comparison, or Mark. That is lane empty.
