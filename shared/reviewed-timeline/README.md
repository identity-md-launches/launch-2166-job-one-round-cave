# Reviewed Timeline

Join Line 2's Unicode Lantern with Line 3's Time Flint to review incident logs
before trusting their apparent text or event order. This is useful for ordinary
UTF-8 service logs and JSONL, independent of this cave. Python 3.9+, standard
library only, offline. No installation, wallet, environment access or services.

From the repository root:

```sh
python3 -B shared/reviewed-timeline/reviewed_timeline.py --demo
python3 -B -m unittest discover -s shared/reviewed-timeline -v
```

The synthetic demo joins two events in an uncertain overlap group. The JSONL
message contains escaped Unicode that the raw text scan cannot see. After JSON
decoding, the message scan finds four patterns: two bidi controls, one mixed
script identifier and a look-alike collision. Its file scan is clean. The report
retains both results; a clean source scan does not suppress decoded findings.

To use your own non-sensitive workspace files:

```sh
python3 -B shared/reviewed-timeline/reviewed_timeline.py service.log queue.jsonl
```

Output is deterministic ASCII JSON. Exit 0: no covered findings (or completed
demo); 1: findings requiring review; 2: invalid input. Findings do not prove
malice, and no findings do not prove safety. `--ignore-unmatched` records every
omission; default behavior rejects malformed logs. Each input is read once,
and both tools use those identical bytes and SHA-256. Duplicate paths, paths
outside the working directory and files over 2 MiB are rejected. At most eight
explicit files are accepted. Run within a stable workspace; path checks are
not protection against concurrent file replacement.

`message_escaped` and all source names are literal `unicode_escape` strings,
safe for display after parsing JSON. Do not unescape them for a terminal.
Original line hashes remain in the events. Source offsets refer to original
bytes (including BOM); message offsets refer to decoded message UTF-8, never
the JSONL file. `source_findings_on_line` is a convenience subset of a capped
source listing; it may be incomplete when `source_listing_truncated` is true.
Message findings have a separate cap and truncation flag. Cross-file and
cross-message identifier comparisons are not performed. No event ordering or
clock-skew guarantee is added. Inputs remain private and unchanged.

The shared wrapper converts upstream calendar overflow into an exit-2 error.
It does not repair upstream parsers or expand their timestamp grammar.
The vendored modules are exact, unmodified snapshots; see PROVENANCE.md. They
let a worker copy this folder alone, with no dependency on the four lines.
