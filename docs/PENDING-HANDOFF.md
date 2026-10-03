# Pending handoff

Git plus this file is the handoff when another checkout may be open. Do not commit, reset, or stash on an open founder Build branch.

## 2026-10-02 — #198 Ix Stage-0 receipt

- **Branch:** `bot/ix-198-stage0` (isolated worktree). This slice is [#198](https://github.com/themark-net/pfy-mentat/issues/198) only. Do not push. No Feature GO.
- **Verdict:** Stage-0 FAIL / I0 awareness. Receipt: [sources/entries/084-ix.md](../sources/entries/084-ix.md). No TOOLS.md row and no `data/tools.json` row.
- **Shown:** Ix `LICENSE` is Apache-2.0 (commercial/research, not copyleft). README hello-world is `ix map .` then `ix explain AuthService` (cited, not run). Quickstart command is `curl -fsSL https://ix-infra.com/install.sh | sh`.
- **Not shown:** a fresh Ubuntu/Mac setup under 5 minutes. The installer says the Docker Desktop download is ~700MB and may take a few minutes, then the image pull may take a few minutes. macOS first launch waits up to 5 minutes before that pull. `arangodb:3.12.11` is Business Source License 1.1 (internal use allowed). It is not vendored.
- **Unchanged:** `TOOLS.md`, `data/tools.json`, pfy runtime, product UI, Make targets, env registry.
- **Verify:** `python3 scripts/pfy_ix_198.py` (exit 0). The check fails if the receipt is missing, if the status claims Stage-0 PASS without license/quickstart/hello-world evidence or while those timing quotes remain, or if product files attach Ix.
- **Risks:** A PASS while the timing quotes remain is a false pass — the check exits 1; promote only with a timed fresh log. Stripping the quotes without re-reading `scripts/install/install.sh` at pin `48687b5b403051f520c54cd14e01f90ddd444bc7` hides the same failure — re-read the installer before any PASS. Reading Apache as covering Arango misses BSL 1.1 — re-read that LICENSE before any embed. Treating the cited `ix map` as a live run hides a broken release — run it outside this repo before a catalog row. A product-file attach is reverted; entry 084 stays the artifact.
- **Next:** leave Ix at I0. Re-time the install outside this repo before any catalog row. Do not pull images or weights on this branch.

## 2026-09-28 — founder standings into portable skills SoT

- **Branch:** `bot/skills-port-standings-20260928` (from main `bd35bad`)
- **Prior:** stalled `bot/skills-port-standings-20260925` @ `d262300` cherry-picked here. That branch was never a PR. Do not force-push `main`.
- **Landed:** `prefer-behavior-and-fail-recover-tests`, `ui-is-the-app-design-in-loop`, `best-effort-and-bot-budget-build-max`
- **SoT:** `bootstrap/grok-cli/skills/<name>/` (org bot skills stay pointers). Project mirror: `.grok/skills/`.
- **Out of scope:** catalog 70–75 HOLD, LIVE_HARD_OFF, product UI, Feature GO.
- **Verify:** `make smoke-grok-skills`
- **Next:** merge the docs/skills PR when checks are green. Pattern: [port-bot-doctrine-to-pfy-sot.md](ops/port-bot-doctrine-to-pfy-sot.md).
