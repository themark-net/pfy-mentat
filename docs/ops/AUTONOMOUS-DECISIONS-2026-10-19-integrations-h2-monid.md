# Autonomous decisions: 2026-10-19 (integrations drop-ins H1 Harness² local, H2 skill discovery)

One line per choice. Format: choice | alternatives | why.

1. H1 targets the 48-case decision set (`data/decision-gates/laya-trial.cases.v0.json`) | JobBench via `harness2-setup jb` | local, labeled, no Hugging Face download and no Vertex judge, deterministic scoring against our own labels, and it is the set `qwen3.6:35b` was picked on (38/48).
2. H1 drives the upstream core loop (`core.recursion.run_parallel`) with our own adapter, preflight and setup steps | `harness2`, `harness2-check` and `harness2-setup` CLIs | the CLIs only take `jb|lab|wb`, `preflight.check()` raises `KeyError` for any other adapter, and setup clones job-bench-eval and pulls from Hugging Face.
3. H1 serves `qwen3.6:35b` from its own `llama-server` (`llamacpp-nommap` lane, `-c 32768`) | Ollama with its default context | OpenCode's prompt does not fit 8192 tokens, Ollama's OpenAI endpoint takes no `num_ctx`, and changing Ollama's config is a system change; an own process can be stopped at exit without touching anyone else's model.
4. H1 drops the `[render]` extra | install it and allow pypi for its wheels | openpyxl and python-pptx only render JobBench and WorkBuddy outputs; pypi stays allowed only for the setuptools/wheel build backend.
5. H1 improvement gate is at least +2 held-out cases with the base scored twice, temperature 0 and seed 230 | at least baseline | 16 held-out cases make a 1-case gain indistinguishable from noise.
6. H1 treats AGENTS.md-derived guardrails as read-only for proposals | allow edits and let Reviewer catch them | hard rules change only by Mark's hand.
7. H2 parses Monid endpoints recursively and derives id and kind | read them from `meta` | `meta` has no provider, id or kind, and 481 of 719 endpoints sit one level deeper.
8. Both drop-ins copy themselves from `origin/main` and base their worktrees there | copy from `origin/bot/integrations-h2-monid` | Build should run what was merged, not a branch that can still move.
