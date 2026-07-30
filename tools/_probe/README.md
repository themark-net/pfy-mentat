# I2 ad-hoc probes (integration stages)

**Stage:** I2 — lightweight copy for ambiguous evaluation ([docs/ops/integration-stages.md](../../docs/ops/integration-stages.md))

## Rules

1. Working tree of a probe **< ~50 MB** (no model weights).  
2. Not an I3 onboard — no default Make dependency on probes.  
3. Prefer `git clone --depth 1` into a **gitignore**d local path; optional committed *stubs* only.  
4. Document uses / features / potential / non-goals before promoting to I3.

## Layout

```
tools/_probe/<tool-slug>/   # optional local only; large trees gitignored
```

This directory may hold small scripts/notes; do not commit upstream clones by default.
