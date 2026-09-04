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


    def paint_si(self, text, fail=False):
        self.msg = text
        style = "F.TLabel" if fail else "Ok.TLabel"
        self.sist.configure(text=text, style=style)
        self.ast.configure(text=text, style=style)

    def space_invaders(self):
        self.paint_si("Space Invaders…", False)
        def work():
            try:
                res = self.board.run_space_invaders() if self.board else {"ok": False, "copy": "FAIL Space Invaders · no board", "error": "no board"}
            except Exception as e:
                res = {"ok": False, "copy": "FAIL Space Invaders", "error": str(e)}
            self.root.after(0, lambda: self.done_si(res))
        threading.Thread(target=work, daemon=True).start()

    def done_si(self, res):
        if res.get("ok"):
            self.paint_si(res.get("copy") or ("PASS Space Invaders · " + str(res.get("path") or "")), False)
        else:
            self.paint_si(res.get("copy") or ("FAIL Space Invaders · " + str(res.get("error") or "")), True)
        self.refresh(user=True)

    def paint_copy(self, text, fail=False):
        self.msg = text
        style = "F.TLabel" if fail else "Ok.TLabel"
        self.cst.configure(text=text, style=style)
        self.ast.configure(text=text, style="