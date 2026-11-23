"""The Monday and Friday emails.

Monday, "The Week Ahead": what is coming up for a vote, and how to reach your own three members before it happens.
Friday, "How They Voted": the week's real votes across the country, then how your own representative and senators voted.

Run after the site is built, because it reads the files the build writes:
    python -m floorrecord.newsletter                     send today's edition (does nothing on other days)
    python -m floorrecord.newsletter --edition friday --dry out/ --rep M001184 --state KY
                                                         write one sample email to a folder instead of sending

Needs two secrets to send: SUPABASE_SERVICE_KEY (reads the subscriber list) and RESEND_API_KEY (delivers the mail).
"""
import argparse
import html
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path

from .common import SITE, config, read_json

INK, T2, MUTED, LINE, TINT = "#14213D", "#3B4A66", "#5A6473", "#DDE3EC", "#F4F6FA"
RED, PURPLE, BLUE = "#D61F45", "#6D28D9", "#2347F5"
WORD = {"yea": "Voted yes", "nay": "Voted no", "present": "Voted present", "nv": "Did not vote"}
FONT = "font-family:Inter,-apple-system,Segoe UI,Helvetica,Arial,sans-serif"
e = html.escape


def nice(day):
    d = date.fromisoformat(day)
    return f"{d.strftime('%b')} {d.day}"


def load():
    data = read_json(SITE / "newsletter-data.json", {})
    reps = {r[0]: {"id": r[0], "name": r[1], "state": r[2], "where": r[3], "party": r[4], "phone": r[6], "pre": "", "role": "Your representative"}
            for r in read_json(SITE / "contacts.json", [])}
    sens = {}
    for r in read_json(SITE / "senators.json", []):
        sens.setdefault(r[2], []).append({"id": r[0], "name": r[1], "state": r[2], "where": r[3], "party": r[4], "phone": r[6], "pre": "senate/", "role": "Your senator"})
    return data, reps, sens


REP, DEM, IND, GREEN, NO, PTINT = "#D61F45", "#2347F5", "#8A93A3", "#17603A", "#9B1C1C", "#F4EFFE"
GOOD = ("Passed", "Confirmed", "Adopted", "Taken Up", "Debate Ended", "Agreed To", "Vote Forced", "Veto Overridden")


def section(title, inner):
    return (f'<tr><td style="padding:30px 32px 0 32px"><table role="presentation" cellpadding="0" cellspacing="0"><tr><td style="background:{PURPLE};color:#fff;'
            f'font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;border-radius:99px;padding:6px 14px">{e(title)}</td></tr></table>'
            f'<div style="margin-top:14px">{inner}</div></td></tr>')


def pill(text, bg, fg="#fff"):
    return f'<span style="display:inline-block;background:{bg};color:{fg};border-radius:99px;padding:3px 11px;font-size:12px;font-weight:700">{e(text)}</span>'


def party_bar(label, counts, total):
    """One row: 'Yes 392' and a bar split into Republican red, Democratic blue and grey for independents."""
    n = sum(counts)
    cells = "".join(f'<td width="{max(1, round(100 * c / n))}%" height="12" bgcolor="{col}" style="background:{col};font-size:0;line-height:0">&nbsp;</td>'
                    for c, col in zip(counts, (REP, DEM, IND)) if c) if n else ""
    width = max(6, round(100 * n / total)) if total else 0
    bar = (f'<table role="presentation" width="{width}%" cellpadding="0" cellspacing="0" style="border-radius:6px;overflow:hidden"><tr>{cells}</tr></table>'
           if n else f'<div style="font-size:12px;color:{MUTED}">none</div>')
    who = " · ".join(f'<span style="color:{col};font-weight:700">{c} {name}</span>' for c, col, name in zip(counts, (REP, DEM, IND), ("R", "D", "I")) if c)
    return (f'<tr><td width="74" style="font-size:13px;font-weight:700;color:{INK};padding:5px 0;white-space:nowrap">{label} {n}</td><td style="padding:5px 0">{bar}</td></tr>'
            f'<tr><td></td><td style="font-size:12px;padding-bottom:4px">{who}</td></tr>')


