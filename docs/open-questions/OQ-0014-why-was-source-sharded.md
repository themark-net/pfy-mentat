# OQ-0014: Why was source sharded / base64-encoded — does the write-pipeline constraint still exist?

- **Priority:** **P1**
- **Status:** **open** (needs owner confirmation; 2026-09-20)
- **Blocks:** confidence that the de-shard (this PR) will not be undone by the next agent run; T-0111
- **Related:** [critical-review-2026-09-20.md](../ops/critical-review-2026-09-20.md) §3.1 · `scripts/check_no_encoded_payloads.py` · `.github/workflows/filemode-operator-scripts.yml`

## Question

**Question:** Why was operator source base64/gzip-encoded and byte-split into shards (2026-09-03..06), and does the write-pipeline constraint that caused it still exist?

Between 2026-09-03 and 2026-09-06 the operator surface was rewritten into forms that cannot be reviewed:

| Commit | Change |
|---|---|
| `ae5d2d2` (#150, 09-03) | `scripts/pfy-board.py` 1,234 lines → 10-line assembler + `_pfy_board_body_00..12.py`; adds `_pfy_board_probe.txt` (`PROBE_5K_OK`) and `_pfy_board_canary.py` |
| `b93ef36` (#153, 09-04) | `scripts/pfy-gui.py` 732 lines → assembler + `_pfy_gui_body_00..08.py`; adds `gui/operator/frontend/.mcp-probe` |
| `c68aed8` (#161, 09-06) | `scripts/pfy` 1,160 lines → 9-line stub + `pfy.payload.b64.00..03` (gzip+base64) |
| later | shards grow to 15 + 11 + 6; `pfy_enterable_162_b.py` gets `_p0/_p1a/_p1b` |

No commit message or doc states a reason. The evidence points to a **tooling limit, not a design choice**:

- Parts are byte-split at ~4,000 chars (not on line boundaries); a probe file literally says `PROBE_5K_OK`.
- `.github/workflows/filemode-operator-scripts.yml` header: “Contents API writes 100644; this feature-branch job restores 100755 via git.” A CI job exists solely to repair file modes broken by pushing through the GitHub Contents API.
- Assemblers carry exact-length checks (`if len(body) != 99448`), i.e. defence against a partial write.

Working hypothesis: the agent pipeline that authored these commits wrote files via GitHub MCP / Contents API (`create_or_update_file` / `push_files`) with a per-call size cap around 4–5 KB and no file-mode control, and the workaround was pushed into the repository.

## Why it matters

- Defeats diff, review, grep, blame; contradicts “receipts over vibes”.
- The gate added in this PR (`scripts/check_no_encoded_payloads.py`, in G0) will **FAIL any future run** of such a pipeline on `scripts/`, `pfy`, `gui/`. If the constraint still exists, the next agent session will be blocked rather than silently re-sharding — which is the intended outcome, but the owner should know.

## Options

### Option A — Constraint is gone (agent pushes via `git`)

- Confirm; keep the gate; close this OQ. Optionally delete the `chmod-launchers` job in `filemode-operator-scripts.yml` (keep the check job).

### Option B — Constraint remains for some agent surface

- Fix the **pipeline**: use a git-capable runner (Cloud agent / self-hosted with `git push`), or split *modules by concept* (which OQ-0013 wants anyway) so no single file needs to exceed the cap — never by byte-splitting or encoding.
- Keep the gate; add a note to AGENTS.md “Do not” list: *never commit base64/gzip payloads or runtime-concatenated shards*.

### Option C — Constraint remains and the owner wants to allow sharding

- Not recommended. Would require an ADR with rejected alternatives and removing the gate.

## What the owner needs to answer

1. Which tool/pipeline produced `ae5d2d2`, `b93ef36`, `c68aed8`? Does it still have a per-file cap or mode limitation?
2. A / B / C.
3. Whether to add the “no encoded payloads” line to AGENTS.md **Do not** (proposed: yes; done in this PR as a one-liner — revert if disagreed).

## Resolution notes

*(pending)*
