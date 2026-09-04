tthickness=1, padx=8, pady=6)
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
            b = b'<!DOCTYPE html><html data-pfy-ui="session"><head><title>pfy</title></head><body>LOOP Attach grok</body></html>'
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("X-Pfy-UI", "session")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
    dump = ThreadingHTTPServer(("127.0.0.1", 0), Dump)
    threading.Thread(target=dump.serve_forever, daemon=True).start()
    dport = dump.server_address[1]
    class Board:
        HOST = "127.0.0.1"
        PORT = dport
        Handler = Ours
    httpd, url = ensure_http(Board)
    try:
        got = urlparse(url).port
        if got == dport:
            return False
        with urllib.request.urlopen(url, timeout=1) as r:
            body = r.read().decode("utf-8", "replace")
            hdr = (r.headers.get("X-Pfy-UI") or "")
        return (
            not leftover_dump(body, hdr)
            and "pfy board" not in body.lower()
            and "start via cli" not in body.lower()
            and "<title>pfy</title>" in body
        )
    finally:
        try:
            httpd.shutdown()
        except Exception:
            pass
        try:
            dump.shutdown()
        except Exception:
            pass

def run_tk(board, selftest=False) -> bool:
    try:
        import tkinter as tk; import tkinter.ttk  # noqa
        root = tk.Tk()
    except Exception:
        return False
    print("native wind