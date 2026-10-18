# Time Flint

Time Flint turns UTF-8 log files into a deterministic incident timeline. It reads
data only; it does not import or execute the services that wrote the logs. Each
event carries its source path, line number, and SHA-256 of the original line;
the output also lists each source file's SHA-256. Input order, timestamp precision, and possible ordering
ambiguity remain visible.

See it work with one command from the repository root:

```sh
python3 -B line-3/tools/time-flint/time_flint.py --demo
```

The demo merges a plain log with JSONL. The minute-precision queue event and the
second-precision request event share an overlap group; the tool does not claim
which happened first. I ran the command and the JSON form locally; both completed
without network access. To analyze your own files:

```sh
python3 -B line-3/tools/time-flint/time_flint.py --json service.log queue.jsonl
```

Plain lines start with an ISO 8601 timestamp followed by whitespace and a
message, for example `2026-10-18T12:00:01.123+02:00 event`. JSONL objects have
exactly one `timestamp`, `time`, or `ts` field; `message`, `msg`, or `event` is
used as the description when present. ISO timestamps require `T` and an explicit
`Z` or numeric UTC offset. JSONL also accepts 10-digit integer epoch seconds or
13-digit integer epoch milliseconds. Blank lines are skipped. All other malformed
or untimestamped lines fail the run with a source and line number. The optional
`--ignore-unmatched` flag records every omission with a line hash and reason in
JSON output; it never discards those lines silently.

Each timestamp is represented as a half-open UTC interval, assuming the logger
truncated rather than rounded to its displayed precision. For example, a
timestamp written only to the minute occupies that entire minute; a timestamp
with three fractional digits occupies one millisecond. Events whose intervals
overlap transitively share an `overlap_group`. This identifies a connected cluster,
not a claim that every pair within it overlaps. The displayed sort order inside
that group is only a stable presentation order. Group numbers have no
meaning across different input sets. The JSON form is suitable for review or
further processing; it contains no runtime timestamp or random field.

Limits: this first piece accepts only these explicit timestamp forms, not syslog
dates, local time without an offset, leap seconds, or events split over multiple
lines. It uses reported timestamps as evidence, so clock skew and dishonest logs
remain outside its claims. Source line hashes are computed after UTF-8 decoding
and stripping line terminators; source file hashes cover the exact input bytes.
No coin is needed for offline log analysis.
