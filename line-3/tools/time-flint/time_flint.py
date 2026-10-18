#!/usr/bin/env python3
"""Build an auditable timeline from offset-aware ISO 8601 and epoch log records."""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


ISO = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?)(Z|[+-]\d{2}:\d{2})$"
)
TEXT = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?(?:Z|[+-]\d{2}:\d{2}))(?:\s+|$)(.*)$"
)
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
DEMO = {
    "service.log": (
        "2026-10-18T10:00:00Z request accepted\n"
        "2026-10-18T10:00:02Z response completed\n"
    ),
    "queue.jsonl": (
        '{"timestamp":"2026-10-18T12:00+02:00","message":"queued near acceptance"}\n'
        '{"ts":1792317601500,"event":"worker began"}\n'
    ),
}


class TimelineError(ValueError):
    pass


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise TimelineError(f"duplicate JSON key: {key}")
        obj[key] = value
    return obj


def micros(dt):
    delta = dt.astimezone(timezone.utc) - EPOCH
    return ((delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds)


def utc_text(value):
    dt = EPOCH + timedelta(microseconds=value)
    return dt.isoformat(timespec="microseconds" if dt.microsecond else "seconds").replace("+00:00", "Z")


def visible(value):
    """Render untrusted log text without terminal control effects."""
    return json.dumps(value, ensure_ascii=True)[1:-1]


def parse_stamp(value):
    """Return UTC half-open interval in microseconds and its declared precision."""
    if isinstance(value, bool):
        raise TimelineError("boolean is not a timestamp")
    if isinstance(value, int):
        digits = len(str(abs(value)))
        if digits == 10:
            start, width, precision = value * 1000000, 1000000, "second"
        elif digits == 13:
            start, width, precision = value * 1000, 1000, "millisecond"
        else:
            raise TimelineError("epoch integer must have 10 seconds or 13 milliseconds digits")
        return start, start + width, precision
    if not isinstance(value, str):
        raise TimelineError("timestamp must be ISO 8601 text or an integer epoch")
    match = ISO.fullmatch(value)
    if not match:
        raise TimelineError("timestamp needs T, explicit Z or ±HH:MM offset, and at most 6 fraction digits")
    body, offset = match.groups()
    try:
        dt = datetime.fromisoformat(body + ("+00:00" if offset == "Z" else offset))
    except ValueError as exc:
        raise TimelineError(f"invalid calendar time: {exc}") from exc
    # datetime.fromisoformat accepts offsets above 23 hours, which are not RFC 3339.
    if offset != "Z" and (int(offset[1:3]) > 23 or int(offset[4:]) > 59):
        raise TimelineError("UTC offset is outside ±23:59")
    fraction = body.partition(".")[2]
    if fraction:
        width, precision = 10 ** (6 - len(fraction)), f"{len(fraction)} fractional digit(s)"
    elif body.count(":") == 2:
        width, precision = 1000000, "second"
    else:
        width, precision = 60000000, "minute"
    start = micros(dt)
    return start, start + width, precision


def parse_line(raw, source, number):
    if raw.lstrip().startswith("{"):
        try:
            obj = json.loads(raw, object_pairs_hook=unique_object)
        except json.JSONDecodeError as exc:
            raise TimelineError(f"invalid JSON: {exc.msg}") from exc
        if not isinstance(obj, dict):
            raise TimelineError("JSONL event must be an object")
        keys = [k for k in ("timestamp", "time", "ts") if k in obj]
        if len(keys) != 1:
            raise TimelineError("JSONL event needs exactly one of timestamp, time, ts")
        stamp = obj[keys[0]]
        message = next((obj[k] for k in ("message", "msg", "event") if k in obj), None)
        if message is None:
            message = {k: v for k, v in obj.items() if k != keys[0]}
        if not isinstance(message, str):
            message = json.dumps(message, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    else:
        match = TEXT.fullmatch(raw)
        if not match:
            raise TimelineError("line needs an offset-aware ISO timestamp prefix or JSONL event")
        stamp, message = match.groups()
    start, end, precision = parse_stamp(stamp)
    return {
        "start_utc": utc_text(start),
        "end_utc_exclusive": utc_text(end),
        "precision": precision,
        "source": source,
        "line": number,
        "line_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        "message": message,
        "_start": start,
        "_end": end,
    }


def build(inputs, ignore_unmatched=False):
    sources, events, errors, omitted = [], [], [], []
    for name, data in inputs:
        sources.append({"source": name, "sha256": hashlib.sha256(data).hexdigest()})
        try:
            content = data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            errors.append(f"{name}: invalid UTF-8 at byte {exc.start}")
            continue
        for number, physical_line in enumerate(content.split("\n"), 1):
            raw = physical_line.removesuffix("\r")
            if not raw.strip():
                continue
            try:
                events.append(parse_line(raw, name, number))
            except TimelineError as exc:
                if ignore_unmatched:
                    omitted.append({
                        "source": name,
                        "line": number,
                        "line_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
                        "reason": str(exc),
                    })
                else:
                    errors.append(f"{name}:{number}: {exc}")
    if errors:
        raise TimelineError("\n".join(errors))
    events.sort(key=lambda e: (e["_start"], e["source"], e["line"]))
    group, furthest_end = 0, None
    for event in events:
        if furthest_end is None or event["_start"] >= furthest_end:
            group += 1
            furthest_end = event["_end"]
        else:
            furthest_end = max(furthest_end, event["_end"])
        event["overlap_group"] = group
        del event["_start"]
        del event["_end"]
    return {"version": 1, "sources": sources, "events": events, "omitted": omitted}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", help="UTF-8 logs or JSONL files; use - for stdin")
    parser.add_argument("--demo", action="store_true", help="analyze two embedded example logs")
    parser.add_argument("--json", action="store_true", help="emit deterministic machine-readable JSON")
    parser.add_argument("--ignore-unmatched", action="store_true", help="explicitly omit malformed/non-event lines")
    args = parser.parse_args(argv)
    if args.demo and args.files:
        parser.error("--demo cannot be combined with files")
    if not args.demo and not args.files:
        parser.error("supply at least one file or --demo")
    if args.files.count("-") > 1:
        parser.error("stdin may be used only once")
    try:
        inputs = (
            [(name, data.encode("utf-8")) for name, data in DEMO.items()]
            if args.demo else
            [(name, sys.stdin.buffer.read() if name == "-" else Path(name).read_bytes()) for name in args.files]
        )
        result = build(inputs, args.ignore_unmatched)
    except (OSError, TimelineError) as exc:
        print(f"time-flint: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=True))
    else:
        print("GROUP  EARLIEST UTC                  LATEST UTC (EXCLUSIVE)        SOURCE:LINE  MESSAGE")
        for event in result["events"]:
            print(f"{event['overlap_group']:>5}  {event['start_utc']:<29} {event['end_utc_exclusive']:<29} "
                  f"{visible(event['source'])}:{event['line']}  {visible(event['message'])}")
        print("Each group connects events through interval overlap; some pairwise orders may still be certain.")
        for item in result["omitted"]:
            print(f"OMITTED {visible(item['source'])}:{item['line']}: {visible(item['reason'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
