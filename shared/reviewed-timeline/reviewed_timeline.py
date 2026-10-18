#!/usr/bin/env python3
"""Offline Unicode evidence joined to an uncertainty-aware incident timeline."""
import argparse
import json
from pathlib import Path
import sys

from vendor import time_flint, unicode_lantern

MAX_FILES = 8
MAX_BYTES = unicode_lantern.MAX_BYTES
DEMO = [
    ("service.log", b"2026-10-18T10:00:00Z owner accepted\n"),
    ("queue.jsonl", b'{"timestamp":"2026-10-18T10:00Z",'
     b'"message":"owner and \\u043ewner \\u202ehidden\\u202c"}\n'),
]


def workspace_inputs(names):
    """Read each explicitly named regular file once, inside the current workspace."""
    if not 1 <= len(names) <= MAX_FILES:
        raise ValueError(f"supply 1..{MAX_FILES} files")
    root = Path.cwd().resolve()
    seen, inputs = set(), []
    for name in names:
        path = Path(name).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("input must be a regular file inside the current workspace")
        if path in seen:
            raise ValueError("the same resolved file was supplied twice")
        seen.add(path)
        with path.open("rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError(f"input exceeds {MAX_BYTES} bytes")
        inputs.append((path.relative_to(root).as_posix(), raw))
    return inputs


def build(inputs, ignore_unmatched=False):
    if not 1 <= len(inputs) <= MAX_FILES:
        raise ValueError(f"supply 1..{MAX_FILES} files")
    names = [name for name, _ in inputs]
    if len(set(names)) != len(names):
        raise ValueError("source names must be unique")
    reviews = [unicode_lantern.scan(raw, name, 100) for name, raw in inputs]
    try:
        timeline = time_flint.build(inputs, ignore_unmatched)
    except (OverflowError, RecursionError) as exc:
        raise ValueError("calendar boundary or input nesting exceeds supported range") from exc
    source_map = {name: review for name, review in zip(names, reviews)}
    for event in timeline["events"]:
        name = event["source"]
        message = event.pop("message")
        message_review = unicode_lantern.scan(message.encode("utf-8"), "<decoded-message>", 100)
        # A raw JSONL scan cannot see controls written as JSON escape sequences.
        event["message_escaped"] = unicode_lantern.escaped(message)
        event["message_review"] = message_review
        review = source_map[name]
        event["source_review_sha256"] = review["sha256"]
        event["source_findings_on_line"] = [
            f for f in review["findings"] if f["line"] == event["line"]]
        event["source_listing_truncated"] = review["truncated"]
    for entry in timeline["sources"] + timeline["events"] + timeline["omitted"]:
        entry["source"] = unicode_lantern.escaped(entry["source"])
    needs_review = any(r["finding_count"] for r in reviews) or any(
        e["message_review"]["finding_count"] for e in timeline["events"])
    return {
        "schema_version": 1,
        "tool": "reviewed-timeline",
        "assessment": "review-required" if needs_review else "no-covered-patterns-found",
        "source_reviews": reviews,
        "timeline": timeline,
        "limitations": [
            "Synthetic demo only; user files are not assumed honest or complete.",
            "Source findings use original UTF-8 byte offsets; decoded-message findings use message-local offsets.",
            "Message strings and source names are unicode_escape representations, not raw display text.",
            "Findings are heuristic and capped at 100 per source and per message; inspect truncated fields.",
            "Overlap groups connect uncertain intervals; presentation order is not causal order.",
            "Clock skew, full Unicode confusables, multiline events and cross-file identifier collisions are not modeled.",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--ignore-unmatched", action="store_true")
    args = parser.parse_args(argv)
    if args.demo and args.files:
        parser.error("--demo cannot be combined with files")
    try:
        result = build(DEMO if args.demo else workspace_inputs(args.files), args.ignore_unmatched)
    except (OSError, UnicodeError, ValueError, time_flint.TimelineError, RecursionError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2))
    return 1 if result["assessment"] == "review-required" and not args.demo else 0


if __name__ == "__main__":
    raise SystemExit(main())
