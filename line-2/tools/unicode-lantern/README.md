# Unicode Lantern

An offline, read-only Unicode triage tool for a worker reviewing an unfamiliar
source file, document, or identifier list. It locates bidirectional controls,
format characters, unusual separators, selected invisible characters, mixed
Latin/Greek/Cyrillic identifiers, NFKC changes, and collisions under a small
explicit look-alike mapping. It never rewrites the input.

Run from the repository root with Python 3.9 or newer; no packages, network,
account, environment variables, or configuration are needed:

```sh
python3 -B line-2/tools/unicode-lantern/unicode_lantern.py --demo
```

The demonstration returns JSON with seven findings and exits successfully. The
example contains a Cyrillic letter resembling the `o` in `owner`, a zero-width
space, two directional controls, and a fullwidth spelling of `owner`. The demo
exists as escaped literals in the program, not as hidden controls in its source.

To inspect your own explicitly selected, non-sensitive UTF-8 text in the current
workspace:

```sh
python3 -B line-2/tools/unicode-lantern/unicode_lantern.py --file line-1/tools/paired-verdict/paired_verdict.py
```

Exit codes for `--file`: **0** means no covered patterns found, **1** means review
findings exist, **2** means invalid arguments, unreadable input, invalid UTF-8, or
an exceeded input limit. `--demo` returns 0 when its scan completes, despite its
intentional findings. JSON goes to stdout; argparse usage errors go to stderr.

Each finding includes one-based line and column, zero-based Unicode character
and UTF-8 byte offsets, escaped evidence, and an explanation. Collision findings
point to the first spelling and its original location. Only LF advances the
line counter; CR and tabs count as one code point. Columns are not display-cell
or UTF-16 offsets. The SHA-256 covers the exact original bytes, including BOMs
and CRLF, and the report identifies the runtime Unicode database version.

All evidence fields contain ASCII escape notation even after JSON parsing;
the JSON serializer also escapes non-ASCII. Do not interpret the escape notation
as terminal control sequences when displaying a report. The tool reads at most
2 MiB plus one sentinel byte and retains at most 1,000 findings. Use
`--max-findings 20` to lower that limit. Scanning continues to count findings;
`truncated` explicitly identifies an incomplete listing. No input files are
modified, no directory is scanned automatically, and paths resolving outside
the current working directory are rejected. Run in a stable workspace: this
path check does not protect against another process replacing a path between
checking and opening it.

## What happened when tried

On this round's Python 3.12.3 / Unicode 15.0.0 runtime:

- The built-in demo reported exactly seven findings, including both look-alike
  collisions with the first `owner` occurrence.
- All 12 unit tests passed. They cover byte offsets after an astral character
  and CRLF, combining marks, output escaping, real normalization behavior,
  repeated identifiers, truncation, malformed UTF-8, limits, and path rejection.
- A read-only scan of the existing 8,674-byte
  `line-1/tools/paired-verdict/paired_verdict.py` reported zero covered patterns.
  Its digest was `ed7f2e286ceb08a9dd88de1b77b4a8858a7856eda5dc9e47d32d0bc3d19ebbe1`.

Re-run the tests:

```sh
python3 -B -m unittest discover -s line-2/tools/unicode-lantern -v
```

## Limits and next pieces

Findings invite review; they do not establish malicious intent. Zero findings
do not establish safety. Legitimate right-to-left writing, emoji variation
selectors, and multilingual identifiers can trigger findings. This is a text
scanner, not a parser: words in comments and strings participate in identifier
comparisons. Script families come from character names, not Unicode Script
properties. The look-alike map is deliberately small and case-sensitive, is not
the Unicode UTS #39 skeleton, and cannot cover every font or script. Unmapped
characters and some invisible rendering behavior remain undetected. Results
can change with the Python Unicode database version, which is recorded.

Useful subsequent pieces include a versioned full confusables database,
language-aware spans, explicit allowlists with reasons, cross-file symbol
comparison, and reviewable repair proposals. No coin or payment is needed for
this text-analysis capability.
