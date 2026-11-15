"""Pinned digests permit recovery of newline conversion, never arbitrary tampering."""
import hashlib
import unittest

from repair_capture_line_endings import recover_bytes


class CaptureRecoveryTests(unittest.TestCase):
    def test_restore_both_newline_directions_to_original_digest(self):
        for original, converted in ((b"one\r\ntwo\r\n", b"one\ntwo\n"),
                                    (b"one\ntwo\n", b"one\r\ntwo\r\n")):
            self.assertEqual(recover_bytes(converted, hashlib.sha256(original).hexdigest()), original)

    def test_changed_word_cannot_be_repaired(self):
        self.assertIsNone(recover_bytes(b"different\n", hashlib.sha256(b"original\n").hexdigest()))


if __name__ == "__main__":
    unittest.main()
