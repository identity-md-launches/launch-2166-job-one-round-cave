# Paired Verdict

Compare two systems on the **same benchmark cases**, where each outcome is pass
(`1`) or fail (`0`). This is useful for a worker choosing between two prompts,
parsers, solvers or implementations without mistaking a few wins for strong
evidence. Python 3.9+; standard library only; no installation or network required.

From the repository root, see it work:

```sh
python3 -B line-1/tools/paired-verdict/paired_verdict.py --demo
```

The demo is explicitly synthetic, not a claim about any real system. When tried,
it returned 40 pairs: baseline 26/40, candidate 34/40, 10 candidate-only passes,
2 baseline-only passes, a +20 percentage-point difference, and an exact two-sided
p-value of 158 / 2^12 = 0.03857421875. With the prespecified alpha of 0.05, that
is evidence favoring the candidate under the stated assumptions.

## Your own benchmark

Create a UTF-8 CSV inside your workspace with this exact header and one row for
each independent case. Run both systems on every case under the same pass rule:

```csv
case,baseline,candidate
parse-empty,1,1
parse-unicode,0,1
parse-truncated,1,0
```

```sh
python3 -B line-1/tools/paired-verdict/paired_verdict.py --input line-1/tools/paired-verdict/example.csv --alpha 0.05
```

`example.csv` is included and labeled as synthetic here. Substitute your own
workspace file. Choose the benchmark, pass rule and alpha before looking at
results. Do not count retries, correlated samples or several outputs for one
problem as independent evidence. A changed case set changes what you measured.
The tool cannot check these experimental assumptions for you.

JSON goes to stdout; errors go to stderr with exit code 2 and no JSON report.
Exit code 0 means a valid analysis, **not** that the candidate is better. Inspect
`interpretation`, the effect size and the assumptions. The tool reads only the
explicit input file, rejects paths resolving outside the current directory,
writes no files, and never contacts a service, wallet or chain. Run it from the
workspace root. This path check is an input guard, not a sandbox against concurrent
filesystem changes.

CSV requirements: exact header order, unique nonempty case IDs without edge
whitespace, exactly three fields per row, and literal `0` or `1` outcomes. Quoted
CSV fields, CRLF and a UTF-8 BOM work. Blank records, missing observations,
duplicates, invalid UTF-8 and malformed rows fail rather than being discarded.
Limits: 2 MiB input, 10,000 pairs. Alpha must be 0.000001 through 0.2 inclusive.

## What the numbers mean

* The 2×2 table preserves the matched structure. The effect is the candidate pass
  rate minus the baseline pass rate, in percentage points.
* The exact conditional McNemar test uses only discordant pairs: let `w` be
  candidate-only passes, `l` baseline-only passes, `d = w + l`, `m = min(w,l)`.
  Under equal discordance probability the two-sided p-value is
  `min(1, 2 * sum(comb(d,k), k=0..m) / 2**d)`.
* Integer arithmetic supplies the exact numerator and denominator exponent.
  The decimal display has 16 significant digits and does not collapse tiny
  p-values to zero. The alpha comparison uses exact integers, not that display.
  Zero discordances return p=1.
* Wilson intervals are approximate, **marginal pass-rate** intervals at confidence
  `1-alpha`. They are not confidence intervals for the paired difference; overlap
  or non-overlap is not the test. All-fail/all-pass endpoints are exactly 0/1.
* Failing to reject equality does not establish equivalence. A small p-value does
  not measure the size or practical value of an improvement. This tool provides
  no correction for multiple comparisons or repeated looks, no power analysis,
  and no guarantees about performance outside the selected benchmark.
* The SHA-256 binds the report to the exact CSV bytes, including its line endings;
  it does not certify that the observations are honest.

## Verification

```sh
python3 -B -m unittest discover -s line-1/tools/paired-verdict -v
```

15 tests passed locally. They enumerate every fair binary sequence through ten
discordant pairs as an independent probability oracle; verify the known demo,
exact alpha boundaries, swapped-label invariance, no discordances, 10,000-pair
balanced and unbalanced cases, interval endpoints, CSV edge cases, path rejection,
resource limits, and CLI behavior. The included CSV was also run through the real
CLI. There are no dependencies or generated test assets.

This first piece measures correctness only. Future pieces can add paired continuous
metrics, multiple-comparison policies, prospective power, and benchmark provenance
without changing Line 1's goal.
