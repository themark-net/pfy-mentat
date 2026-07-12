# One-shot example DoDs (cage / tool smokes)

**Status:** Active (T-0032)  
**Workflow:** [one-shot-workflow.md](one-shot-workflow.md) · ADR-0008  
**Lab:** agent-cage (`make cage-up-mcp` or `make local-ollama-up`)

Use these as **copy-paste DoDs** for `/one-shot`. Agents should still restate and adjust, but defaults are green when the named Make target exits 0.

---

## Global assumptions (all smoke one-shots)

Unless the operator overrides:

- Feature branch; **push/merge only if operator said so**
- No secrets in git; no large weight downloads without OQ
- Prefer **in-cage** verification (`make smoke-*`); host-only is not enough for integration DoDs
- `DEPLOY_PROFILE=local-only` or existing env that passes `make env-check` for local work
- Max **8** implement→test iterations; stop after **3** identical failures
- Stretch goals only if primary DoD is green and budget remains

---

## A. LiteLLM → Ollama (T-0012 / T-0021)

```text
/one-shot Track A smoke: LiteLLM→host Ollama inside agent-cage.

DoD:
1. examples/litellm-ollama has README + pins.env
2. Host gateway up if Ollama is localhost-only: ./examples/litellm-ollama/host-ollama-gateway.sh start
3. make local-ollama-overlay-install && make local-ollama-up (or cage already allows host.docker.internal)
4. make smoke-litellm-ollama exits 0 (completion via LiteLLM inside agent)
5. No cloud keys required (local-only)

Assumptions:
- Model: LITELLM_SMOKE_MODEL=deepseek-coder:latest or smallest local coding model
- Max Ollama pull disk: 0 unless operator set a budget
- May update cage policy for host.docker.internal
```

**Green command:** `make smoke-litellm-ollama`

---

## B. codebase-memory-mcp (T-0021)

```text
/one-shot In-cage smoke for codebase-memory-mcp.

DoD:
1. examples/codebase-memory-mcp fixture + run-in-cage.sh present
2. make smoke-codebase-memory exits 0
3. Smoke reports: version, index status=indexed, search finds fixture symbol
4. Prefer docker-cp host ~/.local/bin/codebase-memory-mcp if present

Assumptions:
- agent-cage agent container running
- GitHub/curl install fallback only if binary missing
```

**Green command:** `make smoke-codebase-memory`

---

## C. repowise (T-0021 / T-0013)

```text
/one-shot In-cage smoke for repowise (zero-LLM health).

DoD:
1. examples/repowise pin REPOWISE_PIP_SPEC=repowise==0.30.0
2. make smoke-repowise exits 0
3. repowise health produces scores/graph on fixture (no API keys)
4. Notes remain: complement codebase-memory, not replace
   (pipelines/smoke/context-tools-compare.md)

Assumptions:
- Python 3.12 in cage (host 3.14 may fail pip resolve)
```

**Green command:** `make smoke-repowise`  
**Both context tools:** `make smoke-context-tools`

---

## D. write-guard MCP (T-0031)

```text
/one-shot Write-guard policy smoke in cage.

DoD:
1. harness/write-guard-mcp package imports; python -m write_guard selftest PASS
2. make smoke-write-guard exits 0
3. audit allows .env write (flagged); enforce denies .env + default-denies delete
4. Default WRITE_GUARD_MODE=audit (OQ-0009)

Assumptions:
- mcp-host permanent wiring optional; smoke validates policy engine in cage
```

**Green command:** `make smoke-write-guard`  
**Host quick check:** `PYTHONPATH=harness/write-guard-mcp/src python3 -m write_guard selftest`

---

## E. Eval MVP (OQ-0002 option 5)

```text
/one-shot Eval harness MVP: tier0 connectivity + tier1 scored task.

DoD:
1. make eval-tier0 exits 0 (smoke-litellm-ollama)
2. make eval-tier1 exits 0 (001-is-palindrome SCORE: PASS)
3. pipelines/eval/results.latest.md updated
4. No DSPy required (deferred)

Assumptions:
- Cage up; host Ollama + gateway
- Tier-1 model present (default EVAL_MODEL=qwen2.5:14b; override as needed)
```

**Green:** `make eval-mvp`

---

## E2. Eval v0.2 suite / matrix (T-0041)

```text
/one-shot Eval harness v0.2: multi-task suite + optional multi-model matrix.

DoD:
1. make eval-v02 exits 0 (tier0 + all tasks, gate EVAL_MODEL)
2. tasks include 001-is-palindrome and 002-fix-sum-evens
3. make eval-matrix exits 0 for gate model; missing models may SKIP
4. pipelines/eval/results.latest.md has suite/matrix rows
5. No DSPy required

Assumptions:
- Cage up; host Ollama + gateway; gate model present (default qwen2.5:14b)
```

**Green:** `make eval-v02` (matrix optional: `make eval-matrix`)

---

## F. Full smoke ladder (regression)

```text
/one-shot Re-run all in-cage catalog smokes (regression).

DoD (each exit 0, or skip with reason if prereq missing):
1. make smoke-write-guard
2. make smoke-codebase-memory
3. make smoke-repowise
4. make smoke-litellm-ollama   # needs host Ollama + gateway
5. pipelines/smoke/*/results.latest.md updated or already current

Assumptions:
- Cage up; Ollama only required for step 4
- Stop on first hard blocker; report which step failed
```

---

## Report template (reminder)

```markdown
## One-shot result: PASS | FAIL | BLOCKED
**DoD:** (checklist with pass/fail)
**Iterations:** n
**Highest cost tier used:** 0-4
**Assumptions:** ...
**Changes:** paths...
**Verify commands:** ...
**Human needed (if any):** one question only
```
