import unittest
import re
from core.hwid import get_hardware_id


class TestHardwareID(unittest.TestCase):
    def test_hwid_format(self):
        hwid = get_hardware_id()
        self.assertTrue(isinstance(hwid, str))
        self.assertTrue(hwid.startswith("VREC-"), f"HWID did not start with VREC-: {hwid}")
        parts = hwid.split("-")
        self.assertEqual(len(parts), 4, f"HWID does not have 4 parts: {hwid}")
        for p in parts[1:]:
            self.assertEqual(len(p), 4, f"Segment {p} is not 4 characters")

    def test_hwid_consistency(self):
        hwid1 = get_hardware_id()
        hwid2 = get_hardware_id()
        self.assertEqual(hwid1, hwid2, "HWID changed across consecutive calls")


if __name__ == "__main__":
    unittest.main()
