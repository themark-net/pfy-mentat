style)

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
            self.paint_copy("PASS copied", False)
        except Exception:
            self.paint_copy("FAIL clipboard — select the one-liner", True)

    def paint_stage(self, text, fail=False):
        self.sst.configure(text=text, style="F.TLabel" if fail else "Ok.TLabel")

    def paint_eval(self, text, fail=False):
        self.tst.configure(text=text, style="F.TLabel" if fail else "Ok.TLabel")

    def test_model(self):
        self.paint_eval("testing…", False)
        self.meta.configure(text="refreshing…")
        try:
            self.btest.configure(state="disabled")
        except Exception:
            pass
        def work():
            try:
                if self.board is None:
                    res = {"ok": False, "copy": "FAIL eval", "error": "no board"}
                else:
                    res = self.board.test_model()
            except Exception as e:
                res = {"ok": False, "copy": "FAIL eval", "error": str(e)}
            self.root.after(0, lambda r=res: self.done_eval(r))
        threading.Thread(target=work, daemon=True).start()

    def done_eval(self, res):
        try:
            self.btest.configure(state="normal")
        except Exception:
            pass
        if res.get("ok"):
            copy = res.get("copy") or "PASS eval"
            if str(copy).startswith("SKIP"):
                self.tst.configure(text=copy, style="M.TLabel")
            elif str(copy).startswith("FAIL"):
                self.paint_eval(copy, True)
            else:
                self.paint_eval(copy, False)
        else:
            self.paint_eval("FAIL " + (res.get("copy") or res.get("error") or "eval"), True)
        self.refresh(user=True)

    def paint_pull(self, text, fail=False):
        self.pst.configure(text=text, style="F.TLabel" if fail else "Ok.TLabel")

    def pull_model(self):
        try:
            name = (self.pullname.get() or "").strip()
        except Exception:
            name = ""
        if not name:
            self.paint_pull("FAIL pull", True)
            return
        self.paint_pull("pulling…", False)
        self.meta.configure(text="refreshing…")
        try:
            self.bpull.configure(state="disabled")
        except Exception:
            pass
        def work():
            try:
                if self.board is None:
                    res = {"ok": False, "copy": "FAIL pull", "error": "no board"}
                else:
                    res = self.board.pull_model(name)
            except Exception as e:
                res = {"ok": False, "copy": "FAIL pull", "error": str(e)}
            self.root.after(0, lambda r=res: self.done_pull(r))
        threading.Thread(target=work, daemon=True).start()

    def done_pull(self, res):
        try:
            self.bpull.configure(