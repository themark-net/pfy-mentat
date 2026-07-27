# Build Task: Implement ADR-0013 (Optional Operator TUIs + Empirical Preference)

**Status:** Ready for Grok Build CLI / one-shot / agent-loops  
**Priority:** High  
**Related ADR:** [ADR-0013](../adr/0013-optional-operator-tuis-empirical-preference.md)  
**Date:** 2026-07-27

## Goal

Make the changes required by ADR-0013 so that operator interfaces (especially the AgenC TUI) are treated as optional, independently scoreable components, and so that developer preference becomes an explicit post-deployment empirical dimension in the rubric.

## Definition of Done

1. **CATEGORIZATION.md**
   - Add a clear section for **Operator Interface Fit / Preference (empirical, post-deployment only)** with the factors listed in ADR-0013.
   - Add a short note that local agent isolation / harness security is a distinct concern (agent-cage remains the primary general-purpose example; marketplace-specific sandboxing is separate).
   - Optionally strengthen tags or a subcategory under Pipeline & CI/CD or a new Security/Harness area for isolation patterns.

2. **TOOLS.md**
   - Update the AgenC row:
     - Remove hard “Reference only — not primary (ADR-0010)” language.
     - Note that the TUI is optional and can be bypassed via MCP/CLI/worker.
     - Reference ADR-0013.
     - Flag preference score as “pending real use” / empirical.
     - Keep existing S1–S4 scores and overall 78 / B-tier for now (objective stages unchanged).
   - Update the operator default sentence at the top if it still hard-references only ADR-0010.

3. **data/tools.json**
   - Mirror the TOOLS.md AgenC notes update (optional TUI, ADR-0013, preference pending).
   - Keep scores and tier unchanged until new empirical data arrives.

4. **docs/adr/README.md**
   - Add row for 0013.
   - Mark 0010 status as “Superseded by 0013” (or equivalent).

5. **Optional but recommended**
   - Short note in bootstrap/agenc/ or integration notes that AgenC can be used as a selectable optional surface.
   - Extend one-shot or agent-loops skill comments / DoD to capture preference receipts after real runs (even if the capture mechanism is later).

## Acceptance criteria

- All files above are updated consistently.
- Triple-write rule respected (TOOLS.md + data/tools.json).
- No change to default primary path (Grok CLI + agent-cage).
- ADR-0010 history is preserved; only its posture is superseded.
- `make` targets or existing smokes still pass (no functional breakage).

## Notes for the builder

- Preference is deliberately left blank / pending. Do not invent a numeric preference score.
- Isolation side-question is already answered in the ADR: agent-cage is not superseded; treat isolation as its own concern.
- Keep language precise and receipt-oriented. No marketing tone.

## Suggested command sequence (illustrative)

```bash
# After reading ADR-0013 and this task
# Edit CATEGORIZATION.md, TOOLS.md, data/tools.json, docs/adr/README.md
# Then verify with existing catalog hygiene if available
```

Once these documentation and catalog updates are complete, the preference dimension and optional-TUI posture are live. Subsequent real-use receipts can fill the preference scores.
