"""Bills a person should look at before the site's description of them is trusted.

Two signs that a bill's official title may no longer describe what is in it:
1. The Senate voted on an amendment "in the nature of a substitute", which replaces the whole text.
2. The saved texts show that a later version is mostly new (see texts.py).

A bill comes off the list when a person has dealt with it in editorial.json: a `carried` note, an approved
summary under `bills`, or an entry under `reviewed`. A substitute also clears by itself when the saved texts
show the bill stayed mostly the same.

Run `python -m floorrecord.review` to print the list.
"""
from .common import DATA, ROOT, read_json
from .ingest import bill_label, bill_slug

ACRONYMS = ("FBI CIA NSA DHS FEMA FAA FCC FDA USDA HUD IRS SEC FERC NEPA NASA NOAA EPA VA GI AI U.S. US NATO AUKUS CBDC FISA SNAP "
            "TANF HBCU NDAA DOD DOE GAO CBO OMB TSA ICE CBP ATF DEA SBA FHA NIH CDC HHS GME NPDES ESA II III IV VI VII VIII IX XI XII").split()


def substitute_votes(data=DATA):
    """Bill slug -> Senate votes on an amendment that replaces the whole text."""
    from .senate import measure_of
    found = {}
    for path in sorted((data / "senate").glob("*/*.json")):
        raw = read_json(path)
        purpose = ((raw.get("amendment") or {}).get("purpose") or "").lower()
        measure = measure_of(raw)
        if "nature of a substitute" in purpose and measure:
            found.setdefault(bill_slug(*measure), []).append(f"s{raw['year']}-{raw['roll']}")
    return found


def flagged(data=DATA, editorial=None):
    """Every bill with a sign that its text was replaced or greatly expanded: slug -> {why, checked}."""
    editorial = read_json(ROOT / "editorial.json", {}) if editorial is None else editorial
    handled = set(editorial.get("carried") or {}) | set(editorial.get("bills") or {}) | set(editorial.get("reviewed") or {})
    out = {}
    for slug, votes in substitute_votes(data).items():
        out[slug] = {"why": [f"The Senate voted on replacing the whole text ({', '.join(votes)})."], "verdict": "", "checked": slug in handled}
    for path in sorted((data / "texts").glob("*.json")):
        rec = read_json(path)
        slug, cmp = path.stem, rec.get("compare")
        if cmp and cmp["verdict"] != "similar":
            row = out.setdefault(slug, {"why": [], "verdict": "", "checked": slug in handled})
            row["verdict"] = cmp["verdict"]
            row["why"].append(f"Only {round(cmp['from_earlier'] * 100)}% of the later text ({cmp['later']}) was in the earlier one ({cmp['earlier']}).")
        elif cmp and slug in out and cmp["later"] in ("es", "eas", "enr"):
            out[slug]["checked"] = True   # the texts show the bill stayed mostly the same after the Senate's substitute
    return out


def to_review(data=DATA, editorial=None):
    bills = read_json(data / "bills.json", {})
    rows = []
    for slug, row in sorted(flagged(data, editorial).items()):
        if not row["checked"]:
            kind, number = slug.rsplit("-", 1)
            rows.append({"slug": slug, "label": bill_label(kind, int(number)), "title": (bills.get(slug) or {}).get("title", ""), "why": row["why"]})
    return rows


def nice_heading(name, keep=()):
    """Bill headings are printed in capitals. Put them in headline capitals, keeping known abbreviations and
    any word spelled a particular way in the bill's own short titles (for example "CBDC")."""
    from .explain import title_case
    spelled = {w.strip(",.").lower(): w.strip(",.") for t in keep for w in t.replace("-", " ").split() if any(c.isupper() for c in w[1:])}
    spelled.update({a.lower(): a for a in ACRONYMS})

    def fix(word):
        bits = word.split("-")
        return "-".join(spelled.get(b.strip(",.'").lower(), b) if b.strip(",.'").lower() in spelled else b for b in bits)
    return title_case(" ".join(fix(w) for w in name.lower().split(" ")))


def text_view(slug, data=DATA):
    """What the bill page shows about a bill's text: the parts of the latest version, and how the versions differ."""
    rec = read_json(data / "texts" / f"{slug}.json")
    if not rec or not rec.get("versions"):
        return None
    versions = rec["versions"]
    latest = versions[-1]
    keep = [t for v in versions for t in v.get("short_titles", [])]
    level = "Division" if any(p[0].startswith("Division") for p in latest["parts"]) else "Title"
    parts = [{"label": p[0], "name": nice_heading(p[1], keep)} for p in latest["parts"] if p[0].startswith(level)]
    inside = sum(1 for p in latest["parts"] if p[0].startswith("Title")) if level == "Division" else 0
    steps = [{"stage": v["stage"], "name": (v.get("short_titles") or [""])[0], "sections": v["sections"],
              "partial": v.get("whole") is False} for v in versions]
    changed = len({(s["name"], s["sections"]) for s in steps if not s["partial"]}) > 1
    cmp = rec.get("compare") or {}
    return {"latest": latest, "parts": parts, "inside": inside, "level": level.lower(), "steps": steps if changed else [],
            "verdict": cmp.get("verdict", ""), "share": round((cmp.get("from_earlier") or 0) * 100)}


if __name__ == "__main__":
    rows = to_review()
    print(f"{len(rows)} bill(s) to review")
    for r in rows:
        print(f"- {r['label']} ({r['slug']}): {r['title'][:80]}\n    " + " ".join(r["why"]))
