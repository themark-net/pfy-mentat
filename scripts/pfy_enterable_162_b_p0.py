#!/usr/bin/env python3
"""Enterable OpenCode open_enterable -- cite #162 (b) / #181 / #193."""
from __future__ import annotations

import os
import importlib.util
import urllib.request
from pathlib import Path

def _load_a():
    path = Path(__file__).resolve().parent / "pfy_enterable_162_a.py"
    spec = importlib.util.spec_from_file_location("pfy_enterable_162_a", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def _load_193():
    path = Path(__file__).resolve().parent / "pfy_attach_usable_193.py"
    spec = importlib.util.spec_from_file_location("pfy_attach_usable_193", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_a = _load_a()
_u = _load_193()
SESSION_REACH_OK = _u.SESSION_REACH_USABLE
SESSION_FILE = _a.SESSION_FILE
read_session_reach = _a.read_session_reach
write_session_reach = _a.write_session_reach
clear_session_reach = _a.clear_session_reach
spawn_terminal_opencode = _a.spawn_terminal_opencode
_focus_pid = _a._focus_pid
write_terminal_pid = _a.write_terminal_pid
read_terminal_pid = _a.read_terminal_pid
resolve_enterable_pid = _a.resolve_enterable_pid
prove_developer_usable = _u.prove_developer_usable
fail_not_usable = _u.fail_not_usable


