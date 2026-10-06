# Build drop-in: Gom Jabbar (jobbar-master), one main for T-0049

Paste everything below the line into Grok Build on nimo.

---
Repo: `~/DEVELOP/jobbar-master/current` (GitHub themark-net/gom-jabbar-grok4). Read AGENTS.md, docs/DECISIONS.md, docs/ARCHITECTURE.md, docs/TODO.md, docs/PENDING-HANDOFF.md first.

Situation (2026-10-06): the local `main` is **9 commits ahead and 9 behind** `origin/main`. The local side is UI and fit work from 2026-09-25 (Home auto-run, matched roles under fit, add-a-role, tailor from matched roles, browser fills; 66 files, about +4.2k lines), also on `origin/founder-build-babysit/*`. `origin/main` has pulls 29–31 (catalog tier + S/A boost, T-0049 CLI fixes, heuristic skill-gap asks). The checkout also has uncommitted edits in `gomjobbar/draft_sources.py`, `gomjobbar/ui/simple.py` and `tests/test_draft_sources.py`. **Leave the checkout and its edits alone.**

Goal: one tree that has both lines of work, so Mark can run T-0049 (daily use of the closed loop on a real journal) on a single `main`.

Steps:
1. `git fetch && git worktree add /tmp/gj-reconcile -b build/reconcile-0925-ui origin/main`, then `git merge --no-ff <local main SHA>` (record the SHA). Resolve conflicts so both behaviors survive. Where they truly contradict, keep origin/main's decision-backed behavior and note the loss in the handoff.
2. Do not add scrapers, Playwright, JobSpy, journal ROI, T-0025, T-0027 or T-0028. No auto-submit (Decision 0006): `submitted` stays false everywhere.
3. If a DSPy / LLM path is touched: with no keys it must use the heuristic path and not hang (pull 30 behavior).

Definition of done (behavior and fail-and-recover):
- Full suite `uv run pytest -q` is green on the merged tree. Report counts before and after.
- A sociable E2E on a temp sim journal (`python -m gomjobbar.sim_dogfood`) walks Today → Capture (mobile fixture) → Jobs → Fit → Tailor → Handoff. It asserts that matched roles appear under the fit score, that `Can you cite Go?` is still emitted for sim role 0 with no LLM, and that the handoff pack has `submitted=false`.
- A recovery test: a malformed posting or failed fetch shows honest error copy and leaves the journal unchanged (no partial `job_leads` row).
- A Streamlit smoke (AppTest or headless) proves Home renders with an empty journal and with a seeded one.
- No real journal is touched. Use `tmp/` paths only.

Handoff: add a dated section to docs/PENDING-HANDOFF.md: merge base, both SHAs, conflicts and how each was resolved, anything dropped, what Mark must try for T-0049.
PR: push `build/reconcile-0925-ui` and write the body to `/tmp/pr-gj-reconcile.md`. Use `gh pr create --draft --body-file` if authenticated, otherwise print `https://github.com/themark-net/gom-jabbar-grok4/compare/main...build/reconcile-0925-ui?expand=1`.
Gates: draft PR, do not merge. Tester and Reviewer gate it, and Mark decides whether the 09-25 UI lands. Do not reset or force-push local `main` or any `founder-build-babysit/*` branch.
