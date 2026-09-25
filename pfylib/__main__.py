"""``python3 -m pfylib toolset|hedge ...`` -- same entry as ``./pfy toolset`` / ``./pfy hedge``."""
from __future__ import annotations

import sys

from .cli import main

sys.exit(main())
