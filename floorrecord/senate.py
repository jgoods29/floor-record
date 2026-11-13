"""The Senate side: its roll calls reshaped to match the House ones, plain-English wording for the
kinds of votes only the Senate takes (confirmations, votes to end debate), and who the senators are."""

import json
import re

from .common import DATA, fetch, read_json, write_json
from .explain import _clip, short_name
from .ingest import LEGIS_URL, bill_label, bill_slug, parse_legis

MEASURE = re.compile(r"\b(H\.\s?R\.|H\.\s?J\.\s?Res\.|H\.\s?Con\.\s?Res\.|S\.\s?J\.\s?Res\.|S\.\s?Con\.\s?Res\.|S\.\s?Res\.|S\.)\s?(\d+)")
SENATE_PAGE = "https://www.senate.gov/legislative/LIS/roll_call_votes/vote{congress}{session}/vote_{congress}_{session}_{num:05d}.htm"

# kind: (what the vote was, a yea means, a nay means, procedural step?)
MEANING = {
    "nomination": ("Senators voted on whether to approve the President's choice for this job.",
                   "confirm the nominee", "reject the nominee", False),
    "cloture_nom": ("Before the Senate votes on a nominee, it first votes to end debate. This was that step, not the final vote.",
                    "end debate and move to a final vote", "keep debating", True),
    "cloture": ("A vote to end debate so the Senate can move ahead. On most bills this takes 60 of the 100 senators, "
                "so a bill can have a majority behind it and still be blocked here.",
                "end debate and move ahead", "keep debating, which blocks it for now", True),
    "passage": ("The final Senate vote on whether to pass it.", "pass it", "reject it", False),
    "amendment": ("A vote on a proposed change to the bill.", "make the change", "reject the change", False),
    "table": ("A vote to set something aside without voting on it directly. Setting it aside usually ends it.",
              "set it aside", "keep it alive", True),
    "proceed": ("A vote on whether the Senate should start work on this.", "take it up", "not take it up", True),
    "discharge": ("A vote to pull this out of committee so the full Senate can take it up.",
                  "pull it out of committee", "leave it in committee", True),
    "veto": ("The President rejected this bill. This vote was on whether to make it law anyway, which takes two-thirds.",
             "override the veto", "let the veto stand", False),
    "waive": ("A senator said this breaks the Senate's budget rules. This vote was on whether to set those rules aside "
              "so it could go ahead, which usually takes 60 votes.", "set the rule aside", "keep the rule in force", True),
    "conviction": ("In an impeachment trial, senators vote guilty or not guilty. Conviction takes two-thirds.",
                   "convict", "acquit", False),
    "ruling": ("A vote on how the Senate's own rules apply here.", "agree", "disagree", True),
    "motion": ("Senators voted on a motion.", "agree to the motion", "reject the motion", True),
}
OUTCOMES = {
    "nomination": ("Confirmed", "Rejected"), "cloture_nom": ("Debate Ended", "Debate Continues"),
    "cloture": ("Debate Ended", "Blocked"), "passage": ("Passed", "Failed"), "amendment": ("Adopted", "Rejected"),
    "table": ("Set Aside", "Kept Alive"), "proceed": ("Taken Up", "Not Taken Up"),
    "discharge": ("Pulled From Committee", "Left In Committee"), "veto": ("Veto Overridden", "Veto Stands"),
    "waive": ("Rule Set Aside", "Rule Upheld"), "conviction": ("Convicted", "Acquitted"),
    "ruling": ("Agreed To", "Rejected"), "motion": ("Agreed To", "Rejected"),
}
GIST = {
    "nomination": ("The Senate approved the President's choice for this job.", "The Senate turned down the President's choice for this job."),
    "cloture_nom": ("The Senate ended debate on this nominee, clearing the way for a final vote.", "The Senate did not end debate on this nominee."),
    "cloture": ("The Senate voted to end debate and move ahead.", "The Senate did not get the votes to end debate, so this is blocked for now."),
    "passage": ("The Senate passed it.", "The Senate voted it down."),
    "amendment": ("The Senate agreed to this change.", "The Senate rejected this change."),
    "table": ("The Senate set this aside, which usually ends it.", "The Senate refused to set this aside."),
    "proceed": ("The Senate agreed to start work on this.", "The Senate declined to start work on this."),
    "discharge": ("The Senate pulled this out of committee.", "The Senate left this in committee."),
    "veto": ("The Senate voted to override the President's veto.", "The Senate did not override the President's veto."),
    "waive": ("The Senate set its budget rules aside so this could go ahead.", "The Senate kept its budget rules in force, which blocks this."),
    "conviction": ("The Senate voted to convict.", "The Senate voted to acquit."),
}


