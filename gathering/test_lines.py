"""Additional read-only checks of Line 3 and 4; known bugs remain visible."""
import importlib.util
from fractions import Fraction
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


t = load("checked_time_flint", "line-3/tools/time-flint/time_flint.py")
u = load("checked_unit_flint", "line-4/tools/unit-flint/unit_flint.py")


class TimeChecks(unittest.TestCase):
    def test_equivalent_offsets(self):
        self.assertEqual(t.parse_stamp("2026-10-18T12:00:00+02:00"),
                         t.parse_stamp("2026-10-18T10:00:00Z"))

    def test_half_open_boundaries_do_not_overlap(self):
        report = t.build([("a", b"2026-10-18T10:00:00Z a\n2026-10-18T10:00:01Z b\n")])
        self.assertEqual([e["overlap_group"] for e in report["events"]], [1, 2])

    def test_transitive_overlap(self):
        raw = b"2026-10-18T10:00Z wide\n2026-10-18T10:00:01Z a\n2026-10-18T10:00:59Z b\n"
        self.assertEqual({e["overlap_group"] for e in t.build([("a", raw)])["events"]}, {1})

    def test_duplicate_json_and_naive_timestamp_rejected(self):
        for raw in (b'{"ts":1792317601,"ts":1792317602}', b"2026-10-18T10:00:00 naive"):
            with self.assertRaises(t.TimelineError):
                t.build([("a", raw)])

    def test_omissions_and_determinism(self):
        data = [("a", b"broken\n2026-10-18T10:00:00Z ok\n")]
        report = t.build(data, True)
        self.assertEqual(len(report["omitted"]), 1)
        self.assertEqual(report, t.build(data, True))

    @unittest.expectedFailure
    def test_known_calendar_overflow_should_be_validation_error(self):
        with self.assertRaises(t.TimelineError):
            t.build([("a", b"9999-12-31T23:59:59Z event\n")])


class UnitChecks(unittest.TestCase):
    def test_exact_decimal_addition(self):
        self.assertEqual(u.Parser("0.1 m + 0.2 m").parse().value, Fraction(3, 10))

    def test_compound_speed(self):
        result = u.Parser("10 km / 2 h").parse()
        self.assertEqual(result.value, Fraction(25, 18))
        self.assertEqual(result.dims, (1, 0, -1, 0))

    def test_prefixes_and_physical_units(self):
        for a, b in [("1 L", "1000 mL"), ("1 N", "1 kg * m / s^2"),
                     ("1 W", "1 J / s"), ("1 KiB", "1024 B")]:
            self.assertEqual(u.Parser(a).parse(), u.Parser(b).parse())

    def test_dimension_mismatch_zero_and_code_rejected(self):
        for text in ("2 m + 3 s", "1 / 0", "unknown(1)", "m^0.5", "m^13"):
            with self.assertRaises(u.UnitError):
                u.Parser(text).parse()

    def test_exact_fraction_display(self):
        self.assertEqual(u.exact_decimal(Fraction(1, 3)), "1/3")
        self.assertEqual(u.exact_decimal(Fraction(-1, 8)), "-0.125")

    @unittest.expectedFailure
    def test_known_nesting_should_be_validation_error(self):
        with self.assertRaises(u.UnitError):
            u.Parser("-" * 1100 + "1").parse()


if __name__ == "__main__":
    unittest.main()
