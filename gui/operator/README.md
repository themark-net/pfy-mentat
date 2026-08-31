# pfy operator GUI (Tauri 2)

Native operator window is the main interface. Linux first. Not Electron. Not Chrome-to-localhost.

CLI prefers gui/operator/src-tauri/target/{release,debug}/pfy-operator when present.
Otherwise scripts/pfy-gui.py: PyGObject WebKit2 if already on the box (native window (webkit)),
else stdlib tkinter (native window (tk)) with the same IA. pywebview is PFY_GUI_DEV=1 only.

Window chrome: sidebar Loop / Engine / Stage / Attach (Org omitted if unused);
header LOCAL WORKER | CLOUD MONITOR + tape; title pfy; Attach grok / Attach opencode sidecar.

Same IA: chips bind ./pfy status live (missing not unknown). Tape READY|SKIP|FAIL.
continue/agent-cage is FAIL plus: pfy harness use grok. Buttons disabled. No fallback spawn.
