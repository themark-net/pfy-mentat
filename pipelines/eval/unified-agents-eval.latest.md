# Unified Agents pack eval

date: 2026-07-31T03:35Z
source: https://github.com/stretchcloud/claude-code-unified-agents
x_post: https://x.com/i/status/2082997925014053075
agents_scored: 53
pass_gate: 52/53 (98%)
mean_overall: 4.06
median_overall: 4.10
pack_decision: PASS → integrate curated

## Port actions

- **docs_map** (20): agent-generator, blockchain-developer, business-analyst, code-reviewer, context-manager, documentation-writer, ecommerce-expert, embedded-engineer, error-detective, fintech-specialist, game-developer, healthcare-dev, mobile-developer, orchestrator, performance-tester, product-strategist, project-manager, requirements-analyst, technical-writer, test-engineer
- **paths** (30): accessibility-auditor, ai-engineer, angular-expert, api-designer, backend-architect, cloud-architect, data-engineer, data-scientist, database-specialist, deployment-manager, devops-engineer, e2e-test-specialist, frontend-specialist, fullstack-engineer, golang-pro, incident-responder, java-enterprise, javascript-pro, kubernetes-expert, monitoring-specialist, nextjs-pro, performance-engineer, prompt-engineer, python-pro, react-pro, rust-pro, security-auditor, typescript-pro, ux-designer, vue-specialist
- **skip** (3): analytics-engineer, mlops-engineer, workflow-optimizer

## Top overall

| name | cat | overall | struct | port | uniq | rel | dens | action | notes |
|------|-----|--------:|-------:|-----:|-----:|----:|-----:|--------|-------|
| ux-designer | creative | 4.6 | 5.0 | 4.0 | 4.0 | 5.0 | 5.0 | paths |  |
| prompt-engineer | data-ai | 4.6 | 5.0 | 4.0 | 4.0 | 5.0 | 5.0 | paths |  |
| backend-architect | development | 4.6 | 5.0 | 4.0 | 4.0 | 5.0 | 5.0 | paths |  |
| devops-engineer | infrastructure | 4.6 | 5.0 | 4.0 | 4.0 | 5.0 | 5.0 | paths |  |
| security-auditor | quality | 4.6 | 5.0 | 4.0 | 4.0 | 5.0 | 5.0 | paths |  |
| frontend-specialist | development | 4.48 | 5.0 | 4.3 | 4.0 | 4.0 | 5.0 | paths |  |
| python-pro | development | 4.48 | 5.0 | 4.3 | 4.0 | 4.0 | 5.0 | paths |  |
| rust-pro | development | 4.48 | 5.0 | 4.3 | 4.0 | 4.0 | 5.0 | paths |  |
| fullstack-engineer | development | 4.4 | 5.0 | 4.0 | 4.0 | 4.0 | 5.0 | paths |  |
| cloud-architect | infrastructure | 4.4 | 5.0 | 4.0 | 4.0 | 4.0 | 5.0 | paths |  |
| ai-engineer | data-ai | 4.3 | 5.0 | 4.0 | 4.0 | 3.5 | 5.0 | paths |  |
| data-engineer | data-ai | 4.3 | 5.0 | 4.0 | 4.0 | 3.5 | 5.0 | paths |  |
| code-reviewer | quality | 4.3 | 5.0 | 4.0 | 2.0 | 5.0 | 5.0 | docs_map | overlap: mattpocock code-review / ponytail-review |
| test-engineer | quality | 4.3 | 5.0 | 4.0 | 2.0 | 5.0 | 5.0 | docs_map | overlap: make smoke-* / eval-structural |
| golang-pro | development | 4.25 | 5.0 | 4.3 | 4.0 | 4.0 | 3.5 | paths | code-heavy |
| typescript-pro | development | 4.25 | 5.0 | 4.3 | 4.0 | 4.0 | 3.5 | paths | code-heavy |
| database-specialist | development | 4.23 | 5.0 | 3.3 | 4.0 | 4.0 | 5.0 | paths | some Claude-specific tooling |
| api-designer | business | 4.22 | 5.0 | 4.0 | 4.0 | 5.0 | 2.5 | paths | heavy code dump (>75%) |
| incident-responder | infrastructure | 4.22 | 5.0 | 4.0 | 4.0 | 5.0 | 2.5 | paths | heavy code dump (>75%) |
| performance-engineer | infrastructure | 4.22 | 5.0 | 4.0 | 4.0 | 5.0 | 2.5 | paths | heavy code dump (>75%) |

