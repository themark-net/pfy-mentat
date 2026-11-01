---
status: draft
lesson: ../lessons/LESSONS.md#l03-shallow-clone-skip
kind: standalone
posts: 1
chars: [198]
posted_url:
---

# 2026-10-31-f-shallow-clone

New draft 2026-10-31. Needs the writer bot's humanizer pass.

Lesson: [l03-shallow-clone-skip](../lessons/LESSONS.md#l03-shallow-clone-skip)

## Post (198 chars)

```text
A test that can't run its check should never pass quietly. Ours returned early in CI's shallow clone and counted as green. Now it calls skipTest with a reason, so a skip reads as a skip, not a pass.
```
