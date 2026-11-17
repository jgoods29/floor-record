"""The text of each bill, saved so it can be read and compared, not only its title and summary.

Why: the Senate sometimes takes a bill the House passed and replaces what is inside it. The official title
stays the same, so a description written from the title describes the wrong thing. Saving each version of
the text and comparing them shows when that has happened.

Source: the Government Publishing Office, https://www.govinfo.gov (no key needed). For each bill we keep
the version as introduced, as passed by its own chamber, as changed by the other chamber, and as sent to
the President. Each bill gets data/texts/<slug>.json (an outline of every version and how alike they are)
and, for versions that are not enormous, the full text in data/texts/full/<slug>.<version>.txt.gz.

What this cannot see: a replacement that has only been offered as an amendment and not yet passed. Its
text is printed in the Congressional Record, not as a bill version. Those are caught from the Senate vote
record instead (an amendment "in the nature of a substitute").
"""
import gzip
import html
import re
import time
import zlib
from datetime import date

from .common import DATA, NotFound, fetch, read_json, write_json

GOVINFO = "https://www.govinfo.gov/content/pkg/BILLS-{c}{kind}{n}{code}/html/BILLS-{c}{kind}{n}{code}.htm"
# Plain names for the stages we keep. Bills that start in the House and in the Senate use different codes.
STAGES = {
    "h": (("ih", "As introduced in the House"), ("eh", "As passed by the House"),
          ("eas", "As changed and passed by the Senate"), ("enr", "As sent to the President")),
    "s": (("is", "As introduced in the Senate"), ("es", "As passed by the Senate"),
          ("eah", "As changed and passed by the House"), ("enr", "As sent to the President")),
}
FULL_TEXT_LIMIT = 2_000_000   # characters; longer versions keep their outline and link only
REPLACED_BELOW = 0.25         # under a quarter of the later text coming from the earlier one: a person should look
KEPT_ABOVE = 0.5              # at least half of the earlier text still there: it was added to, not thrown out

HEADING = re.compile(r"^\s*((?:DIVISION|TITLE|Subtitle|SUBTITLE)\s+[A-Z0-9]+)\s*[-—]+\s*(.+?)\s*$", re.M)
SECTION = re.compile(r"^\s*(?:SEC\.|SECTION)\s+(\d+[A-Z]?)\.\s+(.+?)\s*$", re.M)
SHORT_TITLE = re.compile(r"may\s+be\s+cited\s+as\s+the\s+``(.+?)''", re.S)


def plain_text(page):
    """The bill's words from a govinfo page, without the HTML around them."""
    if isinstance(page, bytes):
        page = page.decode("utf-8", "replace")
    body = re.search(r"<pre>(.*)</pre>", page, re.S | re.I)
    if not body:   # govinfo answers "no such version" with an ordinary page, not an error code
        raise NotFound("no bill text on the page")
    text = html.unescape(re.sub(r"<[^>]+>", "", body.group(1)))
    return text.replace("\r", "")


def outline(text):
    """What is in a version: its short titles, its divisions and titles, and how many sections it has."""
    # The table of contents lists the same headings in lower case ("Sec. 101."); the patterns here match the
    # capitals used in the bill itself, and a heading that appears twice is kept once.
    body = text
    parts = []
    for m in HEADING.finditer(body):
        name = " ".join(m.group(2).split()).strip(". ")
        level, number = m.group(1).split()
        row = [f"{level.capitalize()} {number}", name[:160]]
        if name and row not in parts and len(name) > 2:
            parts.append(row)
    sections = {m.group(1) for m in SECTION.finditer(body)}
    titles = []
    for m in SHORT_TITLE.finditer(text):
        name = " ".join(m.group(1).split())
        if name not in titles and len(name) < 200:
            titles.append(name)
    return {"chars": len(text), "sections": len(sections), "short_titles": titles[:12], "parts": parts[:400]}


def _shingles(text, size=6):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {zlib.crc32(" ".join(words[i:i + size]).encode()) for i in range(0, max(len(words) - size + 1, 0))}


def compare(earlier, later):
    """How alike two versions are. `from_earlier` is the share of the later text that was already in the
    earlier one; `kept` is the share of the earlier text still present in the later one."""
    a, b = _shingles(earlier), _shingles(later)
    both = len(a & b)
    return {"from_earlier": round(both / len(b), 3) if b else 0.0, "kept": round(both / len(a), 3) if a else 0.0}


