# investigate — first-party method rewrite (T-0017)

- **Placement:** first-party (`bootstrap/grok-cli/skills/investigate/`) — installed to `~/.grok/skills/`
- **Upstream inspiration:** https://github.com/garrytan/gstack `investigate/` (MIT)
- **Upstream pin at eval:** `7c9df1c568a9`
- **Not a raw snapshot:** gstack SKILL.md is Claude-harness-generated; see
  `docs/ops/gstack-skill-port-comparison.md` (`raw-port-blocked`, recommended
  `first-party-rewrite`)
- **Taken:** Iron Law, phases (investigate → patterns → hypothesis → fix → report),
  3-strike, blast-radius pause, DEBUG REPORT shape
- **Omitted:** preamble, telemetry, freeze/bin, GBrain, AskUserQuestion protocol,
  auto-generated template body
- **Policy:** ADR-0009 hybrid  
