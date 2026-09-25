#!/usr/bin/env python3
"""Attach Codex developer-usable session -- cite #220 (shim).

Body lives in ``pfylib/attach.py`` parameterised by ``data/harnesses.json``
``codex.attach`` (T-0121; ``~/.local/bin/codex`` fallback is ``bin_fallbacks``).
Same ``--prove`` / ``--selftest`` surface and the same
``open_enterable_codex_session`` / ``live_session_reach`` names the board loads.
Missing Codex is FAIL+next, never a silent stub.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pfylib import attach  # noqa: E402

HARNESS = "codex"
_P = attach.profile(HARNESS)
SESSION_FILE = _P["session_file"]
TERMINAL_PID_FILE = _P["terminal_pid_file"]
ATTACH_BASE_FILE = _P["attach_base_file"]
SESSION_REACH_OK = _P["session_reach_ok"]
NEXT_INSTALL = _P["next_install"]
inspect_models = attach.inspect_models


def open_enterable_codex_session(**deps):
    return attach.open_session(HARNESS, **deps)


def live_session_reach(STATE, pid_alive=None) -> str:
    return attach.live_session_reach(HARNESS, STATE, pid_alive)


def prove_cli(base):
    return attach.prove_cli(base)


def cmd_selftest():
    return attach.selftest(HARNESS)


if __name__ == "__main__":
    raise SystemExit(attach.main(HARNESS, sys.argv[1:], prog=Path(__file__).name))
