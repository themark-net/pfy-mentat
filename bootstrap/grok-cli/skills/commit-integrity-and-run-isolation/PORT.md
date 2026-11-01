# commit-integrity-and-run-isolation: first-party port

- **Placement:** `bootstrap/grok-cli/skills/commit-integrity-and-run-isolation/` (portable SoT)
- **Org Bot skill:** pointer only. SoT: pfy `bootstrap/grok-cli/skills/commit-integrity-and-run-isolation`
- **Taken:** six commit-integrity rules, run-isolation rules, tester probe checklist, rule to commit map (mvp3 review loop, 2026-10-31)
- **Omitted:** bot-only ids, lane names beyond branch references
- **Invoke:** `/commit-integrity-and-run-isolation` after install
- **Verify:** `make smoke-grok-skills` ([skill-verification.md](../../../../docs/ops/skill-verification.md))
