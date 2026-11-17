"""The five-slide Senate leader carousel, on one spacing system.

Every slide: 64px outer margin on all four sides, 32px between every block (down and across),
32px padding inside every card. One block per slide stretches so the content fills the page exactly.
"""
import pathlib, sys
ROOT = pathlib.Path(__file__).parent / 'project'
INK, T2, MUTED, LINE, TINT = '#14213D', '#3B4A66', '#5A6473', '#DDE3EC', '#F4F6FA'
RED, PURPLE, BLUE, DEM = '#D61F45', '#6D28D9', '#2347F5', '#2456A6'
D = "font-family: 'Inter Tight', Inter, sans-serif"
M, G = 64, 32
CARD = f'border: 2px solid {LINE}; border-radius: 28px; padding: {G}px; box-sizing: border-box'
CAP = 'font-size: 23px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; line-height: 1'


def page(title, label, body):
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Inter+Tight:wght@600;700&display=swap" rel="stylesheet">
<style>
body{{margin:0}}
</style>
</helmet>
<div style="width: 1080px; height: 1350px; box-sizing: border-box; background: #FFFFFF; color: {INK}; font-family: Inter, sans-serif; display: flex; flex-direction: column">
<div style="display: flex; height: 16px; flex: none" aria-hidden="true"><div style="flex: 1; background: {RED}"></div><div style="flex: 1; background: {PURPLE}"></div><div style="flex: 1; background: {BLUE}"></div></div>
<div style="display: flex; align-items: center; justify-content: space-between; padding: {M - 16}px {M}px 0 {M}px; flex: none">
<div style="display: flex; align-items: center; gap: 16px"><div style="display: flex; gap: 6px" aria-hidden="true"><div style="width: 18px; height: 18px; border-radius: 5px; background: {RED}"></div><div style="width: 18px; height: 18px; border-radius: 5px; background: {PURPLE}"></div><div style="width: 18px; height: 18px; border-radius: 5px; background: {BLUE}"></div></div><div style="{D}; font-weight: 700; font-size: 36px; line-height: 1; letter-spacing: -0.01em">Floor The Record</div></div>
<div style="font-size: 22px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; line-height: 1; color: {PURPLE}; border: 2px solid #DCCBFB; background: #F7F3FF; border-radius: 999px; padding: 12px 24px">{label}</div>
</div>
<div style="flex: 1; min-height: 0; display: flex; flex-direction: column; gap: {G}px; padding: {G}px {M}px {G}px {M}px">
{body}
</div>
<div style="display: flex; align-items: center; justify-content: space-between; margin: 0 {M}px; padding: {G}px 0 {M}px 0; border-top: 2px solid {LINE}; flex: none">
<div style="font-size: 24px; line-height: 1; color: {T2}; font-weight: 500">Straight from the official record. No spin.</div>
<div style="font-size: 24px; line-height: 1; color: {INK}; font-weight: 700">floortherecord.com</div>
</div>
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":1080,"height":1350}}}}'>
class Component extends DCLogic {{
renderVals() {{
return {{}};
}}
}}
</script>
</body>
</html>
'''


def h1(text, size): return f'<h1 style="margin: 0; {D}; font-weight: 700; font-size: {size}px; line-height: 1.05; letter-spacing: -0.02em">{text}</h1>'
def lede(text): return f'<p style="margin: 0; font-size: 34px; line-height: 1.35; color: {T2}">{text}</p>'
def badge(size=26): return f'<span style="background: {DEM}; color: #FFFFFF; font-weight: 700; border-radius: 8px; padding: 4px 12px; line-height: 1">D</span>'


# ---- 1: hook (the heading block is centred in the space, with equal room above and below)
HOOK = ('Race 1: Who Will Be The Next Senate Majority Leader', 'In The News',
        f'<div style="flex: 1; display: flex; flex-direction: column; justify-content: center; gap: {G}px">'
        f'<div style="{D}; font-weight: 700; font-size: 132px; line-height: 1.02; letter-spacing: -0.025em"><div style="color: {INK}">Who Will Be<br>The Next</div><div style="color: {DEM}">Senate Majority<br>Leader?</div></div>'
        + lede('Two Democrats want the job. Swipe to compare their records.') + '</div>')


# ---- 2: what the job is (one card; its four rows share the height equally)
def duty(title, sub):
    return (f'<div style="flex: 1; display: flex; align-items: center; border-top: 2px solid {LINE}"><div style="display: flex; align-items: flex-start; gap: 24px">'
            f'<div style="width: 28px; height: 6px; flex: none; border-radius: 3px; background: {PURPLE}; margin-top: 18px"></div>'
            f'<div style="display: flex; flex-direction: column; gap: 8px"><div style="{D}; font-weight: 700; font-size: 40px; line-height: 1.05; letter-spacing: -0.02em">{title}</div><div style="font-size: 27px; line-height: 1.3; color: {T2}">{sub}</div></div></div></div>')


def stepn(n, title, sub):
    """Numbered rows are for steps only: things done in order."""
    return (f'<div style="flex: 1; display: flex; align-items: center; gap: {G}px; border-top: 2px solid {LINE}">'
            f'<div style="width: 72px; height: 72px; flex: none; border-radius: 50%; background: {PURPLE}; color: #FFFFFF; display: flex; align-items: center; justify-content: center; {D}; font-weight: 700; font-size: 38px; line-height: 1">{n}</div>'
            f'<div style="display: flex; flex-direction: column; gap: 8px"><div style="{D}; font-weight: 700; font-size: 40px; line-height: 1.05; letter-spacing: -0.02em">{title}</div><div style="font-size: 27px; line-height: 1.3; color: {T2}">{sub}</div></div></div>')


ROLE = ('Race 2: What The Senate Majority Leader Does', 'The Job', '\n'.join([
    h1('What Does The Senate<br>Majority Leader Do?', 76),
    lede('They lead the party with the most seats in the Senate. Their own party&rsquo;s senators choose them. Voters do not.'),
    f'<div style="flex: 1; min-height: 0; display: flex; flex-direction: column; border-bottom: 2px solid {LINE}">'
    + duty('Sets The Schedule', 'Decides which bills and nominees get a vote, and when.')
    + duty('Speaks For The Party', 'The party&rsquo;s main voice in the Senate.')
    + duty('Makes The Deals', 'Negotiates with the other party, the House and the President.')
    + duty('Leads The Strategy', 'Decides how the party&rsquo;s senators approach the big votes.') + '</div>',
    f'<div style="{CARD}; background: #F7F3FF; display: flex; flex-direction: column; gap: 16px"><div style="{CAP}; color: {PURPLE}">Good to know</div><div style="font-size: 29px; line-height: 1.32">When a party holds fewer seats, its leader is called the Minority Leader, and the other party sets the schedule.</div></div>',
]))

# ---- 3: the race and the people (the two cards stretch; their rows line up across both cards)
def who(name, seat, lines):
    rows = ''.join(f'<div style="flex: 1; display: flex; align-items: center; font-size: 28px; line-height: 1.3; padding: 16px 0; border-top: 2px solid {LINE}">{l}</div>' for l in lines)
    return (f'<div style="flex: 1; min-width: 0; {CARD}; padding-bottom: 16px; display: flex; flex-direction: column">'
            f'<div style="{D}; font-weight: 700; font-size: 46px; line-height: 1.05; letter-spacing: -0.02em">{name}</div>'
            f'<div style="display: flex; gap: 12px; align-items: center; font-size: 26px; line-height: 1; color: {T2}; padding: 16px 0 {G}px 0">{badge()}<span>{seat}</span></div>{rows}</div>')


EXPLAIN = ('Race 3: The Race And The People', 'The Race', '\n'.join([
    h1('Two Senators Want The Job', 62),
    lede('Senate Democrats choose their leader in December.<br>Only Democratic senators get a vote.'),
    f'<div style="flex: 1; min-height: 0; display: flex; gap: {G}px">'
    + who('Chuck Schumer', 'New York', ['In the Senate since 1999', 'Has led Senate Democrats since 2017', 'Running to keep the job'])
    + who('Chris Van Hollen', 'Maryland', ['In the Senate since 2017', 'Served in House of Representatives (2003-17)', 'Announced his run on November 12']) + '</div>',
    f'<div style="{CARD}; background: #F7F3FF; display: flex; flex-direction: column; gap: 16px"><div style="{CAP}; color: {PURPLE}">What we show</div><div style="font-size: 29px; line-height: 1.32">How each of them has voted, from the official record. Not who should win.</div></div>',
]))


# ---- 3 and 4: each senator in a nutshell (the three boxes share the leftover height equally)
def tile(num, label, sub): return f'<div style="flex: 1; min-width: 0; {CARD}; display: flex; flex-direction: column; justify-content: center; gap: 8px"><div style="{D}; font-weight: 700; font-size: 76px; line-height: 1; letter-spacing: -0.02em">{num}</div><div style="font-size: 25px; font-weight: 700; line-height: 1.2">{label}</div><div style="font-size: 22px; line-height: 1.2; color: {MUTED}">{sub}</div></div>'


def sen(name, initials, seat, since, role, cast, att, missed, bills, cmtes):
    rows = ''.join(f'<div style="flex: 1; display: flex; align-items: center; font-size: 30px; font-weight: 600; line-height: 1.25; padding: 12px 0; border-top: 2px solid {LINE}">{c}</div>' for c in cmtes)
    return '\n'.join([
        f'<div style="display: flex; gap: {G}px; align-items: center"><div style="width: 168px; height: 168px; border-radius: 50%; background: {TINT}; border: 2px solid {LINE}; box-sizing: border-box; display: flex; align-items: center; justify-content: center; {D}; font-weight: 700; font-size: 62px; color: {MUTED}; flex: none">{initials}</div><div style="display: flex; flex-direction: column; gap: 16px">{h1(name, 76)}<div style="display: flex; gap: 12px; align-items: center; font-size: 30px; line-height: 1; color: {T2}">{badge()}<span>{seat}</span></div><div style="font-size: 26px; line-height: 1; color: {MUTED}">In the Senate since {since} · {role}</div></div></div>',
        f'<div style="flex: 5 1 68px; display: flex; gap: {G}px">{tile(cast, "votes cast", "since January 2025")}{tile(att, "attendance", f"missed {missed} of 923")}{tile(bills, "bills introduced", "since January 2025")}</div>',
        f'<div style="flex: 7; min-height: 0; {CARD}; padding-bottom: 12px; display: flex; flex-direction: column"><div style="{CAP}; color: {MUTED}; padding-bottom: {G}px">Committees</div>{rows}</div>',
        f'<div style="border-radius: 28px; background: {PURPLE}; color: #FFFFFF; padding: 24px {G}px; display: flex; align-items: center; justify-content: space-between; gap: {G}px; font-size: 28px; line-height: 1.2"><div style="font-weight: 700">Check this record yourself</div><div style="font-weight: 500; flex: none">The last slide shows you how &rarr;</div></div>',
    ])


SCHUMER = ('Race 4: Chuck Schumer In A Nutshell', 'In A Nutshell', sen('Chuck Schumer', 'CS', 'New York · Senior senator', '1999', 'Senate Democratic leader', '919', '99.6%', '4', '35', ['Rules and Administration', 'Intelligence (sits in as a party leader)']))
VANHOLLEN = ('Race 5: Chris Van Hollen In A Nutshell', 'In A Nutshell', sen('Chris Van Hollen', 'CV', 'Maryland · Senior senator', '2017', 'in the House before that', '909', '98.5%', '14', '76', ['Appropriations', 'Budget', 'Banking, Housing, and Urban Affairs', 'Foreign Relations']))


# ---- 5: key comparisons (the two tables stretch; every row in a table is the same height)
def vs(label, a, b): return f'<div style="flex: 1; display: grid; grid-template-columns: 1fr 340px 1fr; align-items: center; border-top: 2px solid {LINE}"><div style="{D}; font-weight: 700; font-size: 52px; line-height: 1; letter-spacing: -0.02em">{a}</div><div style="font-size: 24px; line-height: 1.2; font-weight: 600; color: {MUTED}; text-align: center">{label}</div><div style="{D}; font-weight: 700; font-size: 52px; line-height: 1; letter-spacing: -0.02em; text-align: right">{b}</div></div>'
def split(what, a, b, n): return f'<div style="flex: 1; display: grid; grid-template-columns: 110px 1fr 110px; align-items: center; gap: 16px; border-top: 2px solid {LINE}"><div style="font-size: 27px; font-weight: 700">{a}</div><div style="display: flex; flex-direction: column; gap: 4px; text-align: center"><div style="font-size: 27px; font-weight: 600; line-height: 1.2">{what}</div><div style="font-size: 21px; line-height: 1.2; color: {MUTED}">{n}</div></div><div style="font-size: 27px; font-weight: 700; text-align: right">{b}</div></div>'


COMPARE = ('Race 6: Key Comparisons', 'Side By Side', '\n'.join([
    f'<div style="display: flex; justify-content: space-between; align-items: flex-end; gap: {G}px"><div style="display: flex; flex-direction: column; gap: 8px">{h1("Chuck Schumer", 62)}<div style="font-size: 26px; line-height: 1.2; color: {T2}">D · New York</div></div><div style="display: flex; flex-direction: column; gap: 8px; text-align: right">{h1("Chris Van Hollen", 62)}<div style="font-size: 26px; line-height: 1.2; color: {T2}">D · Maryland</div></div></div>',
    '<div style="flex: 1; min-height: 0; display: flex; flex-direction: column">' + vs('In the Senate since', '1999', '2017') + vs('Bills they introduced', '35', '76') + vs('Others&rsquo; bills they backed', '143', '679') + vs('Voted with their party', '98.5%', '100%')
    + f'<div style="font-size: 21px; line-height: 1.2; color: {MUTED}; text-align: center; padding-top: 16px; border-top: 2px solid {LINE}">Bills and votes are from this Congress only, since January 2025. Not their whole careers.</div></div>',
    f'<div style="border-radius: 28px; background: {PURPLE}; color: #FFFFFF; padding: {G}px; display: flex; align-items: center; gap: {G}px"><div style="{D}; font-weight: 700; font-size: 108px; line-height: 1; letter-spacing: -0.03em">96%</div><div style="font-size: 30px; line-height: 1.3; font-weight: 500">of the time, they voted the same way: 871 of the 905 votes where both voted yes or no.</div></div>',
    f'<div style="flex: 1; min-height: 0; display: flex; flex-direction: column"><div style="{CAP}; color: {MUTED}; padding-bottom: 16px">Big votes where they split · since January 2025</div>'
    + split('Blocking an arms sale to Israel', 'No', 'Yes', 'Apr 15, 2026 · Failed, 40 to 59') + split('The 2026 government funding bill', 'Yes', 'No', 'Jan 30, 2026 · Passed, 71 to 29')
    + split('The 2026 defense policy bill', 'Yes', 'No', 'Oct 9, 2025 · Passed, 77 to 20') + split('Sean Duffy for Transportation Secretary', 'Yes', 'No', 'Jan 28, 2025 · Confirmed, 77 to 22') + '</div>',
]))

# ---- 7: your turn (numbers are right here: these are steps, done in order)
ACT = ('Race 7: Check It Yourself', 'Your Turn', '\n'.join([
    h1('Don&rsquo;t Take Our Word For It', 76),
    lede('Every number in this post comes from the public record. Here is how to check it, and how to look up the people who represent you.'),
    f'<div style="flex: 1; min-height: 0; display: flex; flex-direction: column; border-bottom: 2px solid {LINE}">'
    + stepn(1, 'Go To floortherecord.com', 'It is free. You do not need an account.')
    + stepn(2, 'Type A Name Or Your ZIP Code', 'Find any senator or representative.')
    + stepn(3, 'Read How They Voted', 'Every vote, explained in one plain sentence.')
    + stepn(4, 'Decide For Yourself', 'We show the record. What it means is up to you.') + '</div>',
    f'<div style="border-radius: 28px; background: {PURPLE}; color: #FFFFFF; padding: {G}px; display: flex; align-items: center; justify-content: space-between; gap: {G}px"><div style="{D}; font-weight: 700; font-size: 64px; line-height: 1; letter-spacing: -0.02em">floortherecord.com</div><div style="font-size: 28px; line-height: 1.2; font-weight: 600; text-align: right">Link in bio</div></div>',
]))

SLIDES = {'RaceHook': HOOK, 'RaceRole': ROLE, 'RaceExplain': EXPLAIN, 'SenSchumer': SCHUMER, 'SenVanHollen': VANHOLLEN, 'Compare': COMPARE, 'RaceAct': ACT}
if __name__ == '__main__':
    out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT
    for k, (t, l, b) in SLIDES.items():
        (out / f'{k}.dc.html').write_text(page(t, l, b))
    print('wrote', ', '.join(SLIDES))
