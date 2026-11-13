import json
"""Collect official data.

Sources
- House roll calls: Office of the Clerk, https://clerk.house.gov/evs/{year}/roll{NNN}.xml
- Members: the public-domain unitedstates/congress-legislators project
- Bills (optional, needs CONGRESS_API_KEY): the Library of Congress API, https://api.congress.gov

Run:  python -m floorrecord.ingest
Only new roll calls are downloaded; everything already in data/ is kept.
"""
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import date, datetime

from .common import DATA, NotFound, config, fetch, read_json, write_json

CLERK_URL = "https://clerk.house.gov/evs/{year}/roll{roll:03d}.xml"
LEGIS_URL = "https://raw.githubusercontent.com/unitedstates/congress-legislators/gh-pages/legislators-{which}.json"
CONGRESS_API = "https://api.congress.gov/v3"

VOTE_WORDS = {
    "yea": "yea", "aye": "yea",
    "nay": "nay", "no": "nay",
    "present": "present",
    "not voting": "nv",
}

BILL_TYPES = {
    "H R": "hr", "H RES": "hres", "H J RES": "hjres", "H CON RES": "hconres",
    "S": "s", "S RES": "sres", "S J RES": "sjres", "S CON RES": "sconres",
}
BILL_LABELS = {
    "hr": "H.R.", "hres": "H.Res.", "hjres": "H.J.Res.", "hconres": "H.Con.Res.",
    "s": "S.", "sres": "S.Res.", "sjres": "S.J.Res.", "sconres": "S.Con.Res.",
}


def parse_legis(legis):
    """'H RES 1655' -> ('hres', 1655). Returns None for QUORUM, JOURNAL, etc."""
    m = re.match(r"^\s*([A-Z ]+?)\s+(\d+)\s*$", legis or "")
    if not m:
        return None
    kind = BILL_TYPES.get(re.sub(r"\s+", " ", m.group(1)).strip())
    if not kind:
        return None
    return kind, int(m.group(2))


def bill_slug(kind, number):
    return f"{kind}-{number}"


def bill_label(kind, number):
    return f"{BILL_LABELS[kind]} {number}"


def _text(node, path, default=""):
    found = node.find(path)
    if found is None or found.text is None:
        return default
    return found.text.strip()


def _int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def parse_roll_call(xml_bytes, year):
    """Turn one Clerk XML file into a compact dict. Raises ValueError if it is not a roll call."""
    root = ET.fromstring(xml_bytes)
    meta = root.find("vote-metadata")
    if meta is None or not _text(meta, "rollcall-num"):
        raise ValueError("not a roll call document")
    roll = int(_text(meta, "rollcall-num"))
    raw_date = _text(meta, "action-date")
    try:
        iso_date = datetime.strptime(raw_date, "%d-%b-%Y").date().isoformat()
    except ValueError:
        iso_date = f"{year}-01-01"
    time_node = meta.find("action-time")
    clock = (time_node.text or "").strip() if time_node is not None else ""

    official = {}
    by_party = {}
    totals = meta.find("vote-totals")
    if totals is not None:
        for row in totals.findall("totals-by-party"):
            party = _text(row, "party")
            if not party:
                continue
            by_party[party[0].upper()] = {
                "yea": _int(_text(row, "yea-total")), "nay": _int(_text(row, "nay-total")),
                "present": _int(_text(row, "present-total")), "nv": _int(_text(row, "not-voting-total")),
            }
        tv = totals.find("totals-by-vote")
        if tv is not None:
            official = {
                "yea": _int(_text(tv, "yea-total")), "nay": _int(_text(tv, "nay-total")),
                "present": _int(_text(tv, "present-total")), "nv": _int(_text(tv, "not-voting-total")),
            }

    positions = []
    names = {}
    other = False
    for rec in root.iter("recorded-vote"):
        leg = rec.find("legislator")
        if leg is None:
            continue
        bioguide = leg.get("name-id") or ""
        if not bioguide:
            continue
        word = _text(rec, "vote")
        vote = VOTE_WORDS.get(word.lower())
        if vote is None:
            # e.g. a candidate's name in the election of the Speaker
            vote = "other:" + word
            other = True
        positions.append([bioguide, (leg.get("party") or "?")[:1].upper(), leg.get("state") or "", vote])
        names[bioguide] = (leg.get("unaccented-name") or leg.text or "").strip()

    counted = {"yea": 0, "nay": 0, "present": 0, "nv": 0}
    for _, _, _, v in positions:
        if v in counted:
            counted[v] += 1
    if not official:
        official = dict(counted)

    question = _text(meta, "vote-question")
    legis = _text(meta, "legis-num")
    vote_type = _text(meta, "vote-type")
    kind = "standard"
    if other or "QUORUM" in vote_type.upper() or legis.upper() == "QUORUM" or "election of the speaker" in question.lower():
        kind = "special"

    return {
        "id": f"{year}-{roll}", "year": year, "roll": roll,
        "congress": _int(_text(meta, "congress")), "session": _text(meta, "session"),
        "date": iso_date, "time": clock,
        "question": question, "legis": legis, "desc": _text(meta, "vote-desc"),
        "amendment": _text(meta, "amendment-num"), "amendment_author": _text(meta, "amendment-author"),
        "type": vote_type, "result": _text(meta, "vote-result"),
        "kind": kind,
        "totals": official, "by_party": by_party,
        "tally_matches": all(counted[k] == official.get(k, 0) for k in counted) if kind == "standard" else True,
        "positions": positions, "names": names,
        "source": CLERK_URL.format(year=year, roll=roll),
    }


