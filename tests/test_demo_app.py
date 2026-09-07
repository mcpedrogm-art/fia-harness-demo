import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from demo_app import greet


class GreetTest(unittest.TestCase):
    def test_greet_incluye_nombre(self):
        self.assertIn("Ada", greet("Ada"))

    def test_greet_rechaza_nombre_vacio(self):
        with self.assertRaises(ValueError):
            greet("   ")


if __name__ == "__main__":
    unittest.main()
