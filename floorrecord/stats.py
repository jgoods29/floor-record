"""Turn roll calls into the numbers shown on the site.

Definitions (also published on the About page):
- Party position: on each vote, whichever of Yea or Nay most of a party's voting members chose.
  A tie means the party had no position on that vote.
- With party: a member voted Yea or Nay and matched their own party's position.
- Party-split vote: most Republicans and most Democrats were on opposite sides.
- Attendance: share of roll calls where the member voted Yea, Nay or Present.
Special roll calls (quorum calls, the election of the Speaker) are left out of every statistic.
"""
import os
from collections import defaultdict
from statistics import median

from .explain import explain
from .ingest import bill_slug, parse_legis

PARTIES = ("R", "D")
DELEGATE_SEATS = {"DC", "PR", "GU", "VI", "AS", "MP"}
PARTY_NAMES = {"R": "Republican", "D": "Democrat", "I": "Independent"}


def pct(part, whole):
    return round(100.0 * part / whole, 1) if whole else None


def blank():
    return {"eligible": 0, "cast": 0, "counted": 0, "with": 0, "split_counted": 0, "split_with": 0}


def finish(s):
    s["attendance_pct"] = pct(s["cast"], s["eligible"])
    s["with_pct"] = pct(s["with"], s["counted"])
    s["against"] = s["counted"] - s["with"]
    s["against_pct"] = pct(s["against"], s["counted"])
    s["split_with_pct"] = pct(s["split_with"], s["split_counted"])
    s["split_against"] = s["split_counted"] - s["split_with"]
    s["split_against_pct"] = pct(s["split_against"], s["split_counted"])
    s["missed"] = s["eligible"] - s["cast"]
    return s


def party_positions(vote):
    tally = {p: {"yea": 0, "nay": 0} for p in PARTIES}
    for _, party, _, v in vote["positions"]:
        if party in tally and v in ("yea", "nay"):
            tally[party][v] += 1
    out = {}
    for p in PARTIES:
        y, n = tally[p]["yea"], tally[p]["nay"]
        out[p] = "yea" if y > n else "nay" if n > y else None
    return out