def classify(vote):
    q, title = vote["question"].lower(), vote["title"].lower()
    nominee = any(d["type"] == "PN" for d in vote["documents"]) or " to be " in title or "nomination" in title
    if "guilty" in q:
        return "conviction"
    if "nomination" in q:
        return "nomination"
    if "cloture" in q:
        return "cloture_nom" if nominee else "cloture"
    if "veto" in q:
        return "veto"
    if "amendment" in q or "amdt" in q:
        return "amendment"
    if "table" in q:
        return "table"
    if "discharge" in q:
        return "discharge"
    if "proceed" in q:
        return "proceed"
    if "waive" in q or "waive" in title:
        return "waive"
    if "point of order" in q or "decision of the chair" in q or "germane" in q:
        return "ruling"
    if "passage" in q or "resolution" in q or "conference report" in q or "treaty" in q or "on the bill" in q:
        return "passage"
    return "motion"


def carried(result):
    r = (result or "").lower()
    return not any(w in r for w in ("rejected", "defeated", "failed", "not agreed", "not sustained", "not well taken",
                                    "not guilty", "veto sustained", "not germane"))


CABINET = re.compile(r"^(Secretary of (State|the Treasury|Defense|War|the Interior|Agriculture|Commerce|Labor|Health and Human Services|"
                     r"Housing and Urban Development|Transportation|Energy|Education|Veterans Affairs|Homeland Security)|Attorney General)$", re.I)


def nominee(vote):
    """(person, post, group) from the Senate's own title. group: judges, cabinet, ambassadors, military, other, or bloc."""
    pns = [d for d in vote["documents"] if d["type"] == "PN"]
    if len(pns) > 1 or "en bloc" in (vote["title"] + vote["question_text"]).lower():
        return ("", f"A Group Of {len(pns)} Nominations" if 1 < len(pns) < 40 else "A Group Of Nominations", "bloc")
    name = nominee_name(vote)
    person, _, post = name.partition(" For ")
    low = post.lower()
    group = ("judges" if re.search(r"\bjudge\b|associate justice|chief justice", low) else "cabinet" if CABINET.match(post.strip()) else
             "ambassadors" if "ambassador" in low or ("representative" in low and "united nations" in low) else
             "military" if re.search(r"in the (u\.s\. |regular )?(army|navy|air force|marine corps|space force)|joint chiefs", low) else "other")
    return (person if post else "", post or name, group)


def nominee_name(vote):
    """'Evan Rikhye For Judge, District Court of the Virgin Islands' from the Senate's own title."""
    pns = [d for d in vote["documents"] if d["type"] == "PN"]
    if len(pns) > 1 or "en bloc" in (vote["title"] + vote["question_text"]).lower():
        return f"A Group Of {len(pns)} Nominations" if 1 < len(pns) < 40 else "A Group Of Nominations"
    t = re.sub(r"^(Confirmation|Motion to Invoke Cloture(?: on)?|Motion to Proceed to(?: Executive Session to Consider)?)[:\s]*", "",
               vote["title"], flags=re.I).strip()
    t = re.sub(r"^(the )?nomination of ", "", t, flags=re.I)
    m = re.match(r"(.+?)(?:,\s*of\s+[^,]+(?:,\s*(?:an?|the)\s[^,]+)*)?,?\s+to be\s+(?:an?\s+|the\s+)?(.+)$", t, re.I)
    if m:
        person = re.sub(r",?\s+of\s+(?:the\s+)?[A-Z][\w. ]+$", "", m.group(1).strip())
        post = re.sub(r"\s+for (?:a|the) term .*$|,\s*vice .*$|\s*\(.*$", "", m.group(2), flags=re.I).strip(" .,")
        post = re.sub(r"Ambassador (Extraordinary and Plenipotentiary )?of the United States of America to", "Ambassador to", post)
        post = post.replace(" of the United States of America", "").replace("United States ", "U.S. ")
        return _clip(f"{person} For {post}", 96)
    return _clip(t or "A Nomination", 96)


