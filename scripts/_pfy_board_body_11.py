      (STATE / "active-harness").write_text("opencode\n", encoding="utf-8")
        record_last_verb("start opencode")
        return {
            "ok": True, "id": hid, "live": "READY", "pid": proc.pid,
            "sidecar": True, "log": str(log), "base_url": base, "model": model,
        }
    log = STATE / f"sidecar-{hid}.log"
    with log.open("ab") as f:
        proc = subprocess.Popen(
            ["bash", str(PFY), "start", hid],
            cwd=str(ROOT),
            stdout=f,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    return {"ok": True, "id": hid, "live": "READY", "pid": proc.pid, "sidecar": True, "log": str(log)}

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("[pfy] " + (fmt % args) + "\n")
    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if ctype.startswith("text/html"):
            self.send_header("X-Pfy-UI", "session")
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._send(200, html_page().encode("utf-8"), "text/html; charset=utf-8"); return
        if path == "/snapshot":
            self._send(200, json.dumps(snapshot(), indent=2).encode("utf-8"), "application/json; charset=utf-8"); return
        self._send(404, b"not found\n", "text/plain; charset=utf-8")
    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/start":
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                body = json.loads(raw.decode() or "{}")
            except json.JSONDecodeError:
                body = {}
            hid = str((body or {}).get("id") or "")
            result = start_sidecar(hid)
            code = 200 if result.get("ok") else 400
            self._send(code, json.dumps(result).encode("utf-8"), "application/json; charset=utf-8")
            return
        if path == "/stage":
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(length)
            result = run_stage()
            code = 200 if result.get("ok") else 400
            self._send(code, json.dumps(result).encode("utf-8"), "application/json; charset=utf-8")
            return
        if path == "/env":
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(length)
            result = launch_env()
            code = 200 if result.get("ok") else 400
            self._send(code, json.dumps(result).encode("utf-8"), "application/json; charset=utf-8")
            return
        if path == "/models/pull":
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                body = json.loads(raw.decode() or "{}")
            except json.JSONDecodeError:
                body = {}
            name = str((body or {}).get("name") or "")
            result = pull_model(name)
            code = 200 if result.get("ok") else 400
            self._send(code, json.dumps(result).encode("utf-8"), "application/json; charset=utf-8")
            return
        if path == "/eval":
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(length)
            result = test_model()
            code = 200 if result.get("ok") else 400
            self._send(code, json.dumps(result).encode("utf-8"), "application/json; charset=utf-8")
            return
        if path == "/tools":
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                body = json.loads(raw.decode() or "{}")
            except json.JSONDecodeError:
                body = {}
            tid = str((body or {}).get("id") or "")
            on = (body or {}).get("on")
            result = set_tool(tid, on)
            code = 200 if result.get("ok") else 400
            self._send(code, json.dumps(result).encode("utf-8"), "application/json; charset=utf-8")
            return
        self._send(405, b"POST disabled for this path\n", "text/plain; charset=utf-8")

def main():
    args = sys.argv[1:]
    if args[:1] == ["--snapshot"]:
        print(json.dumps(snapshot()))
        return 0
    if args[:1] == ["--start"]:
        hid = args[1] if len(args) > 1 else ""
        result = start_sidecar(hid)
        print(json.dumps(result))
        return 0 if result.get("ok") else 2
    if args[:1] == ["--stage"]:
        result = run_stage()
        print(json.dumps(result))
        return 0 if result.get("ok") else 2
    if args[:1] == ["--env"]:
        result = launch_env()
        print(json.dumps(result))
        return 0 if result.get("ok") else 2
    if args[:1] == ["--pull"]:
        name = args[1] if len(args) > 1 else ""
        result = pull_model(name)
        print(json.dumps(result))
        return 0 if result.get("ok") else 2
    if args[:1] == ["--eval"]:
        result = test_model()
        print(json.dumps(result))
        return 0 if result.get("ok") else 2
    if args[:1] == ["--tool"]:
        tid = args[1] if len(args) > 1 else ""
        onraw = args[2] if len(args) > 2 else "1"
        on = str(onraw).strip().lower() in ("1", "true", "on", "yes")
        result = set_tool(tid, on)
        print(json.dumps(result))
        return 0 if result.get("ok") else 2
    if HOST not in ("127.0.0.1", "localhost"):
        print("error: operator HTTP binds loopback only", file=sys.stderr); return 2
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print("native window")
    try:
