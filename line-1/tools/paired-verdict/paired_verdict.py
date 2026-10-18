#!/usr/bin/env python3
"""Analyze matched binary benchmark outcomes. Standard library; no network or writes."""
import argparse
import csv
import hashlib
import io
import json
import math
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from statistics import NormalDist

MAX_BYTES = 2 * 1024 * 1024
MAX_CASES = 10_000


class InputError(ValueError):
    """A benchmark cannot safely be interpreted."""


def parse_alpha(value):
    if len(value) > 64:
        raise InputError('alpha must contain at most 64 characters')
    try:
        alpha = Decimal(value)
    except InvalidOperation as exc:
        raise InputError('alpha must be a decimal number') from exc
    if not alpha.is_finite() or not Decimal('0.000001') <= alpha <= Decimal('0.2'):
        raise InputError('alpha must be between 0.000001 and 0.2 inclusive')
    return alpha


def read_csv_bytes(raw):
    """Require one complete paired observation per distinct nonempty case ID."""
    if len(raw) > MAX_BYTES:
        raise InputError(f'CSV exceeds {MAX_BYTES} bytes')
    try:
        decoded = raw.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise InputError('CSV must be UTF-8') from exc
    if '\x00' in decoded:
        raise InputError('CSV contains a NUL byte')
    reader = csv.reader(io.StringIO(decoded, newline=''), strict=True)
    try:
        header = next(reader, None)
        if header != ['case', 'baseline', 'candidate']:
            raise InputError('header must be exactly: case,baseline,candidate')
        seen = set()
        pairs = []
        for row in reader:
            line = reader.line_num
            if len(row) != 3:
                raise InputError(f'line {line}: expected exactly three fields; blank rows are invalid')
            case, baseline, candidate = row
            if not case.strip() or case != case.strip():
                raise InputError(f'line {line}: case must be nonempty with no edge whitespace')
            if case in seen:
                raise InputError(f'line {line}: duplicate case ID')
            if baseline not in ('0', '1') or candidate not in ('0', '1'):
                raise InputError(f'line {line}: both outcomes must be exactly 0 or 1')
            seen.add(case)
            pairs.append((int(baseline), int(candidate)))
            if len(pairs) > MAX_CASES:
                raise InputError(f'CSV exceeds {MAX_CASES} paired cases')
    except csv.Error as exc:
        raise InputError(f'invalid CSV near line {reader.line_num}: {exc}') from exc
    if not pairs:
        raise InputError('CSV must contain at least one paired case')
    return pairs


def load_workspace_input(name):
    """Never follow input paths outside the directory the user runs us in."""
    root = Path.cwd().resolve()
    path = Path(name).resolve()
    if not path.is_relative_to(root):
        raise InputError('input must resolve inside the current workspace directory')
    if not path.is_file():
        raise InputError('input must be a regular workspace file')
    with path.open('rb') as handle:
        raw = handle.read(MAX_BYTES + 1)
    pairs = read_csv_bytes(raw)
    return raw, pairs


def exact_mcnemar(wins, losses):
    """Return integer numerator / 2**discordant for the two-sided exact p."""
    if not isinstance(wins, int) or not isinstance(losses, int) or min(wins, losses) < 0:
        raise InputError('discordant counts must be nonnegative integers')
    discordant = wins + losses
    if discordant > MAX_CASES:
        raise InputError('too many discordant cases')
    term = total = 1
    for k in range(1, min(wins, losses) + 1):
        term = term * (discordant - k + 1) // k
        total += term
    denominator = 1 << discordant
    return min(denominator, 2 * total), discordant


def wilson(successes, count, alpha):
    """Approximate marginal confidence interval, not an interval for the paired effect."""
    z = NormalDist().inv_cdf(1 - float(alpha) / 2)
    proportion = successes / count
    z2 = z * z
    divisor = 1 + z2 / count
    midpoint = (proportion + z2 / (2 * count)) / divisor
    half = z * math.sqrt(proportion * (1 - proportion) / count + z2 / (4 * count**2)) / divisor
    return [0.0 if successes == 0 else max(0.0, midpoint - half),
            1.0 if successes == count else min(1.0, midpoint + half)]


