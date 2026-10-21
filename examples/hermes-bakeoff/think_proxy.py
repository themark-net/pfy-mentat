#!/usr/bin/env python3
"""Local proxy that forces the same thinking settings on every chat request.

Both bake-off arms talk to this process instead of Ollama directly. Chat
bodies get think false, temperature 0, seed 1, and reasoning_effort none.
The log records only those fields, never the prompt.
"""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

CHAT_PATHS = {"/v1/chat/completions", "/api/chat"}


def _upstream_root(base_url: str) -> str:
    root = (base_url or "").rstrip("/")
    if root.endswith("/v1"):
        root = root[: -len("/v1")]
    return root


def force_chat_body(raw: bytes) -> tuple[bytes, dict]:
    """Return the rewritten body and the public record. Non-JSON is unchanged."""
    record = {"temperature": 0, "seed": 1, "think": False, "reasoning_effort": "none"}
    try:
        body = json.loads(raw.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return raw, record
    if not isinstance(body, dict):
        return raw, record
    body["temperature"] = 0
    body["seed"] = 1
    body["think"] = False
    body["reasoning_effort"] = "none"
    options = body.get("options")
    if not isinstance(options, dict):
        options = {}
    options["temperature"] = 0
    options["seed"] = 1
    body["options"] = options
    return json.dumps(body).encode("utf-8"), record


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:  # noqa: N802
        self._forward()

    def do_POST(self) -> None:  # noqa: N802
        self._forward()

    def log_message(self, fmt: str, *args) -> None:
        return

    def _forward(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        route = self.path.split("?", 1)[0]
        if self.command == "POST" and route in CHAT_PATHS and raw:
            raw, record = force_chat_body(raw)
            record["path"] = route
            self.server.forced.append(record)  # type: ignore[attr-defined]
        url = self.server.upstream_root + self.path  # type: ignore[attr-defined]
        headers = {}
        ctype = self.headers.get("Content-Type")
        if ctype:
            headers["Content-Type"] = ctype
        request = urllib.request.Request(
            url,
            data=raw if self.command == "POST" else None,
            headers=headers,
            method=self.command,
        )
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                payload = response.read()
                status = response.status
                content_type = response.headers.get("Content-Type") or "application/json"
        except urllib.error.HTTPError as exc:
            payload = exc.read()
            status = exc.code
            content_type = exc.headers.get("Content-Type") or "application/json"
        except Exception as exc:  # noqa: BLE001 -- surface a closed failure, no upstream body
            payload = json.dumps({"error": type(exc).__name__}).encode("utf-8")
            status = 502
            content_type = "application/json"
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        try:
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError):
            return


class ThinkProxy:
    """One forwarding server bound to 127.0.0.1 on a free port."""

    def __init__(self, server: ThreadingHTTPServer, thread: threading.Thread) -> None:
        self._server = server
        self._thread = thread
        port = server.server_address[1]
        self.base_v1 = f"http://127.0.0.1:{port}/v1"
        self.root = f"http://127.0.0.1:{port}"

    @property
    def forced(self) -> list[dict]:
        return self._server.forced  # type: ignore[attr-defined]

    @classmethod
    def start(cls, upstream: str) -> "ThinkProxy":
        root = _upstream_root(upstream)

        server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        server.upstream_root = root  # type: ignore[attr-defined]
        server.forced = []  # type: ignore[attr-defined]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return cls(server, thread)

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2)


def write_forced_log(path: Path, rows: list[dict]) -> None:
    """Public record only. Callers must not pass prompt text."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(row, sort_keys=True) for row in rows]
    path.write_text(("\n".join(lines) + ("\n" if lines else "")), encoding="utf-8")
