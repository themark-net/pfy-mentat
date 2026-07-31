# claude-unified-agents — paths pack

**Upstream:** https://github.com/stretchcloud/claude-code-unified-agents  
**Pin:** `b026de60c0fc5438f53faffb5cd7f43f84ed3267`  
**X:** https://x.com/i/status/2082997925014053075  
**Policy:** ADR-0009 hybrid · integration stage **I1** (paths, not first-party core)  
**Eval:** `python3 scripts/eval_unified_agents_pack.py` → `pipelines/eval/unified-agents-eval.latest.md`

## Why curated (not all 54)

Full pack mixes thin language personas with 1000+ line domain code dumps. Our eval (mean overall **4.06**, pass **98%**) recommended:

| Action | Meaning |
|--------|---------|
| **paths** | Installable skill snapshot (this directory) |
| **docs_map** | Use existing first-party skills instead |
| **skip** | Awareness only |

## Curated skills in this pack

See subdirs with `SKILL.md`. Overlaps (`code-reviewer`, `error-detective`, `orchestrator`) kept for comparison; prefer first-party `/investigate`, mattpocock `code-review`, `/agent-loops` when both apply.

## Refresh

```bash
git clone --depth 1 https://github.com/stretchcloud/claude-code-unified-agents.git /tmp/ccua
# re-run convert from scripts or re-apply this PORT pin
python3 scripts/eval_unified_agents_pack.py --root /tmp/ccua/claude-code-unified-agents/.claude/agents
```

## Do not

- Make Claude Code primary runtime (ADR-0002)
- Subtree-embed full repo (ADR-0003)
- Auto-run unattended multi-agent evolve
