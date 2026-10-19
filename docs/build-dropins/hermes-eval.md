# Build drop-in: Hermes Agent as pfy-mentat's local-first bot interface (eval + plan)

Repo: `themark-net/pfy-mentat` on nimo. Bot-launched headless Build run. BEST_EFFORT. Not a Feature GO. No production wiring.

---

You are Grok Build working **alone and unattended** (no human will answer questions). Do not ask questions; decide, record the decision in the docs, and continue. Honest FAIL beats stub success.

## 0. Where you are (fixed, do not change)

- **Worktree (your cwd):** `/home/mark/DEVELOP/pfy-mentat/tmp/hermes-eval`
- **Branch:** `bot/hermes-eval`, cut from `origin/main` @ `b36234b` (#303). It was created with upstream `origin/main`; push with `git push -u origin bot/hermes-eval` (never push to `main`).
- **Scratch:** `./tmp/` inside this worktree (git-ignored via `.git/info/exclude`). Everything you install or generate that is not a deliverable lives there.
- **Never** edit `/home/mark/DEVELOP/pfy-mentat` (the founder checkout, it has uncommitted changes) or any other worktree under `../`. **Never** touch draft PRs **#255** and **#258** or their branches (`founder-build-babysit/2026-10-04`, `build/loop-agent-picker-0925`).

## 1. Exit card (written before the loop; obey it)

| # | Exit | Rule |
|---|------|------|
| 1 | Goal met | Commits for items A, B, (C if WIN), D exist on `bot/hermes-eval`, offline pytest green, branch pushed, PR opened or PR body + compare URL written (see §7). Status DONE. |
| 2 | Turn cap | Max **8** fix/retry attempts per item. Then record what failed in the handoff and move on (STOPPED_EXIT for that item). |
| 3 | Budget | Live model calls: at most **2 full bake-off passes** per arm (one primary, one re-run of failures/flakes). No sweeping of other models. |
| 4 | Wall clock | The launcher kills you at **3 h**. Budget: setup ≤ 40 min, harness + tests ≤ 50 min, live runs ≤ 60 min, docs + push ≤ 30 min. At **2 h 30 m** stop live work and go straight to docs, handoff, commit, push. |
| 5 | No progress | Same error or same diff **3 times** → stop that path, write it down, take the next item. |
| 6 | Human interrupt | If a file `./tmp/STOP` appears, finish the current commit, write the handoff, push, exit. |
| 7 | Error threshold | 3 consecutive identical failures (install, Ollama, Hermes startup) → stop that arm, mark it **BLOCKED** with the exact error (no secrets) in the eval doc, and still ship docs + handoff. |
| 8 | External | n/a (no merge; Tester/Reviewer gate the merge). |

Final line of your output: `STATUS: DONE|STOPPED_EXIT|BLOCKED — exit #N — <artifact paths> — next: <internal next step>`.

## 2. Host rules (nimo) — hard constraints

- **No sudo. No system services. No systemd units. No daemons left running.** Do not run `hermes gateway`, `hermes dashboard`, the Hermes API server, `hermes setup --portal`, cron, or any Hermes background process. Check `pgrep -af hermes` before you exit and stop only processes **you** started.
- **Other grok processes:** never kill, signal, or `pkill` any `grok` process. A separate career-capture Build run (PID ~320399) is active. Only manage PIDs you spawned yourself.
- **Ollama load modest and serial:** one request in flight at a time, both arms run **sequentially**, never in parallel. Do not pull models (`qwen3.6:35b` is already present). Before loading, check `ollama ps` and `MemAvailable`; require MemAvailable ≥ 22 GiB + 25 GiB headroom, otherwise poll every 60 s for up to 20 min, then exit #7 for the live part. If `qwen3.6:35b` was **not** loaded when you started, unload it at the end with `keep_alive: 0`; if it was already loaded by someone else, leave it alone. Never unload or touch other models.
- **OpenClaw:** `openclaw-gateway.service` (user unit) is stopped and disabled. Leave it that way. You may read `systemctl --user is-active openclaw-gateway` / `is-enabled` and record the result; never start, enable, or restart it.
- **Local-first, no keys:** no API keys beyond the Grok and Cursor logins that already exist. Do not set or request `OPENROUTER_API_KEY`, `NOUS_*`, `ANTHROPIC_*`, `XAI_API_KEY`, etc. Run every Hermes and baseline process with a **scrubbed env** (start from `env -i HOME=$HOME PATH=... LANG=C.UTF-8` and add only the vars below). Ollama needs no key; use the literal placeholder `no-key` where a key field is required.
- **No secrets in output:** never print env dumps, `~/.grok/auth.json`, any `.env`, tokens, or SSH keys. Redact anything key-shaped in logs before committing.
- **Pre-existing Hermes on this host:** `~/.local/bin/hermes` and `~/.hermes/` already exist (Mark's, from 2026-09-24). **Do not use, modify, or read config/secrets from either.** Use only the venv binary you install. Before installing, snapshot `find ~/.hermes -maxdepth 2 -printf '%p %T@ %s\n' | sort > ./tmp/hermes-home-before.txt`; at the end diff against a fresh snapshot and record "~/.hermes untouched: yes/no" in the eval doc (if it changed, say what and treat it as a defect).
- Python on nimo is 3.14; `uv` is at `~/.local/bin/uv`. Prefer `uv venv` / `uv pip` with a Python version Hermes supports (uv may fetch a managed interpreter into its cache; that is fine). No `pip install --user`, no global installs.

## 3. Mandatory reads (skim, do not rewrite)

`AGENTS.md`, `CONTRIBUTING.md`, `.grok/skills/catalog-docs/references/doc-map.md` (triple-write checklist), `docs/build-dropins/README.md`, `docs/PENDING-HANDOFF.md` (top sections), `sources/entries/130-hal0.md` (entry format), `sources/x-posts.md` Entry **048** (prior Hermes feedback-loop note), `.grok/skills/hermes-feedback/PORT.md`, `docs/design/pfy-launcher.md`, `scripts/pfy` (the `hermes` / `opencode` / `grok` attach cases around line 1280-1400 and `scripts/detect-local-runtime.sh`), `data/decision-gates/README.md` + `data/decision-gates/laya-trial.cases.v0.json` (the **48 labeled Choice cases**), `examples/local-bench/` + `docs/dogfood/LOCAL-BENCH-RESULTS.md` … `LOCAL-BENCH-4-EDGE.md` (PRs #270-#273: harness, `qwen3.6:35b` 79.2% Choice baseline, RSS/peak sampler in `pipelines/dogfood/local-bench-4/peak_sampler.py`).

Hermes facts already verified (2026-10-19) — re-verify the pin you install:
- Repo: **https://github.com/NousResearch/hermes-agent** (MIT, default branch `main`). Docs: https://hermes-agent.nousresearch.com/docs (machine index at `/docs/llms.txt`).
- Home dir env var: **`HERMES_HOME`** (default `~/.hermes`). Also useful: `HERMES_IGNORE_USER_CONFIG=1`, `HERMES_API_TIMEOUT`, `HERMES_MAX_ITERATIONS`, `HERMES_INFERENCE_MODEL`, `HERMES_REDACT_SECRETS=true`, `HERMES_WRITE_SAFE_ROOT`.
- Ollama as custom provider: `model: {default: "qwen3.6:35b", provider: "custom", base_url: "http://localhost:11434/v1"}` in `$HERMES_HOME/config.yaml`. Docs say Hermes wants ≥ 64k context for agentic work and Ollama defaults to 2048: set `num_ctx` explicitly (see §5) rather than creating new Ollama model tags if you can; if you must `ollama create` a ctx variant, name it `qwen3.6-hermes-eval-*`, record it, and `ollama rm` it at the end.
- Library use: `from run_agent import AIAgent` with `quiet_mode=True, skip_memory=True, skip_context_files=True, enabled_toolsets=[...], max_iterations=...`, `base_url=`, `api_key="no-key"`. Source install is `git clone` + `source ./activate` (PM); no supported wheel. Do **not** run `scripts/install.sh` / the curl installer (it writes outside the worktree).

## 4. Isolation layout (create exactly this)

```
./tmp/hermes-agent/        # git clone of NousResearch/hermes-agent, pinned SHA recorded
./tmp/.venv-hermes/        # venv for Hermes (or whatever ./activate creates, as long as it is under ./tmp)
./tmp/hermes-home/         # HERMES_HOME — config.yaml, sessions, logs; no secrets
./tmp/bakeoff/             # transcripts, per-task logs (not committed)
```

Export for every Hermes call: `HERMES_HOME=$PWD/tmp/hermes-home`, `HERMES_IGNORE_USER_CONFIG=1` if it does not break the custom-provider config, `HERMES_REDACT_SECRETS=true`, `HERMES_WRITE_SAFE_ROOT=$PWD/tmp/bakeoff`. Prove isolation: a test asserts that after a Hermes run, files exist under `tmp/hermes-home` and `~/.hermes` snapshot is unchanged.

## 5. Items (one commit per item, in this order)

### Item A — catalog entry (commit 1)

- Next free catalog number is **131** (`sources/entries/` tops out at 130 on main; open PRs #255/#258 claim none). Re-check `ls sources/entries | sort | tail` before writing; if 131 is taken, use the next free number.
- Write `sources/entries/131-hermes-agent.md` in the same format as Entry 130: URL (license, stars, release/commit you pinned), summary from upstream README/docs (their claims, labeled as such), **why it matters here** (bot interface + tool-calling loop for pfy-mentat; local Ollama custom provider; MCP; skills; gateway = 20+ channels), fit on nimo (isolated venv + `HERMES_HOME`, no gateway), findings (pre-existing `~/.hermes` + `~/.local/bin/hermes` on nimo; 64k ctx guidance; tool-call auto-repair claim), link back to Entry 048 and `/hermes-feedback`, risk/recovery table, status.
- Follow the doc-map triple-write checklist for whatever it requires at this stage (I0/I1 awareness). Do not invent scores; if a `TOOLS.md` / `data/tools.json` Hermes row already exists, update notes only. Catalog HOLD rules in `AGENTS.md` win over this prompt.
- Commit: `catalog: Entry 131 Hermes Agent (bot interface eval)`.

### Item B — bake-off harness + results (commit 2)

Build `examples/hermes-bakeoff/` (stdlib-first Python; reuse `examples/local-bench` helpers where sensible) with a README, plus `tests/test_hermes_bakeoff.py`.

**Task set (labels written before any model runs; commit the labels in the same commit):** `data/decision-gates/hermes-bakeoff.tasks.v0.json`, **≥ 20 tool-call tasks** (target 24-30), each with an oracle. Build it from:
1. A tool-calling subset of the 48 Choice cases in `laya-trial.cases.v0.json`: the model must answer by calling `submit_choice(case_id, choice, reason)` (no free-text answer counts). Pick ≥ 12 cases spread across labels; record which.
2. ≥ 8 tasks that need real data-fetching tools before answering, against deterministic fixtures in the repo, e.g. `catalog_lookup(entry_number)` over `sources/entries/`, `tools_query(name)` over `data/tools.json`, `bench_receipt(model, metric)` over the local-bench receipts, a 2-step chain (lookup → compute → `submit_answer`), and ≥ 2 "no tool needed / refuse" negatives so over-calling is visible.

**Same tools for both arms.** Expose the task tools through **one stdlib MCP stdio server** in `examples/hermes-bakeoff/` (read-only, fixture-backed, logs every call it receives with args + schema-validity to a JSONL). Both arms connect to that same server, so the tool surface is identical and the oracle reads ground truth from the server log, not from the model's prose. Disable every other tool in both arms (Hermes: only the MCP toolset, no terminal/web/browser/memory/skills creation; baseline: same).

**Arms (same model `qwen3.6:35b` on Ollama `http://localhost:11434/v1`, same `num_ctx`, same temperature 0 / seed if supported, same per-task timeout 180 s, same max tool iterations 6):**
- **(a) Hermes:** pinned source checkout from §4, custom provider config in `HERMES_HOME`, driven non-interactively (prefer `AIAgent.run_conversation` from the library; fall back to the CLI one-shot mode if the library path fights you — record which).
- **(b) Current pfy-mentat local path:** identify honestly what `./pfy` actually execs today for local tool-calling on Ollama (per `scripts/pfy` it attaches `opencode` or `grok` with `OPENAI_BASE_URL` = local engine). Use **`opencode` headless (`opencode run …`) on `qwen3.6:35b` via Ollama's OpenAI-compatible endpoint with the same MCP server** as the primary baseline, with config pointed inside `./tmp` (`XDG_CONFIG_HOME`/`XDG_DATA_HOME` under `./tmp/opencode-*` so `~/.config/opencode` is not modified). If opencode cannot be driven headless against Ollama within the turn cap, fall back to a **direct OpenAI-compatible tool-calling loop** (`/v1/chat/completions` with `tools=`, the minimal loop pfy's harnesses ride on) and label the arm exactly that in the results. Record versions of every binary used.
- Choose `num_ctx`: try 32768 for both arms; if Hermes refuses/warns below its minimum, use 65536 for **both**. Pass it the same way to both (Ollama `options.num_ctx` / a single shared ctx-variant tag). Record it.

**Metrics (define in the README before running; compute from logs, not model claims):**
- **valid tool-call rate** = structured tool calls that parse and validate against the tool's JSON schema ÷ all structured tool-call attempts (server log + client transcript).
- **task success** = oracle pass ÷ tasks (right tool(s), right args, right final `submit_*` value; negatives pass only with zero tool calls / correct refusal).
- **narrate-instead-of-call rate** = tasks where the assistant text contains a tool name / JSON call / "I would call…" but **no** structured call reached the server ÷ tasks that required a call.
- **latency** per task wall clock: p50, p95, mean; also time-to-first-tool-call.
- **peak RAM of the agent process**: VmHWM / max RSS of the agent process tree (Hermes Python process; opencode/baseline process), sampled every 0.5 s like `peak_sampler.py`. Ollama's RSS is reported separately and **not** counted against either agent.

**Clear-margin rule (fixed now, before results):** Hermes **WINS** only if all hold: task success ≥ **+10 pp** over (b); valid tool-call rate not worse by > 2 pp; narrate rate not worse by > 2 pp; p50 latency ≤ 1.5× (b); agent peak RSS ≤ 2 GiB. Otherwise **NO-WIN** (state which condition failed). Also report a simple 95% CI (Wilson) on task success; if the CIs overlap heavily say so plainly.

**Outputs (committed):**
- Raw results: `pipelines/dogfood/hermes-bakeoff/results.json` (per task, per arm: tool calls, validity, oracle verdict, narrate flag, latency, peak RSS, error; plus run metadata: Hermes SHA, opencode/version, Ollama version, num_ctx, MemAvailable before/after, `~/.hermes untouched`, openclaw-gateway is-active/is-enabled). Redact paths under `$HOME` only if they reveal secrets (they should not).
- `docs/eval/hermes-vs-current.md`: method, task set, metrics table both arms, verdict WIN/NO-WIN per the rule, failure autopsy (top 5 failures each arm with transcript excerpts, no secrets), what was not measured, how to reproduce.

**Tests** (offline, no Ollama, no network; must go red if the bug is present):
Tests: prefer E2E/integration/operate-or-FAIL (Trophy). No tautological or implementation-detail unit sprawl. Unit tests only for shaky behavior; must be able to fail with the bug present (sociable where possible). For each risk: how could this fail + how do we recover.
Minimum: (1) harness fails closed with a nonzero exit and a clear FAIL when Ollama is unreachable or the model tag is missing; (2) the MCP server rejects schema-invalid args and the scorer counts them as invalid, not success; (3) narrate detection on recorded fixture transcripts (a text-only "```json {name:…}```" reply is narrate; a real call is not); (4) oracle scoring on a recorded transcript where the model calls the right tool with wrong args → fail; (5) the margin rule on fixture metrics (edge just below +10 pp → NO-WIN); (6) isolation: the Hermes runner refuses to start if `HERMES_HOME` is unset or resolves under `~/.hermes`. Add a `@pytest.mark.live` (deselected by default) test that runs 2 tasks per arm. Run the repo's existing offline suite subset you touched and report counts.

Commit: `eval: Hermes vs current local path bake-off on qwen3.6:35b (Entry 131)`.

### Item C — integration plan, **only if WIN** (commit 3)

If the verdict is NO-WIN, skip this commit and say so in the eval doc and handoff (a short "what would have to change for a re-run" list is enough).

If WIN, write `docs/plans/hermes-bot-interface.md` (design only, **no production wiring**, no changes to `scripts/pfy`, `pfylib/`, or GUI):
- **Thin adapter** so Hermes is swappable: a `BotInterface` contract (start session, send message, stream events, tool-call events, stop, health) with Hermes as one implementation and the current opencode/grok path as another; where it lives (e.g. `pfylib/bot/`), how `./pfy` selects it, config + `HERMES_HOME` per profile, failure modes and fallbacks (Hermes missing/broken → current path, honest FAIL + next).
- **Catalog tools → Hermes:** exposing pfy catalog tools via the MCP server pattern from Item B (preferred) vs Hermes plugins/tools vs Hermes skills (SKILL.md, agentskills.io compatible) — pick one, justify with bake-off evidence, list which catalog tools go first.
- **OpenClaw (optional layer):** OpenClaw's gateway on nimo is stopped and disabled and stays that way; describe it as the optional multi-channel and scheduling layer (vs Hermes's own gateway/cron), what would trigger enabling it, and that it is never required for the local CLI path.
- Security posture: no gateway daemons by default, loopback only, no keys beyond Grok/Cursor, `HERMES_WRITE_SAFE_ROOT`, approval mode.
- Rollout slices with DoD + fail/recover tests per slice, and open questions for Mark.
Commit: `plans: Hermes bot-interface adapter design (WIN on bake-off)`.

### Item D — handoff (commit 4)

`docs/eval/HERMES-EVAL-HANDOFF.md` per the repo-handoff rule: tip SHA + branch, what shipped vs open, verdict and numbers, exact reproduce commands, isolation proof (`~/.hermes` untouched, no daemons left, openclaw still inactive/disabled, model unloaded or left as found), blockers with exact errors, next internal step. Add a short dated section at the top of `docs/PENDING-HANDOFF.md` pointing at it, and add a row for `hermes-eval.md` to `docs/build-dropins/README.md` if not already there.
Commit: `docs: Hermes eval handoff`.

## 6. Cleanup before exit (always, even on STOPPED/BLOCKED)

`pgrep -af 'hermes|opencode|bakeoff'` → stop only your own leftovers; unload `qwen3.6:35b` per §2; `ollama rm` any `qwen3.6-hermes-eval-*` tag you created; re-snapshot `~/.hermes` and diff; confirm `systemctl --user is-active openclaw-gateway` is still `inactive`. Leave `./tmp/` in place (git-ignored) for review.

## 7. Push + PR (no merge)

- `git push -u origin bot/hermes-eval`.
- `gh` is **not logged in** on nimo. Try `gh pr create --draft=false --base main --head bot/hermes-eval --title "eval: Hermes Agent as local-first bot interface (Entry 131)" --body-file ./tmp/hermes-eval.pr-body.md` once; if gh is unauthenticated, do **not** run `gh auth login` — write `./tmp/hermes-eval.pr-body.md` and print the compare URL `https://github.com/themark-net/pfy-mentat/compare/main...bot/hermes-eval` so the bot can open the PR.
- PR body: summary, verdict + headline numbers, commits list, isolation proof, tests run, "No merge. Tester/Reviewer gate."
- Never merge, never force-push, never push to `main`.
