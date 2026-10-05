# Dogfood D4 results — stop resending ~/.grok/skills; safe bundled expose (#265)

**Base:** `a8977c33` (#264)  
**Branch / worktree:** `bot/dogfood-d4-265` · `/home/mark/DEVELOP/pfy-mentat/tmp/dogfood-d4-265`  
**Cite:** #265 only.

## Question

Can `./pfy build -p` keep user `~/.grok/skills` (~37.5k tokens_est) out of the isolated home, expose Grok `bundled/` without write-through into the real tree, measure that exposure, and fail closed when `bundled/` is missing?

## What landed

`scripts/pfy_build_p.py` (after Build run 2):

- Default `skills_bundle_mode=bundled_link`: isolated `GROK_HOME` with
  - **byte copies** of `real_home/bundled/**` into `dest/bundled/` (real dirs; **no file or directory symlinks**)
  - dest copies `chmod a-w` after `shutil.copy2`
  - lean real-file `skills/pfy-jev-decision/SKILL.md` pointer
  - `auth.json` byte copy (never symlink)
  - **nothing** from `real_home/skills`
- Receipt: `skills_bundle_chars`, `skills_bundle_tokens_est` (method **chars/4**, text under dest `bundled/`+`skills/`), `skills_bundle_mode`, separate from preamble/task
- Missing `bundled/`: live exit **1**, reason `bundled_missing`, no grok exec; dry-run may `bundled_skipped`
- `PFY_BUILD_FULL_SKILLS=1`: D3 pointer-only home (no bundled expose)
- Test `test_dest_write_does_not_change_real_bundled_marker`: writing via dest path must not change real marker

## Incident (Build run 1)

Run 1 initially **file-symlinked** bundled into dest. Live measure wrote through symlinks and **changed real `~/.grok/bundled` contents**.

| Tree | Aggregate sha256 (find…\|sha256sum\|sha256sum) |
|------|-----------------------------------------------|
| `~/.grok/skills` before any D4 | `c8caeec1…6db0fb` |
| `~/.grok/skills` after all D4 | `c8caeec1…6db0fb` (**unchanged**) |
| `~/.grok/bundled` before D4 | `87fb78e6…571ebf6` |
| `~/.grok/bundled` after symlink live | `4200f234…09734c` (**mutated**) |
| `~/.grok/bundled` after run2 + copy live | `4200f234…09734c` (**stable**; no further writes) |

Build run 2 replaced symlinks with copies. Outer bot did **not** rewrite Mark's bundled (left as grok rewrote it).

## Build runs

| Run | Purpose | Receipt | rc | Wall | Turns | Calls | Total tokens | Route |
|-----|---------|---------|----|------|-------|-------|--------------|-------|
| 1 | Implement (symlink design) | `…/20261005T074529Z/` | 0 | 1221.2 s | 1 | 33 | **3 550 828** (in 3 456 335 / out 94 493 / cached 3 125 248) | escalate / 3 |
| 2 | Fix write-through → copies | `…/20261005T081341Z/` | 0 | 594.5 s | 1 | 18 | **1 341 251** (in 1 290 172 / out 51 079 / cached 1 190 144) | escalate / 3 |

## Live receipts (trimmed path)

| | Symlink live (unsafe, before fix) | **Copy live (after fix)** |
|--|--:|--:|
| Receipt | `…/20261005T080926Z/` (also holds a dry-run) | **`…/20261005T082823Z/`** |
| rc / wall / calls | 0 / 17.6 s / 1 | **0 / 6.5 s / 1** |
| Total tokens | 17 707 | **17 816** |
| In / out / cached | 17 226 / 481 / 6 528 | **17 369 / 447 / 6 528** |
| `skills_bundle_tokens_est` (disk text) | 2 749 730 | 2 749 730 |
| `preamble_tokens_est` | 87 | 87 |
| stdout | `D4_BUNDLE_OK` | `D4_COPY_OK` |
| dest/bundled | 434 symlinks | **434 regular files, 0 symlinks** |

## Token comparison (be explicit)

| Comparison | Numbers | Like-for-like? |
|------------|---------|----------------|
| D2 tiny skill slice | 623 246 total / 13 calls | **No** — different task, full user skills home |
| D3 implement (untrimmed) | 2 304 367 / 28 calls | **No** — implement body |
| D3 trimmed tiny live | **14 959** / 1 call | **Closest** to D4 copy live (**17 816** / 1 call): same class of trivial reply, isolated home, no user skills |
| D4 symlink live vs copy live | 17 707 vs 17 816 | **Yes** — same prompt class; copy is safe |

Disk `skills_bundle_tokens_est` ~2.75M counts all UTF-8 text under copied bundled (incl. office schemas). **Session** tokens stay ~18k — Grok does not ingest the whole tree each call. User skills (~37.5k tokens_est / ~150 KB) are **not** present in dest (`skills/` only has `pfy-jev-decision`).

**D4 vs D3 ~2.8k session gap (17 816 − 14 959 = 2 857):** receipts share the same trimmed preamble_tokens_est (**87**) and task_prompt_tokens_est (**33**), and the composed `-p` prompt is the same length (490 chars). D3 live (`20261005T073546Z`) was pointer-only isolation (no `skills_bundle_*` fields; in 14 596 / out 363 / cached 10 240). D4 copy live (`20261005T082823Z`) is `skills_bundle_mode=bundled_link` with disk measure 2 749 730 (in 17 369 / out 447 / cached 6 528). The ~2.8k session delta is almost all extra **input** (~2 773), not the 2.75M disk tree — consistent with a small amount of bundled skill discovery/index entering context under `bundled_link`, not full-tree ingest. Receipts do not name which bundled files were loaded, so that is the best evidence-backed reading (not a file-level proof).

**Per-call floor ~18k:** session totals scale with model call count — Tester's e9b30ca gate recorded **55 467** tokens over **3** calls (`live-default-receipt.jsonl`, stamp `20261005T083540Z`; evidence only at `/workspace/pfy-dogfood/pr266-d4-e9b30ca/`, not in-repo) versus DevBot's **17 816** over **1** call (`20261005T082823Z`).

## Fail-on-base / pass-on-head

- `SkillsBundleTests` vs `a8977c33` `pfy_build_p.py`: **6 FAIL** (incl. write-through marker test, receipt fields, missing-bundled)
- Same on head: **OK** (full `tests.test_pfy_build_p` + `tests.test_jev_decision_skill` → 16 OK)

Missing-bundled: live `build_p` exit 1 + receipt `bundled_missing`; `PFY_BUILD_FULL_SKILLS=1` recovers pointer-only (tested).

## Friction

1. File symlinks are unsafe with Grok (write-through) — **copies required**.
2. Stamp collision: dry-run + live shared `20261005T080926Z` receipt (appended). Prefer unique stamps / separate dirs.
3. Copying full bundled (~7.7 MB) into every receipt `grok-home/` is heavy; gitignore keeps it out of git. Future: allowlist SKILL.md-only copy.
4. Implement runs still burn millions of tokens (chicken/egg).

## Outer-bot edits

| File | Reason |
|------|--------|
| `docs/dogfood/D4-RESULTS.md` | Full metrics, write-through incident, comparisons |
| `docs/PENDING-HANDOFF.md` | D4 status + safety note |

Build owned: `scripts/pfy_build_p.py`, `tests/test_pfy_build_p.py`, ops/modules notes, initial D4 stub / handoff lines. Drive-by `docs/dogfood/D3-RESULTS.md` one-liner from Build — reviewed, kept if harmless.

### Outer-bot fix round (Reviewer FAIL / CEO hold — no `./pfy build -p`)

| File | Reason |
|------|--------|
| `tests/test_pfy_build_p.py` | Opt-in `PFY_HOST_BUNDLED_TEST=1` for host bundled probe (skip before any `~/.grok` access; drop host-specific 2.78M cap); add `test_isolated_auth_json_forced_to_0600` |
| `scripts/pfy_build_p.py` | Force isolated `auth.json` to `0600`, isolated home to `0700`; document why `pipelines/dogfood/build/<stamp>/grok-home/` persists (audit; gitignored) |
| `docs/dogfood/D4-RESULTS.md` | Token-gap line D4 17 816 vs D3 14 959; list this fix round |
| `docs/PENDING-HANDOFF.md` | Dated entry for Reviewer fix round |

## Catalog

Toolset `jev` only. No GUI / #258. Not Feature GO.
