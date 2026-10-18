import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import reviewed_timeline as r


class ReviewedTests(unittest.TestCase):
    def test_demo_catches_decoded_json_controls(self):
        report = r.build(r.DEMO)
        self.assertEqual(report["assessment"], "review-required")
        self.assertTrue(all(s["finding_count"] == 0 for s in report["source_reviews"]))
        event = next(e for e in report["timeline"]["events"] if e["source"] == "queue.jsonl")
        self.assertEqual(event["message_review"]["finding_count"], 4)
        self.assertIn(r"\u202e", event["message_escaped"])
        self.assertNotIn("\u202e", event["message_escaped"])

    def test_hashes_bind_same_original_bytes(self):
        raw = b"\xef\xbb\xbf2026-10-18T10:00:00Z event\r\n"
        report = r.build([("a.log", raw)])
        digest = hashlib.sha256(raw).hexdigest()
        self.assertEqual(report["source_reviews"][0]["sha256"], digest)
        self.assertEqual(report["timeline"]["sources"][0]["sha256"], digest)
        self.assertEqual(report["timeline"]["events"][0]["source_review_sha256"], digest)

    def test_raw_findings_join_event_line(self):
        raw = "2026-10-18T10:00:00Z safe\n2026-10-18T10:00:01Z hidden\u200b\n".encode()
        events = r.build([("a.log", raw)])["timeline"]["events"]
        self.assertEqual(events[0]["source_findings_on_line"], [])
        self.assertEqual(events[1]["source_findings_on_line"][0]["line"], 2)

    def test_overlap_uses_precision_not_presentation_order(self):
        events = r.build(r.DEMO)["timeline"]["events"]
        self.assertEqual({e["overlap_group"] for e in events}, {1})
        self.assertEqual({e["precision"] for e in events}, {"minute", "second"})

    def test_repeat_is_byte_deterministic(self):
        self.assertEqual(json.dumps(r.build(r.DEMO), sort_keys=True),
                         json.dumps(r.build(r.DEMO), sort_keys=True))

    def test_bad_input_fails_and_explicit_omission_survives(self):
        data = [("a.log", b"no timestamp\n2026-10-18T10:00:00Z ok\n")]
        with self.assertRaises(r.time_flint.TimelineError):
            r.build(data)
        report = r.build(data, True)
        self.assertEqual(len(report["timeline"]["omitted"]), 1)
        self.assertEqual(len(report["timeline"]["events"]), 1)

    def test_overflow_becomes_normal_validation_error(self):
        for stamp in ("9999-12-31T23:59:59Z", "0001-01-01T00:00:00+01:00"):
            with self.assertRaisesRegex(ValueError, "calendar boundary"):
                r.build([("a.log", (stamp + " event\n").encode())])

    def test_invalid_utf8_size_count_and_duplicates(self):
        for inputs in ([], [("x", b"x")] * 9, [("x", b""), ("x", b"")],
                       [("x", b"\xff")], [("x", b"x" * (r.MAX_BYTES + 1))]):
            with self.assertRaises((ValueError, UnicodeError)):
                r.build(inputs)

    def test_source_names_are_display_safe(self):
        report = r.build([("evil\x1b\u202e.log", b"2026-10-18T10:00:00Z hi\n")])
        for item in report["timeline"]["events"] + report["timeline"]["sources"]:
            self.assertIn(r"\x1b", item["source"])
            self.assertNotIn("\x1b", item["source"])

    def test_truncation_is_explicit(self):
        raw = ("2026-10-18T10:00:00Z " + "\u202e" * 110).encode()
        report = r.build([("a.log", raw)])
        event = report["timeline"]["events"][0]
        self.assertTrue(event["source_listing_truncated"])
        self.assertTrue(event["message_review"]["truncated"])
        self.assertEqual(event["message_review"]["finding_count"], 110)

    def test_paths_reject_escape_before_reading(self):
        with self.assertRaisesRegex(ValueError, "inside"):
            r.workspace_inputs(["../outside.log"])
        # Temporary directory is explicitly created inside the workspace.
        Path("test/scratch").mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir="test/scratch") as directory:
            path = Path(directory) / "a.log"
            path.write_bytes(b"2026-10-18T10:00:00Z hi\n")
            self.assertEqual(len(r.workspace_inputs([str(path)])), 1)
            with self.assertRaisesRegex(ValueError, "twice"):
                r.workspace_inputs([str(path), str(path)])

    def test_cli_exit_codes_and_no_partial_json_on_error(self):
        for args, code in [(["--demo"], 0), ([], 2)]:
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                self.assertEqual(r.main(args), code)
            if code == 0:
                json.loads(out.getvalue())
            else:
                self.assertEqual(out.getvalue(), "")
                self.assertIn("error", err.getvalue())


if __name__ == "__main__":
    unittest.main()
