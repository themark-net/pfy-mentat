/orchestrate — follow ~/.grok/skills/orchestrator/SKILL.md.

This request is PRE-AUTHORIZED by the owner. Ask no questions.

> Fix round 1 for PR #300 (`build/pr284-followups`). Tester FAILED at `31bc2f0` with one blocker (item 12, smolvm image digest) plus 4 follow-ups; Reviewer passed. Review: https://github.com/themark-net/pfy-mentat/pull/300#pullrequestreview-5560106269. Written 2026-10-17.

## Exits (read first; check before every item and every retry)
1. STOP file: if `/home/mark/DEVELOP/pfy-mentat/tmp/pr284-followups/tmp/STOP` exists, stop now (STOPPED_EXIT: stop-file).
2. Tries: at most 3 attempts per item. After the 3rd failure, mark the item SKIPPED with the reason and move on.
3. Item 1 is the blocker. If it ends SKIPPED, still do items 2-5, and put "ITEM 1 SKIPPED" first and in bold in the handoff.
4. No progress: 3 identical failures (same error or same diff) on one item = SKIPPED immediately.
5. Wall clock: write the start time from `date` in the run log. Start no new item after 45 minutes; finish by about 55 minutes (STOPPED_EXIT: time-cap). A backstop `timeout` kills the process at 60 minutes, so commit and push after every item.
6. Red base: if the baseline suite fails, record it and stop (BLOCKED: red-base).
7. Goal met: every item DONE or SKIPPED, final checks recorded (DONE).
On every exit: update the run log and the handoff, commit, push.

## Context
- Worktree (your only working tree): `/home/mark/DEVELOP/pfy-mentat/tmp/pr284-followups`. Branch `build/pr284-followups`, head before this drop-in `31bc2f0`. Base stays origin/main `0d574f0`; don't merge or rebase.
- Run log: append a "Fix round 1" section to `docs/ops/RUN-LOG-pr284-followups.md`. Decisions: append to `docs/ops/AUTONOMOUS-DECISIONS-2026-10-17-pr284-followups.md` (`choice | alternatives | why`). Handoff: add a "Fix round 1 after Tester FAIL @ 31bc2f0" section to `docs/ops/HANDOFF-pr284-followups-2026-10-17.md`.
- Code: `examples/x-intake-local/smoke.py` (shared `timeout_reason`, `pinned`, `PAID_KEYS`, `write`, `PFY_SMOKE_RECEIPT_DIR`), `smoke_103_105.py`, `smoke_106_108.py`, `smoke_109_111.py`, `smoke_112_114.py`, `smoke_115_116.py`; tests in `tests/test_x_intake_smoke_*.py`.

## Hard rules
- Never touch the founder checkout `/home/mark/DEVELOP/pfy-mentat` or other worktrees under `tmp/`. Write nothing outside `~/DEVELOP` except `/tmp`.
- No sudo, no installs, no downloads, no system/service changes, no model loads, no sign-ins, no posting. Don't download or install smolvm. gh is not logged in; don't try.
- Never print, log or commit secrets. In tests use only dummy values like `pfy-test-dummy`.
- Never pause, stop or kill a process you did not start. Keep the host light: one full-suite run at a time.
- Open NO pull request. Push only this branch, normally: `git push origin HEAD:refs/heads/build/pr284-followups`. Never force-push, merge or rebase.
- Behavior-level tests only: drive the real smoke script in a subprocess with stub binaries and assert receipts, stderr and exit codes. No tautological unit tests.
- **Proof of RED per item:** apply the named mutation, run the named test, confirm it FAILS, restore, confirm it passes. Log `RED: <mutant> -> <test>` in the run log. Never commit a mutated state.
- One commit per item: `<area>: fix1 item <n> <short what>`. Run that item's test module(s) before each commit, and push after each.

**Before item 1:** run the baseline full suite `python3 -m unittest discover -s tests -t .` and record the count, result and skips in the run log (expect 367 OK; skipped=4 on nimo).

## Items

