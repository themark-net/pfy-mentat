import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.a import new_name
from src.c import run


class RenameTests(unittest.TestCase):
    def test_new_name(self):
        self.assertEqual(new_name(1), 2)

    def test_run(self):
        self.assertEqual(run(1), 3)
