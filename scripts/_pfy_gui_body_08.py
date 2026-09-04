ype", "text/html; charset=utf-8")
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
    print("native window (tk)", flush=True)
    w = Win(board, root)
    if selftest:
        w.apply(selftest_snap()); root.update_idletasks(); root.update()
        title = root.title()
        has = (
            w.bgrok.cget("text") == "Attach grok"
            and w.bopen.cget("text") == "Attach opencode"
            and w.brefresh.cget("text") == "Refresh status"
            and w.bcopy.cget("text") == "Copy stub one-liner"
            and w.bstage.cget("text") == "Run stage"
            and w.benv.cget("text") == "Launch env"
            and w.bpull.cget("text") == "Pull"
            and w.btest.cget("text") == "Test model"
            and "tools" in w.nav
        )
        w.set_view("loop")
        body = w.body.cget("text") or ""
        loop_ok = "LOOP" in body and "env" in body.lower() and "LOCAL WORKER" not in body and "pfy board" not in body.lower()
        w.copy_stub()
        copied = (w.cst.cget("text") in ("copied", "PASS copied"))
        try:
            clip = root.clipboard_get()
        except Exception:
            clip = ""
        root.destroy()
        return title == "pfy" and has and loop_ok and copied and bool(clip)
    w.poll(int(os.environ.get("PFY_BOARD_REFRESH_MS", "2000"))); root.mainloop(); return True

def main() -> int:
    if os.environ.get("PFY_GUI_SELFTEST")=="1" or "--selftest" in sys.argv:
        return 0 if run_tk(None, True) and selftest_fresh_bind() else 1
    try: board = load_board()
    except Exception as e:
        return stopped_exit(str(e))
    httpd, url = ensure_http(board)
    try:
        if run_webkit(url): return 0
        if run_tk(board, False): return 0
        if os.environ.get("PFY_GUI_DEV")=="1" and run_pywebview(url): return 0
        return stopped_exit("no already-on-box toolkit opened a native window")
    finally:
        if httpd is not None:
            try: httpd.shutdown()
            except Exception: pass

if __name__ == "__main__":
    raise SystemExit(main())
