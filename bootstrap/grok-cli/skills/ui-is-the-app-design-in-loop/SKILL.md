---
name: ui-is-the-app-design-in-loop
description: >
  Use this when routing operator-facing UI work, writing a RELEASE or DoD, or
  reviewing a UI PR. Design stays in the loop; the UI is the app; never ask
  what we already know; keep levers contextual to the current view.
argument-hint: "[review | dod]"
---

# UI is the app (Design in the loop)

Use this when routing operator-facing work, writing a RELEASE/DoD, reviewing a UI PR, or when implement is about to bolt a control onto a screen without a design pack.

See [PORT.md](PORT.md).

## Doctrine (2026-09-25)

- **The UI is the app.** If the human surface is wrong, the product fails — including private dogfood.
- **UX for humans ≈ UI in practice.** Shipped code still has to fit an intuitive interface (not a bolted status dump).
- Bolting is fine for **lab / functionality** probes. It is **not** fine as the product shape.

### Iron principles

1. **Never ask the user what we already know.** Prefill, infer, remember; only ask for missing decisions.
2. **Contextual levers.** Every control is intuitively tied to what is on screen now. No digging for settings; no launching everything via a pile of tags/menus detached from context.

### Integration lesson

Surfaces that are used together should grow together (bots / Build / chat / Imagine). Prefer one coherent place that absorbs function over parallel chrome that never meets.

## Keep Design in the loop (required path)

For **operator-facing** product work (pfy, Leasegrid Sync, Jobbar, Practice Minder, similar):

| Stage | Who | Gate |
|-------|-----|------|
| What’s next | CEO/PM + roadmap | Design is tipped the next 1–3 slices **before** implement starts |
| Structure | **Design** | Short pack in `docs/design/` (IA, primary journey, contextual controls, what we already know → don’t ask). Mobbin/Superdesign OK for references. |
| Implement | Build/Cursor | Follow the pack; DoD cites the design doc path |
| Verify | Tester/Reviewer | FAIL if new chrome asks known facts, buries levers, or ships bolted panels with no design pack on a product/dogfood path |

**BEST_EFFORT lab bolt:** allowed behind a flag/branch for functionality only; must not MERGE as the product UI without Design pass (or CEO waiver).

**Design must know what’s next.** If Design is dark on the roadmap, CEO/PM tips them — don’t invent chrome for a surprise feature mid-implement.

## FAIL / rewrite smells

- Settings graveyard / tag soup to launch everything
- Forms that re-ask profile, paths, or state the app already has
- New feature = new top-level page with no home in current IA
- “Honest state dump” / adapter lectures in operator chrome
- Implement PR with UI and empty or stale `docs/design/` for that slice

## DoD paste line

```
UI: Design-in-loop. Pack in docs/design/ before product UI. Never ask what we know. Levers stay contextual to the current view. Lab bolts OK; product/dogfood UI needs Design pass. UI is the app.
```

## References

Mobbin and Superdesign are optional visual references inside the design pack. This skill does not require an org bot id.

Do not put the founder’s name in agent output. Design/PM/CEO escalate money, legal, credentials, and facts only the founder knows via CEO.
