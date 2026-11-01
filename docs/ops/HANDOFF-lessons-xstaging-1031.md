# Handoff: lessons log and X staging (2026-10-31)

Branch `bot/lessons-xstaging-1031`, worktree `~/DEVELOP/pfy-mentat/tmp/lessons-1031`, cut from `origin/main` 2a74482. Docs only.

## What shipped

- [docs/lessons/LESSONS.md](../lessons/LESSONS.md): 14 cited lessons (L01 to L14) the org learned from its own work. Catalog and other people's X posts are out of scope. Each entry has date, what happened with a citation, the lesson, where it is enforced, and `posted:`.
- [docs/x-staging/README.md](../x-staging/README.md): flow draft, humanized, ready (Mark's review), intent link, posted by Mark. Bots never post. One file per post or thread, X-weighted character counts in frontmatter.
- Seeded posts: thread 1/5 to 5/5 (L01) and standalones A (L04), B (L05), C (L02) as `status: humanized`, lessons `posted: staged`. New drafts D to H (L09, L06, L03, L11, L10) as `status: draft`.
- AGENTS.md links both docs.

## Open

- The 2026-10-31 thread recap text was not in the writer's draft file, so it is not staged. Add it when found.
- Several fixes cited in LESSONS.md are still on `bot/*` branches (mvp3-review-retry, mvp-flake-harness2-1031, mvp-dsv4-1031, doctrine-commit-integrity-1031). The entries say so. When they land, update the "Enforced" lines to main paths.
- L06, L08 and L14 also lean on the org ops journal or another repo (kxbtc15m-scanner, gom-jabbar-grok4); those are named in the entries.

## Next

1. Writer bot: humanizer pass on drafts D to H, set `status: humanized`, lessons `posted: staged`.
2. Mark reviews; on OK, set `ready` and add intent links.
3. After Mark posts: `status: posted`, `posted_url:`, lesson `posted: yes`.
4. New lessons: add an entry with a citation in the same PR or commit as the fix when possible.

## Gate

Docs only: eval-structural CI on the branch, local pregate, Reviewer PASS at the full SHA, then fast-forward main.