def vote_block(v, site):
    ok = v["outcome"] in GOOD
    tags = pill(v["outcome"], GREEN if ok else NO) + (" " + pill("Close vote", PURPLE) if v["close"] else "")
    by, total = v.get("by") or {}, max(1, v["yea"] + v["nay"])
    bars = (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:10px">{party_bar("Yes", by.get("yea", [0, 0, 0]), total)}'
            f'{party_bar("No", by.get("nay", [0, 0, 0]), total)}</table>') if by else f'<div style="font-size:14px;font-weight:700;color:{INK};margin-top:6px">{v["yea"]} to {v["nay"]}</div>'
    return (f'<div style="border:1px solid {LINE};border-top:4px solid {GREEN if ok else NO};border-radius:12px;padding:16px 18px;margin-bottom:12px">'
            f'<div style="font-size:12px;color:{MUTED};margin-bottom:6px">{e(v["chamber"])} · {nice(v["date"])} &nbsp;{tags}</div>'
            f'<a href="{site}{v["pre"]}votes/{v["id"]}/" style="color:{INK};font-size:18px;font-weight:700;text-decoration:none;line-height:1.3">{e(v["name"])}</a>'
            + (f'<div style="font-size:14px;color:{T2};margin-top:6px;line-height:1.5">{e(v["plain"])}</div>' if v["plain"] else "") + bars + "</div>")


