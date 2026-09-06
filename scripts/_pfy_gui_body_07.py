   self.refresh(user=True)

    def paint_tools(self, text, fail=False):
        self.toolst.configure(text=text, style="F.TLabel" if fail else "Ok.TLabel")
        self.msg = text

    def tool_on(self, tid):
        tools = (self.snap or {}).get("tools") or {}
        if tid == "mcp":
            return bool(tools.get("mcp"))
        if tid == "write-guard":
            return bool(tools.get("write_guard"))
        if tid == "extra-tools":
            return (tools.get("tools_mode") or "") == "local_tools"
        return bool((tools.get("skills") or {}).get(tid))

    def toggle_tool(self, tid):
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
        forget = [self.bgrok, self.bopen, self.bsi, self.bsiopen, self.bsifold, self.bsitask, self.bcopyep, self.bcopyst, self.brefresh, self.bcopy, self.bstage, self.benv, self.bpull, self.btest, self.pullname, self.sst, self.est, self.pst, self.rst, self.tst, self.ast, self.cst, self.sist, self.siabs, self.sirel, self.sitask, self.ewhat, self.siopenst, self.toolst]
        forget.extend(self.tool_btns.values())
        for w in forget:
            try: w.pack_forget()
            except Exception: pass
        order = {
            "grok": self.bgrok, "open": self.bopen, "si": self.bsi, "refresh": self.brefresh,
            "copy": self.bcopy, "stage": self.bstage, "env": self.benv,
            "pull": self.bpull, "pullname": self.pullname, "pst": self.pst,
            "test": self.btest, "tst": self.tst, "rst": self.rst,
            "sst": self.sst, "est": self.est, "ast": self.ast, "cst": self.cst, "sist": self.sist,
            "siopen": self.bsiopen, "sifold": self.bsifold, "sitask": self.bsitask,
            "copyep": self.bcopyep, "copyst": self.bcopyst,
            "siabs": self.siabs, "sirel": self.sirel, "sitxt": self.sitask, "ewhat": self.ewhat, "siopenst": self.siopenst,
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
        self.bsi.configure(state="disabled" if stub else "normal")
        self.fail.configure(text=(f"FAIL  {s.get('blocked_copy') or GROK_USE}") if stub else "")
        show_org = (not s.get("agent_lane_collapsed", True)) and bool(s.get("org_messages"))
        if show_org: self.nav["org"].pack(fill="x")
        else:
            self.nav["org"].pa