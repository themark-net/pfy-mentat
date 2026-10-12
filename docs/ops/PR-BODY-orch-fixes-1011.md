# fix: x-intake smoke receipts, har temp HOME, pfylib tmp cleanup

Not a Feature GO. Do not merge until a separate Tester and a separate Reviewer both PASS at the tip of `build/orch-fixes-1011`. Head and counts: `docs/ops/HANDOFF-orch-fixes-1011-2026-10-11.md`.

## Summary

- Smoke receipts for `HARNESS_SHA256`, `GRAPHJIN_SHA256`, and `CM_SHA256` record `expected.<VAR>.value` and `source` (`pin` or `env`). An env override prints `WARN: $VAR=… overrides the pinned …` on stderr and still exits 2 without running the binary when the digest does not match.
- Timeout reasons in the x-intake smokes that already recorded one now use `{tag} timeout` (`smoke.timeout_reason`). A sponsio test with `PFY_XINTAKE_TIMEOUT=0.2` asserts `sponsio probe timeout`.
- `graphjin_world` closes the server log if `Popen` raises.
- The har smoke FAILs when the launch work dir is outside its temp HOME, points `XDG_CONFIG_HOME`, `XDG_CACHE_HOME`, `XDG_DATA_HOME`, and `npm_config_cache` under that HOME, and treats `~/.har/otel-hooks` like the other hook files.
- `.gitignore` covers `pipelines/smoke/{rulora,har,cassmemory,bugpatrol,graphjin,antislop}/`. `pipelines/smoke/kolibri1/latest.json` stays tracked.
- Agent Substrate Stage A lists the `root.path=/` read-only edit and the `process.terminal=false` edit as pasteable `python3` blocks.
- X-intake handoffs say a nimo receipt commit uses `git add -f`. The 2026-10-09 handoff notes the temporary atg pin worktree was removed.
- The cli, toolset, hedge, loop, and attach tests delete the `/tmp/pfylib-*` directories they create.

Catalog HOLD 070–075 is untouched. No model was loaded.

## Test plan

- [ ] `python3 -m unittest discover -s tests -t .` (this run: 203 OK, skipped=4; baseline was 191 OK, skipped=4)
- [ ] Sha pin and env tests for harness, graphjin, and cass-memory (red: no WARN, `source` missing; green: exit 2, stub not executed)
- [ ] Sponsio timeout reason is exactly `sponsio probe timeout` (red: `sponsio probe timed out`)
- [ ] `graphjin_world` test: `Popen` raises, `serve.log` handle is closed (red: `.closed` is false)
- [ ] Har work dir outside the temp HOME exits 1; XDG and npm cache are under the temp HOME; `.har/otel-hooks` fails the smoke
- [ ] `tests.test_pfylib_tmp_cleanup` (red: new `/tmp/pfylib-*` dirs; green: none)
- [ ] Six 103–108 smokes exit 2 and `git status --porcelain pipelines/smoke` is empty; kolibri1 receipt still tracked

## Decisions

17 lines: `docs/ops/AUTONOMOUS-DECISIONS-2026-10-11.md`
