# local-llm-dev-tools — top-level operator entrypoints
# Prefer these from the repo root (avoids "no rule to make target 'test'").
#
# Agent cage is the integration lab. Prefer testing catalog tool installs
# inside the cage (versioned images), not only on the host.

SHELL := /bin/bash
.DEFAULT_GOAL := help
HARNESS := harness/agent-cage

.PHONY: help cage-doctor cage-setup cage-init cage-up cage-up-mcp cage-down \
	cage-shell cage-status cage-test cage-logs cage-smoke-host catalog-json

help:
	@echo "local-llm-dev-tools"
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
	@echo "Or:  cd harness/agent-cage && make help"
	@echo ""
	@echo "Catalog:"
	@echo "  make catalog-json     Validate data/tools.json parses"

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