def analyze(pairs, raw, alpha):
    n = len(pairs)
    if not 1 <= n <= MAX_CASES:
        raise InputError('invalid paired case count')
    table = {'both_pass': 0, 'both_fail': 0, 'candidate_only_pass': 0, 'baseline_only_pass': 0}
    keys = {(1, 1): 'both_pass', (0, 0): 'both_fail',
            (0, 1): 'candidate_only_pass', (1, 0): 'baseline_only_pass'}
    for pair in pairs:
        if pair not in keys:
            raise InputError('outcome must be binary')
        table[keys[pair]] += 1
    wins = table['candidate_only_pass']
    losses = table['baseline_only_pass']
    numerator, exponent = exact_mcnemar(wins, losses)
    denominator = 1 << exponent
    alpha_num, alpha_den = alpha.as_integer_ratio()
    significant = numerator * alpha_den <= denominator * alpha_num
    direction = 'candidate' if wins > losses else 'baseline' if losses > wins else 'tie'
    with localcontext() as context:
        context.prec = 16
        p_decimal = str(Decimal(numerator) / Decimal(denominator))
    baseline = table['both_pass'] + losses
    candidate = table['both_pass'] + wins
    return {
        'schema_version': 1,
        'input_sha256': hashlib.sha256(raw).hexdigest(),
        'paired_cases': n,
        'table': table,
        'baseline': {'passes': baseline, 'pass_rate': baseline / n,
                     'wilson_interval': wilson(baseline, n, alpha)},
        'candidate': {'passes': candidate, 'pass_rate': candidate / n,
                      'wilson_interval': wilson(candidate, n, alpha)},
        'candidate_minus_baseline_percentage_points': 100 * (wins - losses) / n,
        'test': {'name': 'two-sided exact conditional McNemar', 'alpha': str(alpha),
                 'discordant_pairs': exponent, 'p_value_decimal_16_digits': p_decimal,
                 'p_exact_numerator': str(numerator), 'p_exact_denominator_power_of_two': exponent,
                 'reject_equal_discordance_at_alpha': significant,
                 'observed_direction': direction},
        'interpretation': (f'evidence_favors_{direction}' if significant else 'insufficient_evidence_of_difference'),
        'marginal_interval_confidence_level': 1 - float(alpha),
        'interval_note': 'Wilson intervals are approximate marginal pass-rate intervals; they are not paired-effect intervals.',
        'assumptions': [
            'Each row is the same benchmark case evaluated once under each system.',
            'Case pairs are independent; shared tasks, users, seeds or documents may violate this.',
            'The pass rule, benchmark and alpha were chosen before inspecting these results.',
            'This is one comparison; repeated looks or multiple candidates require an additional testing policy.',
            'Failure to reject does not establish equivalence, safety or sufficient statistical power.',
            'The result measures binary success only, not cost, latency, severity or generalization.'
        ]
    }


def demo_csv():
    # Explicitly synthetic demonstration: 24 both pass, 4 both fail, 10 wins, 2 losses.
    pairs = [(1, 1)] * 24 + [(0, 0)] * 4 + [(0, 1)] * 10 + [(1, 0)] * 2
    rows = ['case,baseline,candidate']
    rows += [f'synthetic-{i:03},{b},{c}' for i, (b, c) in enumerate(pairs, 1)]
    return ('\n'.join(rows) + '\n').encode()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--input', help='UTF-8 CSV inside the current workspace')
    source.add_argument('--demo', action='store_true', help='run a labeled synthetic example')
    parser.add_argument('--alpha', default='0.05', help='prespecified test level, 0.000001 through 0.2')
    args = parser.parse_args(argv)
    try:
        alpha = parse_alpha(args.alpha)
        if args.demo:
            raw = demo_csv()
            pairs = read_csv_bytes(raw)
        else:
            raw, pairs = load_workspace_input(args.input)
        result = analyze(pairs, raw, alpha)
        result['data_kind'] = 'synthetic_demonstration' if args.demo else 'user_supplied_benchmark'
    except (InputError, OSError, ValueError) as exc:
        parser.exit(2, f'error: {exc}\n')
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
