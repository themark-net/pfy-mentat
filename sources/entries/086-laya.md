### Entry 086: Laya — open-weight typed decisions on CPU, Jev-compatible `laya-serve`

- **URL**: https://github.com/NandhaKishorM/laya (Apache-2.0, about 31k stars at this read, pushed 2026-10-05)
- **Date**: 2026-10-05 (daily X intake)
- **Source / Poster**: Mark's bookmark of @mizorewww's laya-mlx post, https://x.com/mizorewww/status/2101473552956555427 (the MLX port is https://github.com/mizorewww/laya-mlx, Apple Silicon only). Laya itself is by Convai Innovations; weights at https://huggingface.co/convaiinnovations/laya
- **Summary / Key Claims** (upstream README): Non-autoregressive "System 1" decision engine. Typed `choice`, `score` and `noul` (yes/no probability) answers over text or JSON in one forward pass, no generated JSON to parse. Three checkpoints: `laya` (ModernBERT-large, 421M, 512 ctx, English), `laya-multilingual` (mmBERT-base, 322M, 1024 ctx, up to 8,192 with `max_len`), `laya-typed-decisions` (421M, 1024 ctx). A `Router` picks the checkpoint per request. Device order is CUDA, then MPS, then CPU; CPU runs fp32. `pip install laya`, Python 3.10+. Extras: `laya[serve]`, `laya[mcp]`, `laya[onnx]` (INT8 CPU export). Upstream says the shipped checkpoints work zero-shot but fine-tuning is where accuracy jumps: on its 2,000-decision typed-decisions benchmark the fine-tuned checkpoint scores 0.766 vs 0.362 for the base English checkpoint.
- **Why it matters here**: `laya-serve` exposes `POST /v1/systemone`, the same wire protocol as TypeSafe's hosted Jev, and the README says an existing Jev client only needs its base URL repointed. ADR-0016 has a `typesafe` lane (`POST https://api.typesafe.ai/v1/systemone`) that we can't use because we have no TypeSafe key. Laya is the first candidate that could fill that slot locally on nimo with no key, no signup and no GPU.
- **Fit on nimo** (AMD Strix Halo, 61 GB RAM, no NVIDIA): Yes on paper. The models are 322M to 421M parameters and run on CPU. All three checkpoints are about 2.3 GB on disk. Install goes in a venv under `~/DEVELOP/pfy-mentat/tmp/` only.
- **Extracted Repos / Tools**: https://github.com/NandhaKishorM/laya · https://github.com/mizorewww/laya-mlx (MLX port, Apple only, not usable on nimo) · https://huggingface.co/convaiinnovations/laya
- **TOOLS.md Link**: None yet. I0 awareness. No TOOLS.md row, no `data/tools.json` row, no stage card.
- **Smoke**: `python3 examples/typed-decisions-local/smoke.py --entry laya`. It looks for `$LAYA_PYTHON` or `~/DEVELOP/pfy-mentat/tmp/laya-venv/bin/python`. Missing venv exits 2 with the install line. With the venv it runs the README billing example on CPU and expects `billing`. Receipt: `pipelines/smoke/laya/latest.json`.
- **Next gate (eval-auto trial)**: Run `laya-serve` on nimo bound to 127.0.0.1 and point the ADR-0016 `typesafe` lane's base URL at it. Compare it against CUA-S1-FORMS on the same live wizard/engine Choice options at the ~0.85 gate. Record accuracy, latency and whether the confidence margin is honest. Do not wire it into the default smoke until it passes.
- **Non-goals**: No product attach in this slice. No Make target or env var. No `pip install` outside `~/DEVELOP`. Catalog 70–75 stay HOLD.
- **How this fails / how we recover**:

| Risk | How it fails | Recovery |
|------|----------------|----------|
| Wire contract drift | `laya-serve` answers `/v1/systemone` but a field our client reads differs from Jev | Set `LAYA_JEV_STRICT` (upstream flag) and diff one response against the ADR-0016 parser before the trial counts |
| Confidence read as correctness | Base-checkpoint `answer_confidence` clears 0.85 on a wrong answer | Upstream says confidence is not accuracy. Gate on our own labeled Choice set, not on Laya's number |
| Weights download blocked | HF hub unreachable from nimo | Smoke exits 1 with the error. Retry later; don't vendor weights into the repo |

- **Box receipt (not nimo, 2026-10-05)**: The smoke PASSed on the Grok Bot box (Linux x86_64, 8 vCPU, no GPU) with `laya` 0.3.28 and CPU-only `torch` 2.14.1 in a throwaway venv: `choice=billing`, `answer_confidence=0.9865`, routed to the `english` checkpoint, 16.9 s wall time including the first checkpoint download and load. This shows the CPU path works; it says nothing yet about accuracy on our Choice options or about nimo.
- **Status**: Cataloged I0. Smoke PASS on the Grok Bot box; not yet run on nimo.
