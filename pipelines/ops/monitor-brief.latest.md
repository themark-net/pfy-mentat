# Monitor brief (auto)

Generated: 2026-07-30T06:18Z

## Git

```
## main...origin/main
 M Makefile
 M docs/ops/voice-agent-runner.md
 M examples/voice-stt-edge/agent_runner.py
?? examples/eval-harness/tasks/011-fizzbuzz/
?? examples/eval-harness/tasks/012-slugify/
?? scripts/worker_brief_refresh.py
```

### Recent commits

```
96e1c33 feat: automation batch GAP-01..09,16,28,33 — CI, stages, catalog, product smoke
b7b7dd3 docs: full-repo gap scan 2026-07-30 + file automation issues #38-52
7197200 backlog: voice session sticky, eval-auto soft, scorers, soft smokes (#2-12,26,28)
889855b feat: G0/G1/G2 eval gates — deploy-ready + UX UAT (HD #33)
57bc3d0 backlog batch: product levers + 9 docs/eval issues (#1 #8 #10 #13 #6 #27 #16 #21 #32 #14)
db59043 docs: TODO.md reflect five closed issues (31,5,15,22,23)
9d8fb1f resolve #31 #5 #15 #22 #23: golden lane, ADR/OQ scorers, catalog notes
50b0c81 docs: eval-golden + ADR/OQ scorers in harness README (#31 #5)
```

## Eval / smoke receipts present

- `pipelines/catalog/dashboard.latest.md`
- `pipelines/catalog/todo-github-sync.latest.md`
- `pipelines/eval/deploy-ready.latest.md`
- `pipelines/eval/eval-auto.latest.md`
- `pipelines/eval/golden.latest.md`
- `pipelines/eval/model-pool.latest.md`
- `pipelines/eval/structural.latest.md`
- `pipelines/smoke/asm/results.latest.md`
- `pipelines/smoke/opencode-cage/results.latest.md`
- `pipelines/smoke/product-levers/results.latest.md`
- `pipelines/smoke/voice-stt-edge/results.latest.md`
- `pipelines/smoke/voice-tts/results.latest.md`

## Operator

- Worker: OpenCode + Ollama when local bulk
- Monitor: Grok for hard review / tools
- Gates: `make eval-structural` (G0), `make eval-deploy-ready` (G1)

