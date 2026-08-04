### Entry 057: Not Diamond Code — Intelligent Model Router for Long-Horizon Coding Agents

- **URL**: https://x.com/i/status/2084669945150062619
- **Date**: 2026-08-04
- **Poster**: Tomas Hernando Kofman (@tomas_hk)
- **Summary / Key Claims**: Commercial product announcement: Not Diamond Code routes model + reasoning effort per step for long-horizon coding agents (any harness/gateway, incl. Claude Code). Claims 20–65% cost cut without quality loss; Pareto-optimal on SWE-PolyBench-Verified / LongCodeQA approximating Opus 4.8 Xhigh at 39–61% lower cost; multi-provider (Anthropic + GLM 5.2 + DeepSeek V4 Flash) +3.6% quality and savings 39%→66%. Cache-aware trajectory optimization; privacy-preserving local proxy sends only anonymized metadata. Early access; SOC 2 + ISO 27001. Blog: https://www.notdiamond.ai/blog/not-diamond-code-intelligent-model-routing-for-coding-agents
- **Extracted Repos / Tools**: Product: https://www.notdiamond.ai (early access). Related OSS history: Not-Diamond org (e.g. RoRF, archived notdiamond-python, awesome-ai-model-routing) — not the Code product itself.
- **TOOLS.md Link**: None (quick-eval reject: fails Stage 0 — commercial SaaS router; optimization service is cloud-side; local proxy only forwards derived metadata; no self-hostable <5min path for the full Code product).
- **Notes**: High conceptual relevance for multi-model routing in coding agents and LiteLLM/gateway patterns, but not catalogable as a local-first pipeline component. Worth watching if they open-source the long-horizon router or ship a fully local offline mode. Pattern extract only: reward/cost prediction over agent trajectories, cache-aware mid-session switches, harness-agnostic proxy. Do not pin or subtree.
- **Status**: Quick-evaluated - rejected (fails Stage 0: commercial early-access SaaS, not self-hostable product)
