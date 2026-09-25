"""tk Loop module chrome paints wired / partial / not wired (G-1)."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_gui():
    spec = importlib.util.spec_from_file_location("pfy_gui", ROOT / "scripts" / "pfy-gui.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class LoopTkPaintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gui = _load_gui()

    def test_module_paint_status_mirrors_html(self):
        g = self.gui
        self.assertEqual(g.module_paint_status({"status": "implemented", "stub": False}), "wired")
        self.assertEqual(g.module_paint_status({"status": "partial", "stub": False}), "partial")
        self.assertEqual(g.module_paint_status({"status": "stub", "stub": True}), "not wired")
        self.assertEqual(g.module_paint_status({"status": "implemented", "stub": True}), "not wired")
        self.assertEqual(g.CHIP["wired"], g.CHIP["implemented"])
        self.assertEqual(g.CHIP["not wired"], g.CHIP["stub"])

    def test_loop_text_modules_use_operator_labels(self):
        s = {
            "modules": [
                {"id": "jev", "status": "implemented", "enabled": True, "stub": False},
                {"id": "code-graph", "status": "partial", "enabled": False, "stub": False},
                {"id": "ghost", "status": "stub", "enabled": False, "stub": True},
            ],
            "modules_enabled": ["jev"],
            "modules_task": "interactive",
            "hedge": {},
        }
        body = self.gui.loop_text(s, "SKIP", "(none)", "(none)", "gui", "")
        mods = body.split("MODULES", 1)[1]
        self.assertIn("wired", mods)
        self.assertIn("partial", mods)
        self.assertIn("not wired", mods)
        self.assertNotIn("implemented", mods)
        self.assertNotIn("  stub", mods)
        self.assertIn("STUB", mods)


if __name__ == "__main__":
    unittest.main()
