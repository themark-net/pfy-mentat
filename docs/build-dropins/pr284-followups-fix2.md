/orchestrate — follow ~/.grok/skills/orchestrator/SKILL.md.

This request is PRE-AUTHORIZED by the owner. Ask no questions.

> Fix round 2 for PR #300 (`build/pr284-followups`). Tester FAILED at `c4bee82` on one blocker, B1, which is test-only: the item 12 code is correct, but its tests don't use upstream smolvm's real output. There are two cheap follow-ups as well. Review: https://github.com/themark-net/pfy-mentat/pull/300#pullrequestreview-5560380707. Written 2026-10-17.

## Exits (read first; check before every item and every retry)
1. STOP file: if `/home/mark/DEVELOP/pfy-mentat/tmp/pr284-followups/tmp/STOP` exists, stop now (STOPPED_EXIT: stop-file).
2. Tries: at most 3 attempts per item. After the 3rd failure, mark the item SKIPPED with the reason and move on.
3. Item 1 is the blocker. If it ends SKIPPED, still do items 2-3, and put "ITEM 1 SKIPPED" in bold as the first line of the handoff section.
4. No progress: 3 identical failures (same error or same diff) on one item mean SKIPPED right away.
5. Wall clock: write the start time from `date` in the run log. Start no new item after 30 minutes. Finish by about 40 minutes (STOPPED_EXIT: time-cap). A backstop `timeout` kills the process at 45 minutes, so commit and push after every item.
6. Red base: if the baseline suite fails, record it and stop (BLOCKED: red-base).
7. Goal met: every item is DONE or SKIPPED and the final checks are recorded (DONE).
On every exit: update the run log and the handoff, commit, push.

## Context
- Worktree (your only working tree): `/home/mark/DEVELOP/pfy-mentat/tmp/pr284-followups`. Branch `build/pr284-followups`. Head before this drop-in is `c4bee82`. Don't merge or rebase; the owner merges origin/main after you exit.
- Run log: append a "Fix round 2" section to `docs/ops/RUN-LOG-pr284-followups.md`.
- Decisions: append to `docs/ops/AUTONOMOUS-DECISIONS-2026-10-17-pr284-followups.md` (`choice | alternatives | why`).
- Handoff: add a "Fix round 2 after Tester FAIL @ c4bee82" section to `docs/ops/HANDOFF-pr284-followups-2026-10-17.md`.
- Code:
  - `examples/x-intake-local/smoke.py`: `scrub_env`, `SECRET_ENV_RE`, `PAID_KEYS`, `node_version_env`;
  - `smoke_109_111.py`: `smolvm_image_evidence`, `clean_env`, `DROP_PREFIXES`;
  - `smoke_098_100.py`: `tool_env`;
  - `smoke_103_105.py` and `smoke_106_108.py`: `clean_env`, which already uses `scrub_env`.
- Tests: `tests/test_x_intake_smoke_*.py`.

## Hard rules
- Never touch the founder checkout `/home/mark/DEVELOP/pfy-mentat` or other worktrees under `tmp/`. Write nothing outside `~/DEVELOP` except under `/tmp`.
- No sudo, installs, downloads, system or service changes, model loads, sign-ins or posting. Don't download or install smolvm. gh is not logged in; don't try.
- Never print, log or commit secrets. In tests, use only dummy values like `pfy-test-dummy`. Env-dump stubs record variable NAMES only, never values.
- Never pause, stop or kill a process you did not start. Keep the host light: one full-suite run at a time.
- Open NO pull request. Push only this branch, normally: `git push origin HEAD:refs/heads/build/pr284-followups`. Never force-push, merge or rebase.
- Behavior-level tests: drive the real smoke script in a subprocess with stub binaries, and assert receipts, stderr and exit codes. Item 1 (h) is the one allowed direct call into a function.
- **Item 1 changes tests only.** `smoke_109_111.py`'s smolvm image code is correct per the Tester. Don't change it. If a test seems to need a code change, record that in AUTONOMOUS-DECISIONS and SKIP that part.
- **Proof of RED per item:** for each named mutant:
  1. apply it;
  2. run the named test module with `PYTHONDONTWRITEBYTECODE=1`;
  3. confirm the named test(s) FAIL;
  4. restore with `git checkout -- <file>`, or by reverting your edit;
  5. confirm the module passes.
  Log `RED: <mutant> -> <failing test names>` in the run log. Never commit a mutated state.