def ingest_house(years, log=print):
    new = 0
    for year in years:
        folder = DATA / "votes" / str(year)
        folder.mkdir(parents=True, exist_ok=True)
        have = sorted(int(p.stem) for p in folder.glob("*.json"))
        roll = (have[-1] + 1) if have else 1
        misses = 0
        while misses < 2:
            url = CLERK_URL.format(year=year, roll=roll)
            try:
                vote = parse_roll_call(fetch(url), year)
            except NotFound:
                misses += 1
                roll += 1
                continue
            except (ValueError, ET.ParseError):
                # The Clerk sometimes answers a missing roll call with an HTML page.
                misses += 1
                roll += 1
                continue
            misses = 0
            write_json(folder / f"{roll:04d}.json", vote)
            if not vote["tally_matches"]:
                log(f"  ! {year} roll {roll}: counted positions differ from the official totals")
            new += 1
            roll += 1
            time.sleep(0.25)
        log(f"House {year}: {len(have)} roll calls on file, {new} new so far")
    return new


def load_votes(years=None):
    votes = []
    base = DATA / "votes"
    if not base.exists():
        return votes
    for folder in sorted(base.iterdir()):
        if not folder.is_dir():
            continue
        if years and int(folder.name) not in years:
            continue
        for path in sorted(folder.glob("*.json")):
            votes.append(read_json(path))
    votes.sort(key=lambda v: (v["date"], v["roll"]))
    return votes


def _member_from_legislator(person):
    terms = person.get("terms") or []
    reps = [t for t in terms if t.get("type") == "rep"]
    if not reps:
        return None
    last = reps[-1]
    name = person.get("name", {})
    full = name.get("official_full") or " ".join(x for x in [name.get("first"), name.get("last")] if x)
    party = last.get("party") or ""
    return {
        "bioguide": person["id"]["bioguide"],
        "name": full, "first": name.get("first", ""), "last": name.get("last", ""),
        "party": {"Republican": "R", "Democrat": "D"}.get(party, "I"),
        "state": last.get("state", ""), "district": last.get("district"),
        "since": terms[0].get("start", ""), "house_since": reps[0].get("start", ""),
        "term_end": last.get("end", ""),
        "url": last.get("url", ""),
        "phone": last.get("phone", ""), "contact_form": last.get("contact_form", ""),
        "office": last.get("address", ""), "caucus": {"Republican": "R", "Democrat": "D"}.get(last.get("caucus", ""), ""),
    }


