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
        if path == "/catalog/ask":
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                body = json.loads(raw.decode() or "{}")
            except json.JSONDecodeError:
                body = {}
            name = str((body or {}).get("name") or (body or {}).get("id") or "")
            result = catalog_ask(name)
            code = 200 if result.get("ok") else 400
            self._send(code, json.dumps(result).encode("utf-8"), "application/json; charset=utf-8")
            return
        if path == "/catalog/queue":
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                body = json.loads(raw.decode() or "{}")
            except json.JSONDecodeError:
                body = {}
            name = str((body or {}).get("name") or (body or {}).get("id") or "")
            result = catalog_queue(name)
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
        if path == "/space-invaders":
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(length)
            result = run_space_invaders()
            code = 200 if result.get("ok") else 400
            self._send(code, json.dumps(result).encode("utf-8"), "application/json; charset=utf-8")
            return
        if path == "/space-invaders/open-game":
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(length)
            result = open_space_invaders_game()
            code = 200 if result.get("ok") else 400
            self._send(code, json.dumps(result).encode("utf-8"), "application/json; charset=utf-8")
            return
        if path == "/space-invaders/open-folder":
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(length)
            result = open_space_invaders_folder()
            code = 200 if result.get("ok") else 400
            self._send(code, json.dumps(result).encode("utf-8"), "application/json; charset=utf-8")
            return
        if path in ("/space-invaders/copy-task", "/space-invaders/task"):
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(length)
            result = space_invaders_task()
            code = 200 if result.get("ok") else 400
            self._send(code, json.dumps(result).encode("utf-8"), "application/json; charset=utf-8")
            return
        if path == "/wizard":
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                body = json.loads(raw.decode() or "{}")
            except json.JSONDecodeError:
                body = {}
            step = str((body or {}).get("step") or "")
            value = str((body or {}).get("value") or (body or {}).get("id") or "")
            result = wizard_apply(step, value)
            code = 200 if result.get("ok") else 400
            self._send(code, json.dumps(result).encode("utf-8"), "application/json; charset=utf-8")
            return
        if path in ("/launch", "/launch-session"):
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(length)
            result = launch_wizard_session()
            code = 200 if result.get("ok") else 400
            self._send(code, json.dumps(result).encode("utf-8"), "application/json; charset=utf-8")
            return
        if path in ("/decision/smoke", "/decision"):
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                body = json.loads(raw.decode() or "{}")
            except json.JSONDecodeError:
                body = {}
            dpath = str((body or {}).get("path") or (body or {}).get("value") or "cua-s1-forms")
            result = decision_smoke(dpath)
            code = 200 if result.get("ok") else 400
            self._send(code, json.dumps(result).encode("utf-8"), "application/json; charset=utf-8")
            return
        if path in ("/gab/sync", "/models/gab-sync"):
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(length)
            result = gab_local_sync()
            code = 200 if result.get("ok") else 400
            self._send(code, json.dumps(result).encode("utf-8"), "application/json; charset=utf-8")
            return
        if path in ("/gab/pull", "/models/gab-pull"):
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                body = json.loads(raw.decode() or "{}")
            except json.JSONDecodeError:
                body = {}
            tag = str((body or {}).get("tag") or (body or {}).get("name") or "")
            confirm = bool((body or {}).get("confirm") or (body or {}).get("confirm_tight"))
            opt_in = bool((body or {}).get("opt_in_huge"))
            result = gab_pull(tag, confirm_tight=confirm, opt_in_huge=opt_in)
            code = 200 if result.get("ok") else 400
            self._send(code, json.dumps(result).encode("utf-8"), "application/json; charset=utf-8")
            return
        if path == "/gab/cloud":
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                body = json.loads(raw.decode() or "{}")
            except json.JSONDecodeError:
                body = {}
            model = str((body or {}).get("model") or "auto")
            mod, err = _load_gab_228()
            if mod is None:
                result = {"ok": False, "live": "FAIL", "copy": "FAIL gab -- module missing", "error": err or "missing"}
            else:
                result = mod.cloud_lane(STATE, model=model, ROOT=ROOT)
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
        mode = args[2] if len(args) > 2 else None
        result = start_sidecar(hid, mode=mode)
        print(json.dumps(result))
        return 0 if result.get("ok") else 2
    if args[:1] == ["--mode"]:
        mode = args[1] if len(args) > 1 else ""
        result = set_attach_mode(mode)
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
    if args[:1] == ["--wizard"]:
        step = args[1] if len(args) > 1 else "runtime"
        value = " ".join(args[2:]).strip()
        result = wizard_apply(step, value)
        print(json.dumps(result))
        return 0 if result.get("ok") else 2
    if args[:1] in (["--launch"], ["--launch-session"]):
        result = launch_wizard_session()
        print(json.dumps(result))
        return 0 if result.get("ok") else 2
    if args[:1] == ["--pull"]:
        name = args[1] if len(args) > 1 else ""
        result = pull_model(name)
        print(json.dumps(result))
        return 0 if result.get("ok") else 2
    if args[:1] == ["--recommend"]:
        result = recommend_models()
        print(json.dumps(result))
        return 0 if result.get("ok") else 2
    if args[:1] == ["--try"]:
        name = args[1] if len(args) > 1 else ""
        result = try_recommended_model(name)
        print(json.dumps(result))
        return 0 if result.get("ok") else 2
    if args[:1] in (["--decision"], ["--decision-smoke"]):
        dpath = "cua-s1-forms"
        if "--path" in args:
            i = args.index("--path")
            if i + 1 < len(args):
                dpath = args[i + 1]
        elif len(args) > 1 and not args[1].startswith("-"):
            dpath = args[1]
        result = decision_smoke(dpath)
        print(json.dumps(result))
        return 0 if result.get("ok") else 2
    if args[:1] in (["--gab-sync"], ["--gab-local-sync"]):
        result = gab_local_sync()
        print(json.dumps(result))
        return 0 if result.get("ok") else 2
    if args[:1] == ["--gab-pull"]:
        tag = args[1] if len(args) > 1 else ""
        confirm = "--confirm" in args
        opt_in = "--opt-in-huge" in args
        result = gab_pull(tag, confirm_tight=confirm, opt_in_huge=opt_in)
        print(json.dumps(result))
        return 0 if result.get("ok") else 2
    if args[:1] == ["--gab-cloud"]:
        model = "auto"
        if "--model" in args:
            i = args.index("--model")
            if i + 1 < len(args):
                model = args[i + 1]
        elif len(args) > 1 and not args[1].startswith("-"):
            model = args[1]
        mod, err = _load_gab_228()
        if mod is None:
            result = {"ok": False, "copy": "FAIL gab -- module missing", "error": err or "missing"}
        else:
            result = mod.cloud_lane(STATE, model=model, ROOT=ROOT)
        print(json.dumps(result))
        return 0 if result.get("ok") else 2
    if args[:1] == ["--eval"]:
        result = test_model()
        print(json.dumps(result))
        retur