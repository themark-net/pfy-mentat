# Dogfood D2 results — bot lane via `./pfy build -p` (2026-10-05 PT)

**Plan:** [docs/design/JEV-DECISION-LAYER-AND-PFY-DOGFOOD.md](../design/JEV-DECISION-LAYER-AND-PFY-DOGFOOD.md) §3 (second slice after D1)  
**Base:** `origin/main` @ `0310654` (#261)  
**Branch / worktree:** `bot/dogfood-d2-0310654` · `/home/mark/DEVELOP/pfy-mentat/tmp/dogfood-d2`  
**Lane:** **bot only** (headless nimo). Human-dev lane not run.

## Question under test

Can a bot complete a real tiny I3-touching slice **through** `./pfy build -p` (not bare `grok -p`)?

## Slice executed

PENDING-HANDOFF follow-up after D1 friction merge: update SoT skill `bootstrap/grok-cli/skills/jev-decision/SKILL.md` to prefer `./pfy build -p` over bare `grok -p`, document `./pfy decision route` exit **3** = escalate, sync project mirror `.grok/skills/jev-decision/`, add operate-or-FAIL contract test. Cite **#230** only. Catalog HOLD 70–75. No GUI / #258 / #256 / #53 / #64 / TypeSafe key.

Hand add-ons (Reviewer nits from #261, not Build): `docs/modules/jev-230.md` Failure-modes row — `FAIL conf low` → `ESCALATE conf low (exit 3)`.

## Path under test

```text
./pfy build -p "$(cat /tmp/d2-build-prompt.md)" --cwd $WT
# internally: toolset apply jev --lane local → decision smoke → decision route shadow → grok -p --output-format plain
```

## Measured results

| Metric | Result |
|--------|--------|
| Completion | **PASS** — skill + mirror + contract test landed; PR from isolated worktree; Mark main checkout untouched |
| `./pfy build -p` drove implement | **yes** (rc 0) |
| Gate honesty | **PASS** — route shadow **escalate** exit 3; Build proceeded (no silent auto-act); Tester/Reviewer not claimed replaced |
| Wall time (helper) | **~203 s** (`elapsed_s` 202.848 on `grok_p`; start→done ≈ 203 s) |
| Grok Build turns | **1** (`sessionId` `01a10ae6-ad7d-7503-9487-7a1068c5a177`) |
| Grok model calls | **13** (`grok-4.7-build`) |
| Grok tokens (session) | in **607566** · out **15680** · cached read **503936** · reasoning **12516** · total **623246** |
| TypeSafe tokens | **0** |
| Catalog surfaces used | toolset `jev` (local); code-graph MCP was co-present on host (PASS codebase-memory) but not required for this skill slice |

Receipt: `pipelines/dogfood/build/20261005T071051Z/receipt.jsonl`.

## Shadow log

| Gate | Engine | Result | What we actually did |
|------|--------|--------|----------------------|
| toolset apply jev | local | ok | Continued |
| decision smoke | cua-s1-forms | READY | Continued |
| decision route | cua-s1-forms | **escalate** (exit 3) | Logged; Build did **not** abort |
| implement body | grok-4.7-build | rc 0 in ~203s | Skill + test |

## Friction / findings

1. **`./pfy build -p` worked** for a real skill+test slice — D2 question answered **yes**.
2. Project mirror `.grok/skills/` lacked `jev-decision/` before this slice (bootstrap SoT existed; mirror gap). Synced as part of DoD.
3. Long `grok -p` under the helper: outer nohup stdout can stay empty while receipt/`~/.grok/sessions` carry the truth — poll receipt + session, not only the nohup log.
4. Open-issue pick was thin (remaining opens are #53/#64/catalog/Kolibri-ish); slice taken from PENDING-HANDOFF + #230 cite.

## Verdict

**Yes — a bot can do real work through `./pfy build -p` on main after #261.** Implement body still is Grok Build; pfy owns toolset + decision shadow + plain output-format + session/usage receipt.

## Catalog honesty

Used toolset `jev` only for the wrap. Avoided HOLD 70–75, #258, Kolibri I0, TypeSafe cloud.
