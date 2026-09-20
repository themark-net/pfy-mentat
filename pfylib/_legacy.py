"""Path-import bridge to ``scripts/pfy_*_NNN.py`` (temporary; T-0121).

The issue-numbered modules are not a package, so ``pfylib`` loads them by
file path exactly once and caches the module object. When T-0121 moves a
module under ``pfylib/`` its ``load()`` call site becomes a normal import and
the entry here goes away. Nothing in here duplicates logic from those files.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

from . import registry

_CACHE: dict[str, ModuleType] = {}


def load(name: str, root_dir: Path | None = None) -> ModuleType:
    """Import ``scripts/<name>.py`` by path; raise FileNotFoundError if absent."""
    key = "%s@%s" % (name, registry.root(root_dir))
    if key in _CACHE:
        return _CACHE[key]
    path = registry.root(root_dir) / "scripts" / ("%s.py" % name)
    if not path.is_file():
        raise FileNotFoundError(str(path))
    spec = importlib.util.spec_from_file_location("pfylib_legacy_%s" % name, path)
    if spec is None or spec.loader is None:
        raise ImportError(name)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    _CACHE[key] = mod
    return mod


def jev(root_dir: Path | None = None) -> ModuleType:
    return load("pfy_jev_230", root_dir)
