    want = not self.tool_on(tid)
        self.paint_tools("toggling…", False)
        def work():
            try:
                if self.board is None:
                    res = {"ok": False, "copy": "FAIL tools", "error": "no board"}
                else:
                    res = self.board.set_tool(tid, want)
            except Exception as e:
                res = {"ok": False, "copy": "FAIL tools", "error": str(e)}
            self.root.after(0, lambda r=res: self.done_tool(r))
        threading.Thread(target=work, daemon=True).start()

    def done_tool(self, res):
        if res.get("ok"):
            self.paint_tools(res.get("copy") or "PASS tools", False)
        else:
            self.paint_tools("FAIL " + (res.get("copy") or res.get("error") or "tools"), True)
        self.refresh(user=True)

    def pack_acts(self, names):
        forget = [self.bgrok, self.bopen, self.brefresh, self.bcopy, self.bstage, self.benv, self.bpull, self.btest, self.pullname, self.sst, self.est, self.pst, self.tst, self.ast, self.cst, self.toolst]
        forget.extend(self.tool_btns.values())
        for w in forget:
            try: w.pack_forget()
            except Exception: pass
        order = {
            "grok": self.bgrok, "open": self.bopen, "refresh": self.brefresh,
            "copy": self.bcopy, "stage": self.bstage, "env": self.benv,
            "pull": self.bpull, "pullname": self.pullname, "pst": self.pst,
            "test": self.btest, "tst": self.tst,
            "sst": self.sst, "est": self.est, "ast": self.ast, "cst": self.cst,
        }
        for n in names:
            w = order[n]
            w.pack(side="left", padx=(0, 8))

    def render(self):
        tk = sys.modules["tkinter"]; s = self.snap
        if s.get("error") and not s.get("chips"):
            self.meta.configure(text=str(s.get("error"))); return
        self.meta.configure(text=" · ".join(x for x in (s.get("host") or "", s.get("profile") or "", s.get("ts") or "") if x))
        d, r = s.get("detector") or {}, s.get("status_runtime") or {}
        eng_live = honest(s.get("engine_live") or d.get("status"))
        engine = d.get("engine") or r.get("engine") or "none"
        chips = s.get("chips") or []
        grok = next((c for c in chips if c.get("id")=="grok"), {}) or {}
        tape = s.get("tape") or []
        stub = bool(s.get("active_stub")) or str(s.get("active") or "") in BLOCKED
        self.bgrok.configure(state="disabled" if stub else "normal")
        self.bopen.configure(state="disabled" if stub else "normal")
        self.fail.configure(text=(f"FAIL  {s.get('blocked_copy') or GROK_USE}") if stub else "")
        show_org = (not s.get("agent_lane_collapsed", True)) and bool(s.get("org_messages"))
        if show_org: self.nav["org"].pack(fill="x")
        else:
            self.nav["org"].pack_forget()
            if self.view == "org": self.view = "loop"
        for k,b in self.nav.items():
            b.configure(bg="#243041" if k==self.view else SIDE)
        attached = s.get("active") or "(none)"; verb = (s.get("last_verb") or {}).get("verb") or "(none)"
        if verb in ("env", "launch-env"):
            verb = "Launch env"
        when = (s.get("last_verb") or {}).get("when") or ""
        pid = s.get("sidecar_pid") or ""
        att = attached + (f" pid {pid}" if pid else "")
        stage = next((t for t in tape if t.get("id")=="env-stage"), {}) or {}
        inf = next((t for t in tape if t.get("id")=="inference"), {}) or {}
        lives = [str(inf.get("live") or "SKIP").upper(), str(stage.get("live") or "SKIP").upper()]
        if "FAIL" in lives:
            env_live = "FAIL"
        elif "READY" in lives:
            env_live = "READY"
        else:
            env_live = "SKIP"
        if self.view == "loop":
            note = s.get("monitor_note") or ""
            mpid = s.get("monitor_pid") or ""
            mon = note or (f"pid {mpid}" if mpid else "(none)")
            gpath = s.get("grok_path") or honest(gr