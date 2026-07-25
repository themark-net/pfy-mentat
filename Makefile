# pfy-mentat — top-level operator entrypoints
# Prefer these from the repo root (avoids "no rule to make target 'test'").
#
# Agent cage is the integration lab. Prefer testing catalog tool installs
# inside the cage (versioned images), not only on the host.

SHELL := /bin/bash
.DEFAULT_GOAL := help
HARNESS := harness/agent-cage
LITELLM_EXAMPLE := examples/litellm-ollama

.PHONY: help cage-doctor cage-setup cage-init cage-up cage-up-mcp cage-down \
	cage-shell cage-status cage-test cage-logs cage-smoke-host catalog-json \
	env-init env-check cage-grok-install cage-grok-build cage-grok-up \
	cage-grok-smoke cage-grok-ready cage-grok-uninstall cage-grok-auth-import \
	cage-workspace-sync cage-grok-mcp-preset \
	local-ollama-overlay-install local-ollama-up smoke-litellm-ollama \
	smoke-codebase-memory smoke-repowise smoke-context-tools \
	smoke-write-guard smoke-grok-skills \
	eval-tier0 eval-tier1 eval-mvp eval-suite eval-matrix eval-v02 eval-structural \
	eval-select-models eval-auto \
	cage-grok cage-grok-shell cage-grok-run cage-grok-sessions cage-grok-resume \
	cage-grok-sessions-import-host cage-grok-net-smoke cage-grok-skills-install \
	cage-code-sync cage-code-status cage-code-from-cage cage-code-to-cage

help:
	@echo "pfy-mentat"
	@echo ""
	@echo "Environment (secrets never in git):"
	@echo "  make env-init         Create .env from bootstrap/env/env.example if missing (idempotent)"
	@echo "  make env-check        Validate required vars for DEPLOY_PROFILE"
	@echo ""
	@echo "Agent cage (integration lab) — from repo root:"
	@echo "  make cage-doctor      Host/docker checks"
	@echo "  make cage-setup       Clone pin + install agentcage CLI (idempotent)"
	@echo "  make cage-init        agentcage init → \$$HOME/.agentcage (skips if present)"
	@echo "  make cage-up          Start sandbox"
	@echo "  make cage-up-mcp      Start sandbox + MCP  (do this before cage-test)"
	@echo "  make cage-status      Container health"
	@echo "  make cage-shell       Shell into agent container (generic)"
	@echo "  make cage-test        Policy tests (services must already be up)"
	@echo "  make cage-down        Stop sandbox"
	@echo "  make cage-smoke-host  Host-only smoke (no containers)"
	@echo ""
	@echo "Grok Build in cage (primary operator path — T-0045):"
	@echo "  make cage-grok              # ensure up + workspace + MCP ready, print how to launch"
	@echo "  make cage-grok-shell        # interactive bash at /workspace/pfy-mentat"
	@echo "  make cage-grok-run PROMPT='…'   # new session; prompt is one string"
	@echo "  make cage-grok-sessions         # list Grok sessions for cage repo cwd"
	@echo "  make cage-grok-resume           # continue most recent (or ID=uuid)"
	@echo "  make cage-grok-sessions-import-host  # map host project sessions → cage"
	@echo "  First-time: cage-grok-install → auth-import → build → cage-grok"
	@echo "  Daily:      make cage-grok   then resume | run | shell"
	@echo "  make cage-workspace-sync    # rsync catalog → cage workspace (content only)"
	@echo "  make cage-code-status       # host vs cage HEADs (privileged host)"
	@echo "  make cage-code-from-cage    # import agent commits → host git"
	@echo "  make cage-code-to-cage      # rsync host → cage + align cage git"
	@echo "  make cage-code-sync         # from-cage then to-cage (add PUSH=1 to push origin)"
	@echo "  Auth: host 'grok login' then make cage-grok-auth-import"
	@echo "  Sessions persist: ~/.agentcage/grok-state/sessions (not host ~/.grok alone)"
	@echo "  make cage-grok-net-smoke    # proxy must allow auth.x.ai + cli-chat-proxy"
	@echo "  make cage-grok-skills-install  # first-party skills → cage GROK_HOME"
	@echo "  TUI crash left mouse junk?  host shell:  reset"
	@echo ""
	@echo "LiteLLM + Ollama (in-cage smoke, local-only):"
	@echo "  make local-ollama-overlay-install"
	@echo "  make local-ollama-up"
	@echo "  make smoke-litellm-ollama   # exit 0 required; runs inside agent-cage only"
	@echo "  make smoke-codebase-memory / smoke-repowise / smoke-context-tools"
	@echo "  make smoke-write-guard      # T-0031 write-guard MCP policy smoke"
	@echo "  make smoke-grok-skills      # first-party skill structure (manifest + SKILL.md)"
	@echo "  make smoke-grok-skills INSTALLED=1  # also check ~/.grok/skills"
	@echo "  make eval-structural           # design/coding gates, NO LLM (always run)"
	@echo "  make eval-select-models        # pick gate/matrix models that FIT RAM/disk (may pull)"
	@echo "  make eval-auto                 # select-models + pull-gate + eval-v02"
	@echo "  make eval-tier0|eval-tier1|eval-mvp  # OQ-0002 opt5 scored eval"
	@echo "  make eval-suite|eval-matrix|eval-v02 # v0.2 multi-task / multi-model (needs Ollama)"
	@echo ""
	@echo "Or:  cd harness/agent-cage && make help"
	@echo ""
	@echo "Catalog:"
	@echo "  make catalog-json     Validate data/tools.json parses"
	@echo ""
	@echo "Profiles: local-only | balanced | max-performance  (DEPLOY_PROFILE)"
	@echo "  see config/profiles/ and docs/ops/deployment-profiles.md"

