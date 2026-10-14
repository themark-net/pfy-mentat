"""Codex adapter. Skills always live in ~/.agents/skills. No launch()."""
# resolution follows morluto/rea SupportedClients, MIT
from __future__ import annotations

import os
from pathlib import Path

from .base import Adapter, render_toml_mcp


class CodexAdapter(Adapter):
    id = "codex"
    config_kind = "toml"

    def _home(self) -> Path:
        env = os.environ.get("CODEX_HOME")
        if env:
            return Path(env).expanduser()
        return Path.home() / ".codex"

    def marker_dir(self) -> Path:
        return self._home()

    def config_path(self) -> Path:
        return self._home() / "config.toml"

    def skills_dir(self) -> Path:
        # Shared with OpenCode. Not under CODEX_HOME.
        return Path.home() / ".agents" / "skills"

    def render_config(self, current: bytes | None, item_id: str, entry: dict) -> bytes:
        return render_toml_mcp(current, item_id, entry)
