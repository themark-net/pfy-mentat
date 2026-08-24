# Module: Claude Code adapter

**Purpose:** Exec `claude` from `./pfy start claude-code`. Inference via `LOCAL_OPENAI_BASE_URL` from the ADR-0014 detector when ready (`OPENAI_BASE_URL` defaults to that). Do not invent Claude-specific flags. Optional skills-external / claude-unified-agents path is documentation only; this adapter does not vendor Claude.

## Entry

```bash
./pfy harness use claude-code
./pfy start claude-code
```

Detect: `claude` on PATH.

Missing binary: `STUB harness: claude-code`, issue #57, official installer, exit 2. No fake ready. Credentials/2FA are owner-only.

```bash
curl -fsSL https://claude.ai/install.sh | bash
claude   # login in the CLI
```

Official docs: [Claude Code](https://docs.anthropic.com/en/docs/claude-code)

## Not yet

- Vendoring Claude into git
- Invented Anthropic/Claude env flags
- Other harness adapters
