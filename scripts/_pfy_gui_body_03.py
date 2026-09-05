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

    def _clip(self, text, paint, ok_msg, fail_msg):
        if not text:
            paint(fail_msg, True)
            return
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            try:
                self.root.update_idletasks()
            except Exception:
                pass
            paint(ok_msg, False)
        except Exception:
            paint(fail_msg, True)

    def paint_si_open(self, text, fail=False):
        self.siopenst.configure(text=text, style="F.TLabel" if fail else "Ok.TLabel")
        self.msg = text

    def open_si_game(self):
        self.paint_si_open("opening game…", False)
        def work():
            try:
                res = self.board.open_space_invaders_game() if self.board else {"ok": False, "copy": "FAIL Open game · no board", "error": "no board"}
            except Exception as e:
                res = {"ok": False, "copy": "FAIL Open game", "error": str(e)}
            self.root.after(0, lambda: self.done_si_open(res))
        threading.Thread(target=work, daemon=True).start()

    def done_si_open(self, res):
        cur = dict(getattr(self, "_last_si", {}) or {})
        cur.update(res or {})
        self._last_si = cur
        if res.get("ok"):
            self.paint_si_open(res.get("copy") or "PASS Open game", False)
            if res.get("abs_path"):
                self.siabs.configure(text="abs " + str(res.get("abs_path") or ""))
            if res.get("rel") or res.get("path"):
                self.sirel.configure(text="rel " + str(res.get("rel") or res.get("path") or ""))
        else:
            self.paint_si_open(res.get("copy") or ("FAIL Open game · " + str(res.get("error") or "")), True)
        self.refresh(user=True)

    def open_si_folder(self):
        self.paint_si_open("opening folder…", False)
        def work():
            try:
                res = self.board.open_space_invaders_folder() if self.board else {"ok": False, "copy": "FAIL Open folder · no board", "error": "no board"}
            except Exception as e:
                res = {"ok": False, "copy": "FAIL Open folder", "error": str(e)}
            self.root.after(0, lambda: self.done_si_open(res))
        threading.Thread(target=work, daemon=True).start()

    def copy_si_task(self):
        self.paint_si_open("copying TASK…", False)
        def work():
            try:
                res = self.board.space_invaders_task() if self.board else {"ok": False, "copy": "FAIL Copy TASK · no board", "error": "no board", "task_text": ""}
            except Exception as e:
                res = {"ok": False, "copy": "FAIL Copy TASK", "error": str(e), "task_text": ""}
            self.root.after(0, lambda: self.done_si_task(res))
        threading.Thread(target=work, daemon=True).start()

    def done_si_task(self, res):
        text = str((res or {}).get("task_text") or (res or {}).get("value") or "")
        preview = text if len(text) <= 240 else text[:240] + "…"
        cur = dict(getattr(self, "_last_si", {}) or {})
        cur.update(res or {})
        if text:
            cur["task_text"] = text
        self._last_si = cur
        if preview:
            self.sitask.configure(text=preview)
        if not (res or {}).get("ok"):
            self.paint_si_open((res or {}).get("copy") or "FAIL Copy TASK", True)
            self.refresh(user=True)
            return
        self._clip(text, self.paint_si_open, res.get("copy") or "PASS Copy TASK", "FAIL clipboard — select TASK")
        self.refresh(user=True)

    def copy_endpoint(self):
        res = self._last_env or {}
        val = str(res.get("base_url") or "")
        if not val:
            for s in (res.get("next_steps") or []):
                if (s or {}).get("id") == "endpoint":
                    val = str(s.get("value") or "")
                    break
        self._clip(val, self.paint_env, "PASS Copy endpoint", "FAIL no endpoint" if not val else "FAIL clipboard — select endpoint")

    def copy_pfy_status(self):
        res = self._last_env or {}
        val = "./pfy status"
        for s in (res.get("next_steps") or []):
            if (s or {}).get("id") == "status" and s.get("value"):
                val = str(s.get("value"))
                break
        self._clip(val, self.paint_env, "PASS Copy ./pfy status", "FAIL clipboard — select status")

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