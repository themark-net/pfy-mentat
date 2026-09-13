# Operator launch wizard (compose then Launch session)

Cite **#225** only. Catalog 70–75 HOLD. #198 parked. LIVE_HARD_OFF. Do not reopen #76. Do not add an Env nav tab.

Loop is the primary path. The job is selecting runtime / lane / toolsets / harness, reviewing the compose, then **Launch session** into one enterable TUI. Attach X stays as secondary re-attach. The operator window stays open.

## Steps (operate-or-FAIL)

| Step | Pick | Fail / skip |
|------|------|-------------|
| 1 runtime/health | FreeToken-first live engine | FAIL + `Launch env or ./pfy up` |
| 2 model lane | `local` \| `cloud/subscription` \| `OpenCode free` | FAIL + pick lane. OpenCode free needs OpenCode. cloud/subscription needs Grok\|Claude\|Codex. LIVE_HARD_OFF: pfy does not call cloud APIs. |
| 3 toolsets/skills/modes | `bare` · `orchestration` · `code-graph` · `catalog` | orchestration missing skill → FAIL + `./pfy setup`. code-graph missing Axon and codebase-memory → FAIL + `pip install axoniq`. catalog without prompt / HOLD 70–75 → honest SKIP (not auto-lifted). |
| 4 harness/TUI | OpenCode \| Grok \| Hermes \| Codex \| Claude | FAIL + pick harness. Reuses attach-usable paths (#193/#196/#202/#220/#221). |
| 5 review paint | `runtime · lane · toolsets · harness` | Incomplete → FAIL + complete wizard |

Primary CTA **Launch session** → enterable TUI with composed env **or** FAIL+next. Child inherits `LOCAL_OPENAI_BASE_URL` / `OPENAI_BASE_URL` via attach-usable. Mode handoff via #208. Catalog prompt via #209 when toolset is catalog.

## How to run

```bash
python3 scripts/pfy_launch_wizard_225.py --selftest
python3 scripts/pfy_launch_wizard_225.py --runtime
python3 scripts/pfy_launch_wizard_225.py --lane local
python3 scripts/pfy_launch_wizard_225.py --toolset bare
python3 scripts/pfy_launch_wizard_225.py --harness grok
python3 scripts/pfy_launch_wizard_225.py --review
python3 scripts/pfy_launch_wizard_225.py --launch
./pfy launch
python3 scripts/pfy-board.py --wizard runtime
python3 scripts/pfy-board.py --launch
python3 scripts/pfy-gui.py --selftest
gzip -t <(cat scripts/pfy.payload.b64.* | tr -d '\n' | base64 -d)
```

On Loop (HTML+tk): **Launch session** is the primary button. Launch env remains for runtime. Attach grok/opencode/hermes/codex/claude are secondary (not primary). Attach tab still re-attaches.

## Variables

| Name | Where | Purpose |
|------|-------|---------|
| `PFY_STATE_DIR` | `launch-wizard.json`, `launch-wizard-review.md` | composed wizard + review paint |
| `PFY_ATTACH_MODE` | child env (#208) | `bare` \| `orchestration` \| `code-graph` (catalog maps to bare + catalog prompt) |
| `PFY_CATALOG_ASK_PROMPT` | child env (#209) | next-launch catalog prompt when toolset is catalog |
| `LOCAL_OPENAI_BASE_URL` / `OPENAI_BASE_URL` | attach-usable child | FreeToken-first live base |

Registry: [bootstrap/env/REGISTRY.md](../../bootstrap/env/REGISTRY.md).

## Do not

- Reopen #76 · unpark #198 · catalog 70–75 HOLD
- Add an Env nav tab
- Treat Attach X as the Loop front door
- Paint Launch session ok without composed review
- `LIVE_HARD_OFF`: no cloud embeddings / live catalog writes from this path
- Close the operator window after Launch session
