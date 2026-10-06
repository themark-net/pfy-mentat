# Build drop-in: Lotline, Phase B org-can-do kit

Paste everything below the line into Grok Build on nimo. Fill the three FOUNDER lines first, or leave them `TBD` (the prompt then does only the parts that don't need them).

---
FOUNDER niche #1: TBD
FOUNDER soft-quote channel / broker fee intent: TBD
FOUNDER Stripe Payment Link + DEENIS domain: TBD

Repo: `~/DEVELOP/lotline` (GitHub themark-net/lotline). Read docs/PENDING-HANDOFF.md, README.md, ROADMAP-PRODUCT.md, AGENTS.md, docs/NICHE-PICK-AND-KILL.md, docs/templates/* first.
Worktree: `git fetch && git worktree add /tmp/lotline-b -b build/phase-b-kit origin/main`. The nimo checkout is detached. Leave it alone.

Rule: Phase B (first paid test) is HARD STOP until all three FOUNDER lines are real. Never invent a niche, a quote, a domain or a payment link. Zero infra on nimo. Static site only.

Goal: make Phase B a 30-minute-per-lot routine for Mark the moment he supplies the three inputs.

Build (always):
1. `scripts/deal_sheet.py` (stdlib). Validates a filled deal-sheet CSV (goods or brokered) against the frozen ≤12-field schema. It computes margin, enforces the margin floor and the "soft quote recorded before bid" rule, and appends a bid/no-bid line with a reason to `docs/deal-log.md`. Output is a pass/fail verdict per sheet.
2. A 7-day kill clock: `deal_sheet.py status` reports days left per niche from `docs/NICHE-PICK-AND-KILL.md` and prints PARK when it expires with no quotes.
3. Release check: `scripts/site_check.py --release` fails while `site/index.html` still has `#stripe-link-pending`, `aria-disabled` on Pay, or a TBD domain. In normal CI mode it passes. Wire it into `.github/workflows/ci.yml` (non-release mode).
Build (only if all three FOUNDER lines are filled): put the niche and the 7-day kill into NICHE-PICK-AND-KILL.md, the domain into DEENIS-DOMAIN-ROW.md, and the Payment Link into `site/index.html`. Then `site_check.py --release` must pass.

Definition of done (behavior and fail-and-recover):
- Tests feed real-shaped CSVs: a good goods sheet → GO. A sheet with a bid but no soft quote → NO-GO with reason, and the log line is written. A sheet with 13 fields or a missing column → a clear schema error, and no log line.
- A corrupt or partial CSV leaves `docs/deal-log.md` unchanged (atomic append).
- Release-mode check fails on today's tip and passes on a fixture page with a real-looking link.
- CI is green.

Handoff: update docs/PENDING-HANDOFF.md (what exists, how Mark runs a sheet, which FOUNDER inputs are still TBD).
PR: push and write the body to `/tmp/pr-lotline-b.md`. Use `gh pr create --body-file` if authenticated, otherwise print `https://github.com/themark-net/lotline/compare/main...build/phase-b-kit?expand=1`.
Gates: do not merge. Tester and Reviewer gate it. No bids, purchases, posts or outreach.
