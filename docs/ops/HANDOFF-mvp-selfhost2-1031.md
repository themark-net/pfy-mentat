# Handoff mvp-selfhost2-1031

Branch `bot/mvp-selfhost2-1031`. Worktree `tmp/mvp-selfhost2-1031`. Base at launch `origin/bot/mvp-integrate-1031`. Not merged. No PR. No tag.

Exit: lane empty at 2026-11-01T01:31:14Z. Thirteen human-accepted `./pfy build` cherry-picks are on the branch. One extra invocation (Kolibri attempt A) produced no SHA. The wall cap (stop new items 2026-11-01T07:06:06Z, hard stop 2026-11-01T07:26:06Z) had not fired. Host pressure had not fired. Build invocations used: 14 of 16. Pregate was not run: host busy (`Runner.Worker` was present, and `~/DEVELOP/pfy-mentat/tmp/heavy-1030.lock` was held).

Gate for this branch: Tester plus Reviewer. The commits change runtime behavior in examples and pfylib. This lane does not request the gate and does not merge.

## Items done

| Item | Product SHA | Cloud SHA | Attempts | Wall s | Review | This lane |
|---|---|---|---|---|---|---|
| AgentDescent `snap_dir` | `4a0fe4e` | `35b7585` | 1 | 457 | accept | accept |
| Kolibri absolute receipt | `cdf4d68` | `7a79465` | 1 | 135 | accept | accept |
| typed-decisions absolute receipt | `36bc071` | `a586ad1` | 1 | 167 | accept | accept |
| Adapter `tree_hash` / `desired_skill_hash` | `ae5e5e5` | `f11f7de` | 2 | 1232 | reject, then accept | accept |
| smoke 140 `tree_hash` | `9138656` | `b9de401` | 1 | 251 | accept | accept |
| smoke 137 `tree_hash` | `1faa9fd` | `fdef8d6` | 1 | 131 | accept | accept |
| Adapter `remove_created_file` / `restore_file` | `e6339ca` | `e762c1a` | 1 | 174 | accept | accept |
| harness2 `surface._present` | `67e3333` | `dff338c` | 1 | 360 | accept | accept |
| `install_skill_tree` | `d217349` | `89b35a5` | 1 | 108 | accept | accept |
| hedge `save_ledger` | `3eeab42` | `e8cc4f3` | 1 | 132 | accept | accept |
| setup `save_ledger` | `b6e387a` | `7540153` | 1 | 94 | accept | accept |
| setup `_apply_mcp` | `c97d0a1` | `533f8a2` | 1 | 173 | accept | accept |
| `backup_once` | `18ed977` | `01067f1` | 1 | 79 | accept | accept |

Each product SHA is authored `pfy-cloud-build <pfy-cloud-build@localhost>` and carries `Built-by: ./pfy build (cloud) receipt eval/selfhost2-1031/<slug>/receipt.json`. The red behavior test is the parent commit. Subjects were amended after cherry-pick because the runner cuts the subject at 72 characters.

Receipts and the row log are under `eval/selfhost2-1031/` and `docs/ops/RUN-LOG-mvp-selfhost2-1031.md`.

## How a failure shows, and how it recovers

- AgentDescent `snap_dir`: a symlink records `mode:mt:link:<readlink>` and is not opened. A small regular file still records `sha:<hex>:mode:<octal>`. A missing path is None. A symlinked root records its readlink, and entries under the target are still hashed.
- Kolibri and typed-decisions `write`: a relative receipt directory returns 1 before any mkdir. An absolute directory still writes `latest.json` and returns the caller's code. Empty or unset still uses the default path.
- Adapter hash: a symlink row is the readlink text. A regular file row is still the file bytes. `os.walk(..., followlinks=False)` is used so Python 3.12 does not see `recurse_symlinks`. An outside edit of a link target does not change the digest. A mode-000 target does not raise.
- smoke 140 and smoke 137 `tree_hash`: same readlink rule, with `rglob` and `is_symlink` before `is_file`. Regular fixture bytes stay in the digest. No mode field was added.
- `remove_created_file` / `restore_file`: a symlink, including a broken link or a mode-000 target, returns `warn` and stays. A regular file whose sha matches is still removed, and restore still writes the backup bytes. A symlink backup returns `warn` and is not read.
- harness2 `surface._present`: a symlink is reported as changed and is not opened. A disallowed symlink exits 2, names the path, and leaves the outside bytes and the link in place. A regular harness file keeps the byte comparison.
- `install_skill_tree`: `copytree(..., symlinks=True)` copies the link and does not open the target. A regular tree still installs, writes `.pfy-owned`, and a second install returns `wrote False`. An outside edit of a symlink target does not make the next install rewrite.
- hedge `save_ledger`: a temp file plus `os.replace` replaces a symlink and does not write through it. The outside bytes stay. The ledger path becomes a regular file and `load_ledger` reads the new entries. A later save of that regular file still loads.
- setup `save_ledger`: a symlink skips `is_file` and `read_bytes` and falls through to `atomic_write`. The outside bytes stay. A regular file whose bytes already match returns without a rewrite and keeps the same inode.
- `_apply_mcp`: a symlink is treated as absent, rendered from empty, and replaced. `backup_once` and `file_sha` are not called on the link. The outside bytes stay, and no `.pfy.backup` is created for the link. A regular file still writes once, and a second apply of the same entry returns `wrote False`.
- `backup_once`: a symlink returns `""` and creates no backup. A regular file is copied once to `path + ".pfy.backup"`, and a second call does not overwrite that backup after the file changes.

