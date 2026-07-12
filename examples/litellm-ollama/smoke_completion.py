#!/usr/bin/env python3
"""In-cage smoke: LiteLLM completion → host Ollama (OpenAI-compatible /v1).

Env:
  OPENAI_BASE_URL   default http://host.docker.internal:11435/v1
  LITELLM_SMOKE_MODEL  default deepseek-coder:latest
  OLLAMA_API_KEY    default ollama (ignored by Ollama, required by some clients)
"""
from __future__ import annotations

import os
import sys


def main() -> int:
    base = os.environ.get("OPENAI_BASE_URL", "http://host.docker.internal:11435/v1").rstrip("/")
    model_name = os.environ.get("LITELLM_SMOKE_MODEL", "deepseek-coder:latest")
    api_key = os.environ.get("OLLAMA_API_KEY", "ollama")

    # OpenAI-compatible provider through LiteLLM (works with Ollama /v1)
    litellm_model = f"openai/{model_name}"

    print(f"smoke: base={base} model={litellm_model}", flush=True)

    try:
        from litellm import completion
    except ImportError:
        print("error: litellm not installed in this environment", file=sys.stderr)
        return 1

    resp = completion(
        model=litellm_model,
        api_base=base,
        api_key=api_key,
        messages=[
            {
                "role": "user",
                "content": "Reply with exactly one word: pong",
            }
        ],
        max_tokens=16,
        temperature=0,
    )
    text = (resp.choices[0].message.content or "").strip()
    print(f"smoke: response={text!r}", flush=True)
    if not text:
        print("error: empty completion", file=sys.stderr)
        return 1
    print("smoke: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
