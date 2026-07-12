# agent-cage harness wrapper for pfy-mentat
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
CAGE_SRC ?= $(HOME)/.local/share/pfy-mentat/agent-cage

export AGENTCAGE_DIR
export PATH := $(HOME)/.local/bin:$(PATH)

UNAME_S := $(shell uname -s 2>/dev/null || echo unknown)

GROK_OVERLAY := $(ROOT)/overlays/grok
GROK_IMAGE := pfy-mentat/agent-cage-grok:0.1.0
POLICY ?= default

LOCAL_OLLAMA_OVERLAY := $(ROOT)/overlays/local-ollama
LITELLM_EXAMPLE := $(CATALOG_ROOT)/examples/litellm-ollama
LITELLM_SMOKE_MODEL ?= deepseek-coder:latest
CM_EXAMPLE := $(CATALOG_ROOT)/examples/codebase-memory-mcp
RW_EXAMPLE := $(CATALOG_ROOT)/examples/repowise
REPOWISE_PIP_SPEC ?= repowise==0.30.0

.PHONY: help setup init update up up-mcp down shell status test logs dashboard \
	smoke-host smoke-integration doctor ensure-cli ensure-project \
	grok-overlay-install grok-overlay-uninstall grok-overlay-build grok-up grok-smoke \
	grok-auth-import \
	local-ollama-overlay-install local-ollama-up smoke-litellm-ollama \
	smoke-codebase-memory smoke-repowise smoke-context-tools \
	smoke-write-guard write-guard-overlay-install

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
	@echo "  make grok-auth-import       # copy host ~/.grok/auth.json (OIDC session) into cage"
	@echo "  make grok-overlay-build     # build $(GROK_IMAGE)"
	@echo "  make grok-up                # up --mcp with coding-agent-grok policy"
	@echo "  make grok-smoke             # grok --version inside container"
	@echo "  make grok-overlay-uninstall # remove override from runtime project"
	@echo "  Auth: browser/OIDC → auth.json (primary); XAI_API_KEY optional fallback"
	@echo ""
	@echo "LiteLLM + host Ollama (in-cage smoke):"
	@echo "  make local-ollama-overlay-install"
	@echo "  make local-ollama-up          # policy coding-agent-local + host-gateway"
	@echo "  make smoke-litellm-ollama     # LiteLLM completion inside agent container"
	@echo "Context tools (in-cage):"
	@echo "  make smoke-codebase-memory    # binary index+search fixture"
	@echo "  make smoke-repowise           # pip pin + health (zero LLM)"
	@echo "  make smoke-context-tools      # both + T-0013 compare note"
	@echo "Write-guard:"
	@echo "  make smoke-write-guard        # policy selftest + audit/enforce in cage"
	@echo "  make write-guard-overlay-install"

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
	@mkdir -p "$(AGENTCAGE_DIR)/grok-home"
	@chmod 700 "$(AGENTCAGE_DIR)/grok-home"
	@cp "$(GROK_OVERLAY)/Dockerfile" "$(AGENTCAGE_DIR)/docker/overlays-grok/Dockerfile"
	@cp "$(GROK_OVERLAY)/docker-compose.override.yaml" "$(AGENTCAGE_DIR)/docker/docker-compose.override.yaml"
	@cp "$(GROK_OVERLAY)/coding-agent-grok.yaml" "$(AGENTCAGE_DIR)/policies/coding-agent-grok.yaml"
	@# ensure auth.json path exists so volume mount is a file-friendly dir
	@touch "$(AGENTCAGE_DIR)/grok-home/.keep"
	@echo "Installed Grok overlay into $(AGENTCAGE_DIR)"
	@echo "  docker/docker-compose.override.yaml"
	@echo "  docker/overlays-grok/Dockerfile"
	@echo "  policies/coding-agent-grok.yaml"
	@echo "  grok-home/auth.json mounted at /home/agent/.grok/auth.json"
	@echo "Next: make grok-auth-import   # copy host browser/OIDC session"
	@echo "      make grok-overlay-build && make grok-up"