**1. (BLOCKER) smolvm image digest from a pinned ref, not from output.**
Facts from upstream smolvm v1.26.1 (`093852e8`), checked in source:
- `machine run` never prints a full `sha256:<64hex>` by default.
- It prints, on stderr, `Pulling image <ref>... done.` (`src/cli/mod.rs:172-214`, with `\r` progress redraws).
- On stdout it prints `Using cached image <16-hex key> (host cache hit; no pull)` or `Caching image <16-hex key> (one-time; reused on later runs)` (`src/cli/machine.rs:1068/1082`).
- It accepts digest refs (`name@sha256:<64hex>`, also `name:tag@sha256:...`; see `src/registry.rs:426-470`).
- `machine images --json` needs a named machine, which `machine run` doesn't make, so use the pin.

Today `smoke_109_111.py:220-228` takes the first `sha256:` anywhere in stdout+stderr. That fails every real run, and it takes a guest-printed hash as the image digest (a false PASS).

Fix in `smoke_smolvm`:
- **Default pin.** Add a module constant `SMOLVM_IMAGE_PIN = "alpine:3.22@sha256:5291449c3df73caf6ed85e649dec1b9e818b39a5d8c871e97afc13e9cd5e8fa8"`, with a comment: alpine 3.22 multi-arch index digest, resolved 2026-10-17 from registry-1.docker.io.
- **Override.** `$SMOLVM_IMAGE` may override the pin, but it must match `@sha256:[0-9a-f]{64}$` (case-insensitive, stored lowercase). If it doesn't, exit 2 with reason `SMOLVM_IMAGE must be digest-pinned (name@sha256:<64 hex>)`. Do this check before the KVM check, so it is testable everywhere.
- **Receipt.** `image` (the ref), `image_digest` (the `sha256:...` part of the ref), and `image_digest_source` (`pin` or `env`).
- **Never take a digest from tool or guest output.** Delete the output regex.
- **Prove smolvm used an image.** After `machine run` succeeds, require stderr to contain `Pulling image <ref>`, or stdout to have a line matching `^(Using cached|Caching) image [0-9a-f]{16}\b`. Record the matched line as `image_evidence`. If neither is there, FAIL (exit 1) with reason `smolvm did not report pulling or caching the pinned image`.
- **Test-only KVM override.** Add `PFY_SMOLVM_KVM_PATH` (default `/dev/kvm`) and record `kvm_path` in the receipt. This lets the tests reach `machine run` on hosts without KVM (CI ubuntu, the Tester box), so they no longer skip.
- On the PASS path set `reason` to a short success text (e.g. `ok: guest kernel <k>, host file hidden`) instead of null.

**Rewrite the stub** in `tests/test_x_intake_smoke_109_111.py` to print exactly upstream's text:
- stderr `Pulling image <ref>... done.` on the first run;
- stdout `Caching image 0123456789abcdef (one-time; reused on later runs)` on the first run, and `Using cached image 0123456789abcdef (host cache hit; no pull)` on a second run;
- no `resolved ...@sha256` line;
- plus the guest script output.
- A stub mode, via an env var the stub reads, prints no pull/cache line at all. Another makes the guest also echo `blob sha256:` + 64×`e`.

Tests (all run without KVM via `PFY_SMOLVM_KVM_PATH` pointing at a temp file with rw; remove the old skip). Each mutation must turn its test RED; log each:
- (a) Default pin: PASS, `image_digest` equals the pin digest, source `pin`, `image_evidence` set. Mutation: record the digest from output again → (d) RED.
- (b) Env override with a valid pinned ref: PASS, digest and source `env`.
- (c) Env override `alpine` (unpinned): exit 2, the reason names "digest-pinned". Mutation: drop the pinned-ref check → RED.
- (d) Guest echoes `blob sha256:eeee…`: `image_digest` is still the pinned digest, never the guest's.
- (e) No pull/cache line: exit 1 with the evidence reason. Mutation: remove that FAIL check → RED.
- (f) Second run (cache hit): PASS with the `Using cached image` evidence.

