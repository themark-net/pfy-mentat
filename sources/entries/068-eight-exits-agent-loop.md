### Entry 068: 8 Exits for Agent Loops — Complete Stop-Condition Framework

- **URL**: https://x.com/i/status/2079325855155707941
- **Date**: 2026-07-20
- **Poster**: Hanako (@hanakoxbt)
- **Summary / Key Claims**: "your agent loop needs 8 exits. most people ship only one." Clean, production-oriented taxonomy of stop conditions for agent loops, with concrete triggers and failure modes each exit prevents. Accompanied by a high-quality 40s animated explainer video. Builds on the author's earlier article (quoted). Core claim: a loop with one exit hangs; a loop with eight is a system. Write the exits before you write the prompt.

  The eight exits:
  1. **Goal met** — external evaluator scores against a rubric; stop on pass (not when the model claims done).
  2. **Turn cap** — hard iteration ceiling enforced by the harness, not the prompt.
  3. **Budget cap** — tokens or dollars, whichever hits first; the exit that saves the 3am bill.
  4. **Wall clock** — absolute elapsed-time deadline (deploy windows, business hours).
  5. **No progress** — state hash every turn; halt after N consecutive identical states (busy ≠ moving).
  6. **Human interrupt** — approval gates + external kill switch the model cannot override.
  7. **Error threshold** — consecutive-failure counter that resets on success; halt at n-in-a-row.
  8. **External event** — webhook/poll (PR merged, ticket closed); work becomes irrelevant mid-run.

- **Extracted Repos / Tools**: No primary new code repo. Pure methodology + video. Related reply mentions https://github.com/SolvensAmoris/starkcore (unrelated SAT verifier). Author's body of work repeatedly references loop harness patterns, checkpoints, and 12-factor agents concepts.
- **TOOLS.md Link**: Reinforces / expands the **Finn Loop / eval-loop patterns** row and the broader Autonomous Loops & Agentic Workflows cluster (Entries 018, 021, 024, 027, 031, 032, 048). Recommended as canonical "exit conditions" checklist for any new loop skill or harness. High pipeline value for Grok CLI + agent-cage + write-guard + eval-harness.
- **Notes**: Stage 0 N/A (methodology). Extremely high relevance — this is the missing practical completeness layer on top of the 4-tier autonomy / goal-based / proactive loop material already cataloged. Most prior entries emphasize starting/continuing loops or verification; this one systematically enumerates *how they must be allowed to die*. Directly actionable for T-0048 (port S-tier patterns) and any loop-engineering skill work. The "write the exits first" rule is excellent process hygiene. Video is clean pedagogical asset. Recommend: (1) Catalog as core Autonomous Loops resource. (2) Distill the 8 exits into a first-party skill or section of the loop-engineering pack / AGENTS.md. (3) Use as checklist when reviewing any new autonomous workflow or company-style system. (4) Pair with existing no-progress / error-threshold / budget patterns already in Hermes, fable-method, and eval-loop entries.\n- **Status**: Quick-evaluated - cataloged (methodology reinforcement; pattern extraction queued)
