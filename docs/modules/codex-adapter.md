# Module: Codex adapter

**Purpose:** Exec `codex` from `./pfy start codex`. Inference via `LOCAL_OPENAI_BASE_URL` from the ADR-0014 detector when ready (`OPENAI_BASE_URL` defaults to that). Do not invent Codex-specific flags.

## Entry

```bash
./pfy harness use codex
./pfy start codex
```

Detect: `codex` on PATH.

Missing binary: `STUB harness: codex`, issue #58, official installer, exit 2. No fake ready. Credentials/2FA are owner-only.

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
codex   # login in the CLI
```

Upstream: [openai/codex](https://github.com/openai/codex)

## Not yet

- Vendoring Codex into git
- Invented Codex flags
- Other harness adapters
