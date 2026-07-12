# agent-cage harness wrapper for local-llm-dev-tools
# Multi-OS friendly entry (Linux / macOS / Windows-WSL).
#
# IMPORTANT:
#   - Run targets from this directory OR use repo-root: make cage-*
#   - `agentcage` discovers the project via AGENTCAGE_DIR or ~/.agentcage
#     (after `agentcage init`), NOT the catalog repo root.
#   - Services must be started (`make up` / `make up-mcp`) before `make test`.
#   - Prefer running catalog tool smokes INSIDE the cage (versioned images).

SHELL := /bin/bash
.DEFAULT_GOAL := help

ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
CATALOG_ROOT := $(abspath $(ROOT)/../..)
PIN := $(shell tr -d '[:space:]' < $(ROOT)/PINNED_COMMIT)
UPSTREAM := https://github.com/pnnl/agent-cage.git

# Runtime project directory used by the agentcage CLI (after init).
# Override: make up AGENTCAGE_DIR=/path/to/project
AGENTCAGE_DIR ?= $(HOME)/.agentcage

# Optional source checkout (for pin tracking / editable install). Separate from runtime.
CAGE_SRC ?= $(HOME)/.local/share/local-llm-dev-tools/agent-cage

export AGENTCAGE_DIR
export PATH := $(HOME)/.local/bin:$(PATH)

UNAME_S := $(shell uname -s 2>/dev/null || echo unknown)

GROK_OVERLAY := $(ROOT)/overlays/grok
GROK_IMAGE := local-llm-dev-tools/agent-cage-grok:0.1.0
POLICY ?= default

.PHONY: help setup init update up up-mcp down shell status test logs dashboard \
	smoke-host smoke-integration doctor ensure-cli ensure-project \
	grok-overlay-install grok-overlay-uninstall grok-overlay-build grok-up grok-smoke \
	grok-auth-import

help:
	@echo "agent-cage harness (upstream pin $(PIN))"
	@echo "  AGENTCAGE_DIR=$(AGENTCAGE_DIR)   # runtime project for agentcage CLI"
	@echo "  CAGE_SRC=$(CAGE_SRC)            # optional pinned source clone"
	@echo "  OS=$(UNAME_S)"
	@echo ""
	@echo "First-time (this machine):"
	@echo "  make setup          # install agentcage CLI (+ optional source pin)"
	@echo "  make init           # materialize runtime to AGENTCAGE_DIR (~/.agentcage)"
	@echo "  make up-mcp         # start containers (build/pull images — can take a while)"
	@echo "  make status && make test && make shell"
	@echo "  make down"
	@echo ""
	@echo "From catalog repo root you can use: make cage-up-mcp  (etc.)"
	@echo ""
	@echo "Targets: doctor setup init update up up-mcp down shell status test logs"
	@echo "         dashboard smoke-host smoke-integration"
	@echo "Grok-in-image:"
	@echo "  make grok-overlay-install   # copy overlay into AGENTCAGE_DIR"
	@echo "  make grok-overlay-build     # build $(GROK_IMAGE)"
	@echo "  make grok-up                # up --mcp with coding-agent-grok policy"
	@echo "  make grok-smoke             # shell check: grok --version (stack must be up)"
	@echo "  make grok-overlay-uninstall # remove override from runtime project"

doctor:
	@echo "== OS =="; uname -a || true
	@echo "== docker =="; docker version --format '{{.Server.Version}}' 2>/dev/null || docker version 2>/dev/null | head -5 || echo "MISS docker"
	@echo "== docker compose =="; docker compose version 2>/dev/null || echo "MISS docker compose"
	@echo "== agentcage =="; command -v agentcage >/dev/null && agentcage --version || echo "MISS agentcage (make setup)"
	@echo "== AGENTCAGE_DIR =="; ls -la "$(AGENTCAGE_DIR)" 2>/dev/null | head -8 || echo "missing — run: make init"
	@echo "== pin (source) =="; echo $(PIN)
	@echo "== CAGE_SRC =="; ls -la "$(CAGE_SRC)" 2>/dev/null | head -5 || echo "optional source not cloned"

