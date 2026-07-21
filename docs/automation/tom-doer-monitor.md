# Tom Doerr (@tom_doerr) Monitor Procedure

**Purpose**: Keep the pfy-mentat catalog up to date with high-signal LLM/agent/tool repos posted by @tom_doerr (very active sharer of GitHub repos focused on DSPy, agents, RAG, inference, and related tooling).

**Standing Request** (recorded in memory): Perform regular checks of @tom_doerr posts. Add relevant repos following the standard X-seed process (Entry NNN in sources/x-posts.md + evaluation + catalog update). Apply 7-day relevance volume review.

## Search Template (use via x_keyword_search or manual)

``` 
from:tom_doerr since:YYYY-MM-DD filter:has_mentioned_url (LLM OR agent OR DSPy OR RAG OR inference OR "local llm" OR ollama OR "grok cli" OR mcp OR context OR repo OR github)
```

Limit to recent days. Focus on posts that link to GitHub repos (most of his content does).

## Relevance Criteria (must meet most)

A post/repo is **relevant** for addition if it aligns with the repo purpose (Track • Categorize • Rank • Integrate local/self-hosted LLM dev tools for Grok CLI + MCP memory + pipelines):

- **Primary fit**: Local or self-hostable LLM inference, agents, frameworks, context/RAG/memory systems, tool calling, orchestration (DSPy/LangGraph-style), efficiency tools (token/context optimization), or direct integration points for Grok CLI / LiteLLM / MCP.
- **Code/repo value**: Actual GitHub repository with code, benchmarks, quickstart, or clear usage instructions (not pure discussion or tweet threads without repo).
- **Pipeline impact**: Improves efficiency (tokens, latency, cost, file reads, tool calls), reliability, or integration ease in local/hybrid agent pipelines.
- **Unique or complementary**: Adds distinct value even if there is partial overlap with existing entries (e.g., better benchmarks, lighter implementation, new integration surface). Redundancy is acceptable if measurable improvement is clear (see repowise example).

**Exclude**:
- Pure cloud-only SaaS wrappers with no realistic local/self-hosted path.
- Low-signal reposts or opinion threads without concrete tools/repos.
- Non-LLM/AI tooling (general dev tools unless strongly agent/LLM related).

## Daily / Regular Check Process

1. Run the search query for the desired time window (daily = last 24–48h; or on-demand).
2. For each post with a GitHub link:
   - Fetch basic repo info if needed.
   - Apply relevance criteria above.
   - If relevant: Create new Entry NNN in `sources/x-posts.md` (copy exact format from previous entries, include post URL, summary, extracted repo, relevance notes, and proposed catalog placement).
3. Propose the addition (or auto-add if following established pattern) and update `TOOLS.md` + `data/tools.json` with initial scores per CATEGORIZATION.md.
4. Log the check (date, number of posts reviewed, number added as relevant).

**Trigger phrase for me**: "run tom doer check" or "tom doer daily check" (I will execute the search + filtering + propose additions).

## 7-Day Relevance Volume Review (every 7 days)

**Trigger**: "run 7-day tom doer review" or on the 7th day of the cycle.

**What I will do**:
1. Review all @tom_doerr posts in the past 7 days using the search template.
2. Count **unique relevant tools/repos** that were identified as suitable for the catalog (after applying relevance criteria).
3. Report:
   - Total posts reviewed.
   - Number of unique relevant repos found.
   - Number actually added/proposed in the period.
   - Any patterns (e.g., high volume of DSPy/agent repos, low local-inference signal).

**Decision rule**:
- If **unique relevant tools identified < 7 in the past 7 days**:
  - I will recommend switching the schedule from daily to **weekly**.
  - Option A: Update this document and memory to weekly (I can do this directly).
  - Option B: Notify you with the data and ask for confirmation to change the schedule (use this if you prefer manual control or if the change feels outside current automation scope).
- If volume is consistently high (≥7–10+ unique relevant per week), keep daily or increase scrutiny on quality.

This prevents low-value daily noise while still capturing the good signal @tom_doerr provides.

## Current Schedule Preference

**Initial**: Daily checks (on-demand via trigger phrase), with automatic 7-day volume review.
**Adjustment logic**: As defined above. I will update this section and memory when a change is made.

## Notes & Scope Limitations

- I cannot run fully autonomous persistent background/cron jobs. The practical system is **documented procedure + on-demand execution** when you trigger it ("run tom doer check").
- For closer-to-automatic daily runs, options include:
  - Simple cron job or GitHub Action on your machine/repo that posts a comment or DMs/triggers me with the phrase.
  - Phone/calendar reminder + quick prompt to me.
- All additions still follow the established quality bar and process (no low-quality spam added).
- Overlaps with existing entries are evaluated honestly (measurable improvement required).

## History Log (append new checks here)

| Date | Window | Posts Reviewed | Relevant Found | Added/Proposed | Notes |
|------|--------|----------------|----------------|----------------|-------|
| (Start) | - | - | - | - | Procedure initialized |
| 2026-07-20 | 2026-07-20 | 1 (MUE-X post) | 1 | 1 (Entry 067 MUE-X) | Self-evolving AST-mutation agent; high signal self-modifying + absorption. Stage 0 pass. |

*Maintained to support the 7-day review and schedule tuning.*
