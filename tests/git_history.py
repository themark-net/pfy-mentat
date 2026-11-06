"""Shared check for a commit object cited by a history test.

A missing object is a skip. A present object still has to satisfy the test.
Shallow is not the only reason a checkout can lack an old commit.
"""
from __future__ import annotations

import subprocess
from pathlib import Path


def commit_available(repo: Path, sha: str) -> bool:
    """True when `git cat-file -e <sha>^{commit}` succeeds in repo."""
    if not sha:
        return False
    proc = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", "%s^{commit}" % sha],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 0