def ingest_members(votes, log=print):
    """Details for every member who appears in at least one roll call."""
    needed = set()
    for v in votes:
        for bioguide, _, _, _ in v["positions"]:
            needed.add(bioguide)
    members = {}
    for which in ("current", "historical"):
        if which == "historical" and needed <= set(members):
            break
        try:
            people = __import__("json").loads(fetch(LEGIS_URL.format(which=which), timeout=120))
        except Exception as err:  # keep going with what the roll calls themselves tell us
            log(f"  ! could not load {which} legislators: {err}")
            continue
        for person in people:
            bioguide = person.get("id", {}).get("bioguide")
            if bioguide in needed and bioguide not in members:
                rec = _member_from_legislator(person)
                if rec:
                    members[bioguide] = rec
    write_json(DATA / "members.json", members)
    log(f"Members: {len(members)} of {len(needed)} matched to the legislators list")
    return members


COMMITTEE_URL = "https://raw.githubusercontent.com/unitedstates/congress-legislators/gh-pages/{which}.json"
ROLE_NAMES = (("vice", "Vice Chair"), ("ranking", "Ranking Member"), ("cochair", "Co-Chair"), ("chair", "Chair"), ("ex officio", "Ex Officio"))


def _roster(rows):
    out = []
    for r in rows or []:
        title = (r.get("title") or "").lower()
        role = next((name for words, name in ROLE_NAMES if words in title), "")
        out.append({"id": r.get("bioguide", ""), "name": r.get("name", ""), "side": "maj" if r.get("party") == "majority" else "min",
                    "rank": r.get("rank") or 999, "role": role})
    return sorted(out, key=lambda r: (r["side"], r["rank"]))


def ingest_committees(log=print):
    """House committees, subcommittees and who sits on them, from the public congress-legislators project."""
    try:
        listing = json.loads(fetch(COMMITTEE_URL.format(which="committees-current"), timeout=60))
        membership = json.loads(fetch(COMMITTEE_URL.format(which="committee-membership-current"), timeout=60))
    except Exception as err:
        log(f"  ! committees: {err}")
        return read_json(DATA / "committees.json", [])
    out = []
    for c in listing:
        if c.get("type") != "house" or not membership.get(c["thomas_id"]):
            continue
        subs = [{"id": c["thomas_id"] + sub["thomas_id"], "name": sub["name"], "members": _roster(membership.get(c["thomas_id"] + sub["thomas_id"]))}
                for sub in c.get("subcommittees") or [] if membership.get(c["thomas_id"] + sub["thomas_id"])]
        out.append({"id": c["thomas_id"], "name": c["name"], "kind": "select" if "select" in c["name"].lower() else "standing",
                    "url": c.get("url", ""), "members": _roster(membership[c["thomas_id"]]),
                    "subs": sorted(subs, key=lambda x: x["name"])})
    if out:
        write_json(DATA / "committees.json", out)
        log(f"Committees: {len(out)} committees, {sum(len(c['subs']) for c in out)} subcommittees")
    return out


FLOOR_URL = "https://docs.house.gov/billsthisweek/{d}/{d}.xml"
FLOOR_KINDS = (("suspension", "fast"), ("pursuant to a rule", "rule"))


def legis_from_label(text):
    """'H.R. 3074 ' or 'H. Con. Res. 12' -> ('hr', 3074). None when it is not a numbered measure."""
    return parse_legis(re.sub(r"\s+", " ", (text or "").replace(".", " ")).strip().upper())