Live part: unchanged rule. Only if `~/DEVELOP/pfy-mentat/tmp/smolvm/smolvm` exists and `/dev/kvm` is rw, run the real smoke once and record the output. Otherwise keep "BLOCKED (smolvm not installed on nimo)" in the handoff. Update `sources/entries/109-smolvm.md` only if it mentions the old digest behavior.

**2. 112/115 tests: no receipts in the repo.**
`tests/test_x_intake_smoke_112_114.py` and `tests/test_x_intake_smoke_115_116.py` still write `pipelines/smoke/*/latest.json` in the repo (e.g. 115_116:139 reads `ROOT/pipelines/smoke/openqodex/latest.json`).
- Point every smoke run in those modules at a temp dir via `PFY_SMOKE_RECEIPT_DIR` (setUp/tearDown), and read receipts from there.
- The gitignore tests (`rel = f"pipelines/smoke/{entry}/latest.json"`) must check ignore status with `git check-ignore` on the path without writing a file there, or write and then delete what they created.
- DoD: add a test (or a module-level check) that snapshots `git status --porcelain --ignored pipelines/smoke` before and after running both modules and asserts no change. Mutation: drop `PFY_SMOKE_RECEIPT_DIR` from one test's env → the snapshot check RED.

**3. Timeout text names the step.**
- Change the shared helper to `timeout_reason(step: str, seconds: float) -> str`, returning `f"{step} timeout after {seconds:g}s"`. Keep it the single code path.
- Update every caller (`grep -n 'timeout_reason(' examples/x-intake-local/*.py`, 16 today). Pass the real step name (e.g. `overtime daemon stop`, `smolvm run`, `openqodex review`) and the timeout used.
- Update tests that assert the exact text, and the docs/README that describe it.
- DoD:
  - grep shows no other hand-written timeout text;
  - the sponsio exact-text test and one 112 and one 115 timeout test assert the step name and the seconds;
  - mutation: make `timeout_reason` ignore `step` → those tests RED.

**4. No GitHub tokens or other secrets to child tools.**
- Add `smoke.SECRET_ENV_RE`, a regex for env names to strip: names matching (case-insensitive) `(TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIALS?|_API_KEY|_PAT)$`. This covers `GH_TOKEN`, `GITHUB_TOKEN`, `GH_ENTERPRISE_TOKEN`, `GITHUB_PAT`, `NPM_TOKEN` and `HF_TOKEN`. Add `smoke.scrub_env(env)`, which drops PAID_KEYS plus those names.
- Use it in both `clean_env` helpers (`smoke_103_105.py:79`, `smoke_106_108.py:77`).
- `node --version` (both smokes) gets a minimal allowlist env instead: `PATH`, `LANG`, `LC_ALL`, `TMPDIR`, plus the temp `HOME`.
- DoD: a stub `node` dumps its env, with the parent env set to dummy `GH_TOKEN=pfy-test-dummy`, `GITHUB_TOKEN=pfy-test-dummy`, `NPM_TOKEN=pfy-test-dummy` and `FOO_API_KEY=pfy-test-dummy`. Assert none reach the child, for both smokes, and that `PATH` and `HOME` (temp) do. Mutation: pass `os.environ`-derived `clean_env` without `scrub_env` → RED.

**5. Handoff counts.** In the handoff, state which host each count came from. Record:
- nimo's baseline and final full-suite counts from this run (`Ran N tests ... OK (skipped=K)`);
- that Tester's box saw skipped=6 because of KVM and toolchain.
Fix the "skipped=4" lines so they name nimo. No code change. Docs commit only.

## Finish (always)
1. Full suite on nimo; record `Ran N tests`, result and skips.
2. Local CI: run every `run:` step of `.github/workflows/eval-structural.yml`, plus `python3 scripts/catalog_check.py` and `python3 scripts/check_no_encoded_payloads.py`. Restore regenerated `pipelines/eval/*.latest.md` with `git checkout --` unless main changes them too.
3. Handoff "Fix round 1" section, about 25 lines at most:
   - per item: status, commit, test names and `RED:` lines;
   - baseline and final counts with the host named;
   - the live smolvm status;
   - the exit that fired;
   - the final head SHA.
   Commit `docs: fix1 handoff`, push, stop.
