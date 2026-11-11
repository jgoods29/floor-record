"""Rebuild the Roll Call 317 test fixture in the Clerk's XML format.

The workspace this project was written in could not reach clerk.house.gov, so this fixture is
RECONSTRUCTED from public facts about House Roll Call 317 (Nov 10, 2026): the Clerk's party totals
(R 210-1-7 not voting, D 0-203-11 not voting, I 1-0) and the published names of the one Republican
who voted Nay and the 18 members who did not vote. Every other position follows from the totals.
It exists only to test the code. The live site always downloads the real file.

Usage: python tests/make_fixture.py path/to/legislators-current.json
"""
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

NOT_VOTING = {("Brownley", "CA"), ("Correa", "CA"), ("Gillen", "NY"), ("Horsford", "NV"), ("Jackson", "IL"),
              ("Pelosi", "CA"), ("Pettersen", "CO"), ("Stansbury", "NM"), ("Stevens", "MI"), ("Strickland", "WA"),
              ("Wilson", "FL"), ("De La Cruz", "TX"), ("Dunn", "FL"), ("Fry", "SC"), ("Letlow", "LA"),
              ("Tiffany", "WI"), ("Van Orden", "WI"), ("Yakym", "IN")}
DELEGATES = {"DC", "PR", "GU", "VI", "AS", "MP"}


def main(src):
    people = json.loads(Path(src).read_text())
    rows, tot = [], {}
    for person in people:
        term = person["terms"][-1]
        if term["type"] != "rep" or term["state"] in DELEGATES:
            continue
        party = {"Republican": "R", "Democrat": "D"}.get(term["party"], "I")
        last = person["name"]["last"]
        if (last, term["state"]) in NOT_VOTING:
            vote = "Not Voting"
        elif person["id"]["bioguide"] == "M001184":
            vote = "Nay"
        else:
            vote = "Nay" if party == "D" else "Yea"
        rows.append((last, person["id"]["bioguide"], party, term["state"], vote))
        t = tot.setdefault(party, {"Yea": 0, "Nay": 0, "Present": 0, "Not Voting": 0})
        t[vote] += 1
    rows.sort()
    names = {"R": "Republican", "D": "Democratic", "I": "Independent"}
    out = ['<?xml version="1.0" encoding="UTF-8"?>', "<rollcall-vote>", "<vote-metadata>", "<majority>R</majority>",
           "<congress>119</congress>", "<session>2nd</session>", "<chamber>U.S. House of Representatives</chamber>",
           "<rollcall-num>317</rollcall-num>", "<legis-num>H RES 1655</legis-num>",
           "<vote-question>On Motion to Refer</vote-question>", "<vote-type>YEA-AND-NAY</vote-type>",
           "<vote-result>Passed</vote-result>", "<action-date>10-Nov-2026</action-date>",
           '<action-time time-etz="18:02">6:02 PM</action-time>',
           "<vote-desc>Impeaching Peter Brian Hegseth, Secretary of Defense, for high crimes and misdemeanors</vote-desc>",
           "<vote-totals>"]
    grand = {"Yea": 0, "Nay": 0, "Present": 0, "Not Voting": 0}
    for code in ("R", "D", "I"):
        t = tot.get(code, {"Yea": 0, "Nay": 0, "Present": 0, "Not Voting": 0})
        for k in grand:
            grand[k] += t[k]
        out.append(f"<totals-by-party><party>{names[code]}</party><yea-total>{t['Yea']}</yea-total><nay-total>{t['Nay']}</nay-total>"
                   f"<present-total>{t['Present']}</present-total><not-voting-total>{t['Not Voting']}</not-voting-total></totals-by-party>")
    out.append(f"<totals-by-vote><total-stub>Totals</total-stub><yea-total>{grand['Yea']}</yea-total><nay-total>{grand['Nay']}</nay-total>"
               f"<present-total>{grand['Present']}</present-total><not-voting-total>{grand['Not Voting']}</not-voting-total></totals-by-vote>")
    out += ["</vote-totals>", "</vote-metadata>", "<vote-data>"]
    for last, bioguide, party, state, vote in rows:
        out.append(f'<recorded-vote><legislator name-id={quoteattr(bioguide)} sort-field={quoteattr(last)} unaccented-name={quoteattr(last)} '
                   f'party="{party}" state="{state}" role="legislator">{escape(last)}</legislator><vote>{vote}</vote></recorded-vote>')
    out += ["</vote-data>", "</rollcall-vote>"]
    dest = Path(__file__).parent / "fixtures" / "roll317_reconstructed.xml"
    dest.write_text("\n".join(out) + "\n")
    print(dest, grand, tot)


if __name__ == "__main__":
    main(sys.argv[1])
