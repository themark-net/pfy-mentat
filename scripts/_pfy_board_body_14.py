n 0 if result.get("ok") else 2
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
    if args[:1] == ["--open-game"]:
        result = open_space_invaders_game()
        print(json.dumps(result))
        return 0 if result.get("ok") else 2
    if args[:1] == ["--open-folder"]:
        result = open_space_invaders_folder()
        print(json.dumps(result))
        return 0 if result.get("ok") else 2
    if args[:1] in (["--copy-task"], ["--task"]):
        result = space_invaders_task()
        print(json.dumps(result))
        return 0 if result.get("ok") else 2
    if args[:1] == ["--artifact"]:
        result = space_invaders_artifact()
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
