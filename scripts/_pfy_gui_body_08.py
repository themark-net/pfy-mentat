BOARD_REFRESH_MS", "2000"))); root.mainloop(); return True

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
