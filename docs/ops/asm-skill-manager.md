# asm (agent-skill-manager) — Entry 075 / #26

**Stage:** I1 catalog · HD #37 default **pattern-only** until human chooses adopt.

## Soft smoke (no forced npm global)

```bash
make smoke-asm   # soft-SKIP if node/npm/asm missing
```

## First-party publish path (without asm)

1. Author skill under `bootstrap/grok-cli/skills/<name>/`  
2. `make smoke-grok-skills` / `eval-structural`  
3. Cage install: existing `grok-skills-install` / workspace sync  

asm remains optional multi-CLI distribute layer.
