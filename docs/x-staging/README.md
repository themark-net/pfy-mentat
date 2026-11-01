# X staging

Staging area for X posts that share lessons from [docs/lessons/LESSONS.md](../lessons/LESSONS.md). Only lessons the org learned itself go here, never catalog ideas or other people's posts.

**Bots never post.** Bots draft, humanize and stage. Mark posts from his own account.

## Flow

1. **draft**: a bot writes the post from one LESSONS.md entry. Every claim and number must match the entry's citation.
2. **humanized**: the writer bot does a humanizer pass (plain words, no hype, no em dashes, still at or under 280 characters).
3. **ready**: Mark reviews the text and says OK. Edits go back to `humanized`.
4. **intent link**: a bot generates `https://x.com/intent/post?text=<url-encoded post>` for each post and adds it under the post.
5. **posted**: Mark opens the link and posts it himself. A bot then sets `status: posted`, fills `posted_url:`, and sets `posted: yes` on the lesson.

When a post is staged here, the lesson's `posted:` field is `staged` once it reaches `humanized`, and `yes` once it is posted.

## One file per post or thread

Name: `YYYY-MM-DD-<letter-or-thread>-<slug>.md`. Frontmatter:

```yaml
---
status: draft          # draft | humanized | ready | posted
lesson: ../lessons/LESSONS.md#l01-review-exact-bytes
kind: standalone       # standalone | thread
posts: 1
chars: [182]           # X-weighted count per post; each must be <= 280
posted_url:            # filled after Mark posts
---
```

Each post goes in its own `text` code block under a heading that repeats its character count.

## Counting characters

Count the way X does: most characters count 1, emoji and CJK count 2, and a URL counts 23. Re-count after every edit. A minimal counter:

```python
def xlen(s):
    return sum(1 if (o <= 4351 or 8192 <= o <= 8205 or 8208 <= o <= 8223 or 8242 <= o <= 8247) else 2
               for o in map(ord, s))
```

## Intent links

```python
import urllib.parse as u
print("https://x.com/intent/post?text=" + u.quote(post, safe=""))
```

For a thread, Mark posts 1/N from its link, then replies to it with each next post.

## Index

| File | Kind | Status | Lesson |
|------|------|--------|--------|
| [2026-10-31-thread-ai-review-bytes.md](2026-10-31-thread-ai-review-bytes.md) | thread 1/5 to 5/5 | humanized | L01 |
| [2026-10-31-a-local-vs-cloud.md](2026-10-31-a-local-vs-cloud.md) | standalone A | humanized | L04 |
| [2026-10-31-b-64gb-claim.md](2026-10-31-b-64gb-claim.md) | standalone B | humanized | L05 |
| [2026-10-31-c-flaky-parallel-tests.md](2026-10-31-c-flaky-parallel-tests.md) | standalone C | humanized | L02 |
| [2026-10-31-d-mutants.md](2026-10-31-d-mutants.md) | standalone | draft | L09 |
| [2026-10-31-e-stray-service.md](2026-10-31-e-stray-service.md) | standalone | draft | L06 |
| [2026-10-31-f-shallow-clone.md](2026-10-31-f-shallow-clone.md) | standalone | draft | L03 |
| [2026-10-31-g-state-line.md](2026-10-31-g-state-line.md) | standalone | draft | L11 |
| [2026-10-31-h-pinned-sha.md](2026-10-31-h-pinned-sha.md) | standalone | draft | L10 |

Not staged yet: the 2026-10-31 thread recap. Its text was not in the writer's draft file, so it was not copied here. Add it as its own file when the text is found.
