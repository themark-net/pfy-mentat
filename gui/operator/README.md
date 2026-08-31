# pfy operator GUI (Tauri 2)

Native operator window is the main interface. Linux first. Not Electron. Not Chrome-to-localhost.

CLI prefers gui/operator/src-tauri/target/{release,debug}/pfy-operator when present.
Otherwise scripts/pfy-gui.py: pywebview + WebKitGTK loads the same frontend/, else stdlib tkinter with the same IA (engine status, env-stage, Attach grok / Attach opencode sidecar, loop/session). The window always opens.

Same IA: chips bind ./pfy status live (missing not unknown). LOCAL WORKER vs CLOUD MONITOR. Tape READY|SKIP|FAIL. Agent lane no org loop when empty. grok/opencode attach is sidecar. continue/agent-cage is FAIL plus: pfy harness use grok.