def compute(votes, members, bills, cfg):
    people = {}

    def person(bioguide, party, state, fallback_name):
        if bioguide not in people:
            base = dict(members.get(bioguide) or {})
            if not base:
                base = {"bioguide": bioguide, "name": fallback_name, "first": "", "last": fallback_name,
                        "state": state, "district": None, "since": "", "house_since": "", "term_end": "", "url": ""}
            base["bioguide"] = bioguide
            base.update({"all": blank(), "by_year": defaultdict(blank), "by_issue": defaultdict(blank),
                         "log": [], "sponsored": []})
            people[bioguide] = base
        p = people[bioguide]
        p["party"] = party  # the party on their most recent vote
        p["state"] = p.get("state") or state
        return p

    out_votes = []
    for vote in votes:
        info = explain(vote, bills)
        parsed = parse_legis(vote["legis"])
        slug = bill_slug(*parsed) if parsed else ""
        issue = (bills.get(slug) or {}).get("policy_area", "") if slug else ""
        standard = vote["kind"] == "standard"
        pos = party_positions(vote) if standard else {p: None for p in PARTIES}
        split = bool(pos["R"] and pos["D"] and pos["R"] != pos["D"])
        breakers, absent = [], []
        for bioguide, party, state, v in vote["positions"]:
            p = person(bioguide, party, state, vote["names"].get(bioguide, bioguide))
            with_party = None
            if standard:
                buckets = [p["all"], p["by_year"][vote["year"]]]
                if issue:
                    buckets.append(p["by_issue"][issue])
                for b in buckets:
                    b["eligible"] += 1
                    if v in ("yea", "nay", "present"):
                        b["cast"] += 1
                if party in PARTIES and pos[party] and v in ("yea", "nay"):
                    with_party = v == pos[party]
                    for b in buckets:
                        b["counted"] += 1
                        b["with"] += int(with_party)
                        if split:
                            b["split_counted"] += 1
                            b["split_with"] += int(with_party)
                    if not with_party:
                        breakers.append(bioguide)
                if v == "nv":
                    absent.append(bioguide)
            p["log"].append((len(out_votes), v, with_party))
        t = vote["totals"]
        margin = abs(t.get("yea", 0) - t.get("nay", 0))
        if standard and info["kind"] not in ("adjourn", "journal"):
            sides = ""
            if split:
                yes = "Republicans" if pos["R"] == "yea" else "Democrats"
                no = "Democrats" if yes == "Republicans" else "Republicans"
                sides = f"Most {yes} voted yes and most {no} voted no."
            elif pos["R"] and pos["R"] == pos["D"]:
                sides = f"Most members of both parties voted {'yes' if pos['R'] == 'yea' else 'no'}."
            info["sides"] = sides
            info["plain"] = " ".join(x for x in [info["gist"], sides] if x)
        vote_party = {b: party for b, party, _, _ in vote["positions"]}
        by_party = defaultdict(int)
        for b in breakers:
            by_party[vote_party[b]] += 1
        tags = []
        if standard and margin <= 15:
            tags.append(("close", "Close vote"))
        if split:
            tags.append(("split", "Parties split"))
        for party, n in sorted(by_party.items(), key=lambda kv: -kv[1]):
            # "Broke ranks" only means something when the parties were on opposite sides.
            if split and 1 <= n <= 80:
                word = PARTY_NAMES[party] + ("" if n == 1 else "s")
                tags.append(("broke", f"{n} {word} broke ranks"))
        if info["procedural"]:
            tags.append(("proc", "Procedural step"))
        out_votes.append({
            **{k: vote[k] for k in ("id", "year", "roll", "date", "time", "question", "legis", "desc", "type",
                                    "result", "kind", "totals", "by_party", "tally_matches", "source",
                                    "amendment", "amendment_author")},
            "info": info, "slug": slug, "issue": issue, "party_pos": pos, "split": split,
            "margin": margin, "tags": tags, "broke_by_party": dict(by_party),
            "breakers": breakers, "absent": absent, "positions": vote["positions"],
        })

    min_votes = int(os.environ.get("FLOORRECORD_MIN_VOTES", cfg.get("min_votes_for_ranking", 50)))
    for p in people.values():
        finish(p["all"])
        p["by_year"] = {y: finish(s) for y, s in sorted(p["by_year"].items(), reverse=True)}
        p["by_issue"] = {k: finish(s) for k, s in sorted(p["by_issue"].items(), key=lambda kv: -kv[1]["eligible"])}
        # Delegates from DC and the territories can vote only on some amendments, so they are not ranked.
        p["delegate"] = p["state"] in DELEGATE_SEATS
        p["ranked"] = p["all"]["eligible"] >= min_votes and not p["delegate"]
        p["party_name"] = PARTY_NAMES.get(p["party"], "Independent")
        d = p.get("district")
        p["seat"] = f"{p['state']}-{d}" if d not in (None, "") and d != 0 else (f"{p['state']} at large" if d == 0 else p["state"])
        words = [w for w in p["name"].replace(",", " ").split() if w[:1].isalpha()]
        p["initials"] = (words[0][:1] + words[-1][:1]).upper() if len(words) > 1 else p["name"][:2].upper()
        p["sort"] = (p.get("last") or p["name"]).lower()

    for slug, bill in bills.items():
        sponsor = bill.get("sponsor")
        if sponsor in people:
            people[sponsor]["sponsored"].append(slug)

    medians = {}
    for party in PARTIES:
        vals = [p["all"]["split_with_pct"] for p in people.values()
                if p["party"] == party and p["ranked"] and p["all"]["split_with_pct"] is not None]
        medians[party] = round(median(vals), 1) if vals else None
    att = [p["all"]["attendance_pct"] for p in people.values() if p["ranked"] and p["all"]["attendance_pct"] is not None]

    return {
        "votes": out_votes, "people": people,
        "medians": {"split_with_pct": medians, "attendance_pct": round(median(att), 1) if att else None},
        "min_votes": min_votes,
    }


def pick_featured(votes, pins=(), count=3, window_days=120):
    """The 'big votes' for the home page: pinned votes first, then recent votes that were close or
    saw many members cross party lines. Routine housekeeping votes never qualify."""
    from datetime import date
    by_id = {v["id"]: v for v in votes}
    if not votes:
        return []
    latest = max(date.fromisoformat(v["date"]) for v in votes)
    # A pin holds its place for 90 days, so the top of the home page cannot go stale.
    chosen = [by_id[p] for p in pins if p in by_id and (latest - date.fromisoformat(by_id[p]["date"])).days <= 90]
    scored = []
    for v in votes:
        if v in chosen or v["kind"] != "standard" or v["info"]["routine"]:
            continue
        age = (latest - date.fromisoformat(v["date"])).days
        crossed = len(v["breakers"])
        if age > window_days or not (v["margin"] <= 25 or (v["split"] and crossed >= 10)):
            continue
        score = max(0, 40 - v["margin"]) + min(crossed, 40) * 0.75 + max(0.0, 30 - age / 3) + (0 if v["info"]["procedural"] else 8)
        scored.append((score, v["date"], v["roll"], v))
    scored.sort(key=lambda x: x[:3], reverse=True)
    seen = {v["slug"] for v in chosen if v["slug"]}
    for _, _, _, v in scored:
        if len(chosen) >= count:
            break
        if (v["slug"] and v["slug"] in seen) or v["info"]["name"] in seen:
            continue  # one card per measure, and no near-identical twins
        seen.update({v["slug"], v["info"]["name"]})
        chosen.append(v)
    return chosen[:max(count, 3)]
