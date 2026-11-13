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
from datetime import date
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


def section(title, inner):
    return (f'<tr><td style="padding:26px 32px 0 32px"><div style="font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:{PURPLE}">{e(title)}</div>'
            f'<div style="margin-top:10px">{inner}</div></td></tr>')


def vote_block(v, site):
    tally = f'{v["yea"]} to {v["nay"]}'
    close = f' <span style="background:{RED};color:#fff;border-radius:99px;padding:1px 8px;font-size:11px;font-weight:700">Close vote</span>' if v["close"] else ""
    return (f'<div style="border:1px solid {LINE};border-radius:12px;padding:14px 16px;margin-bottom:10px">'
            f'<div style="font-size:12px;color:{MUTED}">{e(v["chamber"])} · {nice(v["date"])}{close}</div>'
            f'<a href="{site}{v["pre"]}votes/{v["id"]}/" style="color:{INK};font-size:17px;font-weight:700;text-decoration:none;line-height:1.3">{e(v["name"])}</a>'
            f'<div style="font-size:14px;font-weight:700;color:{INK};margin-top:4px">{e(v["outcome"])}, {tally}</div>'
            + (f'<div style="font-size:14px;color:{T2};margin-top:4px">{e(v["plain"])}</div>' if v["plain"] else "") + "</div>")


def person_block(p, week, site, friday):
    head = (f'<div style="font-size:12px;color:{MUTED}">{e(p["role"])} · {e(p["where"])}</div>'
            f'<a href="{site}{p["pre"]}members/{p["id"]}/" style="color:{INK};font-size:17px;font-weight:700;text-decoration:none">{e(p["name"])} ({e(p["party"])})</a>')
    rows = ""
    if friday:
        mine = [v for v in week if p["id"] in v["pos"]][:6]
        for v in mine:
            pos = v["pos"][p["id"]]
            color = {"yea": "#1B7F4B", "nay": "#B42318"}.get(pos, MUTED)
            rows += (f'<div style="font-size:14px;margin-top:8px;color:{T2}"><strong style="color:{color}">{WORD.get(pos, "Other")}</strong> on '
                     f'<a href="{site}{v["pre"]}votes/{v["id"]}/" style="color:{INK}">{e(v["name"])}</a> ({e(v["outcome"].lower())})</div>')
        if not mine:
            rows = f'<div style="font-size:14px;margin-top:8px;color:{MUTED}">No votes on real questions this week.</div>'
    elif p["phone"]:
        rows = f'<div style="font-size:14px;margin-top:6px;color:{T2}">Call the office: <a href="tel:{e(p["phone"])}" style="color:{INK};font-weight:700">{e(p["phone"])}</a></div>'
    return f'<div style="background:{TINT};border-radius:12px;padding:14px 16px;margin-bottom:10px">{head}{rows}</div>'


def build_email(edition, data, people, site, acct, unsub="{{unsub}}"):
    """One finished email: (subject, html). `people` is the reader's representative (if known) and two senators."""
    friday = edition == "friday"
    week, coming = data.get("week", []), data.get("upcoming", [])
    parts = []
    if friday:
        top = sorted(week, key=lambda v: (not v["close"], -date.fromisoformat(v["date"]).toordinal()))[:6]
        title, kicker = "How They Voted", f'{len(week)} votes on real questions in Congress this week.'
        parts.append(section("Across The Country", "".join(vote_block(v, site) for v in top) if top else
                             f'<div style="font-size:15px;color:{T2}">Congress held no votes on real questions this week. It was likely out of session.</div>'))
        if people:
            parts.append(section("Your Own Three" if len(people) == 3 else "Your Members", "".join(person_block(p, week, site, True) for p in people)))
    else:
        title, kicker = "The Week Ahead", "What Congress may vote on, while there is still time to speak up."
        if coming:
            items = "".join(f'<div style="padding:10px 0;border-bottom:1px solid {LINE}"><div style="font-size:16px;font-weight:700;color:{INK}">{e(i["name"])}</div>'
                            f'<div style="font-size:13px;color:{MUTED}">{e(i["label"])} · {e(i["how"])}{" · " + e(i["topic"]) if i["topic"] else ""}</div></div>' for i in coming[:10])
            more = f'<div style="margin-top:10px;font-size:14px"><a href="{site}upcoming/" style="color:{PURPLE};font-weight:700">See all {len(coming)} and what each label means</a></div>'
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
    name = config().get("site_name", "Floor Record")
    address = f'<br>{e(acct["postal_address"])}' if acct.get("postal_address") else ""
    foot = (f'<tr><td style="padding:28px 32px 32px 32px"><div style="border-top:1px solid {LINE};padding-top:16px;font-size:12px;color:{MUTED};line-height:1.6">'
            f'{e(data.get("term", ""))}. Every vote comes from the official record of the House and the Senate. Free and non-partisan.<br>'
            f'You get this because you signed up at {e(name)}. <a href="{unsub}" style="color:{MUTED}">Unsubscribe</a> · <a href="{site}account/" style="color:{MUTED}">Your account</a>{address}</div></td></tr>')
    body = (f'<!doctype html><html lang="en"><body style="margin:0;background:{TINT};{FONT}"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{TINT}"><tr><td align="center" style="padding:20px 10px">'
            f'<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#fff;border-radius:14px;overflow:hidden;{FONT};color:{INK}">'
            f'<tr><td style="font-size:0;line-height:0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td height="8" style="background:{RED}"></td><td height="8" style="background:{PURPLE}"></td><td height="8" style="background:{BLUE}"></td></tr></table></td></tr>'
            f'<tr><td style="padding:26px 32px 0 32px"><div style="font-size:14px;font-weight:700;color:{INK}">{e(name)} · {date.today().strftime("%A, %B")} {date.today().day}</div>'
            f'<div style="font-size:32px;font-weight:800;letter-spacing:-.02em;line-height:1.1;margin-top:10px">{title}</div><div style="font-size:16px;color:{T2};margin-top:8px">{e(kicker)}</div></td></tr>'
            + "".join(parts) + foot + "</table></td></tr></table></body></html>")
    return f"{title}: {date.today().strftime('%B')} {date.today().day}", body


def people_for(sub, reps, sens):
    out = [reps[sub["rep_id"]]] if sub.get("rep_id") in reps else []
    return out + sens.get(sub.get("state") or "", [])


def call(url, headers, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, headers={"Content-Type": "application/json", "User-Agent": "floorrecord-newsletter", **headers})
    with urllib.request.urlopen(req, timeout=30) as r:
        text = r.read().decode()
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
                 {"from": acct["from"], "to": [sub["email"]], "subject": subject, "html": body.replace("{{unsub}}", link), "headers": {"List-Unsubscribe": f"<{link}>"}})
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
