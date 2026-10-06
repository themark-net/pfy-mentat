# Build drop-in: Leasegrid (leasegrid-c), issue #26 Android recovery-file path

Paste everything below the line into Grok Build on nimo. **Pasting this is the founder RELEASE for #26 only.** The org posture is otherwise PAUSED.

---
Repo: `~/DEVELOP/leasegrid-c` (GitHub themark-net/leasegrid-c). Read AGENTS.md, docs/PENDING-HANDOFF.md (including the P4-B #44 section), docs/design/README.md, docs/09-ui-track-P4-ANDROID-POINTER.md, docs/ops/u4-recovery.md, docs/ops/p4-android-dogfood.md first.
Worktree: `git fetch && git worktree add /tmp/lg-26 -b build/android-recovery-relpath-26 origin/main`. The nimo checkout is 12 commits behind and has a dirty `.gitignore`. Do not touch it.

Context: P4-A read and P4-B write (#44, merged in #46) are on main. #28 Offer → settlement has code and `tests/test_offer_settlement.py` on main. #26 is the remaining Android residual: `EXTRA_RECOVERY_FILE` passed as a **relative** path fails, while absolute paths PASS.

Goal: a relative `EXTRA_RECOVERY_FILE` resolves the same way as an absolute one, or fails with honest UI copy and a way back, never silently.

Steps:
1. Run `/investigate` first. Write a root-cause hypothesis (which base dir, which process, scoped storage or Magic Folder download dir) before any fix.
2. Fix in the smallest place (Android intent handling and/or `src/` recovery import). No new settings screen. Design 35–39 and 55–59 stay unchanged.
3. Keep #30 (multi-host Magic Folder 500) and #33 (introducers) out of scope.

Definition of done (behavior and fail-and-recover):
- A test where a relative path under the app's documented base dir restores the same state as the absolute path (same files, same grid membership).
- A test for a relative path that escapes the base dir (`../`) or does not exist: it is refused with the user-facing message from design and the existing state is untouched. Re-running with a good path then succeeds (recovery).
- The existing `android/pytests` and `tests/` stay green. Report counts. Live-grid tests run only if documented as runnable on nimo, otherwise record them as skipped.
- A debug APK builds in GitHub Actions on the PR head. Record the run id in the handoff (no stale run ids).

Handoff: add a #26 section to docs/PENDING-HANDOFF.md (root cause, fix, SHAs, APK run, what Mark checks on the phone) and a note in docs/ops/p4-android-dogfood.md.
PR: push and write the body to `/tmp/pr-lg-26.md` with `Fixes #26`. Use `gh pr create --body-file` if authenticated, otherwise print `https://github.com/themark-net/leasegrid-c/compare/main...build/android-recovery-relpath-26?expand=1`.
Gates: do not merge or cut a release. Tester and Reviewer gate it. No public marketing, no `v*` tag.
