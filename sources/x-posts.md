### Entry 024: Finn Loop — Structured Autonomous Coding Loop with Spec/Build/Review + Linear + Slack Approval

- **URL**: https://x.com/i/status/2076752798532931758
- **Date**: 2026-07-13
- **Poster**: Alex Finn (@AlexFinn)
- **Summary / Key Claims**: Practical implementation of a highly autonomous AI coding loop called the "Finn Loop". Uses 3 custom skills (/spec, /build, /review) across multiple agent sessions. /spec turns ideas into detailed Linear specs. /build loop autonomously implements specs and updates Linear status. /review loop performs security/optimization review, browser testing, screenshots, PR creation, and deploys to Vercel sandbox. Notifications sent via Slack with PR link, test steps, executive summary, and sandbox link. Merge triggered by simple rocket ship emoji reaction. Minimal human input: submit ideas + final approval. Claims dramatic productivity gains (100x output, 95% less manual work) by turning "vibe coding" into a mostly autonomous pipeline with clear human gate at the end.
- **Extracted Repos / Tools**: No new public repo yet (skills offered for release soon; workflow described in detail in the post). Strong pattern using Linear for spec/issue tracking + Slack for human approval signaling + Vercel for testing sandboxes. Directly implementable with existing agents (Claude Code, Codex, etc.) via custom skills.
- **TOOLS.md Link**: New entry under Agent Frameworks & Orchestration / Autonomous Loops & Agentic Workflows (high-value practical pattern). Strong complement to our loop engineering work.
- **Notes**: **Excellent real-world example that maps almost 1:1 to our loop engineering efforts (Entry 018/021/022).** The /spec + /build + /review structure is a concrete realization of goal-based + proactive loops with clear evaluator/review stages and human-in-the-loop approval via lightweight signaling (emoji reaction). Strong overlap with gstack role patterns, Multica issue assignment + autonomous execution, Spec Kit structured planning, and our own 4-tier autonomy + 14-step roadmap. The multi-session loop design (separate /build and /review loops) + external notification/approval channel is production-oriented and directly relevant to building robust autonomous systems on top of AgenC. Low redundancy — it's a high-signal workflow pattern rather than a new framework. High fit for evaluation criteria: Very High Relevance (autonomous coding loops with clear human gate), High Integration Ease (skill-based, works with existing agents), High Reproducibility (detailed steps in post; easy to recreate/adapt), Low Redundancy. Perfect for the repo's reproduction goal. Recommend: (1) Catalog as major practical autonomous loop example. (2) Strong candidate for direct adaptation into our loop-engineering skill pack or new AgenC skills (e.g., spec-builder, autonomous-builder, review-with-sandbox). (3) Monitor for the promised skill releases. (4) Synergistic with our existing loop engineering + harness work for production-grade agent loops.
- **Status**: Processed and cataloged (added as high-value real-world autonomous coding loop pattern; priority for integration into loop-engineering skills)

## Future Entries Format

When adding new X-sourced tools or papers:

```
### Entry NNN: Short Title

- **URL**: https://x.com/...
- **Date**: YYYY-MM-DD
- **Poster**: @handle (Name)
- **Summary**: 1-2 sentence gist + why relevant to local LLM dev pipelines. Note if paper-based.
- **Extracted Repos/Tools**: List with links or 'Paper only: arxiv link'.
- **TOOLS.md Link**: Row or section reference.
- **Notes**: Any caveats, hype vs substance, feasibility if paper, pipeline fit.
```

*This log ensures the catalog remains grounded in primary social signals while allowing rigorous, staged evaluation separate from viral claims. 'Read a paper' is now a supported recurring workflow for tool discovery.*