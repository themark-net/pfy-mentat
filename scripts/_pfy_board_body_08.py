s=%s" % (key, val))
    path.write_text("\n".join(out) + "\n", encoding="utf-8")

def patch_toml_section_enabled(path, section, enabled):
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    header = "[" + section + "]"
    if header not in text:
        return False
    parts = text.split(header, 1)
    body = parts[1]
    nxt = body.find("\n[")
    chunk, rest = (body[:nxt], body[nxt:]) if nxt >= 0 else (body, "")
    if "enabled = true" in chunk or "enabled = false" in chunk:
        chunk = chunk.replace("enabled = true", "enabled = " + ("true" if enabled else "false"), 1)
        if enabled:
            chunk = chunk.replace("enabled = false", "enabled = true", 1)
        else:
            chunk = chunk.replace("enabled = true", "enabled = false", 1)
    else:
        chunk = chunk.rstrip() + "\nenabled = " + ("true" if enabled else "false") + "\n"
    path.write_text(parts[0] + header + chunk + rest, encoding="utf-8")
    return True

def apply_mcp(want):
    if want:
        if not MCP_FRAGMENT.is_file():
            return False, "mcp recipe missing"
        if not MERGE_PY.is_file():
            return False, "mcp merge missing"
        STATE.mkdir(parents=True, exist_ok=True)
        targets = [STATE_GROK, grok_config_path()]
        last_err = ""
        applied = False
        for dest in targets:
            dest.parent.mkdir(parents=True, exist_ok=True)
            rc, out = _run(["python3", str(MERGE_PY), "--config", str(dest), "--no-backup"], timeout=20.0)
            if rc != 0:
                last_err = (out or "mcp merge failed")[-300:]
                continue
            text = dest.read_text(encoding="utf-8", errors="replace") if dest.is_file() else ""
            if "mcp_servers.codebase-memory" not in text:
                last_err = "mcp not in config"
                continue
            applied = True
        if not applied:
            return False, last_err or "mcp merge failed"
        return True, ""
    for dest in (STATE_GROK, grok_config_path()):
        patch_toml_section_enabled(dest, "mcp_servers.codebase-memory", False)
    return True, ""

def apply_write_guard(want):
    wg = write_guard_root()
    if want:
        if wg is None or not (wg / "src" / "write_guard").is_dir():
            return False, "write-guard missing"
        if not WG_OVERLAY.is_file():
            return False, "write-guard overlay missing"
        STATE.mkdir(parents=True, exist_ok=True)
        overlay = WG_OVERLAY.read_text(encoding="utf-8")
        overlay = overlay.replace("enabled: false", "enabled: true").replace("WRITE_GUARD_MODE: audit", "WRITE_GUARD_MODE: enforce")
        overlay = overlay.replace("PYTHONPATH: /workspace/.venvs/write-guard-smoke/lib/python3.12/site-packages", "PYTHONPATH: " + str(wg / "src"))
        overlay = overlay.replace("WRITE_GUARD_ROOTS: /workspace", "WRITE_GUARD_ROOTS: " + str(ROOT))
        (STATE / "mcp-servers.write-guard.yaml").write_text(overlay, encoding="utf-8")
        cage = Path.home() / ".agentcage"
        try:
            cage.mkdir(parents=True, exist_ok=True)
            (cage / "mcp-servers.write-guard.yaml").write_text(overlay, encoding="utf-8")
        except OSError:
            pass
        gpath = grok_config_path()
        block = (
            "\n[mcp_servers.write-guard]\n"
            'command = "python3"\n'
            'args = ["-m", "write_guard", "serve"]\n'
            "enabled = true\n"
        )
        for dest in (STATE_GROK, gpath):
            dest.parent.mkdir(parents=True, exist_ok=True)
            cur = dest.read_text(encoding="utf-8") if dest.is_file() else ""
            if "[mcp_servers.write-guard]" not in cur:
                dest.write_text(cur.rstrip() + block + "\n", encoding="utf-8")
            else:
                patch_toml_section_enabled(dest, "mcp_servers.write-guard", True)
        env = os.environ.copy()
        env["PYTHONPATH"] = str(wg / "src") + os.pathsep + env.get("PYTHONPAT