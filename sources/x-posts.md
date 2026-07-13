### Entry 025: all-agentic-architectures — Benchmark Comparison of 35 Agentic AI Architectures

- **URL**: https://x.com/i/status/2076628874918560153
- **Date**: 2026-07-13
- **Poster**: Tom Dörr (@tom_doerr)
- **Summary / Key Claims**: Comprehensive comparison of 35 different agentic AI architectures against a 17-task benchmark leaderboard. Provides a structured way to evaluate and compare various agent designs, frameworks, and patterns. Includes a GitHub repository with the architectures and benchmark results.
- **Extracted Repos / Tools**: Primary: https://github.com/FareedKhan-dev/all-agentic-architectures — Library comparing 35 agentic architectures on a 17-task benchmark.
- **TOOLS.md Link**: New row under Agent Frameworks & Orchestration / Benchmarks & Evaluation (high-value evaluation resource).
- **Notes**: **Strong addition for our evaluation strategy.** Directly supports the repo's goal of rigorous evaluation and reproduction of best practices. Useful for comparing our AgenC augmentation + loop engineering approaches against other agentic patterns. The 17-task benchmark provides concrete metrics for assessing autonomy tiers, workflow robustness, and tool-use effectiveness. High fit for evaluation criteria: Very High Relevance (agent architecture benchmarking), High Integration Ease (reference library for comparison), High Reproducibility (open benchmark results), Low Redundancy (fills evaluation gap). Recommend: (1) Catalog as core benchmark resource. (2) Use as reference when refining our own evaluation rubric for loop engineering and AgenC skills. (3) Consider running subsets of the 17 tasks against our implementations for objective comparison.
- **Status**: Processed and cataloged (added as major agentic architecture benchmark resource; high value for evaluation framework)

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