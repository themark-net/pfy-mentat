### Entry 076: claude-codex-settings — Battle-tested Configs, Plugins, Hooks & Agents

- **URL**: https://x.com/i/status/2082298878137651635
- **Date**: 2026-07-29 (post); cataloged 2026-07-28
- **Poster**: Tom Dörr (@tom_doerr)
- **Summary / Key Claims**: Battle-tested configurations, plugins, hooks, and agents for Claude Code, Codex CLI, Gemini CLI, and Cursor. Structured to fix common AI coding pitfalls (overcomplication, lack of clarification, unmanaged inconsistencies — references Karpathy critique). Includes plugins for code review, simplification, humanization, second-opinion advisors; hooks for quality enforcement and unsafe-Git blocking; skills for Python/React/frontend/DB/etc.; support for alternative models (Kimi, MiniMax, GLM) via Anthropic-compatible APIs; shared CLAUDE.md / AGENTS.md guidance.
- **Extracted Repos / Tools**: https://github.com/fcakyon/claude-codex-settings — Apache-2.0, ~826 stars. Install via each tool’s plugin marketplace (`claude plugin marketplace add …`, `codex plugin …`, Cursor/Gemini equivalents).
- **TOOLS.md Link**: New row under **Coding & Dev Agents** or **Pipeline & CI/CD** (config/hooks layer). Complements Entry 075 (asm skill manager): asm handles skill install/distribution; this repo supplies opinionated quality hooks, plugins, and shared agent guidance. Useful pattern source for Grok CLI hooks / AGENTS.md / write-guard style policies.
- **Notes**: Stage 0 pass (open, local configs, no SaaS dependency). High practical value for teams running multiple coding agents. Not a runtime itself — distribution of settings/plugins. Recommend: catalog; extract hook patterns (force-push block, simplification-before-commit, AI-buzzword filters) into first-party skill/policy packs; note as reference config set for Claude/Codex/Cursor users in the operator stack.
- **Status**: Quick-evaluated - cataloged (A candidate)
