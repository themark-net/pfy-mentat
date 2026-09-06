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
            self.bpull.configure(state="normal")
        except Exception:
            pass
        if res.get("ok"):
            copy = res.get("copy") or "PASS pull"
            self.paint_pull(copy, False)
        else:
            self.paint_pull("FAIL " + (res.get("copy") or res.get("error") or "pull"), True)
        self.refresh(user=True)

    def paint_env(self, text, fail=False):
        self.est.configure(text=text, style="F.TLabel" if fail else "Ok.TLabel")

    def launch_env(self):
        self.paint_env("launching env…", False)
        self.meta.configure(text="refreshing…")
        try:
            self.benv.configure(state="disabled")
        except Exception:
            pass
        def work():
            try:
                if self.board is None:
                    res = {"ok": False, "copy": "FAIL env", "error": "no board"}
                else:
                    res = self.board.launch_env()
            except Exception as e:
                res = {"ok": False, "copy": "FAIL env", "error": str(e)}
            self.root.after(0, lambda r=res: self.done_env(r))
        threading.Thread(target=work, daemon=True).start()

    def done_env(self, res):
        try:
            self.benv.configure(state="normal")
        except Exception:
            pass
        self._last_env = res or {}
        reach = str((res or {}).get("session_reach") or "").strip()
        if reach:
            self._session_reach = reach
        what = str((res or {}).get("what") or "")
        if what:
            self.ewhat.configure(text=what)
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
        sel