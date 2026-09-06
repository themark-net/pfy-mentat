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
        self.chips = ttk.Frame(right); self.chips.pack(fill="both", expand=True, padx=12, pady=(0,10))

    def set_view(self, k):
        self.view = k; self.render()

    def paint_attach(self, text, fail=False):
        self.msg = text
        self.ast.configure(text=text, style="F.TLabel" if fail else "Ok.TLabel")

    def attach(self, hid):
        self.paint_attach("attaching "+hid+"…", False)
        def work():
            try: snap = self.board.snapshot() if self.board else {}
            except Exception as e: snap, err = {}, str(e)
            else: err = ""
            active = str(snap.get("active") or "")
            if active in BLOCKED:
                res = {"ok": False, "copy": GROK_USE, "error": f"{active} is active — no grok/opencode fallback"}
            else:
                try: res = self.board.start_sidecar(hid) if self.board else {"ok": False, "copy": GROK_USE, "error": "no board"}
                except Exception as e: res = {"ok": False, "copy": GROK_USE, "error": str(e) or err}
            self.root.after(0, lambda: self.done(hid, res))
        threading.Thread(target=work, daemon=True).start()

    def done(self, hid, res):
        reach = str((res or {}).get("session_reach") or "").strip()
        if reach:
            self._session_reach = reach
        if res.get("ok"):
            pid = res.get("pid")
            kind = "monitor" if res.get("role") == "monitor" else hid
            msg = f"attached {kind}" + (f" pid {pid}" if pid else "")
            if reach:
                msg += " · " + reach
            self.paint_attach(msg, False)
        else:
            detail = res.get("error") or res.get("copy") or GROK_USE
            self.paint_attach(f"FAIL Attach {hid} — {detail}", True)
            if hid == "opencode" and not reach:
                self._session_reach = "FAIL"
        self.refresh()


    def paint_si(self, text, fail=False):
        s