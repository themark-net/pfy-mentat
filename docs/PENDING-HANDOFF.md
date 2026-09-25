# pfy-mentat — pending handoff (CEO pause 2026-09-24 ~11:20pm PT)

**Purpose:** Freeze current queue + design map so another model/harness can take over without bot chat history.

**Repo tip (nimo dogfood):** `main` @ `7ea4c8f` (Loop UX #243 merged). Local branches kept: `main`, `dev`, `stage` only.

**Org posture:** PAUSED. No auto RELEASE / Build / Cursor implement until founder says go. Catalog PRs **#70–#75 HOLD**. `LIVE_HARD_OFF` still applies to trading/pred-foundry (out of scope here).

---

## Source of truth

| Kind | Where |
|------|--------|
| Work items | **GitHub issues** (this repo) |
| Catalog HOLD | Open PRs **#70–#75** (do not merge/auto-start) |
| Designs | `docs/design/` (index below) |
| Product/ops | `docs/DESIGN.md`, `docs/TODO.md`, `docs/ARCHITECTURE.md`, `docs/ops/` |
| ADRs | `docs/adr/` |

---

## Open GitHub issues (pending)

| # | Title | Posture |
|---|--------|---------|
| [#24](https://github.com/themark-net/pfy-mentat/issues/24) | T-0016 Colibri / large-model lab (250GB pool) | P2 catalog lab — no rush |
| [#25](https://github.com/themark-net/pfy-mentat/issues/25) | Laguna S 2.1 local smoke (Entry 073) | P2 catalog — when hardware allows |
| [#53](https://github.com/themark-net/pfy-mentat/issues/53) | Epic G8 Simple harness-agnostic launch (`./pfy`) | Children done; epic open until release bar explicit |
| [#64](https://github.com/themark-net/pfy-mentat/issues/64) | First stage acceptance: voice ports dev→stage→main | Release checklist — needs human ACK before promote |
| [#198](https://github.com/themark-net/pfy-mentat/issues/198) | catalog seed: ix-infrastructure/Ix | Eventual Stage-0 only — do not auto-start |
| [#204](https://github.com/themark-net/pfy-mentat/issues/204) | catalog seed: 0xranx/OpenContext | Pointer; implement was #205 (see issue) |

Closed recently (context, not pending): #63 branch delete process; #76 runtime umbrella; PR #243 Loop UX merged.

---

## Open PRs (HOLD — do not auto-start)

| PR | Head | Note |
|----|------|------|
| [#70](https://github.com/themark-net/pfy-mentat/pull/70) | `catalog/statewright-entry-056-v2` | Catalog HOLD |
| [#71](https://github.com/themark-net/pfy-mentat/pull/71) | `catalog/not-diamond-entry-057` | Catalog HOLD |
| [#72](https://github.com/themark-net/pfy-mentat/pull/72) | `catalog/holaos-entry-058` | Catalog HOLD |
| [#73](https://github.com/themark-net/pfy-mentat/pull/73) | `catalog/mco-entry-080` | Catalog HOLD |
| [#74](https://github.com/themark-net/pfy-mentat/pull/74) | `catalog/smythos-studio-entry-081` | Catalog HOLD |
| [#75](https://github.com/themark-net/pfy-mentat/pull/75) | `catalog/axon-entry-082` | Catalog HOLD |

---

## Design export map (`docs/design/`)

| File | Role |
|------|------|
| [README.md](design/README.md) | Index for harness takeover |
| [DESKTOP-SPEC.md](design/DESKTOP-SPEC.md) | Desktop / operator window product lock |
| [DESKTOP-SPEC-228.md](design/DESKTOP-SPEC-228.md) | Gab #228 desktop slice |
| [GAB-228-DEVBOT-HANDOFF.md](design/GAB-228-DEVBOT-HANDOFF.md) | Gab implement handoff |
| [JEV-230-DEVBOT-HANDOFF.md](design/JEV-230-DEVBOT-HANDOFF.md) | Jev #230 attach / routing handoff |
| [JEV-230-CUA-S1-FORMS-LOCK.md](design/JEV-230-CUA-S1-FORMS-LOCK.md) | CUA-S1 forms lock |
| [LOOP-243-JOURNEY.md](design/LOOP-243-JOURNEY.md) | Loop UX journey (shipped PR #243) |
| [LOOP-243-IA.md](design/LOOP-243-IA.md) | Loop IA |
| [LOOP-243-WIREFRAMES.md](design/LOOP-243-WIREFRAMES.md) | Loop wireframes |
| [LOOP-243-NON-GOALS.md](design/LOOP-243-NON-GOALS.md) | Loop non-goals |
| [LOOP-243-DEVBOT-HANDOFF.md](design/LOOP-243-DEVBOT-HANDOFF.md) | Loop implement handoff (shipped) |
| [UX-SCHOOL.md](design/UX-SCHOOL.md) | UX school / foundations |

---

## Dogfood (Mark)

On nimo: `~/DEVELOP/pfy-mentat` on `main` @ `7ea4c8f`.

```bash
./pfy setup && ./pfy
```

Do **not** dogfood `dev`/`stage` tips without checking they match `main` (they often lag).

---

## Standing org rules (takeover)

- Grok bots = coordination only; heavy implement → Grok Build on nimo and/or Cursor.
- Escalate to Mark only for money, legal/IP, irreversible damage, credentials/2FA, or a fact only he knows.
- nimo `~/DEVELOP`: one dir per project; temps in `/tmp` or `~/DEVELOP/<project>/tmp`.

---

## Done when this handoff is useful

Next agent opens this file + `docs/design/README.md`, picks an open issue or waits for founder RELEASE, and does not invent work outside the GitHub queue.
