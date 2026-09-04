n(self.acts, text="Test model", command=self.test_model)
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
        if res.get("ok"):
            pid = res.get("pid")
            kind = "monitor" if res.get("role") == "monitor" else hid
            self.paint_attach(f"attached {kind}" + (f" pid {pid}" if pid else ""), False)
        else:
            detail = res.get("error") or res.get("copy") or GROK_USE
            self.paint_attach(f"FAIL Attach {hid} — {detail}", True)
        self.refresh()

    def paint_copy(self, text, fail=False):
        self.msg = text
        style = "F.TLabel" if fail else "Ok.TLabel"
        self.cst.configure(text=text, style=style)
        self.ast.configure(text=text, style=style)

    def stub_line(self):
        s = self.snap or {}
        if s.get("active_stub") or str(s.get("active") or "") in BLOCKED:
            return s.get("blocked_copy") or GROK_USE
        chips = s.get("chips") or []
        active_id = s.get("active")
        active = next((c for c in chips if c.get("id") == active_id), None)
        stubish = ("stub", "detected-stub", "missing")
        def is_stubish(c):
            return honest(c.get("live")) in stubish
        c = active if active and is_stubish(active) else next(
            (x for x in chips if is_stubish(x) and (x.get("one_liner") or x.get("startable") is False)),
            None,
        )
        if not c:
            return ""
        return c.get("one_liner") or ("./pfy start " + str(c.get("id") or ""))

    def copy_stub(self):
        self.paint_copy("copying…", False)
        line = self.stub_line()
        if not line:
            self.paint_copy("FAIL no stub one-liner", True)
            return
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(line)
            try:
                self.root.update_idletasks()
            except Exception:
                pass
       