# Cage agent uid is 1001 in stock agent-cage image. Host copies are often uid 1000
# and mode 600 → agent cannot read auth.json → Grok falls back to ApiKey → 401 / OIDC noise.
CAGE_AGENT_UID ?= 1001
CAGE_AGENT_GID ?= 1001

grok-auth-import: ensure-project
	@test -f "$(HOME)/.grok/auth.json" \
	  || (echo "error: no host $(HOME)/.grok/auth.json — run 'grok login' on the host first"; exit 1)
	@mkdir -p "$(AGENTCAGE_DIR)/grok-home"
	@chmod 700 "$(AGENTCAGE_DIR)/grok-home"
	@cp "$(HOME)/.grok/auth.json" "$(AGENTCAGE_DIR)/grok-home/auth.json" 2>/dev/null \
	  || sudo cp "$(HOME)/.grok/auth.json" "$(AGENTCAGE_DIR)/grok-home/auth.json"
	@chown $(CAGE_AGENT_UID):$(CAGE_AGENT_GID) "$(AGENTCAGE_DIR)/grok-home/auth.json" 2>/dev/null \
	  || sudo chown $(CAGE_AGENT_UID):$(CAGE_AGENT_GID) "$(AGENTCAGE_DIR)/grok-home/auth.json" 2>/dev/null \
	  || true
	@if python3 -c "import os; st=os.stat('$(AGENTCAGE_DIR)/grok-home/auth.json'); raise SystemExit(0 if st.st_uid==$(CAGE_AGENT_UID) else 1)"; then \
	  chmod 600 "$(AGENTCAGE_DIR)/grok-home/auth.json" 2>/dev/null || sudo chmod 600 "$(AGENTCAGE_DIR)/grok-home/auth.json"; \
	else \
	  chmod 666 "$(AGENTCAGE_DIR)/grok-home/auth.json" 2>/dev/null || sudo chmod 666 "$(AGENTCAGE_DIR)/grok-home/auth.json"; \
	  echo "note: auth.json mode 666 (chown to $(CAGE_AGENT_UID) failed; dir remains 700)"; \
	fi
	@docker exec -u root agent-cage-agent bash -lc \
	  'chown agent:agent /home/agent/.grok/auth.json; chmod 600 /home/agent/.grok/auth.json' \
	  2>/dev/null || true
	@echo "Imported host OIDC/browser session → $(AGENTCAGE_DIR)/grok-home/auth.json"
	@echo "  auth_mode/email (redacted check):"
	@python3 -c "import json,os; p='$(AGENTCAGE_DIR)/grok-home/auth.json'; d=json.load(open(p)); \
	  v=next(iter(d.values())); st=os.stat(p); \
	  print('  mode=', v.get('auth_mode'), ' email=', v.get('email','?'), ' expires_at=', v.get('expires_at','?')); \
	  print('  file uid:gid=', st.st_uid, st.st_gid, ' perm=', oct(st.st_mode)[-3:])"
	@echo "Re-run import after host 'grok login' if the cage session expires."

grok-overlay-uninstall:
	@rm -f "$(AGENTCAGE_DIR)/docker/docker-compose.override.yaml"
	@rm -rf "$(AGENTCAGE_DIR)/docker/overlays-grok"
	@rm -f "$(AGENTCAGE_DIR)/policies/coding-agent-grok.yaml"
	@echo "Removed Grok overlay compose/policy (left grok-home/ and image in place)"
	@echo "To wipe imported auth: rm -rf $(AGENTCAGE_DIR)/grok-home"

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

# agentcage CLI only passes -f docker-compose.yaml (+ mcp). It does NOT load
# docker-compose.override.yaml when -f is set. Grok-up must call compose itself.
COMPOSE_DIR = $(AGENTCAGE_DIR)/docker
COMPOSE_GROK = docker compose -p agent-cage \
	-f $(COMPOSE_DIR)/docker-compose.yaml \
	-f $(COMPOSE_DIR)/docker-compose.mcp.yaml \
	-f $(COMPOSE_DIR)/docker-compose.override.yaml

