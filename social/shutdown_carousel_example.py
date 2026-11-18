"""Wednesday look back: how the 2025 government shutdown ended (H.R. 5371, Public Law 119-37).
Same spacing system as race.py. Every number here is from the Senate and House roll calls and the bill text."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from race_carousel_example import page, h1, lede, duty, stepn, INK, T2, MUTED, LINE, RED, PURPLE, BLUE, DEM, D, G, CARD, CAP
GREY = '#8A93A3'

HOOK = ('Shutdown 1: How The Longest Government Shutdown Ended', 'Look Back',
        f'<div style="flex: 1; display: flex; flex-direction: column; justify-content: center; gap: {G}px">'
        f'<div style="{D}; font-weight: 700; font-size: 124px; line-height: 1.02; letter-spacing: -0.025em"><div style="color: {INK}">How The<br>Longest<br>Government</div><div style="color: {PURPLE}">Shutdown Ended</div></div>'
        + lede('One year ago this month. <br>Swipe to see what was in the bill and who voted for it.') + '</div>')

def when(date, title, sub):
    return (f'<div style="flex: 1; display: flex; align-items: center; gap: {G}px; border-top: 2px solid {LINE}">'
            f'<div style="width: 190px; flex: none; {CAP}; color: {PURPLE}; line-height: 1.25">{date}</div>'
            f'<div style="display: flex; flex-direction: column; gap: 8px"><div style="{D}; font-weight: 700; font-size: 40px; line-height: 1.05; letter-spacing: -0.02em">{title}</div><div style="font-size: 27px; line-height: 1.3; color: {T2}">{sub}</div></div></div>')

WHAT = ('Shutdown 2: What Happened', 'The Shutdown', '\n'.join([
    h1('43 Days Without Funding', 76),
    lede('The Senate needed 60 of its 100 members to agree on a funding bill. For weeks, it could not get there.'),
    f'<div style="flex: 1; min-height: 0; display: flex; flex-direction: column; border-bottom: 2px solid {LINE}">'
    + when('Oct 1<br>2025', 'Funding Ran Out', 'Two Senate votes on the funding bill had already fallen short.')
    + when('Oct 1<br>To Nov 4', '12 More Votes Fell Short', 'The bill kept missing 60 votes while much of the government was shut.')
    + when('Nov 9<br>2025', 'The 15th Vote Got 60', 'Exactly 60 senators voted to move the bill forward.')
    + when('Nov 12<br>2025', 'The Shutdown Ended', 'The House passed the bill and the President signed it.') + '</div>',
]))

BILL = ('Shutdown 3: What The Bill Did, Part 1', 'The Bill · Part 1', '\n'.join([
    h1('It Reopened The Government', 76),
    lede('The bill had eight parts. The first one ended the shutdown.'),
    f'<div style="flex: 1; min-height: 0; display: flex; flex-direction: column; border-bottom: 2px solid {LINE}">'
    + duty('Funded Most Agencies Through January 30, 2026', 'At the prior year&rsquo;s spending levels.')
    + duty('Paid Federal Workers Back', 'Provided the pay workers missed during the shutdown.')
    + duty('Reversed Shutdown Layoffs', 'Undid layoffs made since October 1 and barred new ones through January 30.')
    + duty('Repaid States', 'Paid back states that used their own money to keep federal programs running.') + '</div>',
]))

YEAR = ('Shutdown 4: What The Bill Did, Part 2', 'The Bill · Part 2', '\n'.join([
    h1('It Funded Three Areas Through September 2026', 62),
    lede('Congress writes 12 funding bills a year. This bill carried three of them in full.'),
    f'<div style="flex: 1; min-height: 0; display: flex; flex-direction: column; border-bottom: 2px solid {LINE}">'
    + duty('Agriculture And Food', 'Includes $107.5 billion for food assistance (SNAP) and $8.2 billion for WIC (food aid for mothers, infants, and young children).')
    + duty('Veterans And Military Construction', 'Funds the Department of Veterans Affairs and construction on military bases, such as housing for military families.')
    + duty('Congress Itself', 'Funds the House, the Senate, the Capitol Police, and the Library of Congress.')
    + duty('Plus: Farm Programs', 'Extended programs from the 2018 farm law through September 2026.') + '</div>',
]))

ALSO = ('Shutdown 5: What The Bill Did, Part 3', 'The Bill · Part 3', '\n'.join([
    h1('What Else Was In It', 76),
    f'<div style="flex: 1; min-height: 0; display: flex; flex-direction: column; border-bottom: 2px solid {LINE}">'
    + duty('A Tighter Definition Of Hemp', 'Limits THC in hemp products. One part started November 12, 2026. Congress moved the rest to December 11, 2026.')
    + duty('Lawsuits Over Senators&rsquo; Phone Records', 'Let senators sue for $500,000 if their records were taken without notice. Congress later repealed it.')
    + duty('Health Program Extensions', 'Kept Medicare telehealth rules and community health center funding going through January 30, 2026.')
    + duty('Security Money', '$30 million for the U.S. Marshals, $30 million for Capitol Police aid, and $28 million to protect Supreme Court justices.') + '</div>',
    f'<div style="{CARD}; background: #F7F3FF; display: flex; flex-direction: column; gap: 16px"><div style="{CAP}; color: {PURPLE}">What was not in it</div><div style="font-size: 29px; line-height: 1.32">An extension of health insurance tax credits. Democrats had asked for one. Republicans said to reopen the government first.</div></div>',
]))

def seg(n, total, color): return f'<div style="flex: {n}; background: {color}; min-width: 6px"></div>'
def bar(label, total, parts, seats):
    segs = ''.join(seg(n, total, c) for n, c, _ in parts)
    words = ' &nbsp;·&nbsp; '.join(f'<span style="white-space: nowrap"><span style="display: inline-block; width: 16px; height: 16px; border-radius: 4px; background: {c}; margin-right: 10px"></span>{n} {w}</span>' for n, c, w in parts)
    return (f'<div style="display: flex; flex-direction: column; gap: 12px"><div style="display: flex; align-items: baseline; justify-content: space-between"><div style="{D}; font-weight: 700; font-size: 40px; line-height: 1; letter-spacing: -0.02em">{label}</div><div style="{D}; font-weight: 700; font-size: 40px; line-height: 1">{total}</div></div>'
            f'<div style="display: flex; gap: 4px; height: 28px; border-radius: 8px; overflow: hidden; width: {100 * total / seats:.1f}%">{segs}</div>'
            f'<div style="font-size: 25px; line-height: 1.3; color: {T2}">{words}</div></div>')
def chamber(name, date, result, yes, no):
    return (f'<div style="flex: 1; min-height: 0; {CARD}; display: flex; flex-direction: column; justify-content: space-between; gap: 24px">'
            f'<div style="display: flex; align-items: baseline; justify-content: space-between"><div style="{CAP}; color: {PURPLE}">{name} · {date}</div><div style="{CAP}; color: {MUTED}">{result}</div></div>{yes}{no}</div>')

VOTE = ('Shutdown 6: How They Voted', 'The Vote', '\n'.join([
    h1('How They Voted', 76),
    lede('The final vote on the bill in each chamber.'),
    chamber('Senate', 'Nov 10, 2025', 'Passed 60 to 40',
            bar('Yes', 60, [(52, RED, 'Republicans'), (7, BLUE, 'Democrats'), (1, GREY, 'Independent')], 100),
            bar('No', 40, [(38, BLUE, 'Democrats'), (1, RED, 'Republican'), (1, GREY, 'Independent')], 100)),
    chamber('House', 'Nov 12, 2025', 'Passed 222 to 209',
            bar('Yes', 222, [(216, RED, 'Republicans'), (6, BLUE, 'Democrats')], 435),
            bar('No', 209, [(207, BLUE, 'Democrats'), (2, RED, 'Republicans')], 435)),
]))

def chip(name, st, color): return f'<span style="display: inline-flex; align-items: center; gap: 10px; border: 2px solid {LINE}; border-radius: 999px; padding: 9px 16px; font-size: 23px; line-height: 1; white-space: nowrap"><span style="width: 14px; height: 14px; border-radius: 50%; background: {color}"></span><span style="font-weight: 600">{name}</span><span style="color: {MUTED}">{st}</span></span>'
def group(title, chips): return f'<div style="display: flex; flex-direction: column; gap: 14px"><div style="font-size: 27px; line-height: 1.2; font-weight: 600">{title}</div><div style="display: flex; flex-wrap: wrap; gap: 12px">{chips}</div></div>'
def side(name, groups, grow=1): return f'<div style="flex: {grow} 1 auto; {CARD}; display: flex; flex-direction: column; justify-content: space-between; gap: 24px"><div style="{CAP}; color: {PURPLE}">{name}</div>{groups}</div>'
SEN_YES = [('Catherine Cortez Masto', 'NV', BLUE), ('Dick Durbin', 'IL', BLUE), ('John Fetterman', 'PA', BLUE), ('Maggie Hassan', 'NH', BLUE), ('Tim Kaine', 'VA', BLUE), ('Angus King', 'ME', GREY), ('Jacky Rosen', 'NV', BLUE), ('Jeanne Shaheen', 'NH', BLUE)]
HOUSE_YES = [('Henry Cuellar', 'TX', BLUE), ('Don Davis', 'NC', BLUE), ('Jared Golden', 'ME', BLUE), ('Adam Gray', 'CA', BLUE), ('Marie Gluesenkamp Perez', 'WA', BLUE), ('Tom Suozzi', 'NY', BLUE)]
NAMES = ('Shutdown 7: Who Crossed Party Lines', 'The Names', '\n'.join([
    h1('Who Crossed Party Lines', 76),
    side('Senate', group('7 Democrats And 1 Independent Voted Yes', ''.join(chip(*x) for x in SEN_YES)) + group('1 Republican Voted No', chip('Rand Paul', 'KY', RED))),
    side('House', group('6 Democrats Voted Yes', ''.join(chip(*x) for x in HOUSE_YES)) + group('2 Republicans Voted No', chip('Thomas Massie', 'KY', RED) + chip('Greg Steube', 'FL', RED))),
    f'<div style="font-size: 22px; line-height: 1.2; color: {MUTED}; text-align: center">Blue is Democrat, red is Republican, and grey is Independent.</div>',
]))

ACT = ('Shutdown 8: How Did Yours Vote', 'Your Turn', '\n'.join([
    h1('How Did Yours Vote?', 76),
    lede('See how your two senators and your representative voted on this bill.'),
    f'<div style="flex: 1; min-height: 0; display: flex; flex-direction: column; border-bottom: 2px solid {LINE}">'
    + stepn(1, 'Go To floortherecord.com', 'It is free. You do not need an account.')
    + stepn(2, 'Enter Your ZIP Code', 'Find the three people who represent you.')
    + stepn(3, 'Read How They Voted', 'Then read the bill summarized, with everything that is in it.') + '</div>',
    f'<div style="border-radius: 28px; background: {PURPLE}; color: #FFFFFF; padding: {G}px; display: flex; align-items: center; justify-content: space-between; gap: {G}px"><div style="{D}; font-weight: 700; font-size: 64px; line-height: 1; letter-spacing: -0.02em">floortherecord.com</div><div style="font-size: 28px; line-height: 1.2; font-weight: 600; text-align: right">Link in bio</div></div>',
]))

SLIDES = {'ShutHook': HOOK, 'ShutWhat': WHAT, 'ShutBill': BILL, 'ShutYear': YEAR, 'ShutAlso': ALSO, 'ShutVote': VOTE, 'ShutNames': NAMES, 'ShutAct': ACT}
if __name__ == '__main__':
    out = pathlib.Path(sys.argv[1])
    for k, (t, l, b) in SLIDES.items():
        (out / f'{k}.dc.html').write_text(page(t, l, b))
    print('wrote', ', '.join(SLIDES))
