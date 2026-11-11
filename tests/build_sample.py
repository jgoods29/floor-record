"""Build a one-vote sample site from the Roll Call 317 fixture, to check the pages by eye.

Usage: python tests/build_sample.py [path/to/legislators-current.json]
Writes to .cache/sample-data and .cache/sample-site (never touches data/ or site/).
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ["FLOORRECORD_DATA"] = str(ROOT / ".cache" / "sample-data")
os.environ["FLOORRECORD_SITE"] = str(ROOT / ".cache" / "sample-site")
os.environ.setdefault("FLOORRECORD_MIN_VOTES", "1")
sys.path.insert(0, str(ROOT))

from floorrecord import build, ingest  # noqa: E402
from floorrecord.common import DATA, write_json  # noqa: E402

vote = ingest.parse_roll_call((ROOT / "tests" / "fixtures" / "roll317_reconstructed.xml").read_bytes(), 2026)
write_json(DATA / "votes" / "2026" / "0317.json", vote)
if len(sys.argv) > 1:
    members = {}
    for person in json.loads(Path(sys.argv[1]).read_text()):
        rec = ingest._member_from_legislator(person)
        if rec:
            members[rec["bioguide"]] = rec
    write_json(DATA / "members.json", members)
else:
    ingest.ingest_members([vote])
build.main()