grok-up: ensure-project
	@test -f "$(COMPOSE_DIR)/docker-compose.override.yaml" \
	  || (echo "error: run make grok-overlay-install first"; exit 1)
	@docker image inspect $(GROK_IMAGE) >/dev/null 2>&1 \
	  || (echo "error: $(GROK_IMAGE) missing — run make grok-overlay-build"; exit 1)
	@mkdir -p "$(AGENTCAGE_DIR)/grok-home"
	@if [ ! -f "$(AGENTCAGE_DIR)/grok-home/auth.json" ]; then \
	  echo "warn: no grok-home/auth.json — run make grok-auth-import or device-login in cage"; \
	fi
	@echo "==> docker compose up with Grok override (POLICY=coding-agent-grok)"
	@echo "    Note: agentcage CLI ignores compose override; this target uses -f override explicitly."
	@if [ -f "$(AGENTCAGE_DIR)/.env" ]; then set -a; . "$(AGENTCAGE_DIR)/.env"; set +a; fi; \
	cd "$(COMPOSE_DIR)" && \
	POLICY=coding-agent-grok \
	$(COMPOSE_GROK) --env-file "$(AGENTCAGE_DIR)/.env" up -d 2>/dev/null \
	|| POLICY=coding-agent-grok $(COMPOSE_GROK) up -d
	@echo "Waiting for agent container..."
	@sleep 3
	@# Fix auth.json ownership inside container (bind mount may show host uid)
	@docker exec -u root agent-cage-agent bash -lc \
	  'if [ -f /home/agent/.grok/auth.json ]; then chown agent:agent /home/agent/.grok/auth.json; chmod 600 /home/agent/.grok/auth.json; fi' \
	  2>/dev/null || true
	@docker inspect agent-cage-agent --format 'image={{.Config.Image}}'
	@echo "Next: make grok-smoke && make shell"

grok-smoke: ensure-project
	@echo "==> which image is running?"
	@docker inspect agent-cage-agent --format 'Config.Image={{.Config.Image}}' 2>/dev/null \
	  || (echo "error: agent-cage-agent not running — make grok-up"; exit 1)
	@docker exec -u root agent-cage-agent bash -lc \
	  'if [ -f /home/agent/.grok/auth.json ]; then chown agent:agent /home/agent/.grok/auth.json; chmod 600 /home/agent/.grok/auth.json; ls -ln /home/agent/.grok/auth.json; fi' \
	  2>/dev/null || true
	@echo "==> grok --version + auth smoke inside agent container"
	@docker exec -u agent \
	  -e HOME=/home/agent \
	  -e GROK_HOME=/home/agent/.grok \
	  -e PATH=/usr/local/bin:/home/agent/.local/bin:/usr/bin:/bin \
	  agent-cage-agent bash -lc 'command -v grok; grok --version; test -r /home/agent/.grok/auth.json && echo auth.json:readable || echo auth.json:NOT_READABLE'

# --- Local Ollama (host) + LiteLLM in-cage smoke -----------------------------

# agentcage CLI ignores extra compose files; use docker compose explicitly.
COMPOSE_LOCAL_OLLAMA = docker compose -p agent-cage \
	-f $(COMPOSE_DIR)/docker-compose.yaml \
	-f $(COMPOSE_DIR)/docker-compose.mcp.yaml \
	$(if $(wildcard $(COMPOSE_DIR)/docker-compose.override.yaml),-f $(COMPOSE_DIR)/docker-compose.override.yaml,) \
	-f $(COMPOSE_DIR)/docker-compose.local-ollama.yaml

