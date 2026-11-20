"""The Senate's energy permitting bill (H.R. 2347 as amended by S.Amdt. 6883), passed 62 to 33 on November 19, 2026.
Every claim is from the amendment text as adopted and Senate roll calls 267, 268 and 270."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from race_carousel_example import page, h1, lede, duty, stepn, INK, T2, MUTED, LINE, RED, PURPLE, BLUE, D, G, CARD, CAP
from shutdown_carousel_example import when, bar, chamber, chip, group, side, GREY
from bigger import bigger
LIST = lambda rows: f'<div style="flex: 1; min-height: 0; display: flex; flex-direction: column; border-bottom: 2px solid {LINE}">' + ''.join(rows) + '</div>'
SWIPE = f'<div style="display: flex; align-items: center; gap: 16px; {CAP}; color: {PURPLE}">Swipe To See What It Does<span style="font-size: 34px; line-height: 1">&rarr;</span></div>'
HOOK = ('Option: Hook, What Gets Built Near You', 'This Week In Congress',
        f'<div style="flex: 1; display: flex; flex-direction: column; justify-content: center; gap: {G}px">'
        f'<div style="{D}; font-weight: 700; font-size: 122px; line-height: 1.0; letter-spacing: -0.03em"><div style="color: {INK}">What Gets Built<br>Near You.</div><div style="color: {INK}">How Fast.</div><div style="color: {PURPLE}">And Who<br>Can Stop It.</div></div>'
        + lede('The Senate just voted to change all three, 62 to 33.') + SWIPE + '</div>')
def q(text, color): return f'<div style="flex: 1; display: flex; align-items: center; border-top: 2px solid {LINE}; {D}; font-weight: 700; font-size: 74px; line-height: 1.02; letter-spacing: -0.025em; color: {color}"><div>{text}</div></div>'
HOOKB = ('Permitting 1: The Senate Just Voted On', 'This Week In Congress', '\n'.join([
    f'<div style="{CAP}; color: {PURPLE}">The Senate just voted on</div>',
    f'<div style="flex: 1; min-height: 0; display: flex; flex-direction: column; border-bottom: 2px solid {LINE}">' + q(f'<span style="color: {PURPLE}">The Power Lines</span><br>In Your Area', INK) + q(f'<span style="color: {PURPLE}">The Water</span><br>Near You', INK) + q(f'Who Pays For<br><span style="color: {PURPLE}">The Grid</span>', INK) + q('And Who Can Sue<br>To Stop A Project', INK) + '</div>',
    lede('One bill. It passed 62 to 33.'), SWIPE,
]))
def idea(n, title, sub):
    return (f'<div style="flex: 1; display: flex; align-items: center; gap: {G}px; border-top: 2px solid {LINE}"><div style="width: 72px; height: 72px; flex: none; border-radius: 20px; background: #F1EAFE; color: {PURPLE}; display: flex; align-items: center; justify-content: center; {D}; font-weight: 700; font-size: 40px">{n}</div>'
            f'<div style="display: flex; flex-direction: column; gap: 8px"><div style="{D}; font-weight: 700; font-size: 42px; line-height: 1.05; letter-spacing: -0.02em">{title}</div><div style="font-size: 30px; line-height: 1.3; color: {T2}">{sub}</div></div></div>')
def change(title, sub, was=None, now=None):
    side = '' if now is None else (f'<div style="flex: none; width: 250px; display: flex; align-items: center; justify-content: flex-end; gap: 14px; {D}; font-weight: 700; letter-spacing: -0.02em">'
            + (f'<span style="font-size: 34px; color: {MUTED}; text-decoration: line-through">{was}</span><span style="font-size: 30px; color: {MUTED}">&rarr;</span>' if was else '') + f'<span style="font-size: 46px; color: {PURPLE}; white-space: nowrap">{now}</span></div>')
    return (f'<div style="flex: 1; display: flex; align-items: center; gap: 24px; border-top: 2px solid {LINE}"><div style="flex: 1; display: flex; flex-direction: column; gap: 8px"><div style="{D}; font-weight: 700; font-size: 40px; line-height: 1.05; letter-spacing: -0.02em">{title}</div><div style="font-size: 30px; line-height: 1.3; color: {T2}">{sub}</div></div>{side}</div>')
WHAT = ('Permitting 2: The Bill In One Sentence', 'The Short Version', '\n'.join([
    f'<div style="{CAP}; color: {PURPLE}">The bill in one sentence</div>',
    h1('It Makes Federal Permits For Energy Projects Faster To Get And Harder To Undo', 62),
    lede('A permit is the federal approval a power line, pipeline, solar farm, mine, or power plant needs before it is built.'),
    LIST([idea('A', 'Faster Decisions', 'Shorter deadlines for agencies to review and decide.'),
          idea('B', 'Fewer Ways To Undo A Permit', 'Less time to sue, and limits on cancelling an approval.'),
          idea('C', 'New Rules For The Power Grid', 'Power lines, data centers, and specific kinds of energy.')]),
]))
B1 = ('Permitting 3: Faster Decisions', 'What It Does · A', '\n'.join([
    h1('A: Faster Decisions', 76),
    LIST([change('A Deadline To Decide', 'Permits that do not need an environmental study must be decided within one year.', None, '1 year'),
          change('Faster Wildlife Reviews', 'Reviews of a project&rsquo;s effect on endangered species.', '90', '60 days'),
          change('Longer Water Permits', 'Clean Water Act permits to discharge into water last longer before renewal.', '5', '10 years'),
          change('Power Line Upgrades Skip Review', 'Upgrading lines inside an existing corridor no longer needs a federal environmental review.')]),
]))
B2 = ('Permitting 4: Fewer Ways To Undo A Permit', 'What It Does · B', '\n'.join([
    h1('B: Fewer Ways To Undo A Permit', 70),
    LIST([change(f'Deadline To Sue: <span style="color: {PURPLE}">150 Days</span>', 'A lawsuit over a permit&rsquo;s environmental review must be filed within 150 days.'),
          change(f'Courts: <span style="color: {PURPLE}">Fix It, Not Cancel It</span>', 'In most cases, a court that finds a flaw in an environmental review must send the permit back to be fixed.'),
          change(f'Agencies: <span style="color: {PURPLE}">Approved Stays Approved</span>', 'Limits when an agency can take back or change a permit once a project is fully approved.')]),
]))
B3 = ('Permitting 5: New Rules For The Power Grid', 'What It Does · C', '\n'.join([
    h1('C: New Rules For The Power Grid', 70),
    LIST([change('Data Centers Pay Their Own Way', 'Says data centers should pay the full cost of the power lines built to serve them, not other customers.'),
          change('Long-Distance Power Lines', 'Changes how federal regulators approve and plan lines that cross state lines.'),
          change('Geothermal, Hydropower, And Nuclear', 'New permit and licensing rules for each.')]),
    f'<div style="{CARD}; background: #F7F3FF; display: flex; flex-direction: column; gap: 16px"><div style="{CAP}; color: {PURPLE}">Why the record calls it a tax bill</div><div style="font-size: 30px; line-height: 1.32">The Senate put this package inside H.R. 2347, a House bill to stop taxing most payouts won by survivors of sexual abuse. That bill is still in it, as the last part.</div></div>',
]))
def tile(n, label): return f'<div style="flex: 1; {CARD}; padding: 24px; display: flex; flex-direction: column; gap: 10px"><div style="{D}; font-weight: 700; font-size: 52px; line-height: 1; letter-spacing: -0.02em; color: {PURPLE}; white-space: nowrap">{n}</div><div style="font-size: 25px; line-height: 1.25; color: {T2}">{label}</div></div>'
VOTE = ('Permitting 6: How The Senate Voted', 'The Vote', '\n'.join([
    h1('How The Senate Voted', 76),
    chamber('Senate', 'Nov 19, 2026', 'Passed 62 to 33',
            bar('Yes', 62, [(47, RED, 'Republicans'), (14, BLUE, 'Democrats'), (1, GREY, 'Independent')], 100),
            bar('No', 33, [(30, BLUE, 'Democrats'), (2, RED, 'Republicans'), (1, GREY, 'Independent')], 100)),
    f'<div style="display: flex; gap: 20px">{tile("69&ndash;27", "Nov 18: The vote to add the package")}{tile("65&ndash;31", "Nov 18: The vote to end debate")}{tile("5", "Senators who did not vote on passage")}</div>',
]))
YES = [('Chris Coons', 'DE', BLUE), ('John Fetterman', 'PA', BLUE), ('Ruben Gallego', 'AZ', BLUE), ('Martin Heinrich', 'NM', BLUE), ('John Hickenlooper', 'CO', BLUE), ('Angus King', 'ME', GREY), ('Amy Klobuchar', 'MN', BLUE), ('Gary Peters', 'MI', BLUE), ('Jack Reed', 'RI', BLUE), ('Jacky Rosen', 'NV', BLUE), ('Brian Schatz', 'HI', BLUE), ('Chuck Schumer', 'NY', BLUE), ('Elissa Slotkin', 'MI', BLUE), ('Mark Warner', 'VA', BLUE), ('Sheldon Whitehouse', 'RI', BLUE)]
NAMES = ('Permitting 7: Who Crossed Party Lines', 'The Names', '\n'.join([
    h1('Who Crossed Party Lines', 76),
    lede('Most Republicans voted yes. Most Democrats voted no.'),
    side('Senate', group('14 Democrats And 1 Independent Voted Yes', ''.join(chip(*x) for x in YES)) + group('2 Republicans Voted No', chip('Josh Hawley', 'MO', RED) + chip('Mike Rounds', 'SD', RED))),
    f'<div style="font-size: 24px; line-height: 1.2; color: {MUTED}; text-align: center">Blue is Democrat, Red is Republican, and Grey is Independent.</div>',
]))
NEXT = ('Permitting 8: What Happens Next', 'What Is Next', '\n'.join([
    h1('What Happens Next', 76),
    lede('It is not law yet.'),
    LIST([stepn(1, 'It Goes To The House', 'The House returns November 30.'),
          stepn(2, 'The House Must Pass The Same Text', 'Any change sends it back to the Senate.'),
          stepn(3, 'Then It Goes To The President', 'This Congress ends January 3, 2027. Bills not finished by then start over.')]),
    f'<div style="border-radius: 28px; background: {PURPLE}; color: #FFFFFF; padding: {G}px; display: flex; flex-direction: column; gap: 14px"><div style="font-size: 30px; line-height: 1.2; font-weight: 600">Read the full breakdown and see how your senators voted</div><div style="{D}; font-weight: 700; font-size: 64px; line-height: 1; letter-spacing: -0.02em">floortherecord.com</div></div>',
]))
SLIDES = {'PermHook': HOOKB, 'PermWhat': WHAT, 'PermBill1': B1, 'PermBill2': B2, 'PermBill3': B3, 'PermVote': VOTE, 'PermNames': NAMES, 'PermNext': NEXT}
if __name__ == '__main__':
    out = pathlib.Path(sys.argv[1])
    for k, (t, l, b) in SLIDES.items(): (out / f'{k}.dc.html').write_text(bigger(page(t, l, b)))
    print('wrote', ', '.join(SLIDES))