def measure_of(vote):
    """The bill or resolution a Senate vote was about, as (kind, number), or None for nominations."""
    for text in [d["name"] for d in vote["documents"] if d["type"] != "PN"] + [vote["title"], vote["question_text"]]:
        m = MEASURE.search(text or "")
        if m:
            parsed = parse_legis(re.sub(r"\s+", " ", m.group(0).replace(".", " ")).strip().upper())
            if parsed:
                return parsed
    return None


def explain_senate(vote, bills):
    kind = classify(vote)
    what, yea, nay, procedural = MEANING[kind]
    ok = carried(vote["result"])
    parsed = measure_of(vote)
    label = bill_label(*parsed) if parsed else ""
    rec = bills.get(bill_slug(*parsed)) or {} if parsed else {}
    doc_title = next((d["title"] for d in vote["documents"] if d["type"] != "PN" and d["title"]), "")
    title = rec.get("title") or doc_title or vote["document_text"] or vote["title"]
    if kind in ("nomination", "cloture_nom"):
        name = nominee_name(vote)
    elif parsed:
        name = short_name(doc_title or vote["document_text"], label, rec.get("title", ""))
        name = re.sub(r"^(?:A|An)\s+(?:original\s+)?(?:bill|joint resolution|concurrent resolution|resolution|act)\s+", "", name, flags=re.I)
        name = name[:1].upper() + name[1:]
        if kind == "amendment":
            who = re.match(r"^(.+?) Amdt\.? No\.? ?(\d+)", vote["title"])
            purpose = ((vote.get("amendment") or {}).get("purpose") or "").strip().rstrip(".")
            if purpose and "no statement" not in purpose.lower() and "nature of a substitute" not in purpose.lower():
                purpose = re.sub(r"^to\s+", "", purpose, flags=re.I)
                name = _clip(f"{who.group(1) + ' ' if who else ''}Amendment: {purpose[:1].upper() + purpose[1:]}", 100)
            else:
                name = _clip(f"Amendment by {who.group(1)} to {label}" if who else f"Amendment to {label}", 96)
    else:
        name = _clip(re.sub(r"^Motion to (Invoke Cloture(?: on)?|Proceed to|Table|Waive)[:\s]*", "", vote["title"], flags=re.I) or vote["question"], 96)
    if kind == "waive":
        about = re.search(r"Re:\s*(.+)$", vote["title"])
        name = _clip("Budget Rule Waiver" + (f" For {about.group(1).replace('Amdt.', 'Amendment')}" if about else ""), 96)
    routine = kind == "cloture_nom" or (kind == "proceed" and not parsed) or (kind == "motion" and not parsed and "adjourn" in vote["title"].lower())
    notes = []
    if vote["requirement"] == "3/5":
        notes.append("This vote needed three-fifths of the Senate, which is 60 of 100 senators, not a simple majority.")
    elif vote["requirement"] == "2/3":
        notes.append("This vote needed two-thirds of the senators voting, not a simple majority.")
    if vote.get("tie_breaker"):
        notes.append(f"The vote was tied, and the Vice President broke the tie by voting {vote['tie_breaker']['vote']}.")
    gist = GIST.get(kind, ("", ""))[0 if ok else 1]
    if kind == "amendment" and vote.get("amendment") and vote["amendment"]["purpose"] and "no statement" not in vote["amendment"]["purpose"].lower():
        what = f"A vote on a proposed change to the bill. Its stated purpose: {vote['amendment']['purpose'].rstrip('.')}."
    tag = label or next((d["name"] for d in vote["documents"]), "")
    fine = " · ".join(x for x in [tag if len(vote["documents"]) <= 1 or label else "", vote["question"], f"Senate Vote {vote['roll']}"] if x)
    outcome = OUTCOMES[kind][0 if ok else 1] if kind != "ruling" else vote["result"]
    return {
        "kind": kind, "headline": f"{name}: {outcome}", "what": what, "yea": yea, "nay": nay, "procedural": procedural,
        "two_thirds": vote["requirement"] == "2/3", "label": label, "title": title, "name": name, "outcome": outcome,
        "gist": gist, "plain": gist, "fine": fine, "routine": routine, "source": "rules", "result_note": " ".join(notes),
        "yea_short": yea, "nay_short": nay,
        "nominee": nominee(vote) if kind in ("nomination", "cloture_nom") else None,
    }


