### Entry 028: fable-method — Structured Problem-Solving Loop + Adversarial Verification for Any Model

- **URL**: https://x.com/i/status/2076727080402948561
- **Date**: 2026-07-13
- **Poster**: Alex Prompter (@alex_prompter)
- **Summary / Key Claims**: Distills Fable's problem-solving approach into an installable plugin any model can use. Contains three main components:
  - `fable-method`: Structured problem-solving loop with hard failure thresholds.
  - `fable-loop`: Runs full tasks with adversarial verification agents that check the work.
  - `fable-judge`: Treats every "done, all tests pass" claim as unverified and independently re-runs verification.
  Strong measured results on catching wrong tests, false completion claims, and planted frauds (e.g., Haiku went from 0/4 to 4/4 on catching wrong tests; Sonnet + plugin matched Fable itself on complex research tasks). Importantly, it adds little overhead on ordinary tasks with capable models — value concentrates on traps and weaker/unattended models. MIT licensed with all evaluation transcripts committed. Installable in Claude Code via plugin marketplace.
- **Extracted Repos / Tools**: Primary: https://github.com/Sahir619/fable-method (MIT, full eval transcripts included). Plugin for Claude Code that brings structured verification loops to any model.
- **TOOLS.md Link**: New row under Agent Frameworks & Orchestration / Autonomous Loops & Verification (high-signal verification/hardening tool). Strong fit for loop engineering and agent robustness.
- **Notes**: **Excellent high-signal addition.** Directly complements and extends our loop engineering work (especially goal-based evaluators, adversarial review, and self-healing patterns from Entries 018/021/024/027). The adversarial verification + hard failure thresholds + independent judge approach is a concrete, evaluated implementation of robust goal-based and proactive loops. Strong emphasis on catching false positives in agent output is highly relevant for production hardening. Low-to-medium redundancy — it's a focused verification layer rather than a full framework. High fit for evaluation criteria: Very High Relevance (structured verification + adversarial loops), High Integration Ease (plugin format, works with existing agents), High Reproducibility (MIT + full transcripts), Low Redundancy. Perfect for the repo's focus on reliable autonomous systems. Recommend: (1) Catalog as major verification/hardening resource. (2) Strong candidate for adaptation into our loop-engineering skill pack (e.g., as a fable-method inspired evaluator or judge skill). (3) Excellent for hardening AgenC-based workflows, especially with weaker models or unattended runs.
- **Status**: Processed and cataloged (added as high-value adversarial verification loop resource; priority for skills integration)

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