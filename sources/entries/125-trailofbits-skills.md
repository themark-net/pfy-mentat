### Entry 125: Trail of Bits skills — security-audit skill pack for coding agents (property tests, Semgrep rule writing, variant analysis, sharp edges)

- **URL**: https://github.com/trailofbits/skills (**CC-BY-SA-4.0**, Markdown skills plus helper scripts; 44 plugins / 85 `SKILL.md` files; about 7,618 stars at this read; checked at commit `5c99c03fb8a9`, 2026-10-15)
- **Date**: 2026-10-17 (dev-skills investigation: stop "rookie" systems and security mistakes in Build and bot output)
- **Source / Poster**: Mark's dev-skills ask after leasegrid-c PRs #73 and #74; seen on X via @ai4cybersec, https://x.com/ai4cybersec/status/2110790103392210956, and a reviewer's use on LND PRs, https://x.com/iamflops/status/2047433185948995598
- **Summary / Key Claims** (upstream README and skill frontmatter): Trail of Bits' audit playbook as Claude Code / Codex plugins. Covers smart-contract scanners, C/C++ and Rust review, supply-chain audit, YARA, zeroize audit, an Actions auditor for agent risks, and general skills: `property-based-testing` (Hypothesis, fast-check, proptest), `mutation-testing` (mewt/muton campaigns and surviving-mutant triage), `semgrep-rule-creator`, `variant-analysis` (find other instances of one root cause), `sharp-edges` (footgun APIs and configs), `differential-review` (security review of a diff with blast radius), `fp-check` (true/false-positive verdict with evidence), and `testing-handbook-skills` (atheris, AFL++, cargo-fuzz, sanitizers).
- **Worth porting** (as a Grok `[skills].paths` pack, unmodified files plus attribution):

| Skill | Use here |
|-------|----------|
| `property-based-testing` | Build writes Hypothesis properties for parsers, restored state and redaction (leasegrid B3/B5-class bugs) |
| `semgrep-rule-creator` | Turn each Tester/Reviewer blocker into a project Semgrep rule |
| `variant-analysis` | After a blocker, hunt its siblings before the next gate round |
| `sharp-edges` | Reviewer lens for footgun APIs (QLockFile stale handling, QLocalServer defaults, killpg) |
| `differential-review` | Reviewer pass on a PR diff with blast radius |
| `fp-check` | Triage scanner findings before they become gate noise |
| `testing-handbook-skills/atheris` | Optional nightly Python fuzzing on nimo |

  Skip: blockchain, YARA, Burp, DWARF, Lean, zeroize, C/C++/Rust review, culture/game plugins.
- **License note**: CC-BY-SA-4.0 is share-alike. Pointing Grok at an unmodified snapshot via `[skills].paths` is fine with attribution. If we **edit** a skill (a pfy port like `skills-external/claude-unified-agents/`), the edited text must stay CC-BY-SA-4.0 with attribution and a change note. Keep such ports in their own folder with the upstream LICENSE; never fold the text into pfy-owned first-party skills.
- **Fit on nimo**: Plain files; no GPU, no model, no service. A pinned snapshot under `~/DEVELOP/pfy-mentat/bootstrap/grok-cli/skills-external/trailofbits/` (only the skills above) registered in `[skills].paths`, the same way as `mattpocock/`. Some skills assume Claude Code tools (Task, plugins); Grok reads them as guidance.
- **Verified on the Grok Bot box** (shallow clone in `/workspace`): 44 plugins in `.claude-plugin/marketplace.json`; all 7 port candidates have frontmatter whose `name` equals the folder, descriptions 179–845 chars, bodies 3.9–11.8 KB. A grep for temp-file, PID-lock, AF_UNIX, pid-reuse and TOCTOU topics found **no** skill covering local systems races, so the leasegrid lock/IPC class still needs a pfy-owned skill.
- **Extracted Repos / Tools**: https://github.com/trailofbits/skills · https://github.com/trailofbits/skills/tree/main/plugins/property-based-testing · https://github.com/trailofbits/skills/tree/main/plugins/semgrep-rule-creator · https://github.com/trailofbits/skills/tree/main/plugins/variant-analysis
- **TOOLS.md Link**: None yet. I0 awareness. No TOOLS.md row, no `data/tools.json` row.
- **Smoke**: None in this slice (docs-only entry). Next step is a `make smoke-grok-skills` style frontmatter check over the ported snapshot.
- **Non-goals**: No `claude plugin marketplace add`, no plugin installs, no copying skill text into first-party skills, no mewt/muton install.
- **How this fails / how we recover**:

| Risk | How it fails | Recovery |
|------|----------------|----------|
| Share-alike leak | Edited ToB text lands in a pfy-owned skill | Ports live only under `skills-external/trailofbits/` with LICENSE and attribution; Reviewer checks |
| Context bloat | Big skills crowd a local model's context | Port only the 7 listed; load per task, not always-on |
| Claude-only assumptions | Skill tells the agent to use Task or a plugin command | PORT.md maps Task to `/agent-loops` like the claude-unified-agents port |
| Upstream churn | Skills renamed or reshaped | Pin the commit; refresh deliberately |

- **Status**: Cataloged I0. Read and checked on the Grok Bot box; not installed on nimo.
