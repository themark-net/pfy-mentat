# Agent Substrate catalog handoff: 2026-10-08

Work item: catalog Agent Substrate (https://github.com/agent-substrate/substrate) at I0, and answer Mark's question about whether its shelving (suspend/resume of idle workloads) can be used locally on nimo, with single-node minikube as the target he named. Done by Grok Bot on the Grok Bot box; nimo was not touched.

## What this adds

| File | What |
|------|------|
| `sources/entries/102-agent-substrate.md` | Entry 102 at I0, with a "Local shelving angle" section, a verdict, and a staged eval plan |
| `docs/automation/agent-substrate-2026-10-08-handoff.md` | This handoff |

Add-only. No TOOLS.md row, no `data/tools*.json` change, no stage card, no Make target, catalog HOLD entries 070-075 untouched. Entry number check: highest on main at `b0bb817` was 101 (atg-compile) and no open PR added 102; `python3 scripts/catalog_check.py` PASSes with 102 added.

## Verdict in one paragraph

A lighter local path worth an eval. The whole Substrate stack on minikube is plausible but unsupported upstream (the repo tests single-node kind only), needs Docker plus about 12 GiB and three manual patches (feature gates, proxy ARP sysctl, registry wiring), and only shelves HTTP actors behind its router, so it stays catalog-only for now. Its shelving primitive is gVisor `runsc checkpoint/restore`, which worked on the box without sudo inside an unprivileged user namespace and kept in-memory state across a restore. That primitive is what could free RAM for big local models, so it gets evaluated first (Stage A in the entry); the minikube run is Stage B and only if Mark wants Substrate's router and multiplexing.

## Box-only smoke (not committed, not a nimo receipt)

Environment: Grok Bot box, kernel 6.12, cgroup v2, uid 1000, no sudo. runsc `release-20260824.0-120-g727c8c389c36` extracted from `https://storage.googleapis.com/gvisor/releases/nightly/2026-09-02/x86_64/gvisor.tar.zstd` (sha256 `d547d81401461fd1c679c5c4fa0a6c2b8ef7dc3c22ce23c9e25dcc4c69cfd06f`, the same pin as Substrate's `manifests/ate-install/sandboxconfig-gvisor.yaml`) into `/tmp/runsc-smoke`.

Bundle: `runsc spec -- <cmd>`, then `root.path=/` read-only and `terminal=false`.

| Step | Result |
|------|--------|
| `runsc --rootless --network=none --ignore-cgroups do echo ...` | Works |
| `runsc --rootless ... checkpoint` | Works |
| `runsc --rootless ... restore` | Refused: `Rootless mode not supported with "restore"` |
| Same cycle inside `unshare -Urm --propagation private` (no `--rootless`) | Works. Shell counter checkpointed at tick 6, restored and continued at tick 7; restore about 110 ms |
| 512 MiB Python process (random bytes), same userns path | Checkpoint 0.76 s, image 516 MB (`checkpoint.img`, `pages.img`, `pages_meta.img`), process killed, restore 0.21 s, counting resumed with the same in-memory values |

Commands, for repeating it in Stage A:

```bash
R="./runsc --network=none --ignore-cgroups --root=$PWD/state"
unshare -Urm --propagation private bash -c "
  $R run -detach -bundle b c1 > out1.log 2>&1
  sleep 3; $R checkpoint -image-path $PWD/img c1; $R delete -force c1
  $R restore -detach -image-path $PWD/img -bundle b c2 > out2.log 2>&1
  sleep 2; head -3 out2.log; $R kill c2 KILL; $R delete -force c2"
```

## Recommended next steps (not started)

1. Read-only preflight on nimo (needs Mark's go to run anything there): cgroup v2, `kernel.apparmor_restrict_unprivileged_userns`, `unshare -Ur true`, whether Docker or Podman is already installed.
2. Stage A: runsc checkpoint/restore under `~/DEVELOP/pfy-mentat/tmp/runsc/` at 1 GiB then 8 GiB, then one idle agent sandbox with networking on. Measure `free -g` while shelved and reconnect behavior after restore.
3. Stage B, only if Stage A passes and Mark wants it: minikube docker driver with the flags in Entry 102. Never the minikube gvisor addon, since Substrate runs its own pinned runsc inside runc worker pods.

## Locks respected

Nothing installed or run on nimo. Mark's founder checkouts untouched; work was in a fresh clone under `/tmp` on the box. No sudo, no system packages; the runsc binary and a Python venv for zstd lived only in `/tmp/runsc-smoke` on the box. No accounts, sign-ins or spend. PR opened, not merged.

## How this fails / how we recover

| Risk | How it fails | Recovery |
|------|----------------|----------|
| Entry number collides | Another branch also takes 102 | `catalog_check` FAILs on the duplicate; renumber on rebase, the entry is one self-contained file |
| Box result read as a nimo result | Someone cites the box timings as nimo numbers | Every box number is labeled box-only; only Stage A receipts from nimo count |
| Upstream moves fast | Paths or flags cited here change in a later Substrate release | The entry pins commit `769fd32630aa`; re-read before Stage B |