def person_block(p, week, site, friday):
    col = {"R": REP, "D": DEM}.get(p["party"], IND)
    badge = f'<td width="44" valign="top"><div style="width:36px;height:36px;border-radius:50%;background:{col};color:#fff;font-weight:700;font-size:15px;line-height:36px;text-align:center">{e(p["party"])}</div></td>'
    head = (f'<div style="font-size:12px;color:{MUTED}">{e(p["role"])} · {e(p["where"])}</div>'
            f'<a href="{site}{p["pre"]}members/{p["id"]}/" style="color:{INK};font-size:18px;font-weight:700;text-decoration:none">{e(p["name"])}</a>')
    rows = ""
    if friday:
        mine = [v for v in week if p["id"] in v["pos"]][:6]
        for v in mine:
            pos = v["pos"][p["id"]]
            chip = pill({"yea": "Yes", "nay": "No"}.get(pos, "Missed"), {"yea": GREEN, "nay": NO}.get(pos, IND))
            rows += (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:8px"><tr><td width="66" valign="top">{chip}</td>'
                     f'<td style="font-size:14px;color:{T2};line-height:1.4"><a href="{site}{v["pre"]}votes/{v["id"]}/" style="color:{INK};text-decoration:none">{e(v["name"])}</a>'
                     f' <span style="color:{MUTED}">({e(v["outcome"].lower())})</span></td></tr></table>')
        if not mine:
            rows = f'<div style="font-size:14px;margin-top:8px;color:{MUTED}">No votes on real questions this week.</div>'
    elif p["phone"]:
        rows = (f'<div style="margin-top:10px"><a href="tel:{e(p["phone"])}" style="display:inline-block;background:{PURPLE};color:#fff;font-weight:700;font-size:14px;'
                f'text-decoration:none;border-radius:99px;padding:8px 16px">Call {e(p["phone"])}</a></div>')
    return (f'<div style="background:{TINT};border-left:4px solid {col};border-radius:12px;padding:14px 16px;margin-bottom:10px">'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>{badge}<td>{head}{rows}</td></tr></table></div>')


def stat(num, label, bg, fg):
    return (f'<td width="33%" style="padding:0 5px"><div style="background:{bg};border-radius:12px;padding:14px 8px;text-align:center">'
            f'<div style="font-size:30px;font-weight:800;color:{fg};line-height:1">{num}</div><div style="font-size:12px;font-weight:600;color:{fg};margin-top:4px">{e(label)}</div></div></td>')


def build_email(edition, data, people, site, acct, unsub="{{unsub}}"):
    """One finished email: (subject, html). `people` is the reader's representative (if known) and two senators."""
    friday = edition == "friday"
    when = f"{date.today().strftime('%A, %B')} {date.today().day}"
    week, coming = data.get("week", []), data.get("upcoming", [])
    parts = []
    if friday:
        top = sorted(week, key=lambda v: (not v["close"], -date.fromisoformat(v["date"]).toordinal()))[:6]
        title, kicker = "How They Voted", "The week in Congress, in plain English."
        # Sent after the week it covers (held for the owner's check, or a recess): say so in the heading.
        if week:
            last = max(date.fromisoformat(v["date"]) for v in week)
            monday = last - timedelta(days=last.weekday())
            if date.today() > monday + timedelta(days=5):
                kicker, when = "Last week in Congress, in plain English.", f"Week Of {monday.strftime('%B')} {monday.day}"
        passed = sum(1 for v in week if v["outcome"] in GOOD)
        parts.append(f'<tr><td style="padding:22px 27px 0 27px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
                     f'{stat(len(week), "Real Votes", PTINT, PURPLE)}{stat(passed, "Went Through", "#E8F3EC", GREEN)}{stat(sum(1 for v in week if v["close"]), "Close Calls", "#FBEAEA", NO)}</tr></table></td></tr>')
        parts.append(section("Across The Country", "".join(vote_block(v, site) for v in top)
                             + f'<div style="font-size:12px;color:{MUTED}">Bars show who voted each way: <span style="color:{REP};font-weight:700">red is Republican</span>, <span style="color:{DEM};font-weight:700">blue is Democrat</span>.</div>' if top else
                             f'<div style="font-size:15px;color:{T2}">Congress held no votes on real questions this week. It was likely out of session.</div>'))
        if people:
            parts.append(section("Your Own Three" if len(people) == 3 else "Your Members", "".join(person_block(p, week, site, True) for p in people)))
    else:
        title, kicker = "The Week Ahead", "What Congress may vote on, while there is still time to speak up."
        if coming:
            items = "".join(f'<div style="padding:12px 0;border-bottom:1px solid {LINE}"><a href="{e(i["url"] if i.get("outside") else site + (i.get("url") or "upcoming/"))}" style="font-size:16px;font-weight:700;color:{INK};text-decoration:underline;text-decoration-color:#B9A5F3">{e(i["name"])}</a>'
                            + (f'<div style="font-size:14px;color:{T2};margin-top:4px;line-height:1.45">{e(i["plain"])}</div>' if i.get("plain") else "") +
                            f'<div style="font-size:13px;color:{MUTED};margin-top:4px">{e(i["label"])} &nbsp;{pill(i["how"], PTINT, PURPLE)}{" &nbsp;" + pill(i["topic"], TINT, T2) if i["topic"] else ""}</div></div>' for i in coming[:10])
            more = f'<div style="margin-top:14px"><a href="{site}upcoming/" style="display:inline-block;background:{PURPLE};color:#fff;font-weight:700;font-size:14px;text-decoration:none;border-radius:99px;padding:10px 18px">See All {len(coming)} And What The Labels Mean</a></div>'
            parts.append(section("Coming Up In The House", items + more))
        else:
            parts.append(section("Coming Up In The House", f'<div style="font-size:15px;color:{T2}">The House has not posted a list for this week. It may be out of session.</div>'))
        parts.append(section("Waiting On The Senate", f'<div style="font-size:15px;color:{T2}">The Senate does not post a weekly list. <a href="{site}senate/upcoming/" style="color:{PURPLE};font-weight:700">See what is in line</a>.</div>'))
        if people:
            parts.append(section("Tell Them What You Think", f'<div style="font-size:15px;color:{T2};margin-bottom:10px">A call from someone they represent is counted. It takes two minutes.</div>'
                                 + "".join(person_block(p, week, site, False) for p in people)))
    if not people:
        parts.append(section("Make It Yours", f'<div style="font-size:15px;color:{T2}">Add your ZIP code to <a href="{site}account/" style="color:{PURPLE};font-weight:700">your account</a> and this email will show how your own representative and senators voted.</div>'))
    if acct.get("sponsor"):
        parts.append(section("Presented By", f'<div style="font-size:15px;color:{T2}">{acct["sponsor"]}</div>'))
    parts.append(f'<tr><td align="center" style="padding:30px 32px 0 32px"><a href="{site}" style="display:inline-block;background:{INK};color:#fff;font-weight:700;font-size:15px;text-decoration:none;border-radius:99px;padding:12px 26px">Open Floor The Record</a></td></tr>')
    name = config().get("site_name", "Floor The Record")
    address = f'<br>{e(acct["postal_address"])}' if acct.get("postal_address") else ""
    foot = (f'<tr><td style="padding:28px 32px 32px 32px"><div style="border-top:1px solid {LINE};padding-top:16px;font-size:12px;color:{MUTED};line-height:1.6">'
            f'{e(data.get("term", ""))}. Every vote comes from the official record of the House and the Senate. Free and non-partisan.<br>'
            f'You get this because you signed up at {e(name)}. <a href="{unsub}" style="color:{MUTED}">Unsubscribe</a> · <a href="{site}account/" style="color:{MUTED}">Your account</a>{address}</div></td></tr>')
    squares = "".join(f'<td width="14" height="14" bgcolor="{c}" style="background:{c};border-radius:4px;font-size:0;line-height:0">&nbsp;</td><td width="5"></td>' for c in (RED, PURPLE, BLUE))
    body = (f'<!doctype html><html lang="en"><body style="margin:0;background:{TINT};{FONT}"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{TINT}"><tr><td align="center" style="padding:20px 10px">'
            f'<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#fff;border-radius:14px;overflow:hidden;{FONT};color:{INK}">'
            f'<tr><td style="font-size:0;line-height:0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td height="8" bgcolor="{RED}" style="background:{RED}"></td><td height="8" bgcolor="{PURPLE}" style="background:{PURPLE}"></td><td height="8" bgcolor="{BLUE}" style="background:{BLUE}"></td></tr></table></td></tr>'
            f'<tr><td bgcolor="{INK}" style="background:{INK};padding:26px 32px 28px 32px"><table role="presentation" cellpadding="0" cellspacing="0"><tr>{squares}<td style="padding-left:6px;font-size:15px;font-weight:700;color:#fff">{e(name)}</td></tr></table>'
            f'<div style="font-size:36px;font-weight:800;letter-spacing:-.02em;line-height:1.1;margin-top:16px;color:#fff">{title}</div>'
            f'<div style="font-size:16px;color:#C9D1E0;margin-top:8px">{e(kicker)}</div>'
            f'<div style="font-size:13px;color:#9FB0CC;margin-top:10px">{e(when)}</div></td></tr>'
            + "".join(parts) + foot + "</table></td></tr></table></body></html>")
    return f"{title}: {when.split(', ')[-1]}", body


def people_for(sub, reps, sens):
    out = [reps[sub["rep_id"]]] if sub.get("rep_id") in reps else []
    return out + sens.get(sub.get("state") or "", [])


def call(url, headers, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, headers={"Content-Type": "application/json", "User-Agent": "floorrecord-newsletter", **headers})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            text = r.read().decode()
    except urllib.error.HTTPError as err:
        # say what the service answered (never the keys), so a failed run explains itself
        detail = err.read().decode(errors="replace")[:400]
        print(f"Request to {url.split('?')[0]} failed with {err.code}: {detail}")
        raise
    return json.loads(text) if text else None


def subscribers(url, key):
    out, start = [], 0
    while True:
        rows = call(f"{url}/rest/v1/profiles?select=email,state,rep_id,unsub_token&newsletter=eq.true&order=created_at&offset={start}&limit=1000",
                    {"apikey": key, "Authorization": f"Bearer {key}"})
        out += rows
        if len(rows) < 1000:
            return [r for r in out if r.get("email")]
        start += 1000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edition", choices=["monday", "friday"])
    ap.add_argument("--dry", help="write a sample email into this folder instead of sending")
    ap.add_argument("--rep"), ap.add_argument("--state")
    args = ap.parse_args()
    edition = args.edition or {0: "monday", 4: "friday"}.get(date.today().weekday())
    if not edition:
        print("Not a Monday or a Friday: nothing to send.")
        return
    acct = config().get("accounts") or {}
    site = (acct.get("site_url") or "").rstrip("/") + "/"
    data, reps, sens = load()
    if args.dry:
        subject, body = build_email(edition, data, people_for({"rep_id": args.rep, "state": args.state}, reps, sens), site, acct, unsub=site + "unsubscribe/?t=sample")
        out = Path(args.dry); out.mkdir(parents=True, exist_ok=True)
        (out / f"{edition}.html").write_text(body)
        print(f"Wrote {out / (edition + '.html')}: {subject}")
        return
    sb, skey, rkey = (acct.get("supabase_url") or "").rstrip("/"), os.environ.get("SUPABASE_SERVICE_KEY"), os.environ.get("RESEND_API_KEY")
    if not (sb and skey and rkey and acct.get("from")):
        print("The newsletter is not switched on yet (account service, mail service or From address missing). Nothing sent.")
        return
    people = subscribers(sb, skey)
    made, sent, failed = {}, 0, 0
    for sub in people:
        who = (sub.get("rep_id") or "", sub.get("state") or "")
        if who not in made:     # everyone with the same three members gets the same email, so write each one once
            made[who] = build_email(edition, data, people_for(sub, reps, sens), site, acct)
        subject, body = made[who]
        link = f"{site}unsubscribe/?t={sub['unsub_token']}"
        try:
            call("https://api.resend.com/emails", {"Authorization": f"Bearer {rkey}"},
                 {"from": acct["from"], "to": [sub["email"]], "subject": subject, "html": body.replace("{{unsub}}", link), "headers": {"List-Unsubscribe": f"<{link}>"},
                  **({"reply_to": acct["reply_to"]} if acct.get("reply_to") else {})})
            sent += 1
        except urllib.error.HTTPError as err:
            failed += 1
            if err.code == 429:
                time.sleep(2)
        time.sleep(0.6)   # stay under the mail service's per-second limit
    print(f"{edition.title()} edition: sent {sent}, failed {failed}, {len(made)} versions.")
    if failed and not sent:
        sys.exit(1)


if __name__ == "__main__":
    main()
