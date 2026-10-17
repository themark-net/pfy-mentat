# Handoff: dev-skills catalog entries 125-127 (2026-10-17)

Why: Mark asked whether bots and Build can pick up skill sets that stop "rookie" systems and security mistakes: PID/lockfile races, a world-shared `/tmp` IPC socket, non-portable secret redaction, restoring untrusted Qt state, int overflow, cross-platform gaps and falsely passing tests (leasegrid-c PRs #73 and #74). The investigation's report lives on the Grok Bot box. This PR adds the three external packs it found worth tracking, at **I0**. Docs only. Not a Feature GO.

| Entry | Pack | License | Take |
|------|------|---------|------|
| 125 | [trailofbits/skills](https://github.com/trailofbits/skills) @ `5c99c03` | **CC-BY-SA-4.0** | **Port 7 skills** as a `[skills].paths` snapshot: property-based-testing, semgrep-rule-creator, variant-analysis, sharp-edges, differential-review, fp-check, testing-handbook-skills/atheris. Edited text must stay CC-BY-SA with attribution |
| 126 | [cosai-oasis/project-codeguard](https://github.com/cosai-oasis/project-codeguard) @ `41160d54980b` (main, two commits after the v1.5.0 tag `5bfe8f9`) | CC-BY-4.0 | Reviewer reference only. Web-centric; nothing on temp-file IPC, PID locks or AF_UNIX |
| 127 | [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill) @ `c1c8a8c` | MIT | Local-IPC companion is a Reviewer reference now; full 6-phase audit before a desktop release |

Files: `sources/entries/125-trailofbits-skills.md`, `126-codeguard.md`, `127-cloudflare-security-audit-skill.md`, and this handoff. No TOOLS.md rows, no `data/tools.json` rows, no smoke scripts, no skills installed.

## What was checked (Grok Bot box, shallow clones)

- ToB: 44 plugins in the marketplace; the 7 port candidates have valid frontmatter (`name` equals folder). General TOCTOU guidance exists (rust-review `toctou-finder.md`, sharp-edges `lang-c.md`), but nothing on PID locks, temp-file IPC or PID reuse.
- CodeGuard: 23 core and 85 OWASP rule files; `skills/codeguard/SKILL.md` frontmatter valid; the grep for systems topics found none.
- Cloudflare: validator tests 65/65 pass on Node 20.19.2. `DESKTOP-MOBILE-AND-LOCAL-IPC.md` covers IPC peer auth, world-writable socket paths and local-file TOCTOU.
- Key finding from the investigation: bandit, ruff `S` and semgrep `p/python`+`p/secrets` produced 0 hits on the leasegrid PR #74 blockers, while 7 project-specific Semgrep rules hit 6 of 11 blocker lines. These packs help **write** such rules and tests; they don't replace them.

## Related work (not in this PR)

- nimo `~/.grok`: `prefer-behavior-and-fail-recover-tests` installed into `~/.grok/skills`, and 3 dead `[skills].paths` entries removed (2 under `~/DEVELOP/local-llm-dev-tools`, 1 at `~/DEVELOP/ponytail/skills`; the pfy-mentat snapshots of the same skills are still registered). Backup at `/tmp/grok-config.toml.bak.20261017-135417`.
- leasegrid-c branch `build/dev-safety-rails` holds a Build drop-in (Semgrep rules + ruff, systems-safety skill + AGENTS.md block, proof-of-RED). It launches after v0.1.7 merges.

## Recommended next steps (not started)

1. Port the 7 ToB skills to `bootstrap/grok-cli/skills-external/trailofbits/` as a byte-identical snapshot with the LICENSE text or URI, ToB credit, upstream URL, pinned SHA `5c99c03fb8a9` and upstream notices; a separate pfy-authored PORT.md (Task → `/agent-loops`); and a frontmatter smoke. Any edited ToB file must be marked as adapted CC-BY-SA material; add the path to `manifest.json` and `[skills].paths`.
2. Add a first-party `systems-safety` skill to `bootstrap/grok-cli/skills/` once the leasegrid version has survived a gate round.
3. Try one Cloudflare guidance-mode review of leasegrid-c's `--join` handoff after the v0.1.7 fixes, to see if it would have found the `/tmp` socket.

## Locks respected

Docs only. Nothing installed on nimo from these packs. Mark's main checkout and the #255, #258, #300 and #301 branches untouched; work done in `~/DEVELOP/pfy-mentat/tmp/dev-skills-catalog` on `catalog/dev-skills-125-127` off origin/main `0d574f0`. No accounts, paid keys or spend.

## How this fails / how we recover

| Risk | How it fails | Recovery |
|------|----------------|----------|
| Share-alike text in pfy-owned skills, or missing notices | Someone pastes ToB text into a first-party skill, or commits the snapshot without LICENSE/credit/SHA | Snapshot stays byte-identical in `skills-external/trailofbits/` with LICENSE (or URI), credit, URL, SHA and notices; Reviewer checks |
| Treating packs as the fix | Rules load, but leasegrid-class bugs still ship | The Semgrep gate and proof-of-RED in the leasegrid drop-in are the real gate |
| Stale pins | Upstream renames skills | Pins recorded per entry; refresh deliberately |
