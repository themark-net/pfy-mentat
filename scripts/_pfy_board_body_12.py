nt(self.headers.get("Content-Length") or 0)
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
        if path == "/space-invaders":
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(length)
            result = run_space_invaders()
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
    if args[:1] == ["--space-invaders"]:
        result = run_space_invaders()
        print(json.dumps(result))
        return 0 if result.get("ok") else 2
    if HOST not in ("127.0.0.1", "localhost"):
        print("error: operator HTTP binds loopback only", file=sys.stderr); return 2
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print("native window")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
