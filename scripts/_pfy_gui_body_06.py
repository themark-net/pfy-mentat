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
            gpath = s.get("grok_path") or honest(grok.get("live"))
            txt = f"LOOP\nenv        {env_live}\nattached   {att}\nlast       {verb}  {when}\nmonitor    {mon}\ngrok       {gpath}"
            what = str((getattr(self, "_last_env", {}) or {}).get("what") or "")
            if what:
                txt += "\nwhat       " + what
            if stub: txt += f"\nFAIL       {s.get('blocked_copy') or GROK_USE}"
            if self.msg: txt += "\n" + self.msg
            self.pack_acts(["env", "copyep", "copyst", "open", "grok", "est", "ast"])
        elif self.view == "engine":
            models = s.get("models") or []
            mtxt = " · ".join(str(x) for x in models) if models else "(none)"
            txt = f"ENGINE\nengine     {engine}\nlive       {eng_live}\ngrok       {honest(grok.get('live'))}\nmodels     {mtxt}"
            self.pack_acts(["refresh", "test", "pullname", "pull", "tst", "pst", "rst"])
        elif self.view == "stage":
            sl = stage.get("live") or "SKIP"
            txt = f"STAGE\nenv-stage   {sl}"
            self.pack_acts(["stage", "sst"])
        elif self.view == "attach":
            txt = f"ATTACH\nNOW     attached {attached} · last {verb}"
            si = getattr(self, "_last_si", {}) or {}
            abs_p = str(si.get("abs_path") or "")
            rel_p = str(si.get("rel") or si.get("path") or "")
            task_p = str(si.get("task_text") or si.get("task_md") or "")
            if abs_p or rel_p or task_p:
                if abs_p:
                    txt += "\nabs       " + abs_p
                if rel_p:
                    txt += "\nrel       " + rel_p
                if task_p:
                    prev = task_p if len(task_p) <= 320 else task_p[:320] + "…"
                    txt += "\nTASK      " + prev.replace("\n", " / ")
                txt += "\nnote      Session proof: Attach OpenCode + disk artifact — not a board-hosted game"
            if stub: txt += f"\nFAIL    {s.get('blocked_copy') or GROK_USE}"
            if self.msg: txt += "\n" + self.msg
            # Buttons only (no path labels in the side pack — they clipped off-screen)
            self.pack_acts(["si", "siopen", "sifold", "sitask", "grok", "open", "copy", "ast", "sist", "cst"])
        elif self.view == "tools":
            tools = s.get("tools") or {}
            skills = tools.get("skills") or {}
            def onoff(v):
                return "on" if v else "off"
            extra = onoff((tools.get("tools_mode") or "") == "local_tools")
            txt = (
           