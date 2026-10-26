import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.box import collect


class BoxTests(unittest.TestCase):
    def test_calls_do_not_share_state(self):
        self.assertEqual(collect("a"), ["a"])
        self.assertEqual(collect("b"), ["b"])