## Not kept

Kolibri attempt A (`eval/selfhost2-1031/02-kolibri-receipt/receipt.json`): receipt FAIL, attempts 3, wall 1866s, no SHA. The worktree gate was green and review accepted the small `write()` on attempts 1 and 3. The archive recheck has no `.git`, so `tests.test_x_intake_smoke_103_111_receipts` (`git ls-files`) walked up to the parent clone and failed the recheck. Attempt 2 added `git init` inside `write()`. Review rejected that. The retry (`02b`) used only `tests.test_kolibri_receipt_absolute` and is the landed SHA `cdf4d68`.

Adapter hash attempt 1: review reject. The diff passed `recurse_symlinks` to `Path.rglob`, which raises `TypeError` on Python 3.12. pfylib requires Python >= 3.12. The reject was right. Attempt 2 (`os.walk`) is the landed SHA `ae5e5e5`.

## Skipped

Recorded before item 01, one batch, not a no-progress streak:

- T-0091 voice polish: shelved.
- T-0094 local TTS: needs a local model. This lane is cloud only.
- T-0081 OpenCode-in-cage: docker.
- T-0064 auth file-mount EBUSY: parked.
- T-0043 write-guard mcp-host wiring: parked.
- T-0062 Laguna: hardware.
- T-0046 AgenC: already rejected by ADR-0010.
- T-0016 colibri lab: OQ-0008 and hardware.
- T-0005 stage-letter promotion: OQ-0003.

Not repeated, because another lane already landed or rejected them: the 13 selfhost accepts, the selfhost rejects (smolvm t1 and the tree-sig content-hash loss), the 6 backlog-burn accepts, and dogfood2's tree-sig copies, home sigs, receipt tests, timeout labels, daemon stop, and pregate orphans. No content hash of `smoke_149` `.cache/chroma` or `smoke_109` cache trees. No edit of `scripts/pfy_build_cloud.py`, `scripts/pregate.sh`, `scripts/pfy`, catalog files, or `pfylib/attach.py`.

`examples/x-intake-local/smoke.py`, `smoke_148`, and `smoke_149` still lack the absolute receipt-dir check on this branch. Selfhost already landed that fix on `bot/mvp-selfhost-1031`. This lane did not copy it.

## OQ draft (not filed in the shared index)

`examples/harness2-local/sandbox.py` mode 751: a directory can be searchable and unreadable. Whether doctor or uninstall should chmod it or skip it needs a human decision. Dogfood left it out of `docs/OPEN_QUESTIONS.md`. This lane did not implement it and did not add an OQ row.

## Test evidence

Targeted modules only, `nice -n 19 python3 -m unittest ...`. Python 3.14 is the host. Python 3.12 is `~/.local/share/uv/python/cpython-3.12.12-linux-x86_64-gnu/bin/python3.12`. Each accept line in the run log names the modules and the OK count. Items 04 through 13 were checked on both interpreters. No full `unittest discover`. No `make eval-*`. No `scripts/pregate.sh`.

## Cross-lane requests

For `mvp-cloudfix-1031`, from this lane's builds:

1. The runner stores the cloud subject as the first 72 characters of the task text. Every accept this lane amended the subject after cherry-pick. The body and the `Built-by` trailer were added in that amend. Author stayed `pfy-cloud-build`.
2. Archive recheck extracts the commit with `git archive` and runs the gate in a directory that has no `.git`. A test that runs `git ls-files` walks up to the parent repo and the receipt stays FAIL with no SHA, even when the worktree gate passed and review accepted the diff. The retry prompt then saw a recheck failure. On Kolibri attempt 2 the model added `git init` inside `write()`. Review rejected it. Keep git-status tests out of the cloud gate until recheck has a repo of its own.
3. The item 04 review reject of `recurse_symlinks` was correct. No wrong review verdict on the accepts this lane kept.

Carried, not re-tested here: selfhost's review miss on a tree-sig diff that dropped an in-tree content hash, and the smolvm t1 contradiction between a pull-wins rule and `test_h`. Do not retry smolvm until one of those tests is the contract. `--writable-test` is present on this tree's cloud runner. The older "flag missing" note from selfhost is stale here.

For integrate: take `bot/mvp-selfhost2-1031` as runtime. Tester plus Reviewer. This lane does not merge.

## Next step

Tester plus Reviewer on this branch tip. Do not merge from this lane. The install, ledger, mcp apply, and backup helpers on this branch no longer open a mode-000 symlink. The next product gap that is safe for another lane is a bounded fingerprint for `smoke_149.home_sig` that does not read `.cache/chroma` bodies, with the size cap written down before anyone implements it.
