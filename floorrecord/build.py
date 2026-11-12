"""Build the static website from data/ into site/.

Run:  python -m floorrecord.build
"""
import html
import re
import shutil
from collections import defaultdict
from datetime import date, datetime, timezone

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .common import DATA, ROOT, SITE, config, read_json, write_json
from .explain import apply_wording, short_name, title_case
from .ingest import BILL_LABELS, bill_label, bill_slug, load_votes
from .stats import PARTY_NAMES, compute, pick_featured

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
# Everyday names for the Library of Congress policy areas.
TOPIC_NAMES = {
    "Agriculture and Food": "Farming and food", "Armed Forces and National Security": "Military and security",
    "Civil Rights and Liberties, Minority Issues": "Civil rights", "Commerce": "Business and consumers",
    "Crime and Law Enforcement": "Crime and policing", "Economics and Public Finance": "Budget and spending",
    "Emergency Management": "Disasters and emergencies", "Environmental Protection": "Environment",
    "Finance and Financial Sector": "Banks and finance", "Foreign Trade and International Finance": "Trade",
    "Government Operations and Politics": "Government and elections", "Housing and Community Development": "Housing",
    "International Affairs": "Foreign affairs", "Labor and Employment": "Jobs and workers", "Law": "Courts and law",
    "Public Lands and Natural Resources": "Public lands", "Science, Technology, Communications": "Science and technology",
    "Social Welfare": "Social programs", "Taxation": "Taxes", "Transportation and Public Works": "Transportation",
    "Water Resources Development": "Water", "Arts, Culture, Religion": "Arts, culture and religion",
    "Social Sciences and History": "History and social science", "Sports and Recreation": "Sports and recreation",
    "Congress": "How Congress runs", "Native Americans": "Native American affairs", "Families": "Families and children",
}


def topic_name(area):
    return title_case(TOPIC_NAMES.get(area, area))


HEADING = re.compile(r"(<(h1|h2|h3)\b[^>]*>)(.*?)(</\2>)|(<(span|p) class=\"(?:h1|h2|h3|headline-sm|title|big-line|name)\b[^\"]*\"[^>]*>)(.*?)(</\6>)", re.S)


def title_case_headings(page):
    """Put every heading on a finished page in headline-style capitals, leaving the tags inside alone."""
    def fix(m):
        open_tag, inner, close_tag = (m.group(1), m.group(3), m.group(4)) if m.group(1) else (m.group(5), m.group(7), m.group(8))
        if open_tag.startswith("<p") and "big-line" not in open_tag:
            return m.group(0)  # a paragraph set in heading type is still a sentence
        parts = re.split(r"(<[^>]+>)", inner)
        first = True
        for i, part in enumerate(parts):
            if part.startswith("<") or not part.strip():
                continue
            lead = part[: len(part) - len(part.lstrip())]
            body = html.unescape(part.lstrip())
            cased = title_case(body if first else "x " + body)
            parts[i] = lead + html.escape(cased if first else cased[2:], quote=False)
            first = False
        return open_tag + "".join(parts) + close_tag
    return HEADING.sub(fix, page)


def topic_key(area):
    return "".join(ch if ch.isalnum() else "-" for ch in (area or "").lower()).strip("-")


def custom_topics_for(rec, title, custom):
    """Our own topics (such as AI) that the Library of Congress has no category for.

    A bill belongs when a keyword appears in its title or in the opening of its official summary, so a
    huge bill that mentions the subject once in passing is not swept in.
    """
    found = []
    head = (title or "") + " " + (rec.get("title") or "")
    lead = head + " " + (rec.get("official_summary") or "")[:350]
    for topic in custom:
        words = [w.lower() for w in topic.get("keywords", [])]
        if any(w in lead.lower() for w in words) or any(re.search(p, head) for p in topic.get("title_patterns", [])):
            found.append(topic["name"])
    return found


