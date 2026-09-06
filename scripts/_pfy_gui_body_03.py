elf.msg = text
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
        self._last_si = res or {}
        if res.get("ok"):
            self.paint_si(res.get("copy") or ("PASS Space Invaders · " + str(res.get("path") or "")), False)
            self.siabs.configure(text="abs " + str(res.get("abs_path") or ""))
            self.sirel.configure(text="rel " + str(res.get("rel") or res.get("path") or ""))
            preview = str(res.get("task_text") or res.get("task_md") or "")
            if len(preview) > 240:
                preview = preview[:240] + "…"
            self.sitask.configure(text=preview)
        else:
            self.paint_si(res.get("copy") or ("FAIL Space Invaders · " + str(res.get("error") or "")), True)
        self.refresh(user=True)

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