## All agents

| name | lines | overall | pass | action |
|------|------:|--------:|:----:|--------|
| api-designer | 1649 | 4.22 | Y | paths |
| business-analyst | 1323 | 3.93 | Y | docs_map |
| product-strategist | 198 | 4.0 | Y | docs_map |
| project-manager | 170 | 4.0 | Y | docs_map |
| requirements-analyst | 1269 | 3.62 | Y | docs_map |
| technical-writer | 1671 | 3.62 | Y | docs_map |
| orchestrator | 189 | 3.92 | Y | docs_map |
| ux-designer | 194 | 4.6 | Y | paths |
| ai-engineer | 132 | 4.3 | Y | paths |
| analytics-engineer | 934 | 3.43 | Y | skip |
| data-engineer | 165 | 4.3 | Y | paths |
| data-scientist | 663 | 3.93 | Y | paths |
| mlops-engineer | 805 | 3.43 | Y | skip |
| prompt-engineer | 763 | 4.6 | Y | paths |
| angular-expert | 602 | 4.1 | Y | paths |
| backend-architect | 46 | 4.6 | Y | paths |
| database-specialist | 186 | 4.23 | Y | paths |
| frontend-specialist | 50 | 4.48 | Y | paths |
| fullstack-engineer | 57 | 4.4 | Y | paths |
| golang-pro | 320 | 4.25 | Y | paths |
| java-enterprise | 382 | 3.92 | Y | paths |
| javascript-pro | 404 | 4.1 | Y | paths |
| nextjs-pro | 456 | 4.1 | Y | paths |
| python-pro | 55 | 4.48 | Y | paths |
| react-pro | 469 | 3.85 | Y | paths |
| rust-pro | 228 | 4.48 | Y | paths |
| typescript-pro | 318 | 4.25 | Y | paths |
| vue-specialist | 587 | 4.1 | Y | paths |
| cloud-architect | 80 | 4.4 | Y | paths |
| deployment-manager | 339 | 4.17 | Y | paths |
| devops-engineer | 63 | 4.6 | Y | paths |
| incident-responder | 502 | 4.22 | Y | paths |
| kubernetes-expert | 687 | 4.1 | Y | paths |
| monitoring-specialist | 665 | 4.1 | Y | paths |
| performance-engineer | 649 | 4.22 | Y | paths |
| accessibility-auditor | 1196 | 3.98 | Y | paths |
| code-reviewer | 103 | 4.3 | Y | docs_map |
| e2e-test-specialist | 997 | 3.8 | Y | paths |
| performance-tester | 1071 | 3.78 | Y | docs_map |
| security-auditor | 125 | 4.6 | Y | paths |
| test-engineer | 148 | 4.3 | Y | docs_map |
| agent-generator | 1182 | 3.27 | Y | docs_map |
| blockchain-developer | 141 | 4.2 | Y | docs_map |
| context-manager | 970 | 3.92 | Y | docs_map |
| documentation-writer | 1070 | 3.67 | Y | docs_map |
| ecommerce-expert | 1748 | 3.9 | Y | docs_map |
| embedded-engineer | 1706 | 3.83 | Y | docs_map |
| error-detective | 1019 | 3.92 | Y | docs_map |
| fintech-specialist | 1651 | 3.9 | Y | docs_map |
| game-developer | 1955 | 3.83 | Y | docs_map |
| healthcare-dev | 1612 | 3.83 | Y | docs_map |
| mobile-developer | 180 | 4.2 | Y | docs_map |
| workflow-optimizer | 1106 | 3.02 | N | skip |

## Integration recommendation

1. **Do not** install full Claude Code agent tree as Grok primary (ADR-0002/0009).
2. **Catalog** the pack at I1 (pin + eval receipt).
3. **paths snapshot** curated agents that scored paths + pass_gate.
4. **docs_map** overlaps onto existing first-party skills (gstack-style recipes).
5. Skip domain mega-files as first-party (game/healthcare code dumps) unless product needs them.

