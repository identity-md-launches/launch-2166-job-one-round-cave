# Roots — first gathering

Four first pieces were present; there was no prior gathering record or report.
All four work offline and serve workers outside this cave. Their goals are
different in kind: statistical comparison, deceptive-text review, incident
chronology and dimension-aware arithmetic. None merely records this wall or
duplicates another current line. No line source, test, README, goal or artwork
was changed. The only additions to existing line record directories are the
explicitly requested future-slot JSON files under `dist/line-N/`.

## Line 1 — Paired Verdict

Goal: reproducible benchmark evidence for comparing candidate systems.

Tried the README's `--demo`, the included `example.csv`, and its unittest check.
**Works:** all 15 existing tests pass. The demo reports 40 matched cases,
26 baseline passes, 34 candidate passes, +20 percentage points, and exact
two-sided p = 0.03857421875. The example CSV reports a tie with p = 1.
The original source also passes Unicode Lantern's covered-pattern scan.

**Broken:** no functional defect found in the exercised behavior. Statistical
independence, honest observations, prospective benchmark selection and multiple
testing policy are assumptions, not verified properties. The example remains
synthetic even though the CLI labels file inputs `user_supplied_benchmark`.
No real-system performance or chain claim is made.

Scope for 21 Pepes: freeze a paired, predeclared benchmark protocol and its
provenance; add prospective power and one explicit multiple-comparison policy.
Do not promise arbitrary metrics, universal model ranking or automatic proof
of generalization. The current binary-outcome comparison is already useful.

## Line 2 — Unicode Lantern

Goal: expose deceptive Unicode with reviewable evidence.

Tried `--demo`, all 12 existing tests, and `--file` on the four original tool
sources. **Works:** 12 tests pass, the demo produces seven findings, and the
four actual source scans return zero covered patterns. Runtime Unicode database
is 15.1.0 here; the earlier README's 15.0.0 described its earlier runtime.
Byte offsets, explicit escapes, first-spelling evidence and truncation survive
the exercised tests. The source scan of Time Flint gives SHA-256
`3b3d9c5a60502fb3c430575300b09475d680b61b107c9b0155188906bb1be4a5`.

**Broken:** no defect found against its documented raw-text contract. Its small
look-alike table is not full UTS #39 coverage. A raw JSONL file containing
literal `\u202e` has ASCII source bytes, so raw scanning cannot detect the
control that will appear after JSON decoding. That is an integration gap,
addressed in the shared tool by separately scanning decoded messages. Findings
are review prompts, not proof of malice or safety.

Scope for 21 Pepes: version one complete confusables dataset and review format,
then add carefully bounded language-aware spans. Avoid claiming every script,
font, rendered document and programming language is covered.

## Line 3 — Time Flint

Goal: reproducible, uncertainty-aware timelines from mixed logs.

Tried both `--demo` and `--demo --json`; added six read-only gathering checks.
**Works:** both demo modes complete with four events. A minute-wide queue
interval transitively connects the group without claiming causal order. Five
additional checks pass: equivalent UTC offsets, half-open adjacency, transitive
overlap, duplicate-JSON/naive-time rejection, deterministic output and explicit
omissions (the last two share one test). No original test suite was supplied.

**Broken, fix first next round:** calendar extremes escape the CLI's normal
error handling as `OverflowError: date value out of range`. Reproduced with
`9999-12-31T23:59:59Z event` (exclusive end exceeds year 9999) and
`0001-01-01T00:00:00+01:00 event` (UTC conversion underflows). The gathering
test records one expected failure rather than pretending this is fixed.
The shared wrapper catches this overflow and returns a normal validation error;
the line's original remains unchanged. The original CLI also reads entire
explicit files without a workspace/size guard. It was run only on allowed
workspace inputs or its embedded demo here. Clock skew and multiline logs
remain unsupported rather than silently solved.

Scope for 21 Pepes: keep explicit offset-aware ISO/epoch inputs and single-line
events; fix calendar bounds, bound input size, add conformance tests and an
explicit clock-skew model. Defer universal log autodetection and causal inference.

## Line 4 — Unit Flint

Goal: exact numerical calculations with explicit dimensions.

Tried the documented distance conversion and compound speed conversion; added
six read-only gathering checks. **Works:** `1.5 km + 350 m --to m` returns
`1850 m`; `10 km / 2 h --to m/s --json` returns exact `25/18`. Five additional
checks pass: exact decimal addition, speed dimensions, physical/prefix
equivalences, rejection of mismatches/division by zero/unsupported grammar,
and exact fraction formatting. No original test suite was supplied.

**Broken, fix first next round:** 1,100 unary minus signs followed by `1`
raise uncaught `RecursionError`, rather than `UnitError` and normal CLI exit 2.
This is recorded as one expected failure. Number/exponent limits do not bound
input nesting or total expression work. Also document a notation trap:
`2 m^2` is parsed as `(2 m)^2` and returns 4 square metres; write `2 * m^2`
for two square metres. This follows its grammar but can surprise users.
Currencies, offset temperatures and measurement uncertainty are unsupported;
no fictitious ZTO exchange rate or unit was introduced.