def parse_floor_schedule(xml_text):
    """The House's own weekly list of bills that may come to the floor (docs.house.gov)."""
    root = ET.fromstring(xml_text)
    items = []
    for cat in root.iter("category"):
        kind_text = (cat.get("type") or "").lower()
        how = next((code for words, code in FLOOR_KINDS if words in kind_text), "other")
        for it in cat.iter("floor-item"):
            if (it.get("remove-date") or "").strip():
                continue
            label = " ".join((it.findtext("legis-num") or "").split())
            title = " ".join((it.findtext("floor-text") or "").split())
            if not label and not title:
                continue
            parsed = legis_from_label(label)
            doc = next((f.get("doc-url", "") for f in it.iter("file") if (f.get("doc-type") or "").upper() == "PDF"), "")
            items.append({"label": label, "title": title, "how": how, "category": cat.get("type") or "",
                          "slug": bill_slug(*parsed) if parsed else "", "doc": doc.replace("http://", "https://"),
                          "added": (it.get("add-date") or "")[:10]})
    return {"week": (root.get("week-date") or "")[:10], "updated": (root.get("update-date") or "")[:10], "items": items}


def ingest_upcoming(log=print, today=None):
    """This week's and next week's posted floor schedule. Keeps the last good copy if the House site is down."""
    from datetime import timedelta
    today = today or date.today()
    monday = today - timedelta(days=today.weekday())
    weeks = []
    for start in (monday, monday + timedelta(days=7)):
        d = start.strftime("%Y%m%d")
        try:
            week = parse_floor_schedule(fetch(FLOOR_URL.format(d=d), timeout=60))
        except NotFound:
            continue  # nothing posted for that week (yet)
        except Exception as err:
            log(f"  ! floor schedule {d}: {err}")
            return read_json(DATA / "upcoming.json", {})
        week["week"] = week["week"] or start.isoformat()
        weeks.append(week)
    out = {"fetched": today.isoformat(), "weeks": weeks}
    write_json(DATA / "upcoming.json", out)
    log(f"Upcoming: {sum(len(w['items']) for w in weeks)} items posted across {len(weeks)} week(s)")
    return out


def _api(path, key, **params):
    import json
    from urllib.parse import urlencode
    params.update({"api_key": key, "format": "json"})
    return json.loads(fetch(f"{CONGRESS_API}{path}?{urlencode(params)}"))


def ingest_bills(votes, congress, log=print, limit=400, also=()):
    """Titles, sponsors, policy areas and official summaries from Congress.gov. Optional."""
    key = os.environ.get("CONGRESS_API_KEY", "").strip()
    bills = read_json(DATA / "bills.json", {})
    if not key:
        log("Bills: CONGRESS_API_KEY not set, skipping (pages fall back to the Clerk's titles)")
        return bills
    recent_cutoff = date.today().toordinal() - 30
    wanted = {}
    for v in votes:
        parsed = parse_legis(v["legis"])
        if not parsed:
            continue
        slug = bill_slug(*parsed)
        is_recent = date.fromisoformat(v["date"]).toordinal() >= recent_cutoff
        if slug not in bills or is_recent:
            wanted[slug] = parsed
    for slug in also:  # bills on the posted schedule that have not had a vote yet
        if slug and (slug not in bills or bills[slug].get("fetched", "") < date.fromordinal(recent_cutoff + 23).isoformat()):
            kind, number = slug.rsplit("-", 1)
            wanted[slug] = (kind, int(number))
    done = 0
    for slug, (kind, number) in list(wanted.items())[:limit]:
        try:
            bill = _api(f"/bill/{congress}/{kind}/{number}", key).get("bill", {})
        except Exception as err:
            log(f"  ! {slug}: {err}")
            continue
        sponsor = (bill.get("sponsors") or [{}])[0]
        rec = {
            "title": bill.get("title", ""),
            "introduced": bill.get("introducedDate", ""),
            "sponsor": sponsor.get("bioguideId", ""), "sponsor_name": sponsor.get("fullName", ""),
            "policy_area": (bill.get("policyArea") or {}).get("name", ""),
            "latest_action": (bill.get("latestAction") or {}).get("text", ""),
            "latest_action_date": (bill.get("latestAction") or {}).get("actionDate", ""),
            "official_summary": bills.get(slug, {}).get("official_summary", ""),
            "fetched": date.today().isoformat(),
        }
        try:
            summaries = _api(f"/bill/{congress}/{kind}/{number}/summaries", key).get("summaries") or []
            if summaries:
                import html
                text = html.unescape(re.sub(r"<[^>]+>", " ", summaries[-1].get("text", "")))
                rec["official_summary"] = " ".join(text.split())
        except Exception:
            pass
        bills[slug] = rec
        done += 1
        time.sleep(0.2)
    write_json(DATA / "bills.json", bills)
    log(f"Bills: {done} updated, {len(bills)} on file")
    return bills


