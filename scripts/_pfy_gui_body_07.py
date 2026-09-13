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

    def paint_catalog(self, text, fail=False):
        self.catst.configure(text=text, style="F.TLabel" if fail else "Ok.TLabel")
        self.msg = text

    def catalog_ask(self):
        try:
            name = (self.catname.get() or "").strip()
        except Exception:
            name = ""
        self.paint_catalog("asking…", False)
        def work():
            try:
                if self.board is None:
                    res = {"ok": False, "copy": "FAIL ask", "error": "no board"}
                else:
                    res = self.board.catalog_ask(name)
            except Exception as e:
                res = {"ok": False, "copy": "FAIL ask", "error": str(e)}
            self.root.after(0, lambda r=res: self.done_catalog(r, "ask"))
        threading.Thread(target=work, daemon=True).start()

    def catalog_queue(self):
        try:
            name = (self.catname.get() or "").strip()
        except Exception:
            name = ""
        self.paint_catalog("queueing…", False)
        def work():
            try:
                if self.board is None:
                    res = {"ok": False, "copy": "FAIL queue", "error": "no board"}
                else:
                    res = self.board.catalog_queue(name)
            except Exception as e:
                res = {"ok": False, "copy": "FAIL queue", "error": str(e)}
            self.root.after(0, lambda r=res: self.done_catalog(r, "queue"))
        threading.Thread(target=work, daemon=True).start()

    def done_catalog(self, res, kind="ask"):
        if res.get("ok"):
            self.paint_catalog(res.get("copy") or ("PASS " + kind), False)
            prompt = res.get("prompt") or ""
            if prompt:
                self._catalog_prompt = prompt
        else:
            nxt = res.get("next_step") or ""
            copy = res.get("copy") or res.get("error") or kind
            msg = str(copy)
            if nxt and nxt not in msg:
                msg = msg + " · next: " + nxt
            live = str(res.get("live") or "")
            if live == "SKIP" or msg.startswith("SKIP"):
                self.catst.configure(text=msg if msg.startswith("SKIP") else ("SKIP " + msg), style="M.TLabel")
                self.msg = msg
            else:
                self.paint_catalog("FAIL " + msg if not (msg.startswith("FAIL") or msg.startswith("SKIP")) else msg, True)
        self.refresh(user=True)

    def copy_catalog_prompt(self):
        prompt = str(getattr(self, "_catalog_prompt", "") or (self.snap or {}).get("catalog_prompt") or "")
        if not prompt:
            self.paint_catalog("FAIL no prompt — Ask TUI implement first", True)
            return
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(prompt)
            self.paint_catalog("PASS copied", False)
        except Exception:
            self.paint_catalog("FAIL clipboard — select the prompt", True)

    def pack_acts(self, names):
        forget = [self.bgrok, self.bopen, self.bhermes, self.bcodex, self.bclaude, self.bbare, self.borch, self.bgraph, self.bsi, self.bsiopen, self.bsifold, self.bsitask, self.bcopyep, self.bcopyst, self.brefresh, self.bcopy, self.bstage, self.benv, self.bpull, self.btest, self.breco, self.btry, self.pullname, self.sst, self.est, self.pst, self.rst, self.tst, self.ast, self.cst, self.sist, self.siabs, self.sirel, self.sitask, self.ewhat, self.siopenst, self.toolst, self.recst, self.tryst, self.catname, self.bask, self.bqueue, self.bcatcopy, self.catst]
        forget.extend(self.tool_btns.values())
        for w in forget:
            try: w.pack_forget()
            except Exception: pass
        order = {
            "grok": self.bgrok, "open": self.bopen, "hermes": self.bhermes, "codex": self.bcodex, "claude": self.bclaude,
            "bare": self.bbare, "orch": self.borch, "graph": self.bgraph,
            "si": self.bsi, "refresh": self.brefresh,
            "copy": self.bcopy, "stage": self.bstage, "env": self.benv,
            "pull": self.bpull, "pullname": self.pullname, "pst": self.pst,
            "test": self.btest, "tst": self.tst, "rst": self.rst,
            "reco": self.breco, "try": self.btry, "recst": self.recst, "tryst": self.tryst,
            "catname": self.catname, "ask": self.bask, "queue": self.bqueue, "catcopy": self.bcatcopy, "catst": self.catst,
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
        self.bhermes.configure(state="disabled" if stub else "normal")
        self.bcodex.configure(state="disabled" if stub else "normal")
        self.bclaude.configure(state="disabled" if stub else "normal")
        self.bsi.configure(state="disabled" if stub else "normal")
        self.fail.configure(text=(f"FAIL  {s.get('blocked_copy') or GROK_USE}") if stub else "")
        show_org = (not s.get("agent_lane_collapsed", True)) and bool(s.get("org_messages"))
        if show_org: self.nav["org"].pack(fill="x")
        else:
            self.nav["org"].pa