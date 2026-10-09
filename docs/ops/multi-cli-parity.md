# Multi-CLI parity notes (T-0040)

**Status:** Done 2026-07-30 · **Primary:** Grok CLI (ADR-0002) · **Worker:** OpenCode + Ollama (ADR-0011)  
**Related:** Entry 075 asm · Entry 076 claude-codex-settings · ADR-0009 skill port

## Matrix

| Surface | Skills install | MCP | Cage | Env profiles | Notes |
|---------|----------------|-----|------|--------------|-------|
| **Grok Build** | first-party `bootstrap/grok-cli/skills` + paths | filesystem + write-guard + CM | **primary** `make cage-grok*` | DEPLOY_PROFILE | Operator default |
| **OpenCode** | opencode adapter + skill paths | via config | optional T-0081 | LOCAL_CODER_MODEL | Local bulk worker |
| **Claude Code** | skills via paths / **asm** | project MCP json | not required | CLAUDE.md patterns | Not primary; extract hooks (#27) |
| **Codex / Cursor / Gemini** | asm multi-agent | vendor-specific | n/a | shared guidance packs | Catalog awareness; Entry 076 |
| **Aider / Cline / Continue** | asm registry | plugin-dependent | n/a | — | No forced adoption |

## Honest gaps vs Grok primary

1. **Auth / session** — Grok cage session resume (T-0047) is Grok-specific; Claude/Codex have their own.  
2. **Policy harness** — agent-cage policies tuned for Grok coding-agent; other CLIs not first-class in cage.  
3. **Eval ladder** — implement/matrix assume OpenAI-compatible Ollama path; Claude Code not scored there.  
4. **Skills SoT** — first-party skills authored for Grok skill layout; ports via ADR-0009 hybrid.  

## Non-goals

- No ADR to make Claude Code / Codex primary.  
- No forced multi-CLI install in bootstrap.  
- Parity means **documented capability map**, not feature-equal runtimes.

## Operator path

| Goal | Path |
|------|------|
| Cloud-strong hard tasks | Grok Build / cage |
| Cheap local bulk | OpenCode → Ollama |
| Cross-agent skill distribute | evaluate **asm** (Entry 075, #26) |
| Quality hooks | claude-codex-settings extract (#27) |

## Claude Code (adapter T-0104, attach #221)

Notes only. Primary harness stays Grok (ADR-0002). This section is not a claim that Claude Code is feature-equal, and it is not an install guide.

T-0104 (Claude Code adapter) is **done** in `docs/TODO.md` (issue #57). `data/harnesses.json` id `claude-code`, status `partial`, detect `claude`, `github_issue` 57. Attach: `issue` 221, `script` `pfy_attach_usable_221`, `session_id` `claude`.

- `docs/modules/claude-code-adapter.md` — adapter module: exec `claude` from `./pfy start`; attach usable is issue #221.
- `data/harnesses.json` — registry row above (`status` partial; detect `claude`).
- `scripts/pfy_attach_usable_221.py` — attach usable shim (`--prove` / `--selftest`). Body is `pfylib/attach.py` parameterised by `claude-code.attach`.
- `tests/test_attach.py` — maps `claude-code` to script `pfy_attach_usable_221` and checks `attach.profile("claude")` resolves to id `claude-code`.
- `pfylib/attach.py` — `profile()` accepts the session id `claude` for harness id `claude-code`.
- `pfylib/toolsets.py` — appends the session brief to `CLAUDE.md` under `CLAUDE_CONFIG_DIR`.

Do not read this as feature parity, and do not treat it as steps to install or sign in.
