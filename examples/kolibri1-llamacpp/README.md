# Kolibri-1 local lab: patched llama.cpp + community GGUF

Catalog: [Entry 085](../../sources/entries/085-kolibri-1.md). Model: https://huggingface.co/Aleph-Alpha/Kolibri-1 (Apache-2.0).

The official checkpoint is FP8 (about 78 GB). It needs vLLM plus `aleph-alpha-inference>=1` and at least 2x A100 80GB or 1x H200. nimo has no NVIDIA GPU, so this lab uses the most real local path instead:

| Step | Command | Lands in (gitignored) |
|------|---------|-----------------------|
| Build llama.cpp `edd6e2b` + community `kolibri1` patch | `./build.sh` (`KOLIBRI_BACKEND=vulkan` needs Vulkan headers + `glslc`) | `tmp/kolibri-runtime/` |
| Download `Eliasfpv28/Kolibri-1-Q3_K_S-GGUF` (33.87 GB, sha256-checked) | `./download.sh` | `tmp/models/Kolibri-1-Q3_K_S-GGUF/` |
| Serve (localhost:8081, OpenAI-compatible) | `./serve.sh` | n/a |
| Smoke (EN, DE, tool call) | `make smoke-kolibri1` | `pipelines/smoke/kolibri1/latest.json` |

Paths resolve to the canonical checkout's `tmp/`, so they work from worktrees too. Override with `KOLIBRI_RUNTIME_DIR`, `KOLIBRI_MODEL_DIR`, `KOLIBRI_GGUF`, or `KOLIBRI_PORT`.

**Operate-or-FAIL:** `smoke.py` exits 2 (`FAIL_NO_BACKEND`) and records the exact reason if any of these is true: no patched server, an incomplete GGUF, or a server that does not come up. It exits 1 if a check fails, and 0 only when all three checks pass.

Any other OpenAI-compatible backend works too: `KOLIBRI_BASE_URL=http://host:8000/v1 KOLIBRI_MODEL=Aleph-Alpha/Kolibri-1 KOLIBRI_API_KEY_ENV=NAME_OF_KEY_VAR make smoke-kolibri1`.

**Caveats:** The GGUF is an unofficial, experimental port. Its porter tested only 4k context with no reasoning or tool calling. Stock llama.cpp and Ollama do not load `kolibri1` yet (ggml-org/llama.cpp#29922). The 31.5 GiB file is close to nimo's free RAM (about 31 GB). The CPU backend relies on mmap, so expect slow loads. The Vulkan backend (64 GiB iGPU carve-out on Strix Halo) is the better target.
