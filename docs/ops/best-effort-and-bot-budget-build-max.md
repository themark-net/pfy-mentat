# Best effort and bot-budget / Build-max

**Purpose:** Short pointer. The portable SoT is the first-party skill, shared by Build, cage, and `install.sh`.  
**Skill:** [bootstrap/grok-cli/skills/best-effort-and-bot-budget-build-max/SKILL.md](../../bootstrap/grok-cli/skills/best-effort-and-bot-budget-build-max/SKILL.md)  
**Invoke:** `/best-effort-and-bot-budget-build-max`  
**Verify:** `make smoke-grok-skills` · [skill-verification.md](skill-verification.md)

Default path is **BEST_EFFORT** for docs, skills, and reversible dogfood. **GATED** stays for public release, money, legal/IP, and irreversible prod. Work lands on a named branch and PR. Do not share an open founder Build checkout. A docs/skills port does not issue Feature GO.

The skill holds the two paths, isolation rules, and the failure/recovery table. This note does not duplicate that prose.
