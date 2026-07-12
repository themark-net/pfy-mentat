"""MCP stdio server: mediated read/write/list/delete under policy."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from write_guard.audit import append_event, tail_events
from write_guard.policy import decide, load_policy, resolve_mode, resolve_roots


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def build_mcp():
    """Build FastMCP app (requires mcp package)."""
    from mcp.server.fastmcp import FastMCP

    policy = load_policy()
    mode = resolve_mode(policy)
    roots = resolve_roots(policy)
    mcp = FastMCP("write-guard")

    def _audit(op: str, path: str, allow: bool, reason: str, **extra):
        if mode == "off":
            return
        append_event(
            policy.audit_log,
            op=op,
            path=path,
            allow=allow,
            reason=reason,
            mode=mode,
            extra=extra or None,
        )

    @mcp.tool()
    def list_roots() -> str:
        """List configured write-guard roots and mode."""
        return f"mode={mode} roots={roots} audit_log={policy.audit_log}"

    @mcp.tool()
    def write_status(limit: int = 20) -> str:
        """Return last N audit events (paths only, no file bodies)."""
        events = tail_events(policy.audit_log, n=max(1, min(limit, 100)))
        import json

        return json.dumps(events, indent=2)

    @mcp.tool()
    def list_dir(path: str) -> str:
        """List directory entries under roots."""
        d = decide(path, op="list", mode=mode, policy=policy, roots=roots)
        _audit("list_dir", d.path, d.allow, d.reason)
        if not d.allow:
            return f"DENIED: {d.reason}"
        p = Path(path)
        if not p.is_dir():
            return f"ERROR: not a directory: {path}"
        names = sorted(os.listdir(p))[:500]
        return "\n".join(names) if names else "(empty)"

    @mcp.tool()
    def read_file(path: str) -> str:
        """Read a text file under roots (secrets globs still readable in audit)."""
        d = decide(path, op="read", mode=mode, policy=policy, roots=roots)
        _audit("read_file", d.path, d.allow, d.reason)
        if not d.allow:
            return f"DENIED: {d.reason}"
        p = Path(path)
        if not p.is_file():
            return f"ERROR: not a file: {path}"
        # size cap 2 MiB
        data = p.read_bytes()
        if len(data) > 2 * 1024 * 1024:
            return "ERROR: file too large (>2MiB)"
        return data.decode("utf-8", errors="replace")

    @mcp.tool()
    def write_file(path: str, content: str) -> str:
        """Write text file if policy allows (audit logs always when mode!=off)."""
        d = decide(path, op="write", mode=mode, policy=policy, roots=roots)
        h = _content_hash(content)
        _audit("write_file", d.path, d.allow, d.reason, content_sha256_16=h, bytes=len(content.encode("utf-8")))
        if not d.allow:
            return f"DENIED: {d.reason}"
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"OK wrote {path} ({len(content)} chars) reason={d.reason}"

    @mcp.tool()
    def delete_file(path: str) -> str:
        """Delete file if policy allows (default deny in enforce)."""
        d = decide(path, op="delete", mode=mode, policy=policy, roots=roots)
        _audit("delete_file", d.path, d.allow, d.reason)
        if not d.allow:
            return f"DENIED: {d.reason}"
        p = Path(path)
        if not p.exists():
            return f"ERROR: missing {path}"
        if p.is_dir():
            return "ERROR: refuse directory delete"
        p.unlink()
        return f"OK deleted {path}"

    return mcp


def run_stdio() -> None:
    mcp = build_mcp()
    mcp.run(transport="stdio")