def bill_status(action):
    """A plain status from the official 'latest action' text. Returns (status, has_moved)."""
    a = (action or "").lower()
    if "became public law" in a or "became private law" in a:
        return "Became law", True
    if "vetoed" in a:
        return "Vetoed", True
    if "presented to president" in a or "signed by president" in a:
        return "Sent to the President", True
    if "received in the senate" in a or "passed house" in a or "passed/agreed to in house" in a or "agreed to in house" in a:
        return "Passed the House", True
    if "received in the house" in a or "held at the desk" in a or "passed senate" in a or "passed/agreed to in senate" in a:
        return "Passed the Senate", True
    if "on passage passed" in a or ("suspend the rules and pass" in a and "agreed" in a):
        return "Passed the House", True
    if "motion to reconsider" in a or "motion to refer" in a or "motion to table" in a:
        return "Voted on in the House", True
    if "calendar" in a or "reported" in a:
        return "Approved by committee", True
    if "referred to" in a or "committee" in a:
        return "In committee", False
    return "Introduced", False


def member_line(v, pos):
    """'Voted to pass the bill.' for one member on one vote."""
    if pos == "yea":
        return f"Voted to {v['info']['yea']}."
    if pos == "nay":
        return f"Voted to {v['info']['nay']}."
    if pos == "present":
        return "Voted present."
    if pos == "nv":
        return "Did not vote."
    return "Voted for " + pos.replace("other:", "") + "."



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
    for rec in bills.values():  # tidy summaries collected before the HTML clean-up was added
        if rec.get("official_summary"):
            rec["official_summary"] = " ".join(html.unescape(rec["official_summary"]).split())
    summaries = read_json(DATA / "summaries.json", {})
    ai_votes = read_json(DATA / "ai_votes.json", {})
    editorial = read_json(ROOT / "editorial.json", {})
    result = compute(votes_raw, members, bills, cfg)
    votes, people = result["votes"], result["people"]
    today = datetime.now(timezone.utc).date().isoformat()
    custom = [dict(t, name=title_case(t["name"])) for t in cfg.get("custom_topics") or []]
    popular = [title_case(n) for n in cfg.get("popular_topics") or []]
    for v in votes:
        info = v["info"]
        info["rule_name"], info["rule_plain"] = info["name"], info["plain"]
        apply_wording(info, v["id"], ai_votes, editorial)
        v["topic"] = topic_name(v["issue"]) if v["issue"] else ""
        names = [v["topic"]] if v["topic"] else []
        if v["slug"]:
            names += custom_topics_for(bills.get(v["slug"]) or {}, v["desc"], custom)
        v["topics"] = names
        v["topic_keys"] = [topic_key(n) for n in names]
    # The big votes use wording a person approved, or the automatic wording. Never unreviewed AI text.
    featured = pick_featured(votes, pins=editorial.get("pins") or [])
    for v in featured:
        ai = v["info"]["source"] == "ai"
        v["f_name"] = v["info"]["rule_name"] if ai else v["info"]["name"]
        v["f_plain"] = v["info"]["rule_plain"] if ai else v["info"]["plain"]
    for p in people.values():
        d = p.get("district")
        p["left"] = bool(p.get("term_end")) and p["term_end"] < today
        p["dist_label"] = "Delegate" if p.get("delegate") else ("At large" if not d else f"District {d}")
    topic_counts = defaultdict(int)
    for v in votes:
        if v["kind"] == "standard" and not v["info"]["routine"]:
            for name in v["topics"]:
                topic_counts[name] += 1

    def topic_order(name):
        # Popular topics always come first, in the order set in config.json; the rest by number of votes.
        return (popular.index(name) if name in popular else len(popular), -topic_counts[name], name)

    topics = [{"key": topic_key(n), "name": n, "count": topic_counts[n], "popular": n in popular}
              for n in sorted(topic_counts, key=topic_order)]

    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape(["html"]),
                      trim_blocks=True, lstrip_blocks=True)
    env.filters.update(nicedate=nicedate, comma=lambda n: f"{n:,}", capfirst=capfirst,
                       times=lambda n: "once" if n == 1 else f"{n:,} times",
                       lcfirst=lambda t: t)  # outcomes keep their capitals after a colon
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
        page = env.get_template(template).render(root="../" * depth, **shared, **ctx)
        out.write_text(title_case_headings(page))

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
        m["name"] = title_case(short_name(m["title"], m["label"]))
        m["topic"] = " · ".join(m["votes"][0]["topics"]) if m["votes"] else topic_name(m["rec"].get("policy_area", ""))
        m["kind_name"], m["kind_note"] = KIND_NAMES[m["kind"]]
        m["congress_url"] = (f"https://www.congress.gov/bill/{ordinal(cfg['congress'])}-congress/"
                             f"{CONGRESS_PATH[m['kind']]}/{m['number']}")

    newest = sorted(votes, key=lambda v: (v["date"], v["roll"]), reverse=True)
    ranked = [p for p in people.values() if p["ranked"]]

    # ---- home, lists
    mavericks = sorted([p for p in ranked if p["all"]["split_against_pct"] is not None],
                       key=lambda p: -p["all"]["split_against_pct"])[:5]
    # ---- topics: one page per topic, and "trending" = what the House has voted on most lately
    by_topic = defaultdict(list)
    for v in newest:
        for key in v["topic_keys"]:
            by_topic[key].append(v)
    recent_real = [v for v in newest if v["kind"] == "standard" and not v["info"]["routine"]][:60]
    heat = defaultdict(int)
    for v in recent_real:
        for key in v["topic_keys"]:
            heat[key] += 1
    since = recent_real[-1]["date"] if recent_real else ""
    all_topics = []
    for t in topics:
        vs = by_topic[t["key"]]
        all_topics.append(dict(t, total=len(vs), real=t["count"], latest=vs[0], recent=heat.get(t["key"], 0)))
    # Every topic picker shows the popular topics first, then whatever the House has voted on most lately.
    hot = sorted((t for t in all_topics if not t["popular"] and t["recent"]), key=lambda t: -t["recent"])
    trending = [t for t in all_topics if t["popular"]] + hot[:max(0, 10 - sum(1 for t in all_topics if t["popular"]))]
    if all_topics:
        render("topics/index.html", "topics.html", 1, section="topics",
               popular=[t for t in all_topics if t["popular"]],
               topics=sorted(all_topics, key=lambda t: t["name"]))
        for t in all_topics:
            render(f"topics/{t['key']}/index.html", "topic.html", 2, section="topics", t=t, votes=by_topic[t["key"]],
                   nroutine=t["total"] - t["real"])
    render("index.html", "index.html", 0, section="home", trending=trending, since=since, featured=featured,
           has_topics=bool(all_topics), examples=cfg.get("search_examples") or ["Texas", "Farm Bill", "Taxes"])
    render("votes/index.html", "votes.html", 1, section="votes", votes=newest, featured=featured,
           nroutine=sum(1 for v in votes if v["info"]["routine"]))
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
        ctx["roll_groups"] = [{"title": titles.get(k, k.replace("other:", "Voted for ")), "people": roll[k],
                               "key": k if k in ORDER else f"other-{i}"}
                              for i, k in enumerate(sorted(roll, key=lambda k: ORDER.get(k, 4)))]
        render(f"votes/{v['id']}/index.html", "vote.html", 2, **ctx)

    # ---- member pages
    write_json(SITE / "votes-index.json", [[
        v["id"], nicedate(v["date"]), v["roll"], v["info"]["name"], v["info"]["outcome"] if v["kind"] == "standard" else v["result"],
        v["totals"].get("yea", 0), v["totals"].get("nay", 0), int(v["info"]["routine"] or v["kind"] != "standard"),
        v["topic_keys"], v["info"]["fine"], v["info"]["yea"], v["info"]["nay"]] for v in votes])
    congress_base = f"https://www.congress.gov/bill/{ordinal(cfg['congress'])}-congress/"

    def bill_rows(items, limit=None):
        rows = []
        for kind, number, title, introduced, action_date, action, area in items:
            action = " ".join(html.unescape(re.sub(r"\(?<[^>]*(>|$)", " ", action or "")).split())
            slug, label = bill_slug(kind, number), bill_label(kind, number)
            status, moved = bill_status(action)
            internal = slug in measures
            rows.append({
                "name": title_case(short_name(title, label)), "title": title or label, "label": label, "introduced": introduced,
                "topic": topic_name(area), "action": action, "action_date": action_date, "status": status, "moved": moved,
                "internal": internal,
                "href": f"../../bills/{slug}/" if internal else f"{congress_base}{CONGRESS_PATH[kind]}/{number}",
            })
        return rows[:limit] if limit else rows

    for p in people.values():
        log = p["log"]
        me = p["bioguide"]

        def row(idx, pos, wp):
            v = votes[idx]
            note = ""
            if wp is False:
                party = next(r[1] for r in v["positions"] if r[0] == me)
                same = v["broke_by_party"].get(party, 1)
                word = PARTY_NAMES.get(party, "")
                note = f"The only {word} to vote {pos}." if same == 1 else f"One of {same} {word}s to vote {pos}."
            return {"v": v, "pos": pos, "wp": wp, "phrase": member_line(v, pos), "note": note}

        breaks, notable = [], []
        for idx, pos, wp in reversed(log):
            v = votes[idx]
            if wp is False and len(breaks) < 8:
                breaks.append(row(idx, pos, wp))
            if v["kind"] == "standard" and not v["info"]["routine"] and len(notable) < 6:
                notable.append(row(idx, pos, wp))
            if len(breaks) >= 8 and len(notable) >= 6:
                break
        recent = [{"v": votes[idx], "pos": pos, "wp": wp} for idx, pos, wp in reversed(log[-25:])]
        d = p.get("district")
        state_name = STATES.get(p["state"], p["state"])
        seat_long = f"{state_name}'s {ordinal(d)} District" if d else (f"{state_name}, at large" if d == 0 else state_name)
        mb = read_json(DATA / "member_bills" / f"{me}.json")
        sponsored, cosponsored, co_count = [], [], 0
        p["bills_n"] = p["passed_n"] = p["law_n"] = None
        if mb:
            sponsored = bill_rows(sorted(mb.get("sponsored", []), key=lambda r: r[4] or r[3], reverse=True))
            for i, b in enumerate(sponsored):
                b["extra"] = i >= 8
            moved_on = {"Passed the House", "Passed the Senate", "Sent to the President", "Became law", "Vetoed"}
            p["bills_n"] = len(sponsored)
            p["passed_n"] = sum(1 for b in sponsored if b["status"] in moved_on)
            p["law_n"] = sum(1 for b in sponsored if b["status"] == "Became law")
            co_all = bill_rows(sorted(mb.get("cosponsored", []), key=lambda r: r[3], reverse=True))
            co_count, cosponsored = len(co_all), co_all[:8]
            write_json(SITE / "members" / me / "bills.json",
                       [[b["name"], b["label"], b["status"], int(b["moved"]), b["href"], b["topic"],
                         nicedate(b["introduced"]) if b["introduced"] else ""] for b in co_all])
        my_topics = topics
        render(f"members/{me}/index.html", "member.html", 2, section="members", p=p, s=p["all"],
               breaks=breaks, notable=notable, recent=recent, state_name=state_name, seat_long=seat_long,
               has_bills=mb is not None, sponsored=sponsored, cosponsored=cosponsored, co_count=co_count,
               passed_n=p["passed_n"], law_n=p["law_n"],
               topics=my_topics, by_issue=[(topic_name(a), st) for a, st in p["by_issue"].items()],
               party_median=result["medians"]["split_with_pct"].get(p["party"]),
               att_median=result["medians"]["attendance_pct"])
        write_json(SITE / "members" / me / "votes.json",
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
        "bi": p.get("bills_n"), "ph": p.get("passed_n"), "bl": p.get("law_n"),
    } for p in ranked]
    state_list = sorted({(p["state"], STATES.get(p["state"], p["state"])) for p in ranked}, key=lambda x: x[1])
    render("compare/index.html", "compare.html", 1, section="compare", rows=rows, state_list=state_list)
    render("leaderboard/index.html", "redirect.html", 1, to="../compare/")  # the page's old address

    search = [{"t": p["name"], "s": f"{p['party']}-{p['seat']}", "u": f"members/{p['bioguide']}/",
               "k": f"{p['name']} {STATES.get(p['state'], '')} {p['state']} {p['seat']}".lower()} for p in people.values()]
    search += [{"t": m["name"], "s": m["label"], "u": f"bills/{m['slug']}/",
                "k": " ".join([m["label"], m["label"].replace(".", "").replace(" ", ""), f"{m['kind']}{m['number']}", m["title"],
                               m["topic"]] + sorted({v["info"]["name"] for v in m["votes"]})).lower()}
               for m in measures.values()]
    search += [{"t": t["name"], "s": "Topic", "u": f"topics/{t['key']}/", "k": (t["name"] + " topic").lower()}
               for t in all_topics]
    write_json(SITE / "search.json", search)
    print(f"Built {len(votes)} vote pages, {len(people)} member pages and {len(measures)} bill pages into {SITE}")


if __name__ == "__main__":
    main()
