### Entry 032: Eval Loop — Rubric-Driven Verification to Eliminate AI Slop

- **URL**: https://x.com/i/status/2076669336853606446
- **Date**: 2026-07-13
- **Poster**: Shann³ (@shannholmberg)
- **Summary / Key Claims**: Excellent practical framework for an "eval loop" to prevent AI slop. Core idea: Better prompts and bigger models aren't enough — you need a structured evaluation layer that catches low-quality output before it reaches the user. The base loop is:
  1. Write a specific rubric first (the quality bar)
  2. Agent drafts as usual
  3. Model scores the draft against the rubric (0-1 score)
  4. Anything below the bar goes back for another pass
  5. Every miss caught becomes a permanent new line in the rubric
  Layers of increasing rigor: Self-check → Independent check → LLM council (multiple models) → Human as final gate. Match the layer to the stakes of the output. The rubric acts as a living quality net that improves over time.
- **Extracted Repos / Tools**: No new standalone repo (framework/pattern). Strong conceptual and practical alignment with goal-based evaluation and self-healing loops.
- **TOOLS.md Link**: New row under Agent Frameworks & Orchestration / Autonomous Loops & Agentic Workflows (high-signal eval/verification pattern).
- **Notes**: **High relevance.** This is an outstanding practical reinforcement of our loop engineering work (especially goal-based evaluators, self-healing patterns, and adversarial verification from Entries 018/021/024/027/031). The rubric-driven scoring + iterative improvement of the rubric itself is a clean, implementable way to build reliable evaluation into agent loops. The layered approach (self-check to council to human) gives clear guidance on trading off cost vs. rigor. Strong overlap with fable-method style verification and the generate-test-update feedback loop. High fit for evaluation criteria: Very High Relevance (rubric-driven eval loops), High Integration Ease (patterns are directly portable to skills), High Reproducibility (clear step-by-step framework), Low Redundancy. Excellent for the repo's reproduction goals. Recommend: (1) Catalog as major eval loop resource. (2) Strong candidate for direct integration into our loop-engineering skill pack (e.g., as a rubric-driven evaluator skill or self-healing pattern). (3) Highly actionable for hardening AgenC-based autonomous workflows and reducing low-quality outputs.
- **Status**: Processed and cataloged (added as high-value rubric-driven eval loop resource; priority for skills integration)

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