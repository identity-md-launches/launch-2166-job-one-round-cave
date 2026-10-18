"""Run with: python3 -m unittest discover -s line-2/tools/unicode-lantern -v"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

import unicode_lantern as lantern


class ScanTests(unittest.TestCase):
    def scan(self, text, **kwargs):
        return lantern.scan(text.encode("utf-8"), **kwargs)

    def test_ascii_and_legitimate_non_latin(self):
        for text in ("", "hello = 42\n", "\u4f60\u597d \u4e16\u754c", "\u043f\u0440\u0438\u0432\u0435\u0442", "caf\u00e9"):
            self.assertEqual(self.scan(text)["finding_count"], 0)

    def test_byte_and_character_locations_survive_crlf_and_astral_text(self):
        result = self.scan("\U0001f438\r\n\u00e9\u202e")
        finding = result["findings"][0]
        self.assertEqual({k: finding[k] for k in ("line", "column", "char_offset", "byte_offset")},
                         dict(line=2, column=2, char_offset=4, byte_offset=8))
        self.assertEqual(finding["codepoint"], "U+202E")

    def test_json_and_parsed_evidence_are_display_safe(self):
        result = self.scan("\u202ehello\u202c\x1b", source="name\u202e.txt")
        serialized = json.dumps(result, ensure_ascii=True)
        self.assertTrue(serialized.isascii())
        self.assertEqual(result["findings"][0]["escaped"], r"\u202e")
        self.assertEqual(result["source"], r"name\u202e.txt")
        self.assertNotIn("\x1b", serialized)

    def test_collision_points_to_first_spelling(self):
        result = self.scan("owner\n\u043ewner")
        collision = next(f for f in result["findings"] if f["rule"] == "lookalike-collision")
        self.assertEqual(collision["line"], 2)
        self.assertEqual(collision["first"]["line"], 1)
        self.assertEqual(collision["first"]["escaped"], "owner")
        self.assertEqual(collision["skeleton"], "owner")
        self.assertIn("mixed-script-identifier", [f["rule"] for f in result["findings"]])

    def test_normalization_and_combining_marks(self):
        result = self.scan("caf\u00e9 cafe\u0301")
        self.assertEqual([f["rule"] for f in result["findings"]],
                         ["compatibility-normalization", "lookalike-collision"])
        self.assertEqual(result["findings"][0]["escaped"], r"cafe\u0301")

    def test_repeated_identifiers_do_not_collide_with_themselves(self):
        self.assertEqual(self.scan("owner owner owner")["finding_count"], 0)

    def test_zero_width_nonbreaking_space_and_variation_selectors(self):
        result = self.scan("\u200b\u00a0\ufe0f\u034f\x00")
        self.assertEqual({f["rule"] for f in result["findings"]},
                         {"format-character", "unusual-separator", "variation-selector",
                          "invisible-character", "control-character"})

    def test_truncation_is_explicit_and_counts_all_findings(self):
        result = self.scan("\u202e" * 9, max_findings=2)
        self.assertEqual(result["finding_count"], 9)
        self.assertEqual(len(result["findings"]), 2)
        self.assertTrue(result["truncated"])
        self.assertEqual(result["assessment"], "review-required")

    def test_invalid_utf8_size_and_report_limit_fail_closed(self):
        for raw in (b"\xff", b"a" * (lantern.MAX_BYTES + 1)):
            with self.assertRaises(ValueError):
                lantern.scan(raw)
        for limit in (0, -1, 1001, True):
            with self.assertRaises(ValueError):
                lantern.scan(b"okay", max_findings=limit)

    def test_digest_is_of_original_bytes(self):
        raw = b"text\r\n"
        self.assertEqual(lantern.scan(raw)["sha256"], hashlib.sha256(raw).hexdigest())

    def test_parent_escape_rejected_without_reading(self):
        with self.assertRaises(ValueError):
            lantern.workspace_file(Path.cwd().parent / "outside.txt")

    def test_demo_runs_offline_and_returns_json(self):
        result = subprocess.run([sys.executable, str(Path(lantern.__file__)), "--demo"],
                                capture_output=True, check=True)
        report = json.loads(result.stdout)
        self.assertGreater(report["finding_count"], 0)
        self.assertEqual(result.stderr, b"")


if __name__ == "__main__":
    unittest.main()