cage-doctor:
	@$(MAKE) -C $(HARNESS) doctor

cage-setup:
	@$(MAKE) -C $(HARNESS) setup

cage-init:
	@$(MAKE) -C $(HARNESS) init

cage-up:
	@$(MAKE) -C $(HARNESS) up

cage-up-mcp:
	@$(MAKE) -C $(HARNESS) up-mcp

cage-down:
	@$(MAKE) -C $(HARNESS) down

cage-shell:
	@$(MAKE) -C $(HARNESS) shell

cage-status:
	@$(MAKE) -C $(HARNESS) status

cage-test:
	@$(MAKE) -C $(HARNESS) test

cage-logs:
	@$(MAKE) -C $(HARNESS) logs

cage-smoke-host:
	@$(MAKE) -C $(HARNESS) smoke-host

catalog-json:
	@python3 -c "import json; json.load(open('data/tools.json')); print('data/tools.json: OK')"

cage-grok-install:
	@$(MAKE) -C $(HARNESS) grok-overlay-install

cage-grok-auth-import:
	@$(MAKE) -C $(HARNESS) grok-auth-import

cage-grok-build:
	@$(MAKE) -C $(HARNESS) grok-overlay-build

cage-grok-up:
	@$(MAKE) -C $(HARNESS) grok-up

cage-grok-smoke:
	@$(MAKE) -C $(HARNESS) grok-smoke

cage-workspace-sync:
	@$(MAKE) -C $(HARNESS) workspace-sync

# Host-privileged bidirectional code bridge (see harness/agent-cage/scripts/cage-code-sync.sh)
# PUSH=1  → also git push origin after import
# FORCE=1 → allow dirty / overwrite checks
# SYNC_ARGS extra flags e.g. SYNC_ARGS=--dry-run
cage-code-status:
	@chmod +x harness/agent-cage/scripts/cage-code-sync.sh
	@./harness/agent-cage/scripts/cage-code-sync.sh status $(SYNC_ARGS)

cage-code-from-cage:
	@chmod +x harness/agent-cage/scripts/cage-code-sync.sh
	@./harness/agent-cage/scripts/cage-code-sync.sh from-cage $(if $(filter 1,$(FORCE)),--force,) $(SYNC_ARGS)

cage-code-to-cage:
	@chmod +x harness/agent-cage/scripts/cage-code-sync.sh
	@./harness/agent-cage/scripts/cage-code-sync.sh to-cage $(if $(filter 1,$(FORCE)),--force,) $(SYNC_ARGS)

cage-code-sync:
	@chmod +x harness/agent-cage/scripts/cage-code-sync.sh
	@./harness/agent-cage/scripts/cage-code-sync.sh sync \
	  $(if $(filter 1,$(PUSH)),--push,) \
	  $(if $(filter 1,$(FORCE)),--force,) \
	  $(SYNC_ARGS)

cage-grok-mcp-preset:
	@$(MAKE) -C $(HARNESS) grok-mcp-preset

cage-grok-ready:
	@$(MAKE) -C $(HARNESS) grok-ready

cage-grok:
	@$(MAKE) -C $(HARNESS) grok-ensure

cage-grok-shell:
	@$(MAKE) -C $(HARNESS) grok-shell

cage-grok-run:
	@$(MAKE) -C $(HARNESS) grok-run PROMPT='$(PROMPT)' FLAGS='$(FLAGS)' ARGS='$(ARGS)'

cage-grok-sessions:
	@$(MAKE) -C $(HARNESS) grok-sessions

cage-grok-resume:
	@$(MAKE) -C $(HARNESS) grok-resume ID='$(ID)'

cage-grok-sessions-import-host:
	@$(MAKE) -C $(HARNESS) grok-sessions-import-host

cage-grok-net-smoke:
	@$(MAKE) -C $(HARNESS) grok-net-smoke

cage-grok-skills-install:
	@$(MAKE) -C $(HARNESS) grok-skills-install

cage-grok-uninstall:
	@$(MAKE) -C $(HARNESS) grok-overlay-uninstall

