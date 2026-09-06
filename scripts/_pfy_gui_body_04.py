
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
        # #175: FreeToken-first live base — not Launch env pin
        nxt = "Launch env or ./pfy up"
        val = ""
        try:
            if self.board is not None and hasattr(self.board, "live_openai_base"):
                base, _det = self.board.live_openai_base()
                val = str(base or "").strip()
        except Exception:
            val = ""
        if not val:
            s = getattr(self, "snap", None) or {}
            u = s.get("usage") if isinstance(s.get("usage"), dict) else {}
            if u and u.get("ok") is False:
                nxt = str(u.get("next_step") or nxt)
                self.paint_env("FAIL copy · next: " + nxt, True)
                return
            if u and u.get("ok") is not False:
                val = str(u.get("endpoint") or "").strip()
            if not val or val == "(none)":
                d = s.get("detector") or {}
                sr = s.get("status_runtime") or {}
                st = str(d.get("status") or sr.get("status") or "").strip().lower()
                base = str(d.get("base_url") or sr.get("base_url") or sr.get("endpoint") or "").strip()
                if st == "ready" and base and base != "(none)":
                    val = base
                    if not val.rstrip("/").endswith("/v1"):
                        val = val.rstrip("/") + "/v1"
        if not val or val == "(none)":
            self.paint_env("FAIL copy · next: " + nxt, True)
            return
        self._clip(val, self.paint_env, "PASS copied", "FAIL copy")

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
     