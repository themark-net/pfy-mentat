"""pfylib -- toolset x harness handoff + hedge (ADR-0017).

Named ``pfylib`` because the repo root already has an executable file ``pfy``;
``./pfy`` stays the user-facing name and ``scripts/pfy`` dispatches the
``toolset`` / ``hedge`` verbs to :mod:`pfylib.cli`.

Modules:
  registry  -- load data/harnesses.json + data/toolsets.json; validate shape
  toolsets  -- matrix() / plan() / apply(); Jev reference implementation
  hedge     -- deterministic local-first lane policy + ledger
  cli       -- argparse front end used by ``./pfy toolset`` and ``./pfy hedge``
  _legacy   -- path-import bridge to scripts/pfy_*_NNN.py until T-0121 moves them

Stdlib only. Python >= 3.12.
"""
from __future__ import annotations

__all__ = ["registry", "toolsets", "hedge", "cli"]
__version__ = "0.1.0"
