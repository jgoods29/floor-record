"""Build the static website from data/ into site/.

Run:  python -m floorrecord.build
"""
import shutil
from collections import defaultdict
from datetime import date, datetime, timezone

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .common import DATA, ROOT, SITE, config, read_json, write_json
from .explain import member_phrase
from .ingest import BILL_LABELS, bill_label, load_votes
from .stats import PARTY_NAMES, compute

STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California", "CO": "Colorado",
    "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
    "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", "NC": "North Carolina",
    "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas",
    "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia", "PR": "Puerto Rico", "GU": "Guam",
    "VI": "U.S. Virgin Islands", "AS": "American Samoa", "MP": "Northern Mariana Islands",
}
KIND_NAMES = {
    "hr": ("House bill", "To become law it must pass the House and Senate and be signed by the President."),
    "s": ("Senate bill", "To become law it must pass the Senate and House and be signed by the President."),
    "hres": ("House resolution", "It needs only the House, not the Senate or the President."),
    "sres": ("Senate resolution", "It needs only the Senate."),
    "hjres": ("House joint resolution", "Like a bill, it must pass both chambers; most also need the President's signature."),
    "sjres": ("Senate joint resolution", "Like a bill, it must pass both chambers; most also need the President's signature."),
    "hconres": ("House concurrent resolution", "It needs both chambers but not the President, and does not become law."),
    "sconres": ("Senate concurrent resolution", "It needs both chambers but not the President, and does not become law."),
}
CONGRESS_PATH = {
    "hr": "house-bill", "s": "senate-bill", "hres": "house-resolution", "sres": "senate-resolution",
    "hjres": "house-joint-resolution", "sjres": "senate-joint-resolution",
    "hconres": "house-concurrent-resolution", "sconres": "senate-concurrent-resolution",
}
ORDER = {"yea": 0, "nay": 1, "present": 2, "nv": 3}


def nicedate(value):
    try:
        d = date.fromisoformat(str(value)[:10])
    except ValueError:
        return value
    return f"{d.strftime('%b')} {d.day}, {d.year}"


def ordinal(n):
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def capfirst(s):
    return s[:1].upper() + s[1:] if s else s


