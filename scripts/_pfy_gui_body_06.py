["org"].pack_forget()
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
            if stub: txt += f"\nFAIL       {s.get('blocked_copy') or GROK_USE}"
            if self.msg: txt += "\n" + self.msg
            self.pack_acts(["env", "open", "grok", "est", "ast"])
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
            if stub: txt += f"\nFAIL    {s.get('blocked_copy') or GROK_USE}"
            if self.msg: txt += "\n" + self.msg
            self.pack_acts(["grok", "open", "copy", "ast", "cst"])
        elif self.view == "tools":
            tools = s.get("tools") or {}
            skills = tools.get("skills") or {}
            def onoff(v):
                return "on" if v else "off"
            extra = onoff((tools.get("tools_mode") or "") == "local_tools")
            txt = (
                "TOOLS\n"
                f"one-shot         {onoff(skills.get('one-shot'))}\n"
                f"investigate      {onoff(skills.get('investigate'))}\n"
                f"agent-loops      {onoff(skills.get('agent-loops'))}\n"
                f"hermes-feedback  {onoff(skills.get('hermes-feedback'))}\n"
                f"mcp              {onoff(tools.get('mcp'))}\n"
                f"write-guard      {onoff(tools.get('write_guard'))}\n"
                f"extra tools      {extra}"
            )
            if self.msg: txt += "\n" + self.msg
            self.pack_acts([])
            for w in self.tool_btns.values():
                w.pack(side="left", padx=(0, 8))
            self.toolst.pack(side="left", padx=(0, 8))
        else:
            rows = s.get("org_messages") or []
            txt = "no org loop" if not rows else "ORG\n" + "\n".join(f"{m.get('from')} → {m.get('to')}  {m.get('state') or ''}" for m in rows)
            self.pack_acts([])
        self.body.configure(text=txt)
        for c in self.chips.winfo_children(): c.destroy()
        if self.view == "attach":
            for c in chips:
                hid, live, role, name = c.get("id") or "", honest(c.get("live")), c.get("role") or "", c.get("name") or ""
                fr = tk.Frame(self.chips, bg="#18202c", highlightbackground="#243041", highligh