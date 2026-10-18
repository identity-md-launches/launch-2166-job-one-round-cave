"""Independent small-case enumeration, invariants, parsing and CLI regression tests."""
import contextlib
import io
import itertools
import json
import unittest
from decimal import Decimal
from fractions import Fraction
from unittest.mock import patch
import paired_verdict as p


class ExactTests(unittest.TestCase):
    def test_enumeration_of_fair_binary_outcomes(self):
        # Independent oracle: enumerate equiprobable sequences rather than combinations.
        for n in range(11):
            sums = [sum(outcome) for outcome in itertools.product((0, 1), repeat=n)]
            for wins in range(n + 1):
                losses = n - wins
                extreme = min(wins, losses)
                expected = min(Fraction(1), 2 * Fraction(sum(s <= extreme for s in sums), 2**n))
                numerator, exponent = p.exact_mcnemar(wins, losses)
                self.assertEqual(Fraction(numerator, 2**exponent), expected)

    def test_known_demo(self):
        raw = p.demo_csv()
        report = p.analyze(p.read_csv_bytes(raw), raw, Decimal('.05'))
        self.assertEqual(report['paired_cases'], 40)
        self.assertEqual(report['baseline']['passes'], 26)
        self.assertEqual(report['candidate']['passes'], 34)
        self.assertEqual(report['candidate_minus_baseline_percentage_points'], 20)
        self.assertEqual(report['test']['p_value_decimal_16_digits'], '0.03857421875')
        self.assertEqual(report['interpretation'], 'evidence_favors_candidate')

    def test_threshold_is_compared_exactly(self):
        raw = b'case,baseline,candidate\na,0,1\nb,0,1\nc,0,1\nd,0,1\ne,0,1\n'
        pairs = p.read_csv_bytes(raw)
        self.assertTrue(p.analyze(pairs, raw, Decimal('0.0625'))['test']['reject_equal_discordance_at_alpha'])
        self.assertFalse(p.analyze(pairs, raw, Decimal('0.062499999999999999999'))['test']['reject_equal_discordance_at_alpha'])

    def test_equal_all_pass_and_all_fail(self):
        for pairs in [[(1, 1)], [(0, 0)] * 100, [(0, 1), (1, 0)]]:
            r = p.analyze(pairs, b'fixture', Decimal('.05'))
            self.assertEqual(Decimal(r['test']['p_value_decimal_16_digits']), 1)
            self.assertFalse(r['test']['reject_equal_discordance_at_alpha'])
            for system in ('baseline', 'candidate'):
                lo, hi = r[system]['wilson_interval']
                self.assertTrue(0 <= lo <= r[system]['pass_rate'] <= hi <= 1)

    def test_swapping_labels_preserves_p_and_reverses_effect(self):
        for wins, losses in itertools.product(range(12), repeat=2):
            pairs = [(0, 1)] * wins + [(1, 0)] * losses + [(1, 1)]
            r = p.analyze(pairs, b'a', Decimal('.05'))
            s = p.analyze([(b, a) for a, b in pairs], b'b', Decimal('.05'))
            self.assertEqual(r['test']['p_value_decimal_16_digits'], s['test']['p_value_decimal_16_digits'])
            self.assertEqual(r['candidate_minus_baseline_percentage_points'], -s['candidate_minus_baseline_percentage_points'])

    def test_large_unbalanced_p_does_not_underflow(self):
        r = p.analyze([(0, 1)] * 10_000, b'fixture', Decimal('.05'))
        self.assertGreater(Decimal(r['test']['p_value_decimal_16_digits']), 0)
        self.assertEqual(r['test']['p_exact_numerator'], '2')
        self.assertEqual(r['test']['p_exact_denominator_power_of_two'], 10_000)
        self.assertEqual(r['interpretation'], 'evidence_favors_candidate')

    def test_wilson_boundary_rates_are_inside_intervals(self):
        for n in range(1, 501):
            self.assertEqual(p.wilson(0, n, Decimal('.05'))[0], 0)
            self.assertEqual(p.wilson(n, n, Decimal('.05'))[1], 1)

    def test_large_balanced_table(self):
        numerator, exponent = p.exact_mcnemar(5000, 5000)
        self.assertEqual(numerator, 2**exponent)


class InputTests(unittest.TestCase):
    def test_bom_crlf_quoted_case(self):
        raw = '\ufeffcase,baseline,candidate\r\n"task,1",1,0\r\n'.encode()
        self.assertEqual(p.read_csv_bytes(raw), [(1, 0)])

    def test_bad_inputs(self):
        for raw in [b'', b'case,baseline,candidate\n', b'case,candidate,baseline\na,0,1\n',
                    b'case,baseline,candidate\na,0,1\na,1,0\n',
                    b'case,baseline,candidate\n,0,1\n',
                    b'case,baseline,candidate\n a,0,1\n',
                    b'case,baseline,candidate\na,true,1\n',
                    b'case,baseline,candidate\na,0,1,extra\n',
                    b'case,baseline,candidate\na,0,1\n\n',
                    b'case,baseline,candidate\n"a,0,1\n', b'\xff', b'\x00',
                    b'x' * (p.MAX_BYTES + 1)]:
            with self.subTest(raw=raw[:60]), self.assertRaises(p.InputError):
                p.read_csv_bytes(raw)

    def test_row_limit(self):
        with patch.object(p, 'MAX_CASES', 1), self.assertRaises(p.InputError):
            p.read_csv_bytes(b'case,baseline,candidate\na,0,1\nb,1,0\n')

    def test_alpha_validation(self):
        for a in ['NaN', 'Infinity', '-1', '0', '1', 'abc', '.0000001', '.20001', '1'*65]:
            with self.subTest(alpha=a), self.assertRaises(p.InputError):
                p.parse_alpha(a)
        for a in ['.05', '.000001', '.2']:
            self.assertEqual(p.parse_alpha(a), Decimal(a))

    def test_outside_path_rejected_before_open(self):
        with patch('pathlib.Path.open', side_effect=AssertionError('must not open')):
            with self.assertRaisesRegex(p.InputError, 'inside'):
                p.load_workspace_input('../outside.csv')

    def test_cli_demo_json(self):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            self.assertEqual(p.main(['--demo']), 0)
        self.assertEqual(json.loads(stream.getvalue())['data_kind'], 'synthetic_demonstration')

    def test_cli_invalid_input_no_report(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as exc:
                p.main(['--demo', '--alpha', 'NaN'])
        self.assertEqual(exc.exception.code, 2)
        self.assertEqual(stdout.getvalue(), '')
        self.assertIn('error:', stderr.getvalue())


if __name__ == '__main__':
    unittest.main()
