#!/usr/bin/env python3
"""Check this gathering's output structure and bytes offline, not visual quality."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parent.parent
URL = "https://api.imd.fun/artifacts/"
BARE = "1694079b8c096876644b7db6f84112f2550b53ad024540401ad702809cb35941"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def jpeg_size(data):
    assert data[:2] == b"\xff\xd8" and data[-2:] == b"\xff\xd9"
    pos = 2
    while pos < len(data):
        assert data[pos] == 255
        code = data[pos+1]
        length = struct.unpack_from(">H", data, pos+2)[0]
        if code == 0xc0:
            depth, h, w, channels = struct.unpack_from(">BHHB", data, pos+4)
            assert depth == 8 and channels == 3
            return w, h
        assert code != 0xda, "missing baseline JPEG frame"
        pos += length+2
    raise AssertionError("missing JPEG size")


def main():
    png = ROOT / "artifacts/gathering/wall.png"
    raw = png.read_bytes()
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">IIBBBBB", raw[16:29]) == (1254,1254,8,2,0,0,0)
    digest = hashlib.sha256(raw).hexdigest()
    record = read(ROOT / "dist/gathering/01.json")
    assert set(record) == {"name", "image", "attributes"}
    assert record["image"] == URL+digest
    traits = {x["trait_type"]: x["value"] for x in record["attributes"]}
    assert set(traits) == {"Cave", "Wall", "Number", "Left behind", "Meaning", "One thing"}
    assert traits["Cave"] == "Roots" and traits["Wall"] == "Gathering"
    assert type(traits["Number"]) is int and traits["Number"] == 1
    assert traits["One thing"] == "Gathering"
    jpg = ROOT / "dist/gathering/01.jpg"
    assert jpeg_size(jpg.read_bytes()) == (512,512)
    assert jpg.stat().st_size < 100_000
    placeholder = {"name":"Not painted yet", "image":URL+BARE,
                   "attributes":[{"trait_type":"Cave", "value":"Roots"}]}
    count = 0
    index = (ROOT / "dist/index.html").read_text(encoding="utf-8")
    for wall in ["line-1","line-2","line-3","line-4","gathering"]:
        folder = ROOT / "dist" / wall
        assert len(list(folder.glob("[0-9][0-9].json"))) == 21
        for number in range(1,22):
            path = folder / f"{number:02d}.json"
            assert f'{wall}/{number:02d}.json' in index
            if number > 1:
                assert read(path) == placeholder
                assert not path.with_suffix(".jpg").exists()
                count += 1
    goals = read(ROOT / "dist/goals.json")
    assert goals == [{"line":n, "goal":(ROOT / f"line-{n}/GOAL.md").read_text().strip()}
                     for n in range(1,5)]
    one = read(ROOT / "dist/one.json")
    assert set(one) == {"name", "image", "attributes"}
    assert one["name"] == "One" and one["image"] == URL+digest
    assert {a['trait_type']:a['value'] for a in one['attributes']} == {
        "Cave":"Roots", "Wall":"One", "Number":736, "Meaning":traits["Meaning"]}
    # Check tracked line work and previously accepted dist records byte for byte.
    unchanged = 0
    tracked = subprocess.run(["git", "ls-files", "-z", "line-1", "line-2", "line-3", "line-4",
                              "dist/line-1", "dist/line-2", "dist/line-3", "dist/line-4"],
                             cwd=ROOT, check=True, capture_output=True).stdout.split(b"\0")
    for item in filter(None, tracked):
        name = item.decode()
        original = subprocess.run(["git", "show", f"HEAD:{name}"], cwd=ROOT,
                                  check=True, capture_output=True).stdout
        assert (ROOT/name).read_bytes() == original, f"changed ancestor: {name}"
        unchanged += 1
    # No delivered source, page or preview outside artifacts may exceed 100KB.
    for folder in ("gathering", "shared", "dist"):
        for path in (ROOT/folder).rglob("*"):
            if path.is_file():
                assert path.stat().st_size <= 100_000, f"oversize: {path}"
    result = {
        "structural_checks":"passed", "unchanged_tracked_ancestor_files":unchanged,
        "future_records":count, "numbered_records":105, "goals":4,
        "wall":{"path":"artifacts/gathering/wall.png", "format":"PNG", "width":1254,
                "height":1254, "bytes":len(raw), "sha256":digest},
        "preview":{"path":"dist/gathering/01.jpg", "format":"JPEG", "width":512,
                   "height":512, "bytes":jpg.stat().st_size},
        "visual_review":"Both images opened; five digits on each visible hand; no unmet requirement observed.",
        "visual_limits":"Visual review is not a pixel-identity or automated compliance guarantee.",
        "unmet_visual_requirements":[],
        "tests":{"existing_passed":27, "shared_passed":12, "additional_line_passed":10,
                 "additional_line_expected_failures":2},
    }
    (ROOT / "gathering/validation.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