local-ollama-overlay-install: ensure-project
	@test -f "$(LOCAL_OLLAMA_OVERLAY)/coding-agent-local.yaml"
	@test -f "$(LOCAL_OLLAMA_OVERLAY)/docker-compose.local-ollama.yaml"
	@cp "$(LOCAL_OLLAMA_OVERLAY)/coding-agent-local.yaml" \
	  "$(AGENTCAGE_DIR)/policies/coding-agent-local.yaml"
	@cp "$(LOCAL_OLLAMA_OVERLAY)/docker-compose.local-ollama.yaml" \
	  "$(COMPOSE_DIR)/docker-compose.local-ollama.yaml"
	@echo "Installed local-ollama overlay:"
	@echo "  policies/coding-agent-local.yaml"
	@echo "  docker/docker-compose.local-ollama.yaml"
	@echo "Next: $(LITELLM_EXAMPLE)/host-ollama-gateway.sh start"
	@echo "      make local-ollama-up && make smoke-litellm-ollama"

local-ollama-up: ensure-project
	@test -f "$(COMPOSE_DIR)/docker-compose.local-ollama.yaml" \
	  || (echo "error: run make local-ollama-overlay-install first"; exit 1)
	@test -f "$(AGENTCAGE_DIR)/policies/coding-agent-local.yaml" \
	  || (echo "error: missing coding-agent-local policy — make local-ollama-overlay-install"; exit 1)
	@# Host gateway (user-space) so Docker can reach 127.0.0.1-bound Ollama
	@$(LITELLM_EXAMPLE)/host-ollama-gateway.sh start
	@echo "==> docker compose up with local-ollama fragment (POLICY=coding-agent-local)"
	@if [ -f "$(AGENTCAGE_DIR)/.env" ]; then set -a; . "$(AGENTCAGE_DIR)/.env"; set +a; fi; \
	cd "$(COMPOSE_DIR)" && \
	POLICY=coding-agent-local \
	LITELLM_SMOKE_MODEL=$(LITELLM_SMOKE_MODEL) \
	DEPLOY_PROFILE=$${DEPLOY_PROFILE:-local-only} \
	$(COMPOSE_LOCAL_OLLAMA) up -d
	@sleep 3
	@docker inspect agent-cage-agent --format 'image={{.Config.Image}} status={{.State.Status}}' 2>/dev/null \
	  || (echo "error: agent-cage-agent not running"; exit 1)
	@echo "Policy should allow host.docker.internal. Next: make smoke-litellm-ollama"

smoke-litellm-ollama: ensure-project
	@test -f "$(LITELLM_EXAMPLE)/run-in-cage.sh" \
	  || (echo "error: missing $(LITELLM_EXAMPLE)/run-in-cage.sh"; exit 1)
	@$(LITELLM_EXAMPLE)/host-ollama-gateway.sh start
	@docker inspect agent-cage-agent --format '{{.State.Status}}' 2>/dev/null | grep -q running \
	  || (echo "error: agent not running — make local-ollama-up first"; exit 1)
	@# Stage recipe into cage workspace (may be owned by cage agent; use docker cp)
	@docker exec -u root agent-cage-agent bash -lc \
	  'mkdir -p /workspace/examples/litellm-ollama && chown agent:agent /workspace/examples /workspace/examples/litellm-ollama'
	@docker cp "$(LITELLM_EXAMPLE)/." agent-cage-agent:/workspace/examples/litellm-ollama/
	@docker exec -u root agent-cage-agent bash -lc \
	  'chown -R agent:agent /workspace/examples/litellm-ollama && chmod +x /workspace/examples/litellm-ollama/*.sh /workspace/examples/litellm-ollama/smoke_completion.py'
	@echo "==> in-cage LiteLLM → Ollama smoke (model=$(LITELLM_SMOKE_MODEL))"
	@docker exec -u agent \
	  -e HOME=/home/agent \
	  -e PATH=/home/agent/.local/bin:/usr/local/bin:/usr/bin:/bin \
	  -e OPENAI_BASE_URL=http://host.docker.internal:11435/v1 \
	  -e OLLAMA_HOST=http://host.docker.internal:11435 \
	  -e LITELLM_SMOKE_MODEL=$(LITELLM_SMOKE_MODEL) \
	  -e DEPLOY_PROFILE=local-only \
	  agent-cage-agent bash -lc \
	  'cd /workspace/examples/litellm-ollama && bash ./run-in-cage.sh'
	@echo "smoke-litellm-ollama: PASS"
	@printf '| %s | PASS | %s | in-cage LiteLLM→Ollama via host.docker.internal:11435 |\n' \
	  "$$(date -Iseconds)" "$(LITELLM_SMOKE_MODEL)" \
	  >> "$(CATALOG_ROOT)/pipelines/smoke/litellm-ollama/results.latest.md"

