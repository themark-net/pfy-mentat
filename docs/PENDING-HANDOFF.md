# Pending handoff

Git plus this file is the handoff when another checkout may be open. Do not commit, reset, or stash on an open founder Build branch.

## 2026-10-04 — Kolibri-1 catalog + local smoke lab (Entry 085)

- **Branch:** `bot/kolibri-1` (from main `53b24ec`). Worktree `/home/mark/DEVELOP/pfy-mentat/tmp/kolibri-1`. Operator ask: "Add to pfy-mentat. Pull it and test." (X post 2106306843052052616)
- **Landed:** `sources/entries/085-kolibri-1.md` (084 is taken by open PR #254), a TOOLS.md row (B, 72, public-docs scores), a `data/tools.json` row + `data/tool_integration_stages.json` (I0), `examples/kolibri1-llamacpp/` (build/download/serve/smoke), `make smoke-kolibri1`, and the receipt `pipelines/smoke/kolibri1/latest.json`.
- **Paths checked:** (a) Community GGUFs exist, but every one needs a llama.cpp source patch; stock llama.cpp and Ollama have no `kolibri1` (llama.cpp#29922 open). The smallest is `Eliasfpv28/Kolibri-1-Q3_K_S-GGUF` at 33.87 GB. (b) The only other registered machine, GROKBOT-WIN, is offline; nimo is AMD Strix Halo (Radeon 8060S, 64 GiB VRAM carve-out, 61 GiB RAM, no NVIDIA). (c) Kolibri is not on OpenRouter and has no HF inference-provider mapping. No Aleph Alpha, OpenRouter, or HF key names are in nimo env or `.env`.
- **Done on nimo:** The patched llama.cpp (`edd6e2b` + `kolibri1-runtime.patch`, CPU backend) built OK in `tmp/kolibri-runtime/build-cpu`. The Q3_K_S GGUF is downloading (16-way ranged, about 8-10 MB/s) into `tmp/models/Kolibri-1-Q3_K_S-GGUF/` (gitignored). No official 78 GB FP8 weights were pulled. Only config/tokenizer/card were fetched, into `tmp/models/Kolibri-1-meta/`.
- **Smoke at PR time:** `FAIL_NO_BACKEND` (exit 2). Reason: the GGUF download was incomplete. That is honest, not a stub.
- **Next:** (1) When `download.sh` prints `DL_OK` (sha256 verified), run `make smoke-kolibri1` (CPU, mmap; the 31.5 GiB file is about equal to free RAM, so loads may be slow). Commit the new receipt and flip the stage to I1 only on PASS. (2) For the GPU path (64 GiB iGPU), Vulkan headers + `glslc` are needed for `KOLIBRI_BACKEND=vulkan ./build.sh`. Get them via a user-space SDK under ~/DEVELOP or with apt, which **needs Mark's approval**. (3) The official FP8 path needs NVIDIA (at least 2x A100 80GB) or a hosted endpoint; set `KOLIBRI_BASE_URL` to reuse the smoke.
- **Out of scope:** catalog 70–75 HOLD, other open PRs, Feature GO.

## 2026-09-28 — founder standings into portable skills SoT

- **Branch:** `bot/skills-port-standings-20260928` (from main `bd35bad`)
- **Prior:** stalled `bot/skills-port-standings-20260925` @ `d262300` cherry-picked here. That branch was never a PR. Do not force-push `main`.
- **Landed:** `prefer-behavior-and-fail-recover-tests`, `ui-is-the-app-design-in-loop`, `best-effort-and-bot-budget-build-max`
- **SoT:** `bootstrap/grok-cli/skills/<name>/` (org bot skills stay pointers). Project mirror: `.grok/skills/`.
- **Out of scope:** catalog 70–75 HOLD, LIVE_HARD_OFF, product UI, Feature GO.
- **Verify:** `make smoke-grok-skills`
- **Next:** merge the docs/skills PR when checks are green. Pattern: [port-bot-doctrine-to-pfy-sot.md](ops/port-bot-doctrine-to-pfy-sot.md).