- One commit per item: `<area>: fix2 item <n> <short what>`. Run that item's test module(s) before each commit, and push after each.

**Before item 1:** run the baseline full suite `python3 -m unittest discover -s tests -t .` and record the count, result and skips in the run log. Expect 373 OK, skipped=4 on nimo.

## Items

**1. (BLOCKER) Make the smolvm stub match what upstream prints, and add a wrong-ref case. Tests only.**
Facts from upstream smolvm v1.26.1 (`093852e8`), checked in source:
- A plain `machine run --image <ref> -- …` (what the smoke runs, `smoke_109_111.py:~256`) calls `pull_with_progress` on every run (`src/cli/machine.rs:2010`). The pull happens on every run, not just the first.
- `pull_with_progress` (`src/cli/mod.rs:172-214`) writes to **stderr only**, in this order:
  1. `eprint!("Pulling image {ref}...")`, with no newline;
  2. progress redraws `"\rPulling image {ref}... [" + 20 chars of '=' / '>' / ' ' + "] {pct}%"`;
  3. optionally `"\rPulling image {ref}... [====================] 100% — syncing..."`;
  4. finally `eprintln!("\rPulling image {ref}... done.                              ")`, which is `done.` plus 30 spaces and then a newline.
- `Caching image <16hex> (one-time; reused on later runs)` and `Using cached image <16hex> (host cache hit; no pull)` (stdout, `machine.rs:1068/1082`) come only from `ensure_init_layer`. That is gated by `(!params.init.is_empty() || self.oci_cache)` (`machine.rs:1570`), so the smoke's plain command never prints them.

Today the stub (`tests/test_x_intake_smoke_109_111.py:25-50`) prints a cache line on every evidence run, so every test takes the stdout branch. Two mutants survive:
- **M19a:** disable the stderr branch in `smolvm_image_evidence`, e.g. `return None` just before `needle = ...`.
- **M21:** `needle = "Pulling image "`, so any ref matches.

Change the test file only:
- **Stub, plain run** (no `--oci-cache` in argv). On EVERY run, write to stderr exactly upstream's sequence for the `--image` ref:
  1. `"Pulling image " + ref + "..."`;
  2. at least two progress redraws (e.g. 25% `[=====>              ]` and 60%), plus the `— syncing...` redraw;
  3. `"\rPulling image " + ref + "... done." + " " * 30 + "\n"`.
  Flush stderr. Write nothing about images on stdout.
- **Stub, `--oci-cache` in argv:** also print the stdout cache line, `Caching image 0123456789abcdef (one-time; reused on later runs)` on the stub's first run and `Using cached image 0123456789abcdef (host cache hit; no pull)` later. Keep the run counter file next to the stub.
- **Keep** the modes `no-evidence` (no pull or cache text at all) and `guest-blob`.
- **Add mode `wrong-ref`:** the pull text names `alpine:3.21@sha256:` + 64×`a` instead of the requested ref.
- Update the header comment to cite the facts above.

Tests (each mutant below must turn RED):
- **(a)** Default pin: PASS. `image_evidence` == `"Pulling image " + SMOLVM_PIN + "... done."`, which is what the code's `split("\r")[-1].strip()` gives. Kills M19a.
- **(b)–(e):** keep as they are, running on the new stub.
- **(f)** Rewrite. Two plain runs in the same root both PASS, and both record the `Pulling image <pin>... done.` evidence, because upstream pulls on every plain run. Drop the claim that a second plain run reports `Using cached image`.
- **(g)** New. `wrong-ref` mode: exit 1, reason `smolvm did not report pulling or caching the pinned image`. Kills M21.
- **(h)** New. The stdout cache-line branch, to keep M19b (stdout branch removed) killed:
  - run the stub directly in a subprocess as `machine run --oci-cache --image <pin> -- true`, twice;
  - give its stdout and stderr to `smolvm_image_evidence`, imported from `examples/x-intake-local/smoke_109_111.py` via `importlib` with `sys.path` set the same way the module expects;
  - assert the first call returns the `Caching image 0123456789abcdef …` line and the second the `Using cached image …` line.
  - If importing the module has side effects, record that in AUTONOMOUS-DECISIONS and instead assert on the stub's raw stdout plus the `_IMAGE_CACHE_LINE` regex.

RED, all logged:
- M19a → (a) and (f) FAIL;
- M21 → (g) FAILs;
- M19b (stdout loop disabled) → (h) FAILs.
Also log a `grep` of the stub source showing the cache lines print only under `--oci-cache`.