# --- codebase-memory-mcp + repowise in-cage smokes (T-0021 / T-0013) --------

smoke-codebase-memory: ensure-project
	@test -f "$(CM_EXAMPLE)/run-in-cage.sh"
	@docker inspect agent-cage-agent --format '{{.State.Status}}' 2>/dev/null | grep -q running \
	  || (echo "error: agent not running — make up-mcp or local-ollama-up first"; exit 1)
	@docker exec -u root agent-cage-agent bash -lc \
	  'mkdir -p /workspace/examples/codebase-memory-mcp /home/agent/.local/bin && chown -R agent:agent /workspace/examples /home/agent/.local 2>/dev/null || true'
	@# Prefer host binary (~270MB) to avoid re-download; fallback install inside cage
	@if [ -x "$(HOME)/.local/bin/codebase-memory-mcp" ]; then \
	  docker cp "$(HOME)/.local/bin/codebase-memory-mcp" agent-cage-agent:/home/agent/.local/bin/codebase-memory-mcp; \
	  docker exec -u root agent-cage-agent bash -lc 'chown agent:agent /home/agent/.local/bin/codebase-memory-mcp && chmod +x /home/agent/.local/bin/codebase-memory-mcp'; \
	fi
	@docker cp "$(CM_EXAMPLE)/." agent-cage-agent:/workspace/examples/codebase-memory-mcp/
	@docker exec -u root agent-cage-agent bash -lc \
	  'chown -R agent:agent /workspace/examples/codebase-memory-mcp && chmod +x /workspace/examples/codebase-memory-mcp/run-in-cage.sh'
	@echo "==> in-cage codebase-memory-mcp smoke"
	@docker exec -u agent \
	  -e HOME=/home/agent \
	  -e PATH=/home/agent/.local/bin:/usr/local/bin:/usr/bin:/bin \
	  agent-cage-agent bash -lc \
	  'cd /workspace/examples/codebase-memory-mcp && bash ./run-in-cage.sh'
	@echo "smoke-codebase-memory: PASS"
	@mkdir -p "$(CATALOG_ROOT)/pipelines/smoke/codebase-memory-mcp"
	@printf '| %s | PASS | codebase-memory-mcp | in-cage index+search fixture |\n' \
	  "$$(date -Iseconds)" >> "$(CATALOG_ROOT)/pipelines/smoke/codebase-memory-mcp/results.latest.md"

smoke-repowise: ensure-project
	@test -f "$(RW_EXAMPLE)/run-in-cage.sh"
	@docker inspect agent-cage-agent --format '{{.State.Status}}' 2>/dev/null | grep -q running \
	  || (echo "error: agent not running — make up-mcp or local-ollama-up first"; exit 1)
	@docker exec -u root agent-cage-agent bash -lc \
	  'mkdir -p /workspace/examples/repowise && chown -R agent:agent /workspace/examples'
	@docker cp "$(RW_EXAMPLE)/." agent-cage-agent:/workspace/examples/repowise/
	@docker exec -u root agent-cage-agent bash -lc \
	  'chown -R agent:agent /workspace/examples/repowise && chmod +x /workspace/examples/repowise/run-in-cage.sh'
	@echo "==> in-cage repowise smoke (pip $(REPOWISE_PIP_SPEC))"
	@docker exec -u agent \
	  -e HOME=/home/agent \
	  -e PATH=/home/agent/.local/bin:/usr/local/bin:/usr/bin:/bin \
	  -e REPOWISE_PIP_SPEC=$(REPOWISE_PIP_SPEC) \
	  agent-cage-agent bash -lc \
	  'cd /workspace/examples/repowise && bash ./run-in-cage.sh'
	@echo "smoke-repowise: PASS"
	@mkdir -p "$(CATALOG_ROOT)/pipelines/smoke/repowise"
	@printf '| %s | PASS | %s | in-cage health (zero LLM) |\n' \
	  "$$(date -Iseconds)" "$(REPOWISE_PIP_SPEC)" \
	  >> "$(CATALOG_ROOT)/pipelines/smoke/repowise/results.latest.md"