def _legislation_rows(payload, key, congress):
    rows = []
    for item in payload.get(key) or []:
        kind = (item.get("type") or "").lower()
        if item.get("congress") != congress or kind not in BILL_LABELS or not item.get("number"):
            continue  # skips amendments and earlier Congresses
        action = item.get("latestAction") or {}
        rows.append([kind, int(item["number"]), (item.get("title") or "")[:220], item.get("introducedDate") or "",
                     action.get("actionDate") or "", (action.get("text") or "")[:200],
                     (item.get("policyArea") or {}).get("name") or ""])
    return rows


def ingest_member_bills(bioguides, congress, log=print, per_run=40, max_age_days=10):
    """What each member introduced and signed onto this Congress, from Congress.gov. Optional.

    Refreshes the stalest members first and stops after `per_run` members. Each member takes several
    requests, so a small batch keeps a routine update to a few minutes; with six runs a day the whole
    House is refreshed about every two days.
    """
    key = os.environ.get("CONGRESS_API_KEY", "").strip()
    if not key:
        log("Member bills: CONGRESS_API_KEY not set, skipping")
        return
    folder = DATA / "member_bills"
    folder.mkdir(parents=True, exist_ok=True)
    today = date.today()
    ages = []
    for b in sorted(bioguides):
        have = read_json(folder / f"{b}.json")
        age = (today - date.fromisoformat(have["fetched"])).days if have else 10 ** 6
        if age >= max_age_days:
            ages.append((-age, b))
    done = 0
    for _, b in sorted(ages)[:per_run]:
        rec = {"fetched": today.isoformat(), "sponsored": [], "cosponsored": []}
        try:
            for field, path, pages in (("sponsored", "sponsored-legislation", 2), ("cosponsored", "cosponsored-legislation", 4)):
                payload_key = "sponsoredLegislation" if field == "sponsored" else "cosponsoredLegislation"
                for page in range(pages):
                    payload = _api(f"/member/{b}/{path}", key, limit=250, offset=page * 250)
                    items = payload.get(payload_key) or []
                    rec[field] += _legislation_rows(payload, payload_key, congress)
                    # Lists come newest first; stop once a page reaches an earlier Congress or runs out.
                    if len(items) < 250 or any((i.get("congress") or congress) < congress for i in items):
                        break
                    time.sleep(0.15)
        except Exception as err:
            log(f"  ! bills for {b}: {err}")
            continue
        write_json(folder / f"{b}.json", rec)
        done += 1
        time.sleep(0.15)
    log(f"Member bills: {done} members refreshed, {len(ages) - done} still waiting")


def main():
    cfg = config()
    ingest_house(cfg["years"])
    votes = load_votes(cfg["years"])
    if not votes:
        print("No roll calls found. Check the network connection and the years in config.json.")
        sys.exit(1)
    ingest_members(votes)
    ingest_committees()
    upcoming = ingest_upcoming()
    ingest_bills(votes, cfg["congress"], also=[i["slug"] for w in upcoming.get("weeks", []) for i in w["items"]])
    ingest_member_bills({p[0] for v in votes for p in v["positions"]}, cfg["congress"])
    from .explain import ai_summaries, ai_vote_lines
    ai_summaries(votes, cfg)
    ai_vote_lines(votes, cfg)
    print(f"Done: {len(votes)} roll calls on file.")


if __name__ == "__main__":
    main()
