: str(log),
            }
        record_sidecar_pid("opencode", proc.pid)
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


def run_space_invaders():
    """Session proof: Attach OpenCode required, then workspace/space-invaders. Cite #155."""
    import importlib.util
    path = ROOT / "scripts" / "pfy_space_invaders.py"
    if not path.is_file():
        return {
            "ok": False, "live": "FAIL",
            "copy": "FAIL Space Invaders · module missing",
            "error": str(path), "path": "",
        }
    spec = importlib.util.spec_from_file_location("pfy_space_invaders", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.run(
        root=ROOT,
        state=STATE,
        which_bin=which_bin,
        write_opencode_config=write_opencode_config,
        live_openai_base=live_openai_base,
        inspect_models=inspect_models,
        record_last_verb=record_last_verb,
        active_harness=active_harness,
        pid_alive=pid_alive,
    )

def _load_verify_159():
    """Load pfy_verify_159 or return (None, error). Cite #159."""
    import importlib.util
    path = ROOT / "scripts" / "pfy_verify_159.py"
    if not path.is_file():
        return None, str(path)
    try:
        spec = importlib.util.spec_from_file_location("pfy_verify_159", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod, ""
    except Exception as e:
        return None, str(e)[:400]

def open_space_invaders_game():
    mod, err = _load_verify_159()
    if mod is None:
        return {"ok": False, "live": "FAIL", "copy": "FAIL Open game · module missing", "error": err}
    try:
        return mod.open_game(ROOT)
    except Exception as e:
        return {"ok": False, "live": "FAIL", "copy": "FAIL Open game", "error": str(e)[:400]}

def open_space_invaders_folder():
    mod, err = _load_verify_159()
    if mod is None:
        return {"ok": False, "live": "FAIL", "copy": "FAIL Open folder · module missing", "error": err}
    try:
        return mod.open_folder(ROOT)
    except Exception as e:
        return {"ok": False, "live": "FAIL", "copy": "FAIL Open folder", "error": str(e)[:400]}

def space_invaders_task():
    mod, err = _load_verify_159()
    if mod is None:
        return {"ok": False, "live": "FAIL", "copy": "FAIL Copy TASK · module missing", "error": err, "task_text": ""}
    try:
        return mod.task_payload(ROOT)
    except Exception as e:
        return {"ok": False, "live": "FAIL", "copy": "FAIL Copy TASK", "error": str(e)[:400], "task_text": ""}

def space_invaders_artifact():
    mod, err = _load_verify_159()
    if mod is None:
        return {"ok": False, "live": "FAIL", "copy": "FAIL artifact · module missing", "error": err}
    try:
        return mod.artifact_get(ROOT)
    except Exception as e:
        return {"ok": False, "live": "FAIL", "copy": "FAIL artifact", "error": str(e)[:400]}

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
        asset = frontend_static(path)
        if asset:
            fp, ctype = asset
            self._send(200, fp.read_bytes(), ctype); return
        if path == "/snapshot":
            self._send(200, json.dumps(snapshot(), indent=2).encode("utf-8"), "application/json; charset=utf-8"); return
        if path == "/space-invaders/artifact":
            result = space_invaders_artifact()
            code = 200 if result.get("ok") else 404
            self._send(code, json.dumps(result).encode("utf-8"), "application/json; charset=utf-8"); return
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
            length = i