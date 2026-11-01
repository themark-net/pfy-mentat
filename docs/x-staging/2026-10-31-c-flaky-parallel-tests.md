---
status: humanized
lesson: ../lessons/LESSONS.md#l02-run-isolation
kind: standalone
posts: 1
chars: [163]
posted_url:
---

# 2026-10-31-c-flaky-parallel-tests

Standalone C, humanized 2026-10-31.

Lesson: [l02-run-isolation](../lessons/LESSONS.md#l02-run-isolation)

## Post (163 chars)

```text
Running 10 AI dev lanes on one box turned up a new class of flaky test: anything that watches shared /tmp or ~/.cache. Fix: give every run its own TMPDIR and HOME.
```