smoke-context-tools: smoke-codebase-memory smoke-repowise
	@test -f "$(CATALOG_ROOT)/pipelines/smoke/context-tools-compare.md"
	@echo "smoke-context-tools: PASS (see pipelines/smoke/context-tools-compare.md)"

# --- write-guard MCP (T-0031) ------------------------------------------------

WG_PKG := $(CATALOG_ROOT)/harness/write-guard-mcp
WG_EXAMPLE := $(CATALOG_ROOT)/examples/write-guard-mcp

write-guard-overlay-install: ensure-project
	@mkdir -p "$(AGENTCAGE_DIR)/overlays-write-guard"
	@cp "$(ROOT)/overlays/write-guard/mcp-servers.write-guard.yaml" \
	  "$(AGENTCAGE_DIR)/overlays-write-guard/mcp-servers.write-guard.yaml"
	@cp "$(ROOT)/overlays/write-guard/README.md" \
	  "$(AGENTCAGE_DIR)/overlays-write-guard/README.md"
	@echo "Installed write-guard overlay docs → $(AGENTCAGE_DIR)/overlays-write-guard/"
	@echo "  Enable MCP entry after package is on mcp-host PATH (see overlay README)."

smoke-write-guard: ensure-project
	@test -f "$(WG_EXAMPLE)/run-in-cage.sh"
	@test -d "$(WG_PKG)/src/write_guard"
	@docker inspect agent-cage-agent --format '{{.State.Status}}' 2>/dev/null | grep -q running \
	  || (echo "error: agent not running — make up-mcp first"; exit 1)
	@docker exec -u root agent-cage-agent bash -lc \
	  'mkdir -p /workspace/examples/write-guard-mcp/pkg && chown -R agent:agent /workspace/examples'
	@# stage package + example driver
	@docker cp "$(WG_PKG)/." agent-cage-agent:/workspace/examples/write-guard-mcp/pkg/
	@docker cp "$(WG_EXAMPLE)/run-in-cage.sh" agent-cage-agent:/workspace/examples/write-guard-mcp/run-in-cage.sh
	@docker cp "$(WG_EXAMPLE)/README.md" agent-cage-agent:/workspace/examples/write-guard-mcp/README.md
	@docker exec -u root agent-cage-agent bash -lc \
	  'chown -R agent:agent /workspace/examples/write-guard-mcp && chmod +x /workspace/examples/write-guard-mcp/run-in-cage.sh'
	@echo "==> in-cage write-guard smoke"
	@docker exec -u agent \
	  -e HOME=/home/agent \
	  -e PATH=/home/agent/.local/bin:/usr/local/bin:/usr/bin:/bin \
	  -e WRITE_GUARD_SRC=/workspace/examples/write-guard-mcp/pkg \
	  agent-cage-agent bash -lc \
	  'cd /workspace/examples/write-guard-mcp && bash ./run-in-cage.sh'
	@echo "smoke-write-guard: PASS"
	@mkdir -p "$(CATALOG_ROOT)/pipelines/smoke/write-guard-mcp"
	@printf '| %s | PASS | write-guard-mcp 0.1.0 | selftest+audit+enforce in cage |\n' \
	  "$$(date -Iseconds)" >> "$(CATALOG_ROOT)/pipelines/smoke/write-guard-mcp/results.latest.md"
