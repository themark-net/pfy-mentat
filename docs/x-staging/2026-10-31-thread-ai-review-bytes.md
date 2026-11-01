---
status: humanized
lesson: ../lessons/LESSONS.md#l01-review-exact-bytes
kind: thread
posts: 5
chars: [178, 232, 243, 255, 189]
posted_url:
---

# 2026-10-31-thread-ai-review-bytes

Thread 1/5 to 5/5, drafted and humanized 2026-10-31 (text from the writer's xposts.py).

Lesson: [l01-review-exact-bytes](../lessons/LESSONS.md#l01-review-exact-bytes)

## Post 1 (178 chars)

```text
1/5 We gate every AI-written change with a second AI reviewer plus a tester. Today the tester found four ways a commit got past review without the reviewer actually seeing it. 🧵
```

## Post 2 (232 chars)

```text
2/5 Hole 1: the test step ran after review and could rewrite a file the reviewer had already approved. The rewritten version is what got committed. Fix: hash what was reviewed, hash what's being committed, and refuse if they differ.
```

## Post 3 (243 chars)

```text
3/5 Hole 2: symlinks. A link inside the repo pointed at a file outside it. It got followed, so that file's contents landed in the review prompt and the receipts. Fix: never follow links, and treat any link that leaves the repo as out of scope.
```

## Post 4 (255 chars)

```text
4/5 Hole 3: the prompt silently cut diffs at 8,000 characters, but the size limit counted lines, so one long line hid everything after it. Hole 4: binary changes showed up as "Binary files differ." Fix: if the reviewer can't see the whole diff, refuse it.
```

## Post 5 (189 chars)

```text
5/5 The lesson: an AI review only counts for the exact bytes it saw. Treat it as a contract on content, not on file names. If your agent setup stages files by name after review, check that.
```
