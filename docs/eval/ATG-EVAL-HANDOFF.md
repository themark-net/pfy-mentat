# Handoff: atg-framework eval, toolset ranking, Build drop-ins (2026-10-06)

**Branch:** `bot/atg-eval` (worktree `tmp/atg-eval`) off `origin/main` @ `e009030`. Docs only. Not a Feature GO. No catalog stage changed.

## What landed
- [ATG-FRAMEWORK-EVAL.md](ATG-FRAMEWORK-EVAL.md): paper map, PoC run, blockers, 9 pfy integration points (adopt / adapt / skip).
- [TOOLSET-RANKING.md](TOOLSET-RANKING.md): top 11 candidates for local-only nimo, plus what is already integrated.
- [../build-dropins/](../build-dropins/README.md): 6 Build prompts + an index. Run atg-framework first.
- `sources/entries/093-atg-framework-eval.md`, plus a section in `docs/PENDING-HANDOFF.md`.

## Evidence
- atg-framework `main` @ `29bca8a`, copied to `/tmp/atg-eval-copy`: 35 passed, 1 deselected. Offline toy printed `mock total={'value': 25} waves=2 parallel=2`.
- No model was loaded (a GLM-4.5-Air bench was running). The live compile is still unproven.

## Open / for Mark
1. Model for the live atg toy: atg NEXT.md says `qwen2.5:14b`, and pfy bench says point atg at `qwen3.6:35b`. Pick one, or let the drop-in run both in sequence.
2. ATG catalog card refresh (TOOLS.md, `tool_integration_stages.json`, `atg-coupling.md`, missing `tools.json` object). It is in the pfy-mentat drop-in, not done here.
3. Gom Jabbar: local `main` is 9 ahead and 9 behind origin. Should the 09-25 UI line land, given the bot handoff froze UI edits?
4. Leasegrid #26 and Practice Minder M3 prompts each count as a founder RELEASE when pasted.

## Next
Paste `docs/build-dropins/atg-framework.md` into Build.
