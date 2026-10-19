"""Fail closed before any model call. No pull. No key."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Callable

# 22 GiB model weight plus 25 GiB headroom, in KiB (MemAvailable units).
MEM_FLOOR_KIB = (22 + 25) * 1024 * 1024


def mem_available_kib() -> int:
    for line in open("/proc/meminfo", encoding="utf-8"):
        if line.startswith("MemAvailable:"):
            return int(line.split()[1])
    raise RuntimeError("MemAvailable missing from /proc/meminfo")


def ollama_root(base_url: str) -> str:
    root = base_url.rstrip("/")
    if root.endswith("/v1"):
        root = root[: -len("/v1")]
    return root


def check_ollama(base_url: str, model: str, fetch: Callable[[str], dict] | None = None) -> tuple[int, str]:
    """Exit 2 when Ollama is down or the tag is absent. Does not load the model."""
    url = ollama_root(base_url) + "/api/tags"

    def _default(target: str) -> dict:
        request = urllib.request.Request(target, method="GET")
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    getter = fetch or _default
    try:
        body = getter(url)
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return 2, f"FAIL: Ollama unreachable at {base_url} ({type(exc).__name__})"
    except Exception as exc:  # noqa: BLE001 — any fetch failure is unreachable
        return 2, f"FAIL: Ollama unreachable at {base_url} ({type(exc).__name__})"
    names = []
    for item in body.get("models") or []:
        if isinstance(item, dict) and item.get("name"):
            names.append(item["name"])
    if model not in names:
        return 2, f"FAIL: model tag missing: {model}"
    return 0, "OK"
