# Dogfood D1 results — bot lane (2026-10-05 PT)

**Plan:** [docs/design/JEV-DECISION-LAYER-AND-PFY-DOGFOOD.md](../design/JEV-DECISION-LAYER-AND-PFY-DOGFOOD.md) §3  
**Base:** `origin/main` @ `29b74ac` (#259)  
**Branch / worktree:** `dogfood/d1-jev-pfy-wrap` · `/home/mark/DEVELOP/pfy-mentat/tmp/dogfood-d1-20261004`  
**Lane:** **bot only** (headless nimo). Human-dev lane not run — see § How Mark runs D1-dev.

## Slice executed

Docs/chore stub named by the plan: versioned offline `data/decision-gates/` for org `push_hold` shadow mode + cross-links in `docs/ops/jev-230.md` / `docs/PENDING-HANDOFF.md`. No product UI, no #258, no Kolibri, no catalog HOLD lift, no TypeSafe key.

## Path under test

```text
./pfy toolset apply jev --harness grok --lane local --yes
./pfy decision smoke
python3 scripts/pfy_jev_230.py --selftest
./pfy decision route          # shadow; conf-low → escalate (no auto-act)
grok -p "$PROMPT" --cwd $WT --always-approve --output-format plain
```

Env from apply (local): `PFY_DECISION_PATH=cua-s1-forms`, `PFY_JEV_OFFLINE=1`, `TYPESAFE_API_KEY` unset.

## Measured results

| Metric | Result |
|--------|--------|
| Completion | **PASS** — stub files + doc links landed; PR opened from isolated worktree; Mark main checkout untouched |
| Gate honesty | **PASS** — Tester/Reviewer not claimed replaced; route **conf low** → escalate only; no silent auto-act |
| Wall time (bot lane) | **~125 s** dominated by `grok -p` body; pfy apply/smoke/selftest/route each **&lt;1 s** |
| Grok Build turns | **1** headless turn (`sessionId` `01a10adb-187f-7da2-ac61-ab84f23e3606`) |
| Grok model calls | **11** (`grok-4.7-build`) |
| Grok tokens (session) | in **533928** · out **10087** · cached read **427776** · reasoning **6914** · total **544015** |
| TypeSafe tokens | **0** (no key; offline) |
| Catalog surfaces used | toolset `jev` (implemented), Grok CLI path; no I0/HOLD rows |

Receipts: `pipelines/dogfood/d1/` (`timeline.txt`, `shadow.jsonl`, `decision-*.log`, `grok-usage.txt`, `friction.jsonl`).

## Shadow log (beside actual action)

| Gate | Engine | Result | What we actually did |
|------|--------|--------|----------------------|
| `decision smoke` | cua-s1-forms | READY | Continued |
| `decision route` | cua-s1-forms | **FAIL conf low** (exit 1) | **Did not** auto-pick model/tool; escalated to fixed `grok -p` body prompt |
| implement body | grok-4.7-build | rc 0 in 125s | Wrote `data/decision-gates/*` + doc links |

Decision-layer state after smoke (usable local path) was snapshotted in `pipelines/dogfood/d1/decision-layer-state.json`.

## Friction (exact failures)

1. **First `grok -p` invocation** failed immediately (`rc=2`, 0s): `invalid value 'text' for --output-format` (valid: `plain|json|streaming-json|streaming-messages-json`). Recovered by retry with `--output-format plain`. **Not a pfy failure** — operator flag error. Logged in `friction.jsonl`.
2. **`./pfy decision route` exit 1 / conf low** — correct honesty for D1 (no silent auto-act), but looks like a hard fail in scripts; bots need a documented “shadow escalate” exit convention so coordinators don’t treat it as toolset breakage.
3. **No first-class `./pfy` headless Build wrapper** — D1 still shells `grok -p` after pfy setup; pfy augments (toolset + decision) rather than replacing Build for the write path.
4. **`grok usage` needs session id** — not printed by default on `-p` success; had to discover under `~/.grok/sessions/…`.

No bare-`grok -p`-only comparison run was required: pfy did not stall; after the flag fix the wrapped path completed the same slice.

## Verdict

**Yes — with caveats — a bot can use `./pfy` tooling *around* bare `grok -p` for this kind of docs/chore slice.**

- **Works today:** local `jev` toolset apply (writes only `$PFY_STATE_DIR` + `GROK_HOME/skills`), Mark-free smoke/selftest, shadow route that refuses to auto-act on conf low, then Grok Build for the body.
- **Does not replace Build:** implement still needs `grok -p` (or Cursor). D1 shows **augment**, not full replace.
- **Top fixes next:** (1) document/normalize conf-low exit codes for shadow gates; (2) add a thin `./pfy build -p` (or `dogfood`) helper that exports toolset env + runs decision smoke + invokes `grok -p --output-format plain`; (3) print session id / usage summary after headless runs; (4) live `push_hold` dual-run shadow bridge (plan step 3).

## How Mark runs D1-dev (~10 minutes)

Human lane of D1: same slice, but you drive Launch/Attach instead of headless `-p`.

```bash
# 1. Isolated worktree (never the open founder Build tree)
cd ~/DEVELOP/pfy-mentat
git fetch origin main
git worktree add -b dogfood/d1-dev-$(date +%Y%m%d) tmp/dogfood-d1-dev origin/main
cd tmp/dogfood-d1-dev

# 2. Local jev toolset (no TypeSafe key)
./pfy toolset apply jev --harness grok --lane local --yes
export PFY_DECISION_PATH=cua-s1-forms PFY_JEV_OFFLINE=1
unset TYPESAFE_API_KEY

# 3. Prove decision layer
./pfy decision smoke
python3 scripts/pfy_jev_230.py --selftest
./pfy decision route   # if conf low: escalate manually — do not force auto

# 4. Human path (LOOP-243): Launch opens grok or OpenCode only
./pfy launch decision cua-s1-forms
# In the native window: Attach/Launch grok (or OpenCode). Ask it for the same
# D1 chore (data/decision-gates stub + ops/handoff links) or a fresh tiny docs chore.

# 5. Stop when the chore is committed on the dogfood branch; open a PR yourself
#    or hand the branch to a bot. Do not merge Feature GO from this lane.
```

Budget: about **10 minutes** if smoke is green and the chore stays docs-only. If `decision smoke` FAIL → stop and use bare `grok -p` in the worktree; file the FAIL copy in the PR.

## Catalog honesty

Used only: toolset `jev` (already implemented for grok), Grok CLI. Avoided: #258 picker, Kolibri I0, catalog HOLD 70–75, TypeSafe cloud.
