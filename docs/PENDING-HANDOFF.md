# Pending handoff

Git plus this file is the handoff when another checkout may be open. Do not commit, reset, or stash on an open founder Build branch.

## 2026-10-04 — DRAFT: Loop agent-picker (split from PR #256)

- **Branch:** `build/loop-agent-picker-0925`
- **Why split:** Sep 25 Build added a grok/OpenCode/Hermes/Codex/Claude/Gab Loop agent picker, per-agent toolset paint, and dynamic "Open … with …" CTA (`gui/operator/frontend/*`, `scripts/pfy-gui.py`, `pfylib/loop_paint.py`, board/launch wiring, `ensure_compose_defaults`).
- **Conflicts with:** `docs/design/LOOP-243-*` on main (landed Oct 1, newer): Loop is **not** a harness picker; Launch session opens **grok or OpenCode only**.
- **Decision:** newer design lock wins for now. This branch is DRAFT until a Design pack revisits picker vs LOOP-243.
- **Sibling:** non-GUI CLI/catalog work stays on `build/pfy-cli-catalog-cards-0925` (PR #256).

## 2026-09-28 — founder standings into portable skills SoT

- **Branch:** `bot/skills-port-standings-20260928` (from main `bd35bad`)
- **Prior:** stalled `bot/skills-port-standings-20260925` @ `d262300` cherry-picked here. That branch was never a PR. Do not force-push `main`.
- **Landed:** `prefer-behavior-and-fail-recover-tests`, `ui-is-the-app-design-in-loop`, `best-effort-and-bot-budget-build-max`
- **SoT:** `bootstrap/grok-cli/skills/<name>/` (org bot skills stay pointers). Project mirror: `.grok/skills/`.
- **Out of scope:** catalog 70–75 HOLD, LIVE_HARD_OFF, product UI, Feature GO.
- **Verify:** `make smoke-grok-skills`
- **Next:** merge the docs/skills PR when checks are green. Pattern: [port-bot-doctrine-to-pfy-sot.md](ops/port-bot-doctrine-to-pfy-sot.md).
