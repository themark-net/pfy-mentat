# Daily X intake handoff — 2026-10-11

Routine: daily X intake for pfy-mentat (Grok Bot). Sources this run: Mark's new X bookmarks and the watch list (@tom_doerr, @DanKornas and the rest of the routine's list) since the last run. Deduped against TOOLS.md, `data/tools*.json`, `sources/` (including the weekly Tom Dörr pull) and the routine's own log; none of the three tools below, nor anything on the LATER list, appeared anywhere in the catalog. Previous X intake slice (Entries 106-108) merged as PR #286 (`27c2d3b`); `main` had 108 as the highest entry when this slice was numbered.

## What this slice adds

| Entry | Tool | Why | Runs on nimo? |
|------|------|-----|---------------|
| 109 | [smolvm](https://github.com/smol-machines/smolvm) | Branchable, checkpointable microVMs (libkrun, KVM on Linux), any OCI image, no Docker daemon, egress allow lists, credential substitution. **Eval-auto candidate** vs our worktree-only isolation for unattended Grok Build runs | Probably, from the v1.26.1 tarball under `tmp/smolvm` with `HOME` under `tmp/`, if Mark's user can read/write `/dev/kvm` (not checked; a `kvm` group change needs Mark). Never the `curl \| bash` installer. On the Grok Bot box: release verified, no VM booted (no KVM access), smoke exits 2 |
| 110 | [Brigade](https://github.com/escoffier-labs/brigade) | Local file-first control plane: work ledger with atomic claims, verification receipts with log digests, memory handoffs, harness projection. Comparison point for our orchestrator-in-worktree lane + Tester/Reviewer sha pinning + handoff docs | Yes, `brigade-cli==0.27.0` in a venv under `tmp/`, `BRIGADE_NO_UPDATE_CHECK=1` (otherwise a daily version check to check.brigade.tools), throwaway clone only. Smoke PASSed on the Grok Bot box under a read-only root with no network |
| 111 | [runx](https://github.com/runxhq/runx) | Governed skill runtime that seals a signed, verifiable receipt per run with no account. Pattern reference for a pfy skill-run receipt | Yes, the v0.9.1 static binary under `tmp/runx` plus a `cli-v0.9.1` clone for the example; needs a throwaway Ed25519 seed for real signatures. Never `curl \| sh` or `npm i -g`. Smoke PASSed on the Grok Bot box under a read-only root with no network |

Files: `sources/entries/109-smolvm.md`, `110-brigade.md`, `111-runx.md`, `examples/x-intake-local/smoke_109_111.py` (three new checks that reuse the helpers in `smoke.py`; `smoke_098_100.py` is unchanged), the folder README, and this handoff. No TOOLS.md rows, no `data/tools.json` rows, no stage cards, no Make target, no `.gitignore` change. Box receipts are not committed; commit receipts only from a real nimo run. Those receipt directories are gitignored, so committing a real nimo receipt uses `git add -f pipelines/smoke/<entry>/latest.json`.

Fix after Tester/Reviewer review: one shared `PAID_KEYS` in `smoke.py` (now also stripping `GROK_API_KEY`, the union of the three old lists) is imported by `smoke_103_105.py`, `smoke_106_108.py` and `smoke_109_111.py`. In `smoke_109_111.py` every tool command runs in its own session and a timeout SIGKILLs its whole process group, bwrap adds `--unshare-pid` (smolvm is never bwrap-wrapped), and `$SMOLVM_SHA256` / `$RUNX_SHA256` / `$BRIGADE_VERSION` overrides are recorded in the receipt under `expected` (value, `pin` or `env`) with a stderr WARN. `tests/test_x_intake_smoke_109_111.py` runs the brigade smoke on a stub that checks `GROK_API_KEY` is absent and that a forked child does not outlive a 1s `PFY_XINTAKE_TIMEOUT`.

This slice was written by the routine directly through the GitHub connector rather than `./pfy build -p`, since it is docs plus one stdlib script and nimo was not needed for it.

## How to gate

On nimo each `python3 examples/x-intake-local/smoke_109_111.py --entry smolvm|brigade|runx` should exit 2 with an operator reason, since nothing is staged under `~/DEVELOP/pfy-mentat/tmp` yet. To get a PASS, stage what the reason names:

- smolvm: `smolvm-1.26.1-linux-x86_64.tar.gz` and `checksums.sha256` from the v1.26.1 release, tarball sha256 `bcae519f7dad3cead2deaa0362a42a1ad7bffce73ea7a28161dea6822c559654`, unpacked as `~/DEVELOP/pfy-mentat/tmp/smolvm/` (the smoke pins `smolvm-bin` at `62ed0353d664c2d6d78bd87ecf3213c64464003f51cb58506b87b187b1a6494a`). Then check `ls -l /dev/kvm` and `id`: if Mark's user cannot read/write it, the smoke keeps exiting 2 and adding the user to `kvm` is Mark's call. The first run unpacks sparse 10 + 20 GiB (apparent) templates beside the binary and pulls `alpine` from Docker Hub. `SMOLVM_CHECKPOINT=1` adds checkpoint/rewind.
- brigade: `python3 -m venv ~/DEVELOP/pfy-mentat/tmp/brigade/.venv && ~/DEVELOP/pfy-mentat/tmp/brigade/.venv/bin/pip install brigade-cli==0.27.0`. No `brigade setup`, no pipx/uv.
- runx: `runx-0.9.1-x86_64-unknown-linux-musl.tar.gz` (sha256 `59eee2af81d24d0f8ba2416e2bac55d147ed93693e6a41ffe7c2cfd5cba98cc7`, matching its `.sha256` asset), `runx` and `runx-js-worker` into `~/DEVELOP/pfy-mentat/tmp/runx/`, plus `git clone --depth 1 --branch cli-v0.9.1 https://github.com/runxhq/runx.git ~/DEVELOP/pfy-mentat/tmp/runx/src`. Node from PATH or `tmp/runx/node`.

Or point `$SMOLVM_BIN`, `$BRIGADE_BIN`, `$RUNX_BIN` / `$RUNX_SRC` / `$RUNX_NODE` at a staged copy. Receipts go to `pipelines/smoke/<entry>/latest.json`. Each smoke FAILs (exit 1) on: a guest that fails to run, reports the host kernel, sees or changes a host sentinel file, a checkpoint that does not rewind, smolvm state in the real HOME; a task that is not ready or can be claimed twice, a verify receipt not bound to HEAD or not recording the real exit code, `receipts verify` not clean or not catching a tampered log, an update-check cache in the temp HOME; a run that does not seal, a fresh receipt that does not verify in production mode, a receipt that verifies against another key or after tampering. When `bwrap` works, brigade and runx run with a read-only root and no network, so any write outside the temp HOME/scratch dir or any network call fails the step.

What was checked on the Grok Bot box (all in `/tmp`, temp HOMEs): brigade and runx PASS with bwrap containment, again in the no-bwrap fallback mode, and again with networking removed (`unshare -rn`); smolvm exits 2 because `/dev/kvm` is not accessible to the box user (an earlier direct `machine run` attempt failed with "kvm permission denied" and wrote state only to its temp HOME). Negative paths: no prereqs gives exit 2 for each; a wrong `$SMOLVM_SHA256` or `$RUNX_SHA256` gives exit 2 without exec; `$BRIGADE_VERSION=9.9.9` gives exit 2; a runx clone of `main` instead of `cli-v0.9.1` gives exit 2; `PFY_XINTAKE_TIMEOUT` set tiny gives exit 1 with a timeout reason for brigade and runx. The smolvm boot, isolation and checkpoint code paths have **not** been run anywhere; the first nimo run with KVM access is their first test. `python3 -m py_compile` is clean.

Repo checks on the Grok Bot box, in a shallow clone of `main` at `27c2d3b` with this slice copied in: `python3 scripts/catalog_check.py` PASS (n_json=7). `python3 -m unittest discover -s tests -t .` ran 190 tests with 1 failure, `tests.test_hedge.DetectorTests.test_detector_runs_offline` (`'partial'` not in the allowed statuses), identical on untouched `main` on the box (190 tests, same single failure), so it comes from the box environment, not this slice. `make` is not installed on the box.

## Recommended next steps (not started)

1. **Eval-auto trial: smolvm vs the worktree-only isolation of unattended Grok Build runs**, after Mark decides on `/dev/kvm` access on nimo. Stage the tarball under `tmp/smolvm`, `HOME` under `~/DEVELOP/pfy-mentat/tmp/smolvm-home`, get the smoke to PASS (with `SMOLVM_CHECKPOINT=1`), then run one small pfy-mentat Build task inside a machine: a throwaway clone mounted (never Mark's main checkout), `--net` with `--allow-host` for GitHub and the Build endpoint only, credentials via `--credential` rather than copying `~/.grok/auth.json` into the guest. Compare setup time, run time, whether Build works inside the guest at all, host files touched (should be none outside the mount), and whether a checkpoint/rewind beats `git worktree remove` for recovering a bad run. Run when nimo isn't in a benchmark; keep `--mem` modest.
2. Brigade: no trial yet. If the lane needs claim safety for parallel Build runs, try only `work task/claim/verify` and `receipts verify` in a throwaway clone and compare its receipts with the "checks ran at sha X" lines Tester/Reviewer write today.
3. runx: no trial. Copy the receipt idea (subject, authority/grant, execution boundary, exit, seal, verify that refuses placeholder signatures) into a small pfy skill-run receipt design.

## LATER (logged, not cataloged this run)

- **context-guru** — https://github.com/rossoctl/context-guru (Apache-2.0, Go). Context-reduction proxy for coding agents, aimed at Claude Code / Codex; check whether it fronts a Grok or local endpoint before cataloging.
- **overmind** — https://github.com/overmind-core/overmind (AGPL-3.0, Python). Trace-to-eval "continuously improving agents" platform; heavy, and AGPL.
- **agent-sdk-go** — https://github.com/agenticenv/agent-sdk-go (Apache-2.0, Go). Durable execution / journaling for Go agents; pattern reference for resumable loops.

SKIPPED: **mcp-gateway** (GitHub license NOASSERTION).

## Locks respected

Catalog 70-75 HOLD untouched. Nothing installed or downloaded on nimo. Mark's main checkout and stashes untouched; a read-only shallow clone of public `main` in `/tmp` on the Grok Bot box was used for dedupe greps and the repo checks. No accounts, sign-ins, paid keys or spend (runx and Brigade hosted surfaces unused; smolvm's smol cloud unused). Tools were tested only on the Grok Bot box in `/tmp` with temp HOMEs; no model was called by any of them. No installer scripts (`curl | bash`, `curl | sh`) were run anywhere.

## How this fails / how we recover

| Risk | How it fails | Recovery |
|------|----------------|----------|
| Entry numbers collide | Another branch also adds 109-111 | Renumber on rebase; entries are self-contained files |
| Smoke in CI without prereqs | Exit 2 read as red | Not wired into CI or Make; exit 2 is the honest "can't run here" |
| smolvm code paths untested | First nimo run FAILs on a flag or output shape | The FAIL reason names the step; fix the smoke in a follow-up, don't treat it as a tool verdict |
| KVM access needs a system change | `kvm` group not granted on nimo | Smoke stays exit 2; trial waits for Mark |
| Brigade phones home | Run without `BRIGADE_NO_UPDATE_CHECK` | Variable set in smoke and any trial; smoke FAILs if the cache appears |
| runx placeholder signatures | Default receipts trusted as proof | Smoke uses a real throwaway seed; entry says never to rely on `--allow-local-development-signatures` |
| Release churn | smolvm shipped three releases in two days; Brigade main is 0.28 beta; runx example layout changed after 0.9.1 | Binaries sha-pinned, Brigade version-pinned, runx example tag-pinned; smokes FAIL or exit 2 with a reason |
