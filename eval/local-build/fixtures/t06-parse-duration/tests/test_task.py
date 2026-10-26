import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.duration import parse_duration


class DurationTests(unittest.TestCase):
    def test_hours_minutes(self):
        self.assertEqual(parse_duration("1h30m"), 5400)

    def test_minutes(self):
        self.assertEqual(parse_duration("2m"), 120)

    def test_seconds(self):
        self.assertEqual(parse_duration("45s"), 45)