ensure-cli:
	@command -v agentcage >/dev/null 2>&1 || (echo "error: agentcage not on PATH. Run: make setup"; echo "hint: export PATH=\"\$$HOME/.local/bin:\$$PATH\""; exit 1)

ensure-project:
	@test -f "$(AGENTCAGE_DIR)/docker/docker-compose.yaml" \
	  || test -f "$(AGENTCAGE_DIR)/docker-compose.yaml" \
	  || (echo "error: no Agent Cage project at AGENTCAGE_DIR=$(AGENTCAGE_DIR)"; \
	      echo "Run: make init    # or: agentcage init"; exit 1)

setup:
	@mkdir -p "$(dir $(CAGE_SRC))"
	@if [ ! -d "$(CAGE_SRC)/.git" ]; then \
	  echo "==> clone $(UPSTREAM) @ $(PIN) → $(CAGE_SRC)"; \
	  git clone --filter=blob:none $(UPSTREAM) "$(CAGE_SRC)"; \
	  git -C "$(CAGE_SRC)" checkout $(PIN); \
	else \
	  echo "==> source already at $(CAGE_SRC); make update to re-pin"; \
	fi
	@echo "==> install agentcage CLI (uv tool preferred)"
	@if command -v uv >/dev/null 2>&1; then \
	  uv tool install -e "$(CAGE_SRC)" 2>/dev/null \
	    || uv tool install -e "$(CAGE_SRC)"; \
	else \
	  (cd "$(CAGE_SRC)" && python3 -m pip install -e . --user); \
	fi
	@command -v agentcage >/dev/null 2>&1 \
	  && echo "agentcage CLI OK: $$(agentcage --version 2>/dev/null || true)" \
	  || (echo "warn: agentcage not on PATH — add \$$HOME/.local/bin to PATH"; exit 1)
	@echo "Next: make init   then   make up-mcp"

init: ensure-cli
	@echo "==> agentcage init --path $(AGENTCAGE_DIR)"
	agentcage init --path "$(AGENTCAGE_DIR)" --no-completion
	@echo "Runtime project: $(AGENTCAGE_DIR)"
	@echo "Next: make up-mcp"

update:
	@test -d "$(CAGE_SRC)/.git" || (echo "run make setup first"; exit 1)
	git -C "$(CAGE_SRC)" fetch origin
	git -C "$(CAGE_SRC)" checkout $(PIN)
	@echo "source checked out $(PIN)"

up: ensure-cli ensure-project
	@echo "==> agentcage up  (AGENTCAGE_DIR=$(AGENTCAGE_DIR) POLICY=$(POLICY))"
	@echo "    First run builds images — may take several minutes."
	POLICY=$(POLICY) agentcage up --policy $(POLICY)

up-mcp: ensure-cli ensure-project
	@echo "==> agentcage up --mcp  (AGENTCAGE_DIR=$(AGENTCAGE_DIR) POLICY=$(POLICY))"
	@echo "    First run builds images — may take several minutes."
	POLICY=$(POLICY) agentcage up --mcp --policy $(POLICY)

down: ensure-cli ensure-project
	agentcage down

shell: ensure-cli ensure-project
	agentcage shell

status: ensure-cli ensure-project
	agentcage status

test: ensure-cli ensure-project
	@echo "==> Requires running services. If agent is not running: make up-mcp"
	agentcage test --quick

logs: ensure-cli ensure-project
	agentcage logs

dashboard: ensure-cli ensure-project
	agentcage dashboard

smoke-host:
	@$(MAKE) doctor
	@test -n "$(PIN)"
	@python3 -c "import json; json.load(open('$(CATALOG_ROOT)/data/tools.json'))"
	@test -f "$(ROOT)/manifest.json"
	@echo "smoke-host: OK (no containers required)"

