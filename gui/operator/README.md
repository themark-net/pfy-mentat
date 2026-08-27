# pfy operator GUI (Tauri 2)

Native operator window is the main interface. Linux first. Not Electron. Not Chrome-to-localhost.

CLI prefers gui/operator/src-tauri/target/release/pfy-operator when present.
Otherwise scripts/pfy-gui.py (pywebview + WebKitGTK) loads the same frontend/.

Build one-liner (not required for the pywebview path; CI does not build Rust here):
cd gui/operator/src-tauri && cargo build --release

If pywebview is missing, scripts/pfy-gui.py prints an install tip and exits 2.

Same IA: chips bind ./pfy status live (missing not unknown). LOCAL WORKER vs CLOUD MONITOR. Tape READY|SKIP|FAIL. Agent lane no org loop when empty. grok/opencode attach is sidecar. continue/agent-cage is FAIL plus: pfy harness use grok.
