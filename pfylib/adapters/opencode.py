"""OpenCode adapter. Skills always live in ~/.agents/skills. No launch()."""
# resolution follows morluto/rea SupportedClients, MIT
from __future__ import annotations

import os
from pathlib import Path

from .base import Adapter, render_json_mcp


def _parent(data: dict) -> dict:
    """V2 when mcp.servers exists; otherwise V1 mcp.<name>."""
    mcp = data.get("mcp")
    if not isinstance(mcp, dict):
        mcp = {}
        data["mcp"] = mcp
    servers = mcp.get("servers")
    if isinstance(servers, dict):
        return servers
    return mcp


class OpenCodeAdapter(Adapter):
    id = "opencode"
    config_kind = "json"

    def config_path(self) -> Path:
        env = os.environ.get("OPENCODE_CONFIG_DIR")
        if env:
            return Path(env).expanduser() / "opencode.json"
        xdg = os.environ.get("XDG_CONFIG_HOME")
        if xdg:
            return Path(xdg).expanduser() / "opencode" / "opencode.json"
        return Path.home() / ".config" / "opencode" / "opencode.json"

    def marker_dir(self) -> Path:
        return self.config_path().parent

    def skills_dir(self) -> Path:
        # Shared with Codex. Copying twice in one run is idempotent.
        return Path.home() / ".agents" / "skills"

    def render_config(self, current: bytes | None, item_id: str, entry: dict) -> bytes:
        return render_json_mcp(current, item_id, entry, _parent)
