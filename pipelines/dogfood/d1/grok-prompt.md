Implement D1 dogfood chore ONLY in this worktree. Cite dogfood D1 / ADR-0016 / #230 only. Catalog HOLD 70-75. No Mark. No product UI. No #258. No Kolibri. No TypeSafe account/spend. No TYPESAFE_API_KEY.

## DoD
1. Add `data/decision-gates/README.md` explaining versioned offline decision-gate stubs for org/pfy shadow mode (Choice/Score/Noul criteria + conf gate in-repo; offline fallback; no SDK lock-in). Mention primary local path is CUA-S1-FORMS / org-spinny-decide; TypeSafe cloud optional and unkeyed.
2. Add `data/decision-gates/push_hold.shadow.v0.json` — a small schema stub for the org `push_hold` gate (state fields like ci/kronos/known_red, criteria keys push|hold|escalate, conf_gate 0.55 note matching org-spinny defaults, schema_version, engine preference local). This is documentation/schema only — do NOT call any API and do NOT implement a live bridge.
3. Add a short cross-link bullet at the end of `docs/ops/jev-230.md` pointing to `data/decision-gates/` and noting D1 dogfood.
4. Update the Jev section **Next** bullets in `docs/PENDING-HANDOFF.md` so item (2) says D1 bot lane in progress / stub landed; keep all other handoff sections intact (including #256 and Kolibri watch-only).
5. Do NOT create docs/dogfood/D1-RESULTS.md — the orchestrator will add the receipt separately.
6. Run no network installs. Keep changes docs/data only (plus the ops/handoff docs above).

After edits: `git status` and stop. Do not push. Do not open a PR.
