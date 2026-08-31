import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from mav_client import m2r_datetime_to_epoch


import unittest

class TestMavClientDatetime(unittest.TestCase):
    def test_m2r_datetime_to_epoch_iso_z(self):
        ts_str = "2026-08-31T17:34:28.753936790Z"
        epoch = m2r_datetime_to_epoch(ts_str)
        self.assertGreater(epoch, 0)
        self.assertAlmostEqual(epoch, 1788197668.753936, delta=1.0)


if __name__ == "__main__":
    unittest.main()
