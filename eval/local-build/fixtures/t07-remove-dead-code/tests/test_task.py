import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import src.work as work


class DeadTests(unittest.TestCase):
    def test_live(self):
        self.assertEqual(work.live(), 1)

    def test_dead_is_gone(self):
        self.assertFalse(hasattr(work, "dead_code"))
