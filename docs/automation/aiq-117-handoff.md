# AI-Q Entry 117 handoff — 2026-10-14

Mark approved NVIDIA AI-Q (https://github.com/NVIDIA-AI-Blueprints/aiq) as catalog Entry 117. Entries 112–116 stay on open PRs 292/293 and are not on this branch. This slice is I0 only: no TOOLS.md row, no `data/tools.json` row, no stage card, no Make target. Catalog HOLD 070–075 was not touched.

Worktree: `~/DEVELOP/pfy-mentat/tmp/aiq-117`, branch `catalog/aiq-117`, cut from `origin/main` `f1224d7`. Push is `git push -u origin catalog/aiq-117` only.

## Verdict

**Works local.** Smoke exit 0, receipt verdict `PASS`, report 425 characters.

The question was one recent Rust news headline. The report named "Rustls 0.23.46 Released With Four Security Fixes" and cited `https://www.phoronix.com/news/Rustls-0.23.46-Released` (Phoronix). That page was not re-fetched here (Cloudflare 403), so the headline is the agent report, not a second source check.

Receipt (gitignored, not committed): `pipelines/smoke/aiq/latest.json`.

A direct `ChatOpenAI` probe through the same venv, before `nat run`, returned `pong` in 25.8s. That checked the OpenAI client path. The PASS above is the blueprint `nat run`.

## What ran

1. Research clone at `~/DEVELOP/pfy-mentat/tmp/aiq/src`, pin `951a1a1114e9818073ddbe2a5fdbfa824751f4d3` (2026-10-10, `fix(ui): upgrade next and sharp to clear npm audit findings (#494)`). Package `deep-researcher-agent` 2.2.0, Apache-2.0, 898 stars at the unauthenticated API read. `nvidia-nat` / `nvidia-nat-core` 1.8.0. `nemo-relay` git rev `ffb24817442bac99212da0971b13bdad5bc4d84d`.
2. `python3 examples/x-intake-local/smoke_117.py --stage` — `uv sync --python 3.13 --frozen --group dev` into `~/DEVELOP/pfy-mentat/tmp/aiq/.venv`. Host CPython is 3.14.4; the package requires `>=3.11,<3.14`, so the venv is CPython 3.13.11 under `tmp/aiq/python`. `uv` is 0.9.26 (`scripts/setup.sh` prefers `>=0.11.25`; frozen sync exited 0). `nat, version 1.8.0`.
3. `python3 examples/x-intake-local/smoke_117.py --entry aiq` — local YAML, every LLM role `_type: openai` at `http://localhost:11434/v1` model `qwen3.6:35b`, literal `api_key: local-dummy`, DuckDuckGo News only, clarifier and escalation off. Ollama `/api/tags` had the model. `nat run --input` produced the report above.
4. Unit tests in `tests/test_x_intake_smoke_117.py`: sentinel env keys never reach the child, a stub grandchild dies on timeout, unstaged `AIQ_ROOT` exits 2, and `pipelines/smoke/aiq/` is gitignored while `pipelines/smoke/kolibri1/latest.json` is not. Those runs set `AIQ_RECEIPT` to a temp file. The first full-suite run, before that override, replaced the operator receipt with the unstaged exit 2; the PASS receipt was restored from the smoke log and the original JSON.
5. `python3 -m unittest discover -s tests -t .` — **232 tests, OK, skipped=4** (12.4s).
6. `python3 scripts/catalog_check.py` — **PASS** `n_json=7` `toolsets=8` `linked=2` `catalog_tool=null:6` `tools_md=51` `stage_cards=51` `i1_cards_open=0` `stage_only=4`.

## LLM and tool findings (detail in the entry)

`_type: openai` accepts `base_url` and builds `ChatOpenAI` (`nat/llm/openai_llm.py` 33–40, `nat/plugins/langchain/llm.py` 219–247). `_type: nim` also has `base_url` but builds `ChatNVIDIA` (`nat/llm/nim_llm.py` 34–40, `nat/plugins/langchain/llm.py` 175–214). A YAML literal `api_key` satisfies the blueprint validator with no env var (`config_validation.py` 56–64).

Keyless here: DuckDuckGo News (`ddgs`, no key). Not keyless, and not in the smoke: Tavily, paper search (`SERPER_API_KEY`), NVIDIA embeddings / the knowledge layer (`NVIDIAEmbedding` default `nvidia/nemotron-3-embed-1b` at `integrate.api.nvidia.com`). Polymarket is public HTTP and was left out so the only search tool is DuckDuckGo. No NIM container (no NVIDIA GPU, no NGC key).

`nat run --input` calls `os._exit(0)` 0.2s after the response (`agents/chat_researcher/register.py` 840–849). The smoke requires a non-empty non-error report.

## Downloads

Stage root `~/DEVELOP/pfy-mentat/tmp/aiq`. Hashes also in `stage-receipt.json` there and copied into the smoke receipt `downloads` object.

| Artifact | sha256 |
|----------|--------|
| AI-Q commit | `951a1a1114e9818073ddbe2a5fdbfa824751f4d3` |
| `uv.lock` | `5398b76fae1913a9b046c0975bd746a107e15670f4df4f72b977375fc35c76b3` |
| `uv pip freeze` (339 packages) | `61cbbe1906e96e0d8532cea56342561089f0066a2e7bcdbcfa7a30f9d3b3196a` |
| `nvidia_nat_core-1.8.0` wheel (from `uv.lock`) | `645bcc995f73598016b750f7849decb24bea857549f96f5fcbbd8ff37f0c3fc5` |
| `nvidia_nat_langchain-1.8.0` wheel (from `uv.lock`) | `8120ad2b972ce2d90fae1e7f95b3daf6b463310e0105fc330896bfb069a5d403` |
| `nemo_relay-0.8.0` manylinux wheel (retained file) | `baee7b6846b632848cd56bd630a330292d49678fae4e13a388a59334fcb9e1b7` |

26 files whose names contain `.whl` were hashed (mostly local editable wheels plus a few leftovers). uv does not retain most downloads as `.whl` files. At this read `wheels-v5` held 334 `*.http` objects. The authoritative per-wheel pin is `uv.lock` (`wheels[].hash`), covered by the lock sha256 above. CPython 3.13.11 was installed by uv; no installer tarball was left to hash. `nemo-relay` git rev `ffb24817442bac99212da0971b13bdad5bc4d84d`.

## How to re-run

Ollama must be up on this machine with `qwen3.6:35b`. No NVIDIA, Tavily, or NGC key.

```sh
python3 examples/x-intake-local/smoke_117.py --stage
python3 examples/x-intake-local/smoke_117.py --entry aiq
```

`--stage` is the only clone and `uv sync`. It refuses a root outside `~/DEVELOP`. `--entry` alone exits 2 when `tmp/aiq/.venv/bin/nat` is missing. `PFY_XINTAKE_TIMEOUT` overrides the 900s research timeout. `$AIQ_ROOT`, `$AIQ_SRC`, `$AIQ_BIN`, `$AIQ_OLLAMA_URL`, and `$AIQ_RECEIPT` override paths. Leave `AIQ_RECEIPT` unset for a real run. The research child is not bubblewrap-wrapped, because it must reach Ollama and DuckDuckGo. Receipt: `pipelines/smoke/aiq/latest.json`.

## Blockers

- No `NVIDIA_API_KEY`, no Tavily key, no NGC key, no NVIDIA GPU. Hosted NIM, NIM containers, Tavily, paper search, and the knowledge layer stay out.
- Default upstream CLI is NIM + Tavily. The local config is a generated stand-in, not an upstream file.
- Host Python 3.14 cannot install the package. Staging depends on the uv-managed CPython 3.13.11 under `tmp/aiq/python`.
- A deep intent still enters deep research with the clarifier disabled. The smoke query is one factual question and the deep caps are short; a different question can still spend the 180s deep budget.
- `os._exit(0)` means a zero exit is not proof. The receipt report is the proof.
- The cited Phoronix URL was not re-checked (Cloudflare 403).
- Research is not network-isolated. A future containment wrap has to leave Ollama and DuckDuckGo reachable.
- Not installed on nimo. I0 only. No PR was opened from this slice.

## Files

`sources/entries/117-aiq.md`, `examples/x-intake-local/smoke_117.py`, `examples/x-intake-local/README.md`, `tests/test_x_intake_smoke_117.py`, `.gitignore` (`pipelines/smoke/aiq/` only), this handoff.

## Locks respected

No sudo, no system changes, writes under `~/DEVELOP` only. No secrets printed or committed. No merge. PRs 255 and 258 not opened or edited. Other checkouts not touched. Receipts and the stage tree stay outside git.