def version_url(congress, kind, number, code):
    return GOVINFO.format(c=congress, kind=kind, n=number, code=code)


def _verdict(result):
    """'similar': mostly the same bill. 'expanded': the earlier text is still inside but is now a small part of
    something much larger. 'replaced': most of the earlier text is gone and most of the later text is new."""
    if result["from_earlier"] >= REPLACED_BELOW:
        return "similar"
    return "expanded" if result["kept"] >= KEPT_ABOVE else "replaced"


def review(rec):
    """Compare the version a chamber passed with what the other chamber did to it."""
    have = {v["code"]: v for v in rec.get("versions", [])}
    own = next((c for c in ("eh", "es") if c in have), None) or next((c for c in ("ih", "is") if c in have), None)
    # The final version is the fairest comparison. Before there is one, use the other chamber's version only if it
    # replaced the whole text; a version that lists a few separate changes is not the whole bill.
    other = "enr" if "enr" in have else next((c for c in ("eas", "eah") if c in have and have[c].get("whole")), None)
    rec["compare"] = None
    rec["review"] = False
    if own and other and "_text" in have[own] and "_text" in have[other]:
        result = compare(have[own]["_text"], have[other]["_text"])
        result.update({"earlier": own, "later": other})
        result["verdict"] = _verdict(result)
        rec["compare"] = result
    elif rec.get("compare_saved"):
        rec["compare"] = rec["compare_saved"]
    rec["review"] = bool(rec["compare"]) and rec["compare"]["verdict"] != "similar"
    return rec


def collect(slug, congress, old=None, get=fetch, save_full=True):
    """Fetch any versions of one bill that are not on file yet. Returns the record for data/texts/<slug>.json."""
    kind, number = slug.rsplit("-", 1)
    old = old or {}
    known = {v["code"]: v for v in old.get("versions", [])}
    versions = []
    for code, label in STAGES["h" if kind.startswith("h") else "s"]:
        if code in known:
            row = dict(known[code])
            path = DATA / "texts" / "full" / f"{slug}.{code}.txt.gz"
            if path.exists():
                row["_text"] = gzip.decompress(path.read_bytes()).decode("utf-8")
            versions.append(row)
            continue
        url = version_url(congress, kind, number, code)
        try:
            text = plain_text(get(url))
        except NotFound:
            continue
        row = {"code": code, "stage": label, "url": url, "full_text": False}
        row.update(outline(text))
        if code in ("eas", "eah"):
            row["whole"] = bool(re.search(r"strike\s+(?:out\s+)?all\s+after\s+the\s+(?:enacting|resolving)\s+clause", text, re.I))
        row["_text"] = text
        if save_full and len(text) <= FULL_TEXT_LIMIT:
            path = DATA / "texts" / "full" / f"{slug}.{code}.txt.gz"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(gzip.compress(text.encode("utf-8"), mtime=0))
            row["full_text"] = True
        versions.append(row)
        time.sleep(0.3)
    rec = {"versions": versions, "checked": date.today().isoformat(), "compare_saved": old.get("compare")}
    review(rec)
    rec.pop("compare_saved", None)
    for v in rec["versions"]:
        v.pop("_text", None)
    return rec


def ingest_texts(bills, congress, first=(), log=print, per_run=40, get=fetch):
    """Save bill texts a batch at a time: bills named in `first` (Senate votes, comparison pages) go first,
    then the ones with the newest activity. A bill is looked at again only after something has happened to it."""
    folder = DATA / "texts"
    order = [s for s in dict.fromkeys(first) if s in bills]
    order += sorted((s for s in bills if s not in order), key=lambda s: bills[s].get("latest_action_date", ""), reverse=True)
    done, flagged = 0, []
    for slug in order:
        if done >= per_run:
            break
        old = read_json(folder / f"{slug}.json")
        if old and old.get("checked", "") >= (bills[slug].get("latest_action_date") or ""):
            continue
        try:
            rec = collect(slug, congress, old, get=get)
        except Exception as err:   # never let a text problem stop the vote update
            log(f"  ! text of {slug}: {err}")
            continue
        write_json(folder / f"{slug}.json", rec, compact=False)
        done += 1
        if rec["review"]:
            flagged.append(f"{slug} ({rec['compare']['verdict']})")
    log(f"Bill texts: {done} bills checked this run" + (f"; a person should look at: {', '.join(flagged)}" if flagged else ""))
    return done