def load_senate_votes(years, senators, bills):
    """Senate roll calls in the same shape as the House ones, so the same counting and pages work for both."""
    by_lis = {s["lis"]: s for s in senators.values() if s.get("lis")}
    votes = []
    for year in years:
        for path in sorted((DATA / "senate" / str(year)).glob("*.json")):
            raw = read_json(path)
            positions, names, by_party = [], {}, {}
            for lis, party, state, cast, last, first in raw["positions"]:
                who = by_lis.get(lis)
                key = who["bioguide"] if who else lis
                party = party if party in ("R", "D") else "I"
                positions.append([key, party, state, cast])
                names[key] = who["name"] if who else f"{first} {last}".strip()
                row = by_party.setdefault(party, {"yea": 0, "nay": 0, "present": 0, "nv": 0})
                if cast in row:
                    row[cast] += 1
            parsed = measure_of(raw)
            legis = ""
            if parsed:
                legis = next(k for k, v in {"H R": "hr", "H J RES": "hjres", "H CON RES": "hconres", "H RES": "hres", "S": "s",
                                            "S J RES": "sjres", "S CON RES": "sconres", "S RES": "sres"}.items() if v == parsed[0]) + f" {parsed[1]}"
            votes.append({
                "id": f"s{raw['year']}-{raw['roll']}", "year": raw["year"], "roll": raw["roll"], "date": raw["date"], "time": raw["time"],
                "question": raw["question"], "legis": legis, "desc": raw["document_text"] or raw["title"],
                "type": raw["requirement"], "result": raw["result"],
                "kind": "standard" if all(p[3] in ("yea", "nay", "present", "nv") for p in positions) else "special",
                "totals": raw["totals"], "by_party": by_party, "tally_matches": raw["tally_matches"],
                "source": SENATE_PAGE.format(congress=raw["congress"], session=raw["session"], num=raw["roll"]),
                "amendment": (raw.get("amendment") or {}).get("number", ""), "amendment_author": "",
                "positions": positions, "names": names, "info": explain_senate(raw, bills),
            })
    votes.sort(key=lambda v: (v["date"], v["roll"]))
    return votes


def ingest_senators(log=print):
    """Who the senators are, from the same public list used for House members."""
    seen = {p[0] for path in (DATA / "senate").glob("*/*.json") for p in read_json(path)["positions"]}
    if not seen:
        return {}
    out = {}
    try:
        people = [p for which in ("current", "historical") for p in json.loads(fetch(LEGIS_URL.format(which=which), timeout=90))
                  if p["id"].get("lis") in seen]
    except Exception as err:
        log(f"  ! senators: {err}")
        return read_json(DATA / "senators.json", {})
    for person in people:
        terms = [t for t in person.get("terms") or [] if t.get("type") == "sen"]
        if not terms:
            continue
        last, name = terms[-1], person.get("name") or {}
        full = name.get("official_full") or " ".join(x for x in [name.get("first"), name.get("last")] if x)
        party = last.get("party") or ""
        out[person["id"]["bioguide"]] = {
            "bioguide": person["id"]["bioguide"], "lis": person["id"]["lis"], "name": full, "first": name.get("first", ""),
            "last": name.get("last", ""), "state": last.get("state", ""), "district": None,
            "party": "R" if party.startswith("Rep") else "D" if party.startswith("Dem") else "I",
            "caucus": {"Republican": "R", "Democrat": "D"}.get(last.get("caucus", ""), ""),
            "since": terms[0].get("start", ""), "house_since": terms[0].get("start", ""), "term_end": last.get("end", ""),
            "url": last.get("url", ""), "phone": last.get("phone", ""), "contact_form": last.get("contact_form", ""),
            "office": last.get("address", ""), "rank": last.get("state_rank", ""), "class": last.get("class"),
        }
    write_json(DATA / "senators.json", out)
    log(f"Senators: {len(out)} of {len(seen)} matched to the legislators list")
    return out