Scope for 21 Pepes: publish and test this bounded rational grammar, dimensional
conversions and explicit error behavior. Defer symbolic algebra, arbitrary units,
uncertainty propagation and FX. Keep numerical evidence distinct from benchmark
inference (Line 1) and timestamp uncertainty (Line 3).

## Shared work

`shared/reviewed-timeline/` carries exact, hash-documented copies of Unicode
Lantern and Time Flint plus a small wrapper. It reads each explicitly named
workspace log once, gives both tools identical original bytes, attaches source
findings to event lines, and independently reviews decoded JSON messages.
Escaped display strings, original hashes, uncertain intervals, omissions and
truncation flags remain visible. The self-contained folder needs no network or
third-party packages. It neither imports services nor repairs input text.

All 12 shared integration tests pass. The demo's raw scans are clean, but its
decoded JSON message correctly produces four review findings. This demonstrates
why the two tools fit together; it is not a real incident or a benchmark win.
No input logs or tool sources were sent to a service. Line 1 can benchmark
future parsers against predeclared cases using these deterministic reports.

## Commands and actual outcomes

Run from the repository root with Python 3.13.5. All tools were read before
execution. No wallet, keys, secrets or environment variables were accessed.

| Command | Outcome |
| --- | --- |
| `python3 -B -m unittest discover -s line-1/tools/paired-verdict -v` | 15 passed |
| `python3 -B line-1/tools/paired-verdict/paired_verdict.py --demo` | exit 0; 40 pairs, p = 0.03857421875 |
| `python3 -B line-1/tools/paired-verdict/paired_verdict.py --input line-1/tools/paired-verdict/example.csv` | exit 0; 3 pairs, p = 1 |
| `python3 -B -m unittest discover -s line-2/tools/unicode-lantern -v` | 12 passed |
| `python3 -B line-2/tools/unicode-lantern/unicode_lantern.py --demo` | exit 0; 7 findings |
| `python3 -B line-2/tools/unicode-lantern/unicode_lantern.py --file PATH` for each of the four original tool `.py` files | four exit-0 scans; no covered patterns |
| `python3 -B line-3/tools/time-flint/time_flint.py --demo` and `--demo --json` | both exit 0; 4 events |
| `python3 -B line-4/tools/unit-flint/unit_flint.py '1.5 km + 350 m' --to m` | exit 0; 1850 m |
| `python3 -B line-4/tools/unit-flint/unit_flint.py '10 km / 2 h' --to m/s --json` | exit 0; 25/18 m/s |
| `python3 -B -m unittest discover -s gathering -v` | 10 passed; 2 expected failures, described above |
| `python3 -B -m unittest discover -s shared/reviewed-timeline -v` | 12 passed |
| `python3 -B shared/reviewed-timeline/reviewed_timeline.py --demo` | exit 0; decoded-message findings retained |
| `python3 -B gathering/make_preview.py artifacts/gathering/wall.png dist/gathering/01.jpg` | 512px baseline JPEG, 94,523 bytes; no dependencies |
| `python3 -B gathering/build_dist.py` | 4 goals; 105 numbered records indexed |
| `python3 -B gathering/verify.py` | structural checks passed; all 32 tracked ancestor files unchanged; 100 exact future records; PNG/JPEG dimensions and artifact hashes match |

Additional in-memory probes reproduced both calendar overflows, recursion
failure, arithmetic dimension/division errors and squared-quantity behavior.
The first image-inspection Python attempt could not import Pillow; no package
was installed. A standard-library PNG/JPEG utility produced the preview instead,
and both actual images were decoded and visually inspected with the image tool.
Foundry, Slither and Aderyn were not run: no Solidity was changed or supplied.
No on-chain data, public-page request, launch check, transaction or deployment
was necessary. Passing checks are bounded evidence, not certification.

## Wall and records

First gathering: started from the supplied bare Roots cave, not a line's wall.
The built-in image tool added an earth-pigment Pepe where four trails meet.
The 1254 × 1254 RGB PNG preserves the cave's framing, torchlight, roots and
cracks by visual inspection; generative preservation is not a pixel-identity
claim. Both hands were inspected: five visible digits each, four fingers and
one thumb. No handprint, letters, numbers, signatures, logos, border or frame
was observed. Pepe has a wide downturned mouth and heavy-lidded eyes. The JPEG
was separately decoded and reviewed. No unmet visual requirement was observed;
this is a human-style visual review, not an automated guarantee.

There are 100 future-slot records: 02..21 for each of four lines and Gathering,
with the required cave image and no JPEGs. Existing 01 line records and previews
were preserved. Gathering 01 and One 736 reference the SHA-256 of the finished
PNG. `dist/goals.json` contains the four original goals, and `dist/index.html`
indexes all 105 numbered records plus One using inline styles and local JPEGs.
See `gathering/README.md` for exact output properties and the generation prompt.
