import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.text import slugify


class SlugTests(unittest.TestCase):
    def test_words(self):
        self.assertEqual(slugify("Hello World"), "hello-world")

    def test_dashes(self):
        self.assertEqual(slugify("  A--B  "), "a-b")
