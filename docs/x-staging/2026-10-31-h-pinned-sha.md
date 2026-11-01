---
status: draft
lesson: ../lessons/LESSONS.md#l10-pinned-sha
kind: standalone
posts: 1
chars: [223]
posted_url:
---

# 2026-10-31-h-pinned-sha

New draft 2026-10-31. Needs the writer bot's humanizer pass.

Lesson: [l10-pinned-sha](../lessons/LESSONS.md#l10-pinned-sha)

## Post (223 chars)

```text
We don't open PRs on our own repos. Review gates a pinned commit SHA, then main fast-forwards to it. If main moves during the gate, we merge main in and re-check the delta. A rebase would change the SHA the review approved.
```
