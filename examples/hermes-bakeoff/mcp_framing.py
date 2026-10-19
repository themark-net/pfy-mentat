"""Stdlib MCP stdio framing.

The Hermes pin's MCP SDK writes and reads one JSON-RPC object per line.
Content-Length frames are still accepted on read so an older client can
connect. Nothing here is a secret.
"""

from __future__ import annotations

import json
from typing import Any, BinaryIO


def read_message(stream: BinaryIO) -> dict[str, Any] | None:
    """Read one JSON-RPC message. None at EOF."""
    header = bytearray()
    while True:
        chunk = stream.read(1)
        if not chunk:
            return None
        header += chunk
        if header.startswith(b"{"):
            while not header.endswith(b"\n"):
                more = stream.read(1)
                if not more:
                    return None
                header += more
            return json.loads(header.decode("utf-8").strip())
        if header.endswith(b"\r\n\r\n") or header.endswith(b"\n\n"):
            break
        if len(header) > 8192:
            raise ValueError("MCP header exceeded 8192 bytes")
    length = None
    for line in header.decode("utf-8", "replace").splitlines():
        if line.lower().startswith("content-length:"):
            length = int(line.split(":", 1)[1].strip())
    if length is None:
        raise ValueError("MCP frame missing Content-Length")
    body = stream.read(length)
    if len(body) < length:
        return None
    return json.loads(body.decode("utf-8"))


def write_message(stream: BinaryIO, payload: dict[str, Any]) -> None:
    data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    stream.write(data + b"\n")
    stream.flush()
