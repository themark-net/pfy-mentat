import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.calc import add


class AddTests(unittest.TestCase):
    def test_one_plus_one(self):
        self.assertEqual(add(1, 1), 2)