# Full path: host checks → ensure project → up-mcp → test (leaves stack up)
smoke-integration: smoke-host ensure-cli
	@if [ ! -f "$(AGENTCAGE_DIR)/docker/docker-compose.yaml" ] && [ ! -f "$(AGENTCAGE_DIR)/docker-compose.yaml" ]; then \
	  $(MAKE) init; \
	fi
	@$(MAKE) up-mcp
	@$(MAKE) status
	@$(MAKE) test || true
	@echo ""
	@echo "smoke-integration: stack should be UP. Inspect with: make shell | make status"
	@echo "Tear down: make down"
	@echo "Catalog tool smokes: install/run inside 'make shell' (/workspace); see README."

# --- Grok-in-image overlay ---------------------------------------------------

grok-overlay-install: ensure-project
	@test -f "$(GROK_OVERLAY)/Dockerfile"
	@mkdir -p "$(AGENTCAGE_DIR)/docker/overlays-grok"
	@cp "$(GROK_OVERLAY)/Dockerfile" "$(AGENTCAGE_DIR)/docker/overlays-grok/Dockerfile"
	@cp "$(GROK_OVERLAY)/docker-compose.override.yaml" "$(AGENTCAGE_DIR)/docker/docker-compose.override.yaml"
	@cp "$(GROK_OVERLAY)/coding-agent-grok.yaml" "$(AGENTCAGE_DIR)/policies/coding-agent-grok.yaml"
	@echo "Installed Grok overlay into $(AGENTCAGE_DIR)"
	@echo "  docker/docker-compose.override.yaml"
	@echo "  docker/overlays-grok/Dockerfile"
	@echo "  policies/coding-agent-grok.yaml"
	@echo "Next: ensure XAI_API_KEY in $(AGENTCAGE_DIR)/.env then: make grok-overlay-build && make grok-up"

grok-overlay-uninstall:
	@rm -f "$(AGENTCAGE_DIR)/docker/docker-compose.override.yaml"
	@rm -rf "$(AGENTCAGE_DIR)/docker/overlays-grok"
	@rm -f "$(AGENTCAGE_DIR)/policies/coding-agent-grok.yaml"
	@echo "Removed Grok overlay files from $(AGENTCAGE_DIR) (image left in place)"

grok-overlay-build: ensure-project
	@docker image inspect agent-cage-agent:latest >/dev/null 2>&1 \
	  || (echo "error: agent-cage-agent:latest missing — run make up once to build base"; exit 1)
	@test -f "$(AGENTCAGE_DIR)/docker/overlays-grok/Dockerfile" \
	  || (echo "error: run make grok-overlay-install first"; exit 1)
	docker build \
	  -t $(GROK_IMAGE) \
	  --build-arg BASE_IMAGE=agent-cage-agent:latest \
	  -f "$(AGENTCAGE_DIR)/docker/overlays-grok/Dockerfile" \
	  "$(AGENTCAGE_DIR)/docker/overlays-grok"
	@echo "Built $(GROK_IMAGE)"

grok-up: ensure-cli ensure-project
	@test -f "$(AGENTCAGE_DIR)/docker/docker-compose.override.yaml" \
	  || (echo "error: run make grok-overlay-install first"; exit 1)
	@if [ -z "$$XAI_API_KEY" ] && [ -f "$(AGENTCAGE_DIR)/.env" ]; then \
	  set -a; . "$(AGENTCAGE_DIR)/.env"; set +a; \
	fi
	@if [ -z "$$XAI_API_KEY" ]; then \
	  echo "warn: XAI_API_KEY not set — grok may fail auth until you add it to $(AGENTCAGE_DIR)/.env"; \
	fi
	$(MAKE) up-mcp POLICY=coding-agent-grok

grok-smoke: ensure-cli ensure-project
	@echo "==> grok --version inside agent container"
	docker exec -u agent agent-cage-agent bash -lc 'export PATH="/home/agent/.local/bin:/home/agent/.grok/bin:$$PATH"; grok --version'