Commit `tests: fix2 item 1 upstream-exact smolvm stub and wrong-ref case`.

**2. Tests that kill the env-scrub mutants for tool children.**
Two mutants survive:
- **M26:** `scrub_env` keeps secret-shaped names, i.e. it filters only `PAID_KEYS` (drop the `SECRET_ENV_RE` clause).
- **M28:** drop `|_PAT` from `SECRET_ENV_RE`.

The existing tests plant only PAID_KEYS names, or check the `node --version` env.
- In `tests/test_x_intake_smoke_103_105.py` and `tests/test_x_intake_smoke_106_108.py`, add a test that runs the real smoke with a stub TOOL child, not node. The stub writes the sorted env var NAMES it sees to a file next to itself.
- Plant these dummy names in the parent env, all with the value `pfy-test-dummy`: `NPM_TOKEN`, `GITHUB_PAT`, `GH_ENTERPRISE_TOKEN`, `HF_TOKEN`, `FOO_API_KEY`, `DB_PASSWORD`, `MY_SECRET`, `AWS_CREDENTIALS`.
- Assert that none of them reach the tool child, and that `PATH` does, along with the temp `HOME` (check HOME via a separate `HOME` value file, not values in general).
- If a smoke in these modules has no tool child that is easy to stub, use whichever tool child is reachable with existing stubs, and record the choice in AUTONOMOUS-DECISIONS.

RED:
- M26 → both new tests FAIL;
- M28 → both FAIL on `GITHUB_PAT`.

Commit `tests: fix2 item 2 tool-child env scrub tests`.

**3. Use `scrub_env` in `smoke_109_111.clean_env` and `smoke_098_100.tool_env`.**
- Both still pass non-PAID secret-shaped names to tool children: smolvm, brigade and runx for 109_111, and the 098_100 tools. The Tester leaked all 8 non-PAID dummies.
- Build `clean_env` (109_111) from `scrub_env(os.environ)` and keep the `DROP_PREFIXES` filter and the existing updates.
- Build `tool_env` (098_100) from `scrub_env(os.environ)` too, with an updated docstring. Import `scrub_env` from `smoke` the same way each module already imports from it.
- Tests:
  - In `tests/test_x_intake_smoke_109_111.py`, have the smolvm stub (which already runs through `clean_env`) write its env NAMES to a file next to itself. Plant the 8 dummies from item 2 and assert none reach it, while `PATH` does.
  - In `tests/test_x_intake_smoke_098_100.py`, do the same with one tool child that runs through `tool_env`.

RED: revert each helper to its old PAID_KEYS-only comprehension. The matching new test FAILs (two mutants, two logged RED lines).

Commit `smoke: fix2 item 3 scrub secret-shaped env in 109_111 and 098_100`.

## Finish (always)
1. Run the full suite on nimo. Record `Ran N tests`, the result and the skips.
2. Local CI:
   - every `run:` step of `.github/workflows/eval-structural.yml`, plus `python3 scripts/catalog_check.py` and `python3 scripts/check_no_encoded_payloads.py`;
   - if the structural eval overlaps another unittest run on the host, wait and rerun it;
   - restore regenerated `pipelines/eval/*.latest.md` and `pipelines/catalog/dashboard.latest.md` with `git checkout --`.
3. Handoff "Fix round 2 after Tester FAIL @ c4bee82" section, about 25 lines at most:
   - per item: status, commit, test names and the `RED:` lines;
   - baseline and final counts, naming the host;
   - live smolvm status: still BLOCKED, not installed on nimo, unless `~/DEVELOP/pfy-mentat/tmp/smolvm/smolvm` exists;
   - the exit that fired;
   - **Deferred follow-ups (not done in this PR):**
     1. timeouts in 112 overtime main, festival and 115 openqodex name the entry, not the sub-step (`new`, …);
     2. overtime still PASSes "daemon stopped" when `daemon stop` times out and no `overtimed.lock` exists (this predates the PR);
     3. other smoke tests still write ignored receipts into the repo's `pipelines/smoke` (103_111_receipts writes 9, 117_118 writes 2, 098_100 and 119_121 write 3 each);
     4. the smolvm evidence check also accepts a guest-stdout `Caching image <16hex>` line. Anchoring evidence to stderr `Pulling image <ref>` would close that (low risk; the guest runs the smoke's own script).
   Commit `docs: fix2 handoff`, push, stop.
