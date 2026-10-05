import unittest
import datetime
from core.hwid import get_hardware_id
from core.license_verifier import LicenseVerifier
from licensing_admin.admin_keygen import generate_license_key


class TestLicensingSystem(unittest.TestCase):
    def setUp(self):
        self.verifier = LicenseVerifier()
        self.hwid = get_hardware_id()

    def test_valid_license_activation(self):
        key = generate_license_key("Test Customer", self.hwid, "PRO", "LIFETIME")
        res = self.verifier.verify_key(key)
        self.assertTrue(res["valid"], f"Valid license failed verification: {res}")
        self.assertEqual(res["user"], "Test Customer")
        self.assertEqual(res["tier"], "PRO")
        self.assertEqual(res["expires"], "LIFETIME")

    def test_mismatched_hwid_rejection(self):
        other_hwid = "VREC-9999-8888-7777"
        key = generate_license_key("Attacker", other_hwid, "PRO", "LIFETIME")
        res = self.verifier.verify_key(key)
        self.assertFalse(res["valid"], "License for another HWID should not validate on this PC")
        self.assertIn("locked to another machine", res.get("error", ""))

    def test_expired_license_rejection(self):
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        key = generate_license_key("Expired User", self.hwid, "PRO", yesterday)
        res = self.verifier.verify_key(key)
        self.assertFalse(res["valid"], "Expired license should not validate")
        self.assertIn("expired", res.get("error", "").lower())

    def test_tampered_key_rejection(self):
        key = generate_license_key("Normal User", self.hwid, "PRO", "LIFETIME")
        # Tamper payload
        parts = key.split(".")
        tampered_key = parts[0][:-2] + "AA." + parts[1]
        res = self.verifier.verify_key(tampered_key)
        self.assertFalse(res["valid"], "Tampered license key must be rejected")

    def test_20digit_numeric_license_key(self):
        key = generate_license_key("Student", "AUTO_ONLINE_BIND", "PRO", "LIFETIME", use_compact=True)
        # Should be in XXXX-XXXX-XXXX-XXXX-XXXX format
        parts = key.split("-")
        self.assertEqual(len(parts), 5, f"Key {key} does not have 5 blocks")
        self.assertTrue(all(len(p) == 4 for p in parts), f"Blocks are not 4 chars each: {parts}")
        self.assertEqual(len(key.replace("-", "")), 20)
        self.assertTrue(key.replace("-", "").isdigit(), "Key should be numeric digits")

        res = self.verifier.verify_key(key, check_online=False)
        self.assertTrue(res["valid"], f"20-digit numeric key failed verification: {res}")
        self.assertEqual(res["tier"], "PRO")
        self.assertEqual(res["expires"], "LIFETIME")

    def test_20digit_alphanumeric_license_key(self):
        pub_norm = b"".join(self.verifier.public_key_pem.strip().splitlines())
        from licensing_admin.admin_keygen import generate_5block_compact_key
        _, key = generate_5block_compact_key(pub_norm)
        parts = key.split("-")
        self.assertEqual(len(parts), 6)  # RECPLAY-B1-B2-EXP-SIG1-SIG2

        res = self.verifier.verify_key(key, check_online=False)
        self.assertTrue(res["valid"], f"5-block alphanumeric key failed verification: {res}")
        self.assertEqual(res["tier"], "PRO")

    def test_20digit_without_hyphens_and_with_prefix(self):
        key = generate_license_key("User", "AUTO_ONLINE_BIND", "PRO", "LIFETIME", use_compact=True)
        raw_key = key.replace("-", "")
        self.assertEqual(len(raw_key), 20)

        # Without hyphens
        res1 = self.verifier.verify_key(raw_key, check_online=False)
        self.assertTrue(res1["valid"], f"Raw 20-digit key failed verification: {res1}")

        # With RECPLAY- prefix
        prefixed_key = f"RECPLAY-{key}"
        res2 = self.verifier.verify_key(prefixed_key, check_online=False)
        self.assertTrue(res2["valid"], f"Prefixed 20-digit key failed verification: {res2}")

    def test_tampered_20digit_key_rejection(self):
        key = str(generate_license_key("User", "AUTO_ONLINE_BIND", "PRO", "LIFETIME", use_compact=True))
        # Flip a digit in the signature
        last_char = "0" if key[-1] != "0" else "1"
        tampered_key = key[:-1] + last_char
        res = self.verifier.verify_key(tampered_key, check_online=False)
        self.assertFalse(res["valid"], "Tampered 20-digit key must be rejected")
        self.assertIn("tampered", res.get("error", "").lower())


if __name__ == "__main__":
    unittest.main()

