ate="normal")
        except Exception:
            pass
        if res.get("ok"):
            copy = res.get("copy") or ("SKIP env" if str(res.get("live") or "") == "SKIP" else "PASS env")
            if str(copy).startswith("SKIP"):
                self.est.configure(text=copy, style="M.TLabel")
            else:
                self.paint_env(copy, False)
        else:
            self.paint_env("FAIL " + (res.get("copy") or res.get("error") or "env"), True)
        self.refresh(user=True)

    def run_stage(self):
        self.paint_stage("running env-stage…", False)
        self.meta.configure(text="refreshing…")
        try:
            self.bstage.configure(state="disabled")
        except Exception:
            pass
        def work():
            try:
                if self.board is None:
                    res = {"ok": False, "copy": "FAIL env-stage", "error": "no board"}
                else:
                    res = self.board.run_stage()
            except Exception as e:
                res = {"ok": False, "copy": "FAIL env-stage", "error": str(e)}
            self.root.after(0, lambda r=res: self.done_stage(r))
        threading.Thread(target=work, daemon=True).start()

    def done_stage(self, res):
        try:
            self.bstage.configure(state="normal")
        except Exception:
            pass
        if res.get("ok"):
            copy = res.get("copy") or "PASS env-stage"
            if str(copy).startswith("SKIP"):
                self.sst.configure(text=copy, style="M.TLabel")
            else:
                self.paint_stage(copy, False)
        else:
            self.paint_stage("FAIL " + (res.get("copy") or res.get("error") or "env-stage"), True)
        self.refresh(user=True)

    def paint_refresh(self, text, fail=False, skip=False):
        style = "M.TLabel" if skip else ("F.TLabel" if fail else "Ok.TLabel")
        self.rst.configure(text=text, style=style)

    def refresh_now(self):
        if self.busy:
            self.paint_refresh("SKIP refresh", fail=False, skip=True)
        else:
            self.paint_refresh("refreshing…", False)
        self.refresh(user=True)

    def refresh(self, user=False):
        if self.board is None:
            if user:
                self.meta.configure(text="FAIL refresh")
                self.fail.configure(text="FAIL  " + GROK_USE)
                self.paint_refresh("FAIL refresh", True)
            return
        if self.busy:
            if user:
                self.pending_user = True
                self.meta.configure(text="refreshing…")
                try:
                    self.brefresh.configure(state="disabled")
                except Exception:
                    pass
            return
        self.busy = True
        if user:
            self.meta.configure(text="refreshing…")
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
                    line = "PASS refr