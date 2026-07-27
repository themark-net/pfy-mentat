# Voice agent operator targets (include from top Makefile or: make -f make/voice.mk <target>)
# Installable path + interactive REPL + agent run.

.PHONY: voice-agent-install voice-repl voice-agent-run voice-agent-long-mock

voice-agent-install:
	@chmod +x examples/voice-stt-edge/install-voice-agent.sh \
	  examples/voice-stt-edge/smoke.sh examples/voice-stt-edge/smoke-agent.sh \
	  examples/voice-stt-edge/voice-repl.sh examples/voice-stt-edge/agent_runner.py \
	  examples/voice-stt-edge/python.sh 2>/dev/null || true
	./examples/voice-stt-edge/install-voice-agent.sh

voice-repl:
	@chmod +x examples/voice-stt-edge/voice-repl.sh examples/voice-stt-edge/python.sh 2>/dev/null || true
	./examples/voice-stt-edge/voice-repl.sh

# One-shot agent run (text). Default local; set VOICE_AUTO_AGENT=grok to escalate.
voice-agent-run:
	@chmod +x examples/voice-stt-edge/agent_runner.py examples/voice-stt-edge/python.sh 2>/dev/null || true
	VOICE_LONG_TASK="$${VOICE_LONG_TASK:-1}" python3 examples/voice-stt-edge/agent_runner.py \
	  --mode "$${VOICE_AUTO_AGENT:-opencode}" \
	  --long-task \
	  --transcript "$${VOICE_TEXT:-Reply with STATUS/DOD/EXIT/NEXT for a healthy install}" \
	  --target "$${VOICE_TARGET:-worker}" \
	  --timeout "$${VOICE_AGENT_TIMEOUT:-600}" \
	  --out-dir examples/voice-stt-edge/.generated \
	  --repo .

voice-agent-long-mock:
	@export VOICE_LONG_TASK=1; \
	python3 examples/voice-stt-edge/agent_runner.py --mode mock --long-task \
	  --transcript "mock long-task receipt" --target worker \
	  --out-dir examples/voice-stt-edge/.generated --repo .; \
	python3 examples/eval-harness/tasks/008-voice-receipt/score.py \
	  examples/voice-stt-edge/.generated/last-reply.txt
