# Continue.dev config recipe

Copy this snippet into Continue. Do **not** git-vendor the IDE.

This is an IDE **config recipe**, not a CLI harness. After `./pfy start` (or the ADR-0014 detector), set `apiBase` from `$LOCAL_OPENAI_BASE_URL`. Append `/v1` if it is missing.

Replace the dummy `apiBase` in `config.json` with `$LOCAL_OPENAI_BASE_URL` (ensure `/v1`). The FreeToken example is `:1919`, not Ollama-only.

Detect order (first live wins):

1. FreeToken `:1919`
2. llama-swap `:9292`
3. llama-server `:8080`
4. Ollama `:11434` last

`./pfy start continue` remains **STUB** exit 2. Docker/binary is not ready. Do not exec the IDE from pfy.
