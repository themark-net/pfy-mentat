# Module: OpenCode host adapter

**Purpose:** Secondary operator surface. Skills SoT stays `bootstrap/grok-cli/skills` (`OPENCODE_SKILLS`). Inference via `LOCAL_OPENAI_BASE_URL` from the detector (not Ollama-only).

## Entry

```bash
./pfy harness use opencode
./pfy start opencode
```

Package notes: [bootstrap/opencode/README.md](../../bootstrap/opencode/README.md)

Missing `opencode` / `opencode-cli`: `STUB harness: opencode`, issue #55, exit 2.

## Not yet

- OpenCode-in-cage parity (T-0081)
- Replacing Grok as default harness
- Forking a second skill tree
