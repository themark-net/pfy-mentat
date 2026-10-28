# RUN-LOG mvp2 trial

Branch `bot/mvp2-trial`. Base for every arm is `997d89264495861a178713ccf7d4447ea828afc4`. No rebase, no force-push, no PR, no merge to main.

Overview: Six small build-only tasks, each with a red acceptance test planted in a fresh worktree, run on local `./pfy build --local` and on one headless cloud Build pass (one retry if the gate fails). Patches stay under `eval/mvp2/patches/`. The trial branch records specs, receipts, and the verdict.

Phases:
- specs | `eval/mvp2/tasks`, `eval/mvp2/gates`, `eval/mvp2/run_trial.py` | six specs, gates red in the sandbox on the base | none | lead
- local arms | `tmp/mvp2-runs` | one local receipt per task, sequential, one model | specs | lead
- cloud arms | `tmp/mvp2-runs` | one cloud gate per task, at most one retry, after the local model is idle | local arms | lead
- handoff | `eval/mvp2/REPORT.md`, `docs/ops/HANDOFF-mvp2-trial.md`, this log | verdict, push `bot/mvp2-trial` | cloud arms | lead

Risks: one GPU and a 32 GiB free-memory guard, so arms are serial. Swap is nearly full, so a second model is not started. Cloud is capped at six tasks plus one retry. Weekly budget percent is not readable here without printing tokens.

## Decisions

See `docs/ops/AUTONOMOUS-DECISIONS-2026-10-27.md`.

## Phases

- specs | proven red in bwrap on 997d892 (failures t1=1 t2=1 t3=1 t4=2 t5=1 t6=3, errors 0). Harness commit follows. Local arms not started.
- local arms | pending
- cloud arms | pending
- handoff | pending
