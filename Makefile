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
	cage-grok-smoke cage-grok-uninstall cage-grok-auth-import \
	local-ollama-overlay-install local-ollama-up smoke-litellm-ollama \
	smoke-codebase-memory smoke-repowise smoke-context-tools \
	smoke-write-guard

help:
	@echo "pfy-mentat"
	@echo ""
	@echo "Environment (secrets never in git):"
	@echo "  make env-init         Create .env from bootstrap/env/env.example if missing"
	@echo "  make env-check        Validate required vars for DEPLOY_PROFILE"
	@echo ""
	@echo "Agent cage (integration lab) — from repo root:"
	@echo "  make cage-doctor      Host/docker checks"
	@echo "  make cage-setup       Clone pin + install agentcage CLI"
	@echo "  make cage-init        agentcage init → \$$HOME/.agentcage (once)"
	@echo "  make cage-up          Start sandbox"
	@echo "  make cage-up-mcp      Start sandbox + MCP  (do this before cage-test)"
	@echo "  make cage-status      Container health"
	@echo "  make cage-shell       Shell into agent container"
	@echo "  make cage-test        Policy tests (services must already be up)"
	@echo "  make cage-down        Stop sandbox"
	@echo "  make cage-smoke-host  Host-only smoke (no containers)"
	@echo ""
	@echo "Grok-in-cage (versioned image overlay):"
	@echo "  make cage-grok-install / cage-grok-auth-import / cage-grok-build"
	@echo "  make cage-grok-up / cage-grok-smoke / cage-grok-uninstall"
	@echo "  Auth: import host ~/.grok/auth.json (browser/OIDC) or device-login in cage"
	@echo ""
	@echo "LiteLLM + Ollama (in-cage smoke, local-only):"
	@echo "  make local-ollama-overlay-install"
	@echo "  make local-ollama-up"
	@echo "  make smoke-litellm-ollama   # exit 0 required; runs inside agent-cage only"
	@echo "  make smoke-codebase-memory / smoke-repowise / smoke-context-tools"
	@echo "  make smoke-write-guard      # T-0031 write-guard MCP policy smoke"
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