local-ollama-overlay-install:
	@$(MAKE) -C $(HARNESS) local-ollama-overlay-install

local-ollama-up:
	@$(MAKE) -C $(HARNESS) local-ollama-up

smoke-litellm-ollama:
	@$(MAKE) -C $(HARNESS) smoke-litellm-ollama

smoke-codebase-memory:
	@$(MAKE) -C $(HARNESS) smoke-codebase-memory

smoke-repowise:
	@$(MAKE) -C $(HARNESS) smoke-repowise

smoke-context-tools:
	@$(MAKE) -C $(HARNESS) smoke-context-tools

smoke-write-guard:
	@$(MAKE) -C $(HARNESS) smoke-write-guard

# First-party Grok skills: manifest ↔ SKILL.md structure (no LLM). See docs/ops/skill-verification.md
# INSTALLED=1 also checks $GROK_HOME/skills (default ~/.grok/skills)
smoke-grok-skills:
	@python3 bootstrap/grok-cli/scripts/verify_skills.py $(if $(filter 1,$(INSTALLED)),--installed,)

eval-tier0:
	@$(MAKE) -C $(HARNESS) eval-tier0

eval-tier1:
	@$(MAKE) -C $(HARNESS) eval-tier1

eval-mvp:
	@$(MAKE) -C $(HARNESS) eval-mvp

eval-suite:
	@$(MAKE) -C $(HARNESS) eval-suite

eval-matrix:
	@$(MAKE) -C $(HARNESS) eval-matrix

eval-v02:
	@$(MAKE) -C $(HARNESS) eval-v02

# Design/coding structural gates (skills, tools.json, text scorers) — no LLM/Ollama
eval-structural:
	@python3 examples/eval-harness/run_structural.py --write-md pipelines/eval/structural.latest.md

# Hardware-fit model pick (not limited to already-pulled). Host: ollama tags on :11434.
# EVAL_PULL_GATE=0 to only list; default pulls gate if missing and ollama CLI present.
eval-select-models:
	@python3 examples/eval-harness/select_ollama_models.py \
	  $(if $(filter 0,$(EVAL_PULL_GATE)),,--pull-gate)
	@python3 examples/eval-harness/select_ollama_models.py --exports 2>/dev/null \
	  | grep -E '^(EVAL_|LITELLM_)' > /tmp/pfy-eval-model-exports.sh
	@echo "==> shell exports → /tmp/pfy-eval-model-exports.sh"
	@cat /tmp/pfy-eval-model-exports.sh
	@echo "Re-run suite with:  set -a; . /tmp/pfy-eval-model-exports.sh; set +a; make eval-suite"
	@echo "(typo watch: set +a  not  set +1)"

# Select fit models (pull gate if needed) then full v0.2 ladder.
# Tries EVAL_GATE_CANDIDATES in order until suite passes (chat/instruct before base FIM).
eval-auto: eval-structural
	@$(LITELLM_EXAMPLE)/host-ollama-gateway.sh start 2>/dev/null \
	  || ./examples/litellm-ollama/host-ollama-gateway.sh start
	@python3 examples/eval-harness/select_ollama_models.py --pull-gate
	@python3 examples/eval-harness/select_ollama_models.py --exports 2>/dev/null \
	  | grep -E '^(EVAL_|LITELLM_)' > /tmp/pfy-eval-model-exports.sh
	@echo "==> using selected models:"; cat /tmp/pfy-eval-model-exports.sh
	@set -a; . /tmp/pfy-eval-model-exports.sh; set +a; \
	  cands="$${EVAL_GATE_CANDIDATES:-$$EVAL_GATE_MODEL}"; \
	  ok=0; \
	  IFS=','; for g in $$cands; do \
	    g=$$(echo "$$g" | tr -d ' '); \
	    [[ -z "$$g" ]] && continue; \
	    echo "==> eval-v02 gate candidate: $$g"; \
	    if $(MAKE) eval-v02 \
	      EVAL_MODEL="$$g" EVAL_GATE_MODEL="$$g" \
	      EVAL_MODELS="$${EVAL_MODELS}" \
	      LITELLM_SMOKE_MODEL="$${LITELLM_SMOKE_MODEL:-deepseek-coder:latest}"; then \
	      ok=1; echo "eval-auto: PASS with gate $$g"; break; \
	    fi; \
	    echo "eval-auto: gate $$g failed — try next candidate"; \
	  done; \
	  [[ $$ok -eq 1 ]] || { echo "eval-auto: all gate candidates failed"; exit 1; }

env-init:
	@if [ -f .env ]; then \
	  echo ".env already exists (not overwriting)"; \
	else \
	  cp bootstrap/env/env.example .env; \
	  echo "Created .env from bootstrap/env/env.example — edit secrets before use"; \
	fi
	@echo "Registry: bootstrap/env/REGISTRY.md"
	@echo "Profiles: config/profiles/{local-only,balanced,max-performance}.env"

env-check:
	@python3 bootstrap/env/check_env.py
