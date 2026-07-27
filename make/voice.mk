# Voice agent operator targets (included from top Makefile; also: make -f make/voice.mk <target>)
# Installable path + interactive REPL + agent run + deterministic e2e.

.PHONY: voice-agent-install voice-repl voice-agent-run voice-agent-long-mock \
	voice-agent-e2e voice-agent-local-receipt voice-agent-tool-microtask

voice-agent-install:
	@chmod +x examples/voice-stt-edge/install-voice-agent.sh \
	  examples/voice-stt-edge/smoke.sh examples/voice-stt-edge/smoke-agent.sh \
	  examples/voice-stt-edge/voice-repl.sh examples/voice-stt-edge/agent_runner.py \
	  examples/voice-stt-edge/python.sh examples/voice-stt-edge/e2e-develop-loop.sh \
	  examples/voice-stt-edge/ci-optional-local-long-task.sh \
	  examples/voice-stt-edge/tool-use-microtask.sh \
	  examples/voice-stt-edge/lib-local-model.sh 2>/dev/null || true
	./examples/voice-stt-edge/install-voice-agent.sh

voice-repl:
	@chmod +x examples/voice-stt-edge/voice-repl.sh examples/voice-stt-edge/python.sh 2>/dev/null || true
	./examples/voice-stt-edge/voice-repl.sh

# One-shot agent run (text). Default local long-task; set VOICE_AUTO_AGENT=grok to escalate.
# VOICE_TEXT=… to pass transcript; else uses last-transcript / agent-prompt in .generated.
voice-agent-run:
	@chmod +x examples/voice-stt-edge/agent_runner.py examples/voice-stt-edge/python.sh 2>/dev/null || true
	@MODE="$${VOICE_AGENT_MODE:-$${VOICE_AUTO_AGENT:-opencode}}"; \
	EXTRA=(); \
	if [[ -n "$${VOICE_TEXT:-}" ]]; then EXTRA+=(--transcript "$$VOICE_TEXT"); fi; \
	if [[ "$${VOICE_LONG_TASK:-1}" != "0" ]]; then EXTRA+=(--long-task); export VOICE_LONG_TASK=1; fi; \
	examples/voice-stt-edge/python.sh examples/voice-stt-edge/agent_runner.py \
	  --mode "$$MODE" \
	  "$${EXTRA[@]}" \
	  --target "$${VOICE_TARGET:-worker}" \
	  --timeout "$${VOICE_AGENT_TIMEOUT:-600}" \
	  --max-turns "$${VOICE_AGENT_MAX_TURNS:-8}" \
	  --out-dir examples/voice-stt-edge/.generated \
	  --repo "$(CURDIR)"

voice-agent-long-mock:
	@export VOICE_LONG_TASK=1; \
	python3 examples/voice-stt-edge/agent_runner.py --mode mock --long-task \
	  --transcript "mock long-task receipt" --target worker \
	  --out-dir examples/voice-stt-edge/.generated --repo .; \
	python3 examples/eval-harness/tasks/008-voice-receipt/score.py \
	  examples/voice-stt-edge/.generated/last-reply.txt; \
	python3 examples/eval-harness/tasks/009-voice-last-run/score.py \
	  examples/voice-stt-edge/.generated/last-run.json

# Deterministic develop loop (no LLM): recipe mode writes fixture + re-runs eval-structural.
voice-agent-e2e:
	@chmod +x examples/voice-stt-edge/e2e-develop-loop.sh 2>/dev/null || true
	./examples/voice-stt-edge/e2e-develop-loop.sh

# T-0097: hard 008 when local model present; SKIP artifact if no model / infra.
voice-agent-local-receipt:
	@chmod +x examples/voice-stt-edge/ci-optional-local-long-task.sh \
	  examples/voice-stt-edge/lib-local-model.sh 2>/dev/null || true
	./examples/voice-stt-edge/ci-optional-local-long-task.sh

# T-0098: OpenCode tools model must write known marker file (SKIP if no model).
voice-agent-tool-microtask:
	@chmod +x examples/voice-stt-edge/tool-use-microtask.sh \
	  examples/voice-stt-edge/lib-local-model.sh 2>/dev/null || true
	./examples/voice-stt-edge/tool-use-microtask.sh
