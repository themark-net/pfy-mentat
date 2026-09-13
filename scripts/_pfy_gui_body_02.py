 = ttk.Button(self.acts, text="Pull", command=self.pull_model)
        self.btest = ttk.Button(self.acts, text="Test model", command=self.test_model)
        self.tool_btns = {}
        for tid, lab in (("one-shot","one-shot"),("investigate","investigate"),("agent-loops","agent-loops"),("hermes-feedback","hermes-feedback"),("mcp","mcp"),("write-guard","write-guard"),("extra-tools","extra tools")):
            self.tool_btns[tid] = ttk.Button(self.acts, text=lab, command=lambda x=tid: self.toggle_tool(x))
        self.toolst = ttk.Label(self.acts, text="", style="M.TLabel")
        self.pullname = ttk.Entry(self.acts, width=22)
        self.sst = ttk.Label(self.acts, text="", style="M.TLabel")
        self.est = ttk.Label(self.acts, text="", style="M.TLabel")
        self.pst = ttk.Label(self.acts, text="", style="M.TLabel")
        self.rst = ttk.Label(self.acts, text="", style="M.TLabel")
        self.tst = ttk.Label(self.acts, text="", style="M.TLabel")
        self.ast = ttk.Label(self.acts, text="", style="Ok.TLabel")
        self.cst = ttk.Label(self.acts, text="", style="M.TLabel")
        self.sist = ttk.Label(self.acts, text="", style="M.TLabel")
        self.bsiopen = ttk.Button(self.acts, text="Open game", command=self.open_si_game)
        self.bsifold = ttk.Button(self.acts, text="Open folder", command=self.open_si_folder)
        self.bsitask = ttk.Button(self.acts, text="Copy TASK", command=self.copy_si_task)
        self.bcopyep = ttk.Button(self.acts, text="Copy endpoint", command=self.copy_endpoint)
        self.bcopyst = ttk.Button(self.acts, text="Copy ./pfy status", command=self.copy_pfy_status)
        self.siabs = ttk.Label(self.acts, text="", style="M.TLabel")
        self.sirel = ttk.Label(self.acts, text="", style="M.TLabel")
        self.sitask = ttk.Label(self.acts, text="", style="M.TLabel")
        self.ewhat = ttk.Label(self.acts, text="", style="M.TLabel")
        self.siopenst = ttk.Label(self.acts, text="", style="M.TLabel")
        self._last_env = {}
        self._last_si = {}
        self._session_reach = ""
        self._attach_mode = "bare"
        self.breco = ttk.Button(self.acts, text="Recommend", command=self.recommend_models)
        self.btry = ttk.Button(self.acts, text="Try recommended", command=self.try_recommended)
        self.recst = ttk.Label(self.acts, text="", style="M.TLabel")
        self.tryst = ttk.Label(self.acts, text="", style="M.TLabel")
        self.catname = ttk.Entry(self.acts, width=22)
        self.bask = ttk.Button(self.acts, text="Ask TUI implement", command=self.catalog_ask)
        self.bqueue = ttk.Button(self.acts, text="Queue for org", command=self.catalog_queue)
        self.bcatcopy = ttk.Button(self.acts, text="Copy prompt", command=self.copy_catalog_prompt)
        self.catst = ttk.Label(self.acts, text="", style="M.TLabel")
        self.bsess = ttk.Button(self.acts, text="Launch session", command=self.launch_session)
        self.blocal = ttk.Button(self.acts, text="local", command=lambda: self.wizard_step("lane", "local"))
        self.bcloud = ttk.Button(self.acts, text="cloud/subscription", command=lambda: self.wizard_step("lane", "cloud/subscription"))
        self.bofree = ttk.Button(self.acts, text="OpenCode free", command=lambda: self.wizard_step("lane", "opencode-free"))
        self.bcatalog = ttk.Button(self.acts, text="catalog", command=lambda: self.wizard_step("toolsets", "catalog"))
        self.bhopenc = ttk.Button(self.acts, text="OpenCode", command=lambda: self.wizard_step("harness", "opencode"))
        self.bhgrok = ttk.Button(self.acts, text="Grok", command=lambda: self.wizard_step("harness", "grok"))
        self.bhhermes = ttk.Button(self.acts, text="Hermes", command=lambda: self.wizard_step("harness", "hermes"))
        self.bhcodex = ttk.Button(self.acts, text="Codex", command=lambda: self.wizard_step("harness", "codex"))
        self.bhclaude = ttk.Button(self.acts, text="Claude", command=lambda: self.wizard_step("harness", "claude"))
        self.chips = ttk.Frame(right); self.chips.pack(fill="both", expand=True, padx=12, pady=(0,10))

    def set_view(self, k):
        self.view = k; self.render()

    def paint_attach(self, text, fail=False):
        self.msg = text
        self.ast.configure(text=text, style="F.TLabel" if fail else "Ok.TLabel")

    def set_mode(self, mode):
        mode = (mode or "bare").strip() or "bare"
        self._attach_mode = mode
        if self.board and hasattr(self.board, "set_attach_mode"):
            try:
                res = self.board.set_attach_mode(mode)
            except Exception as e:
                res = {"ok": False, "error": str(e), "copy": "FAIL mode"}
            if res.get("ok"):
                self._attach_mode = res.get("mode") or mode
                self.paint_attach("using: "+self._attach_mode, False)
            else:
                nxt = res.get("next_step") or "select bare | orchestration | code-graph on Attach"
                detail = res.get("copy") or res.get("error") or "mode"
                self.paint_attach("FAIL mode — %s · %s" % (detail, nxt), True)
        else:
            self.paint_attach("using: "+self._attach_mode, False)
        if self.view == "loop":
            self.wizard_step("toolsets", self._attach_mode)
            return
        self.render()

    def wizard_step(self, step, value=""):
        self.paint_attach("wizard "+step+"…", False)
        def work():
            try:
                if self.board and hasattr(self.board, "wizard_apply"):
                    res = self.board.wizard_apply(step, value)
                else:
                    res = {"ok": False, "copy": "FAIL wizard", "error": "no board"}
            except Exception as e:
                res = {"ok": False, "copy": "FAIL wizard", "error": str(e)}
            self.root.after(0, lambda r=res: self.done_wizard(r, step))
        threading.Thread(target=work, daemon=True).start()

    def done_wizard(self, res, step=""):
        skip = str((res or {}).get("live") or "").upper() == "SKIP" or bool((res or {}).get("skipped"))
        if res.get("ok"):
            if res.get("mode"):
                self._attach_mode = res.get("mode")
            self.paint_attach(res.get("copy") or ("READY "+step), False)
        else:
            nxt = res.get("next_step") or "Launch env or ./pfy up"
            detail = res.get("copy") or res.get("error") or "wizard"
            if nxt and nxt not in str(detail):
                detail = "%s · %s" % (detail, nxt)
            self.paint_attach(detail if skip else ("FAIL wizard — %s" % detail), not skip)
        self.refresh()

    def launch_session(self):
        self.paint_attach("Launch session…", False)
        def work():
            try:
                if self.board and hasattr(self.board, "launch_wizard_session"):
                    res = self.board.launch_wizard_session()
                else:
                    res = {"ok": False, "copy": "FAIL launch", "error": "no board", "next_step": "complete wizard review (runtime · lane · toolsets · harness)"}
            except Exception as e:
                res = {"ok": False, "copy": "FAIL launch", "error": str(e)}
            self.root.after(0, lambda r=res: self.done_launch_session(r))
        threading.Thread(target=work, daemon=True).start()

    def done_launch_session(self, res):
        reach = str((res or {}).get("session_reach") or "").strip()
        if reach:
            self._session_reach = reach
        skip = str((res or {}).get("live") or "").upper() == "SKIP" or bool((res or {}).get("skipped"))
        if res.get("ok") and res.get("usable") is not False:
            pid = res.get("pid")
            hid = res.get("id") or res.get("harness") or ""
            msg = res.get("copy") or ("attached " + hid)
            if pid and ("pid" not in msg):
                msg += " pid %s" % pid
            if reach and reach not in msg:
                msg += " · " + reach
            self.paint_attach(msg, False)
        else:
            nxt = res.get("next_step") or "complete wizard review (runtime · lane · toolsets · harness)"
            detail = res.get("error") or res.get("copy") or "launch"
            if nxt and nxt not in str(detail):
                detail = "%s · %s" % (detail, nxt)
            self.paint_attach(detail if skip else ("FAIL Launch session — %s" % detail), not skip)
            if not reach:
                self._session_reach = "FAIL"
        self.refresh()

    def attach(self, hid):
        self.paint_attach("attaching "+hid+"…", False)
        mode = self._attach_mode or "bare"
        def work():
            try: snap = self.board.snapshot() if self.board else {}
            except Exception as e: snap, err = {}, str(e)
            else: err = ""
            active = str(snap.get("active") or "")
            if active in BLOCKED:
                res = {"ok": False, "copy": GROK_USE, "error": f"{active} is active — no grok/opencode fallback"}
            else:
                try:
                    if self.board:
                        res = self.board.start_sidecar(hid, mode=mode)
                    else:
                        res = {"ok": False, "copy": GROK_USE, "error": "no board"}
                except TypeError:
                    try: res = self.board.start_sidecar(hid) if self.board else {"ok": False, "copy": GROK_USE, "error": "no board"}
                    except Exception as e: res = {"ok": False, "copy": GROK_USE, "error": str(e) or err}
                except Exception as e: res = {"ok": False, "copy": GROK_USE, "error": str(e) or err}
            self.root.after(0, lambda: self.done(hid, res))
        threading.Thread(target=work, daemon=True).start()

    def done(self, hid, res):
        reach = str((res or {}).get("session_reach") or "").strip()
        if reach:
            self._session_reach = reach
        if res.get("ok") and res.get("usable") is not False:
            pid = res.get("pid")
            kind = "monitor" if res.get("role") == "monitor" else hid
            msg = f"attached {kind}" + (f" pid {pid}" if pid else "")
            if reach:
                msg += " · " + reach
            self.paint_attach(msg, False)
        else:
            nxt = res.get("next_step") or ""
            detail = res.get("error") or res.get("copy") or GROK_USE
            if nxt and nxt not in str(detail):
                detail = f"{detail} · {nxt}"
            self.paint_attach(f"FAIL Attach {hid} — {detail}", True)
            if hid in ("opencode", "hermes", "grok", "codex", "claude", "claude-code") and not reach:
                self._session_reach = "FAIL"
        self.refresh()


    def paint_si(self, text, fail=False):
        s