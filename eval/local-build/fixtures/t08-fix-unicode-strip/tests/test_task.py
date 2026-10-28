import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.clean import normalize


class CleanTests(unittest.TestCase):
    def test_strip_and_case(self):
        self.assertEqual(normalize("  Caf\u00e9  "), "caf\u00e9")
        self.assertEqual(normalize("\tHi\n"), "hi")
