eta.configure(text="refreshing…")
            self.paint_refresh("refreshing…", False)
            try:
                self.brefresh.configure(state="disabled")
            except Exception:
                pass
        def work():
            try:
                snap = self.board.snapshot()
            except Exception as e:
                snap = {"error": str(e)}
            self.root.after(0, lambda s=snap, u=user: self.apply(s, user=u))
        threading.Thread(target=work, daemon=True).start()

    def apply(self, s, user=False):
        pending = self.pending_user
        self.pending_user = False
        self.busy = False
        try:
            self.brefresh.configure(state="normal")
        except Exception:
            pass
        self.snap = s or {}
        self.render()
        if user:
            err = self.snap.get("error") and not (self.snap.get("chips") or [])
            if err:
                self.paint_refresh("FAIL refresh", True)
                self.meta.configure(text="FAIL refresh")
            else:
                ts = self.snap.get("ts") or ""
                host = self.snap.get("host") or ""
                if ts:
                    line = "PASS refresh · " + " · ".join(x for x in (host, ts) if x)
                    self.paint_refresh(line, False)
                    self.meta.configure(text=" · ".join(x for x in (host, self.snap.get("profile") or "", ts) if x))
                else:
                    self.paint_refresh("PASS refresh · refreshed", False)
                    cur = str(self.meta.cget("text") or "")
                    if "refreshed" not in cur:
                        self.meta.configure(text=(cur + " · refreshed").strip(" ·"))
        if pending:
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
 