ff((tools.get("tools_mode") or "") == "local_tools")
            txt = (
                "TOOLS\n"
                f"one-shot         {onoff(skills.get('one-shot'))}\n"
                f"investigate      {onoff(skills.get('investigate'))}\n"
                f"agent-loops      {onoff(skills.get('agent-loops'))}\n"
                f"hermes-feedback  {onoff(skills.get('hermes-feedback'))}\n"
                f"mcp              {onoff(tools.get('mcp'))}\n"
                f"write-guard      {onoff(tools.get('write_guard'))}\n"
                f"extra tools      {extra}"
            )
            if self.msg: txt += "\n" + self.msg
            self.pack_acts([])
            for w in self.tool_btns.values():
                w.pack(side="left", padx=(0, 8))
            self.toolst.pack(side="left", padx=(0, 8))
        else:
            rows = s.get("org_messages") or []
            txt = "no org loop" if not rows else "ORG\n" + "\n".join(f"{m.get('from')} → {m.get('to')}  {m.get('state') or ''}" for m in rows)
            self.pack_acts([])
        self.body.configure(text=txt)
        for c in self.chips.winfo_children(): c.destroy()
        if self.view == "attach":
            for c in chips:
                hid, live, role, name = c.get("id") or "", honest(c.get("live")), c.get("role") or "", c.get("name") or ""
                fr = tk.Frame(self.chips, bg="#18202c", highlightbackground="#243041", highlightthickness=1, padx=8, pady=6)
                fr.pack(side="left", padx=4, pady=4, anchor="n")
                tk.Label(fr, text=hid, bg="#18202c", fg=FG, font=("sans-serif", 10, "bold")).pack(anchor="w")
                tk.Label(fr, text=live, bg="#18202c", fg=CHIP.get(live, CHIP["missing"]), font=("sans-serif", 9, "bold")).pack(anchor="w")
                tk.Label(fr, text=f"{role} · {name}", bg="#18202c", fg=MUTED).pack(anchor="w")
                if hid in BLOCKED:
                    tk.Label(fr, text=GROK_USE, bg="#111823", fg=FG, font=("monospace", 9)).pack(anchor="w", pady=(4,0))

    def poll(self, ms=2000):
        self.refresh()
        def tick():
            self.refresh(); self.root.after(ms, tick)
        self.root.after(ms, tick)

def selftest_snap():
    return {"ts":"selftest","host":"selftest","profile":"","detector":{"engine":"none","status":"missing","base_url":""},
            "engine_live":"missing","usage":[],"chips":[{"id":"grok","live":"missing","role":"harness","name":"Grok CLI"},
            {"id":"continue","live":"stub","role":"harness","name":"Continue"}],
            "tape":[{"id":"inference","label":"inference","live":"SKIP"},{"id":"env-stage","label":"env-stage","live":"SKIP"},
                    {"id":"harness-attach","label":"harness attach","live":"SKIP"}],
            "detect_order":[],"active":"grok","active_stub":False,"blocked_copy":GROK_USE,
            "last_verb":{"verb":"gui","when":""},"now":"idle","processes":[],"agent_lane_collapsed":True,
            "tools":{"skills":{"one-shot":True,"investigate":True,"agent-loops":True,"hermes-feedback":True},"mcp":False,"write_guard":False,"tools_mode":"split"}}

def selftest_fresh_bind():
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from urllib.parse import urlparse
    import urllib.request
    class Dump(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass
        def do_GET(self):
            b = b"<!DOCTYPE html><html><head><title>pfy board</title></head><body>127.0.0.1:8765 start via CLI nimo honest-state</body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
    class Ours(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass
        def do_GET(self):
            b = b'<!DOCTYPE html><html data-pfy-ui="session"><head><title>pfy</title></head><body>LOOP Attach grok</body>