---
name: loop-engineering-roadmap
version: 1.0.0
category: autonomy
priority: high
description: Full 14-step roadmap for loop engineering — from manual prompting to fully autonomous agent loops using goal-based evaluation, scheduled loops, proactive dispatch, SKILL.md, worktrees, MCP, and system quality focus.
tags: [loop-engineering, autonomy, agent-loops, self-healing]
---

# 14-Step Loop Engineering Roadmap

This skill turns an agent into a reliable "employee that ships while you sleep." It provides the complete structured path from manual prompting to production-grade autonomous loops.

## Core Principles
- Loop quality depends on system quality.
- Tokens are the real cost — optimize ruthlessly.
- Separate planning, execution, evaluation, and oversight.
- Use MCP, SKILL.md, worktrees, and persistent memory.
- Always include human-in-the-loop gates for high-stakes actions.

## The 14 Steps

1. **Manual Prompting Baseline** — Start with clear, scoped prompts in a single session. Document requirements and success criteria.
2. **Define /goal** — Explicitly state what "done" looks like (tests passing, target scores, bugs cleared, PR ready, etc.).
3. **Implement Goal-Based Evaluator** — Create a separate evaluator agent/model that checks against the goal and sends the main agent back until criteria are met (70% autonomy).
4. **Add Turn-Based Control** — For exploration when requirements are unclear (25% autonomy): one task per round, control returns to you.
5. **Introduce Time-Based Loops** — Schedule periodic checks (e.g., /loop every 5 minutes: check PRs, address review comments, fix CI) (60% autonomy).
6. **Build Proactive Router** — Event fires → router dispatches child agents in parallel → review model oversees output. No human online needed (95% autonomy).
7. **Integrate SKILL.md** — Load reusable skills for planning, coding, review, security, etc. Make skills composable and versioned.
8. **Add Worktrees / Isolated Workspaces** — Each major task or agent gets its own worktree or sandbox for safe parallel execution.
9. **Implement MCP for Tools** — Expose file system, terminal, web/X search, image/video, and custom tools via MCP (client + server).
10. **Add Self-Healing & Traces** — Agents update their own docs, commit traces/worksheets, and use git tags for session continuity.
11. **Cross-Agent Reviews & Personas** — Use different models/personas (maintainability, security, performance, "AI smells") for review gates.
12. **Benchmark & Profiling** — Automatic performance benchmarks, false-confidence audits, and end-of-shift validations.
13. **Task Queue & Night Shift** — Maintain TODOS.md or integrated queue. Support autonomous "night shift" loops that run without supervision.
14. **Production Hardening** — Full permissions model, sandboxing, security audit, monitoring dashboard, and scheduled background agents. Add human approval gates for high-risk actions.

## Usage

Load this skill and ask the agent:

"Follow the 14-step loop engineering roadmap to implement [task] autonomously."

Or invoke specific steps: "/loop-engineering step 6" for proactive router setup.

## Expected Output Format
- Structured plan with autonomy tier chosen
- Success criteria (/goal)
- Evaluator strategy
- Trace of loop iterations
- Final deliverables with review evidence

## References & Related Skills
- 4-tier-autonomy.md (core tiers)
- gstack-role-patterns (specialist behaviors)
- self-healing-docs
- mcp-tool-registry

This skill is part of the Loop Engineering pack for AgenC augmentation.
