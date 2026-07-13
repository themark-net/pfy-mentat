# pfy-mentat — top-level operator entrypoints
# Prefer these from the repo root (avoids "no rule to make target 'test'").
#
# Agent cage is the integration lab. Prefer testing catalog tool installs
# inside the cage (versioned images), not only on the host.

SHELL := /bin/bash
.DEFAULT_GOAL := help
HARNESS := harness/agent-cage

.PHONY: help cage-doctor cage-setup cage-init cage-up cage-up-mcp cage-down \
	cage-shell cage-status cage-test cage-logs cage-smoke-host catalog-json \
	env-init env-check cage-grok-install cage-grok-build cage-grok-up \
	cage-grok-smoke cage-grok-ready cage-grok-uninstall cage-grok-auth-import \
	cage-workspace-sync cage-grok-mcp-preset \
	local-ollama-overlay-install local-ollama-up smoke-litellm-ollama \
	smoke-codebase-memory smoke-repowise smoke-context-tools \
	smoke-write-guard eval-tier0 eval-tier1 eval-mvp eval-suite eval-matrix eval-v02 \
	cage-grok cage-grok-shell cage-grok-run cage-grok-sessions cage-grok-resume \
	cage-grok-sessions-import-host cage-grok-net-smoke

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
	@echo "  make cage-workspace-sync    # re-sync catalog → /workspace/pfy-mentat"
	@echo "  Auth: host 'grok login' then make cage-grok-auth-import"
	@echo "  Sessions persist: ~/.agentcage/grok-state/sessions (not host ~/.grok alone)"
	@echo "  make cage-grok-net-smoke    # proxy must allow auth.x.ai + cli-chat-proxy"
	@echo "  TUI crash left mouse junk?  host shell:  reset"
	@echo ""
	@echo "LiteLLM + Ollama (in-cage smoke, local-only):"
	@echo "  make local-ollama-overlay-install"
	@echo "  make local-ollama-up"
	@echo "  make smoke-litellm-ollama   # exit 0 required; runs inside agent-cage only"
	@echo "  make smoke-codebase-memory / smoke-repowise / smoke-context-tools"
	@echo "  make smoke-write-guard      # T-0031 write-guard MCP policy smoke"
	@echo "  make eval-tier0|eval-tier1|eval-mvp  # OQ-0002 opt5 scored eval"
	@echo "  make eval-suite|eval-matrix|eval-v02 # v0.2 multi-task / multi-model"
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
