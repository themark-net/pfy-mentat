# agent-cage harness wrapper for local-llm-dev-tools
# Multi-OS friendly entry (Linux / macOS / Windows-WSL). Prefer `make` over ad-hoc bash.
#
# Usage:
#   make setup          # shallow clone upstream at PINNED_COMMIT
#   make up             # start sandbox
#   make up-mcp         # start with MCP overlay
#   make shell          # shell into agent container
#   make status test down
#   make smoke-host     # host-side checks (docker, pins) without full cage
#
# Override clone location:
#   make setup CAGE_DIR=/path/to/agent-cage

SHELL := /bin/bash
.DEFAULT_GOAL := help

ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
CATALOG_ROOT := $(abspath $(ROOT)/../..)
PIN := $(shell tr -d '[:space:]' < $(ROOT)/PINNED_COMMIT)
UPSTREAM := https://github.com/pnnl/agent-cage.git
CAGE_DIR ?= $(HOME)/.local/share/local-llm-dev-tools/agent-cage
UNAME_S := $(shell uname -s 2>/dev/null || echo unknown)

.PHONY: help setup update up up-mcp down shell status test logs dashboard smoke-host smoke-integration doctor

help:
	@echo "agent-cage harness (pin $(PIN))"
	@echo "  CAGE_DIR=$(CAGE_DIR)"
	@echo "  OS=$(UNAME_S)"
	@echo ""
	@echo "Targets: setup update up up-mcp down shell status test logs dashboard"
	@echo "         smoke-host smoke-integration doctor"

doctor:
	@echo "== OS =="; uname -a || true
	@echo "== docker =="; docker version --format '{{.Server.Version}}' 2>/dev/null || docker version 2>/dev/null | head -5 || echo "MISS docker"
	@echo "== docker compose =="; docker compose version 2>/dev/null || echo "MISS docker compose"
	@echo "== python/uv =="; python3 --version; command -v uv >/dev/null && uv --version || echo "uv optional"
	@echo "== pin =="; echo $(PIN)
	@echo "== cage dir =="; ls -la $(CAGE_DIR) 2>/dev/null | head -5 || echo "not cloned (make setup)"

setup:
	@mkdir -p "$(dir $(CAGE_DIR))"
	@if [ ! -d "$(CAGE_DIR)/.git" ]; then \
	  echo "==> clone $(UPSTREAM) @ $(PIN)"; \
	  git clone --filter=blob:none $(UPSTREAM) "$(CAGE_DIR)"; \
	  git -C "$(CAGE_DIR)" checkout $(PIN); \
	else \
	  echo "==> already cloned; make update to re-pin"; \
	fi
	@echo "==> install agentcage CLI (uv tool preferred)"
	@if command -v uv >/dev/null 2>&1; then \
	  uv tool install -e "$(CAGE_DIR)" || true; \
	  command -v agentcage >/dev/null 2>&1 || uv tool install -e "$(CAGE_DIR)"; \
	else \
	  (cd "$(CAGE_DIR)" && python3 -m pip install -e . --user); \
	fi
	@command -v agentcage >/dev/null 2>&1 && agentcage --help >/dev/null && echo "agentcage CLI OK" || echo "warn: agentcage not on PATH (check uv tool dir / ~/.local/bin)"
	@echo "Next: make up   or   make up-mcp"

update:
	@test -d "$(CAGE_DIR)/.git" || (echo "run make setup first"; exit 1)
	git -C "$(CAGE_DIR)" fetch origin
	git -C "$(CAGE_DIR)" checkout $(PIN)
	@echo "checked out $(PIN)"

up: setup
	@if command -v agentcage >/dev/null 2>&1; then \
	  (cd "$(CAGE_DIR)" && agentcage up); \
	else \
	  echo "agentcage CLI missing; falling back to docker compose"; \
	  (cd "$(CAGE_DIR)/docker" && docker compose up -d); \
	fi

up-mcp: setup
	@if command -v agentcage >/dev/null 2>&1; then \
	  (cd "$(CAGE_DIR)" && agentcage up --mcp); \
	else \
	  (cd "$(CAGE_DIR)/docker" && docker compose -f docker-compose.yaml -f docker-compose.mcp.yaml up -d); \
	fi

down:
	@if command -v agentcage >/dev/null 2>&1; then \
	  (cd "$(CAGE_DIR)" && agentcage down); \
	else \
	  (cd "$(CAGE_DIR)/docker" && docker compose down); \
	fi

shell:
	@if command -v agentcage >/dev/null 2>&1; then \
	  (cd "$(CAGE_DIR)" && agentcage shell); \
	else \
	  (cd "$(CAGE_DIR)/docker" && docker compose exec agent bash); \
	fi

status:
	@if command -v agentcage >/dev/null 2>&1; then \
	  (cd "$(CAGE_DIR)" && agentcage status); \
	else \
	  (cd "$(CAGE_DIR)/docker" && docker compose ps); \
	fi

test:
	@if command -v agentcage >/dev/null 2>&1; then \
	  (cd "$(CAGE_DIR)" && agentcage test --quick); \
	else \
	  echo "install agentcage CLI for policy tests (make setup)"; exit 1; \
	fi

logs:
	@if command -v agentcage >/dev/null 2>&1; then \
	  (cd "$(CAGE_DIR)" && agentcage logs); \
	else \
	  (cd "$(CAGE_DIR)/docker" && docker compose logs -f --tail=100); \
	fi

dashboard:
	@if command -v agentcage >/dev/null 2>&1; then \
	  (cd "$(CAGE_DIR)" && agentcage dashboard); \
	else \
	  echo "open http://127.0.0.1:9090"; \
	fi

# Host-side smoke: no containers required
smoke-host:
	@$(MAKE) doctor
	@test -n "$(PIN)"
	@python3 -c "import json; json.load(open('$(CATALOG_ROOT)/data/tools.json'))"
	@test -f "$(ROOT)/manifest.json"
	@echo "smoke-host: OK"

# Integration smoke: requires setup + docker; starts cage, runs quick test, tears down
smoke-integration: smoke-host
	@$(MAKE) up
	@$(MAKE) test || true
	@echo "smoke-integration: cage up + test attempted; run make down when done"
	@echo "Catalog workspace can be mounted into cage workspace/ for tool evals"
	@echo "See README.md § Testing catalog tools"