def main():
    cfg = config()
    votes_raw = load_votes(cfg["years"])
    if not votes_raw:
        raise SystemExit("No roll calls in data/. Run `python -m floorrecord.ingest` first.")
    members = read_json(DATA / "members.json", {})
    bills = read_json(DATA / "bills.json", {})
    summaries = read_json(DATA / "summaries.json", {})
    result = compute(votes_raw, members, bills, cfg)
    votes, people = result["votes"], result["people"]

    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape(["html"]),
                      trim_blocks=True, lstrip_blocks=True)
    env.filters.update(nicedate=nicedate, comma=lambda n: f"{n:,}", capfirst=capfirst,
                       times=lambda n: "once" if n == 1 else f"{n:,} times")
    years = sorted({v["year"] for v in votes})
    span = str(years[0]) if len(years) == 1 else f"{years[0]}–{years[-1]}"
    shared = {
        "site": cfg, "span": span, "nvotes": len(votes), "npeople": len(people),
        "updated": nicedate(datetime.now(timezone.utc).date().isoformat()), "min_votes": result["min_votes"],
        "state_names": STATES,
    }

    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    shutil.copytree(ROOT / "static", SITE / "static")
    (SITE / ".nojekyll").write_text("")

    def render(path, template, depth, **ctx):
        out = SITE / path
        out.parent.mkdir(parents=True, exist_ok=True)
        html = env.get_template(template).render(root="../" * depth, **shared, **ctx)
        out.write_text(html)

    # ---- measures
    measures = {}
    for v in votes:
        if not v["slug"]:
            continue
        kind, number = v["slug"].rsplit("-", 1)
        m = measures.setdefault(v["slug"], {
            "slug": v["slug"], "kind": kind, "number": int(number), "label": bill_label(kind, int(number)),
            "rec": bills.get(v["slug"], {}), "votes": [], "title": "",
        })
        m["votes"].append(v)
    for m in measures.values():
        m["votes"].sort(key=lambda v: (v["date"], v["roll"]), reverse=True)
        m["title"] = m["rec"].get("title") or next((v["desc"] for v in m["votes"] if v["desc"]), m["label"])
        m["kind_name"], m["kind_note"] = KIND_NAMES[m["kind"]]
        m["congress_url"] = (f"https://www.congress.gov/bill/{ordinal(cfg['congress'])}-congress/"
                             f"{CONGRESS_PATH[m['kind']]}/{m['number']}")

    newest = sorted(votes, key=lambda v: (v["date"], v["roll"]), reverse=True)
    ranked = [p for p in people.values() if p["ranked"]]

    # ---- home, lists
    mavericks = sorted([p for p in ranked if p["all"]["split_against_pct"] is not None],
                       key=lambda p: -p["all"]["split_against_pct"])[:5]
    render("index.html", "index.html", 0, section="home", latest=newest[:8], mavericks=mavericks)
    render("votes/index.html", "votes.html", 1, section="votes", votes=newest)
    by_state = defaultdict(list)
    for p in people.values():
        by_state[p["state"]].append(p)
    states = [(s, sorted(g, key=lambda p: (p.get("district") or 0, p["sort"])))
              for s, g in sorted(by_state.items(), key=lambda kv: STATES.get(kv[0], kv[0]))]
    render("members/index.html", "members.html", 1, section="members", states=states)
    bill_list = sorted(measures.values(), key=lambda m: (m["votes"][0]["date"], m["votes"][0]["roll"]), reverse=True)
    render("bills/index.html", "bills.html", 1, section="bills", bills=bill_list)
    render("about/index.html", "about.html", 1, section="about")
    render("404.html", "404.html", 0, section="")

    # ---- vote pages
    for v in votes:
        ctx = {"v": v, "section": "votes", "bill": measures.get(v["slug"]), "ai": summaries.get(v["slug"])}
        sponsor_id = (bills.get(v["slug"]) or {}).get("sponsor")
        ctx["sponsor"] = people.get(sponsor_id)
        seats = sorted(v["positions"], key=lambda r: (ORDER.get(r[3], 4), {"R": 0, "D": 1}.get(r[1], 2), people[r[0]]["sort"]))
        ctx["seats"] = [(r[3] if r[3] in ORDER else "nv", f"{people[r[0]]['name']} ({r[1]}-{r[2]}): {r[3]}") for r in seats]
        ctx["parties"] = []
        for code in ("R", "D", "I"):
            t = v["by_party"].get(code)
            if t and sum(t.values()):
                ctx["parties"].append({"code": code, "name": PARTY_NAMES[code] + ("s" if code != "I" else ""), **t})
        vote_of = {r[0]: r for r in v["positions"]}
        breakers, groups = [], {}
        for b in v["breakers"]:
            _, party, _, pos = vote_of[b]
            same = sum(1 for x in v["breakers"] if vote_of[x][1] == party)
            note = f"The only {PARTY_NAMES[party]} to vote {pos}" if same == 1 else f"One of {same} {PARTY_NAMES[party]}s to vote {pos}"
            breakers.append({"p": people[b], "vote": pos, "note": note})
            groups.setdefault(party, {"code": party, "name": PARTY_NAMES[party], "vote": pos, "people": []})["people"].append(people[b])
        ctx["breakers"] = sorted(breakers, key=lambda b: b["p"]["sort"])
        ctx["breaker_groups"] = [dict(g, people=sorted(g["people"], key=lambda p: p["sort"])) for _, g in sorted(groups.items())]
        absent = {}
        for a in v["absent"]:
            party = vote_of[a][1]
            absent.setdefault(party, {"code": party, "name": PARTY_NAMES.get(party, "Independent"), "people": []})["people"].append(people[a])
        ctx["absent_groups"] = [dict(g, people=sorted(g["people"], key=lambda p: p["sort"]))
                                for _, g in sorted(absent.items(), key=lambda kv: {"D": 0, "R": 1}.get(kv[0], 2))]
        roll = defaultdict(list)
        for r in sorted(v["positions"], key=lambda r: people[r[0]]["sort"]):
            roll[r[3]].append((people[r[0]], r[1]))
        titles = {"yea": "Voted Yea", "nay": "Voted Nay", "present": "Voted Present", "nv": "Did not vote"}
        ctx["roll_groups"] = [{"title": titles.get(k, k.replace("other:", "Voted for ")), "people": roll[k]}
                              for k in sorted(roll, key=lambda k: ORDER.get(k, 4))]
        render(f"votes/{v['id']}/index.html", "vote.html", 2, **ctx)

    # ---- member pages
    write_json(SITE / "votes-index.json", [[v["id"], nicedate(v["date"]), v["roll"], v["info"]["headline"], v["result"],
                                            v["totals"].get("yea", 0), v["totals"].get("nay", 0)] for v in votes])
    for p in people.values():
        log = p["log"]
        breaks = []
        for idx, pos, wp in reversed(log):
            if wp is False:
                v = votes[idx]
                vote_of = {r[0]: r for r in v["positions"]}
                same = sum(1 for x in v["breakers"] if vote_of[x][1] == vote_of[p["bioguide"]][1])
                party_word = PARTY_NAMES.get(vote_of[p["bioguide"]][1], "")
                note = f"The only {party_word} to vote {pos}." if same == 1 else f"One of {same} {party_word}s to vote {pos}."
                breaks.append({"v": v, "pos": pos, "phrase": member_phrase(v, pos, bills), "note": note})
                if len(breaks) == 8:
                    break
        recent = [{"v": votes[idx], "pos": pos, "wp": wp} for idx, pos, wp in reversed(log[-25:])]
        d = p.get("district")
        state_name = STATES.get(p["state"], p["state"])
        seat_long = f"{state_name}'s {ordinal(d)} District" if d else (f"{state_name}, at large" if d == 0 else state_name)
        sponsored = [measures[s] for s in p["sponsored"] if s in measures]
        render(f"members/{p['bioguide']}/index.html", "member.html", 2, section="members", p=p, s=p["all"],
               breaks=breaks, recent=recent, state_name=state_name, seat_long=seat_long, sponsored=sponsored,
               party_median=result["medians"]["split_with_pct"].get(p["party"]),
               att_median=result["medians"]["attendance_pct"])
        write_json(SITE / "members" / p["bioguide"] / "votes.json",
                   [[idx, pos, None if wp is None else int(wp)] for idx, pos, wp in log])

    # ---- bill pages
    for m in measures.values():
        render(f"bills/{m['slug']}/index.html", "bill.html", 2, section="bills", b=m, ai=summaries.get(m["slug"]),
               sponsor=people.get(m["rec"].get("sponsor")))

    # ---- leaderboard and search
    rows = [{
        "id": p["bioguide"], "n": p["name"], "sort": p["sort"], "p": p["party"], "st": p["state"],
        "seat": f"{p['party_name']} · {p['seat']}",
        "wp": p["all"]["split_with_pct"], "ap": p["all"]["split_against_pct"],
        "br": p["all"]["split_against"] if p["all"]["split_counted"] else None,
        "vc": p["all"]["cast"], "at": p["all"]["attendance_pct"],
    } for p in ranked]
    state_list = sorted({(p["state"], STATES.get(p["state"], p["state"])) for p in ranked}, key=lambda x: x[1])
    render("leaderboard/index.html", "leaderboard.html", 1, section="leaderboard", rows=rows, state_list=state_list)

    search = [{"t": p["name"], "s": f"{p['party']}-{p['seat']}", "u": f"members/{p['bioguide']}/",
               "k": f"{p['name']} {STATES.get(p['state'], '')} {p['state']} {p['seat']}".lower()} for p in people.values()]
    search += [{"t": m["label"], "s": m["title"][:60], "u": f"bills/{m['slug']}/",
                "k": f"{m['label']} {m['label'].replace('.', '').replace(' ', '')} {m['kind']}{m['number']} {m['title']}".lower()}
               for m in measures.values()]
    write_json(SITE / "search.json", search)
    print(f"Built {len(votes)} vote pages, {len(people)} member pages and {len(measures)} bill pages into {SITE}")


if __name__ == "__main__":
    main()
