import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.cli import main


class CliTests(unittest.TestCase):
    def test_upper(self):
        self.assertEqual(main(["--upper", "Hi"]), "HI")
