"""Member stat card, sports-page style: Hakeem Jeffries. Numbers from House roll calls, January 3, 2025 through November 18, 2026."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from race_carousel_example import page, h1, lede, stepn, INK, T2, MUTED, LINE, RED, PURPLE, BLUE, D, G, CARD, CAP
NUM = f"{D}; font-weight: 700; font-variant-numeric: tabular-nums; letter-spacing: -0.02em"
CAPS = "font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; line-height: 1"

def bio(k, v): return f'<div style="display: flex; align-items: baseline; gap: 20px"><div style="width: 230px; flex: none; {CAPS}; font-size: 24px; color: {MUTED}">{k}</div><div style="font-size: 32px; line-height: 1.15; font-weight: 600">{v}</div></div>'
def stat(label, n, rank): return f'<div style="flex: 1; display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 26px 8px 20px"><div style="{CAPS}; font-size: 20px; letter-spacing: 0.04em; color: {MUTED}; text-align: center; white-space: nowrap">{label}</div><div style="{NUM}; font-size: 74px; line-height: 1">{n}</div><div style="font-size: 24px; line-height: 1.2; font-weight: 700; color: {PURPLE}; text-align: center; min-height: 58px">{rank}</div></div>'
def panel(title, inner, right=''): return f'<div style="border: 2px solid {LINE}; border-radius: 28px; overflow: hidden; flex: none"><div style="background: {INK}; color: #FFFFFF; display: flex; align-items: center; justify-content: space-between; padding: 18px {G}px"><div style="{CAPS}; font-size: 26px">{title}</div><div style="{CAPS}; font-size: 22px; opacity: 0.75">{right}</div></div>{inner}</div>'

CARD1 = ('Jeffries 1: Player Card', 'Member Stats', '\n'.join([
    f'<div style="display: flex; align-items: center; gap: {G}px">'
    f'<div style="width: 208px; height: 208px; flex: none; border-radius: 50%; background: #EEF2FF; border: 8px solid {BLUE}; display: flex; align-items: center; justify-content: center; {D}; font-weight: 700; font-size: 84px; letter-spacing: -0.03em; color: {BLUE}">HJ</div>'
    f'<div style="display: flex; flex-direction: column; gap: 14px"><div style="{D}; font-size: 92px; line-height: 0.95; letter-spacing: -0.03em"><div style="font-weight: 600; color: {T2}">Hakeem</div><div style="font-weight: 700">Jeffries</div></div>'
    f'<div style="font-size: 30px; line-height: 1.2; color: {T2}"><span style="display: inline-block; width: 16px; height: 16px; border-radius: 50%; background: {BLUE}; margin-right: 12px"></span>Democrat (DEM) · New York&rsquo;s 8th District</div></div></div>',
    f'<div style="flex: 1; min-height: 0; display: flex; flex-direction: column; justify-content: space-evenly; border-top: 2px solid {LINE}; border-bottom: 2px solid {LINE}">'
    + bio('Position', 'House Minority Leader') + bio('Born', 'August 4, 1970 (56)') + bio('Hometown', 'Brooklyn, New York')
    + bio('In The House', 'Since 2013') + bio('Party Leader', 'Since 2023')
    + bio('Status', f'<span style="display: inline-block; width: 16px; height: 16px; border-radius: 50%; background: {PURPLE}; margin-right: 12px"></span>Nominated For Speaker, Nov 18, 2026') + '</div>',
    panel('2025&ndash;26 Stats', f'<div style="display: flex">{stat("Votes Cast", "681", "of 688<br>possible votes")}<div style="width: 2px; background: {LINE}"></div>{stat("Missed", "2", "T-34th Fewest<br>of 421 members")}<div style="width: 2px; background: {LINE}"></div>{stat("With His Party", "98.7%", "21st highest<br>among DEM")}<div style="width: 2px; background: {LINE}"></div>{stat("Bills Introduced", "5", "Co-Signed: 32")}</div>'),
]))

def tile(label, n): return f'<div style="flex: 1; border: 2px solid {LINE}; border-radius: 22px; overflow: hidden"><div style="background: {INK}; color: #FFFFFF; {CAPS}; font-size: 22px; text-align: center; padding: 14px 6px">{label}</div><div style="{NUM}; font-size: 70px; line-height: 1; text-align: center; padding: 22px 0 24px">{n}</div></div>'
WID = [110, 110, 110, 150, 184]
def thead(cols): return f'<div style="display: flex; align-items: center; padding: 0 0 14px; border-bottom: 3px solid {INK}"><div style="flex: 1; {CAPS}; font-size: 22px; color: {MUTED}">Splits</div>' + ''.join(f'<div style="width: {WID[i]}px; flex: none; text-align: center; {CAPS}; font-size: 20px; letter-spacing: 0.04em; color: {MUTED}; line-height: 1.15">{c}</div>' for i, c in enumerate(cols)) + '</div>'
def trow(label, vals, shade=False): return f'<div style="flex: 1; display: flex; align-items: center; border-bottom: 2px solid {LINE};{" background: #F6F8FB;" if shade else ""}"><div style="flex: 1; padding-left: 12px; white-space: nowrap; {D}; font-weight: 700; font-size: 33px; letter-spacing: -0.01em">{label}</div>' + ''.join(f'<div style="width: {WID[i]}px; flex: none; text-align: center; {NUM}; font-size: 34px; color: {INK if i >= 3 else T2}">{v}</div>' for i, v in enumerate(vals)) + '</div>'

SPLITS = ('Jeffries 2: Splits', 'Member Stats', '\n'.join([
    h1('2025&ndash;26 Voting Record', 70),
    f'<div style="font-size: 28px; line-height: 1.2; color: {T2}; margin-top: -12px">House votes, January 3, 2025 through November 18, 2026</div>',
    f'<div style="display: flex; gap: 20px">{tile("Yes Votes", "297")}{tile("No Votes", "384")}{tile("Present", "4")}{tile("Missed", "2")}</div>',
    f'<div style="flex: 1; min-height: 0; display: flex; flex-direction: column">' + thead(['Votes', 'Yes', 'No', 'With His<br>Party*', 'With Most<br>Republicans**'])
    + trow('2025', [362, 142, 217, '98.9%', '29.8%']) + trow('2026', [326, 155, 167, '98.4%', '31.1%'], True)
    + trow('On Bills', [318, 163, 153, '98.4%', '49.4%']) + trow('On Amendments', [90, 13, 77, '97.8%', '33.3%'], True)
    + trow('Everything Else', [280, 121, 154, '99.3%', '7.6%']) + trow('All Votes', [688, 297, 384, '98.7%', '30.4%'], True) + '</div>',
    f'<div style="display: flex; flex-direction: column; gap: 10px; font-size: 27px; line-height: 1.25; color: {T2}"><div><strong style="color: {INK}">*</strong> Voted same way as most DEM (672 of 681 Y/N votes)</div><div><strong style="color: {INK}">**</strong> Voted same way as most REP (207 of 681 Y/N votes)</div><div><strong style="color: {INK}">***</strong> On 202 of them, both parties voted the same way</div></div>',
]))

def lrow(date, name, desc, his, dems, tag='', shade=False, res='Passed'):
    c = '#0E7A3B' if his == 'Yes' else '#B42318'
    t = f'<span style="{CAPS}; font-size: 20px; color: {PURPLE}; border: 2px solid #DCCBFB; background: #F7F3FF; border-radius: 999px; padding: 6px 12px; margin-left: 14px; position: relative; top: -4px; white-space: nowrap">{tag}</span>' if tag else ''
    return (f'<div style="flex: 1; display: flex; align-items: center; gap: 20px; border-bottom: 2px solid {LINE};{" background: #F6F8FB;" if shade else ""}"><div style="width: 118px; flex: none; padding-left: 12px; {NUM}; font-size: 27px; color: {MUTED}">{date}</div>'
            f'<div style="flex: 1; display: flex; flex-direction: column; gap: 7px"><div style="{D}; font-weight: 700; font-size: 33px; line-height: 1.1; letter-spacing: -0.01em">{name}{t}</div><div style="font-size: 28px; line-height: 1.22; color: {T2}">{desc}</div></div>'
            f'<div style="width: 84px; flex: none; text-align: center; {D}; font-weight: 700; font-size: 36px; color: {c}">{his}</div><div style="width: 136px; flex: none; display: flex; flex-direction: column; align-items: center; gap: 8px"><div style="{CAPS}; font-size: 22px; color: {INK}">{res}</div><div style="{NUM}; font-size: 30px; color: {T2}">{dems}</div></div></div>')
LHEAD = f'<div style="display: flex; align-items: center; gap: 20px; padding-bottom: 12px; border-bottom: 3px solid {INK}"><div style="width: 118px; padding-left: 12px; {CAPS}; font-size: 22px; color: {MUTED}">Date</div><div style="flex: 1; {CAPS}; font-size: 22px; color: {MUTED}">Vote</div><div style="width: 84px; text-align: center; {CAPS}; font-size: 22px; color: {MUTED}; line-height: 1.15">His<br>Vote</div><div style="width: 136px; text-align: center; {CAPS}; font-size: 22px; color: {MUTED}; line-height: 1.15">Result<br>DEM Y&ndash;N</div></div>'
def logslide(title, label, head, rows, foot): return (title, label, '\n'.join([h1(head, 64), f'<div style="flex: 1; min-height: 0; display: flex; flex-direction: column">{LHEAD}{rows}</div>', f'<div style="font-size: 25px; line-height: 1.3; color: {MUTED}">{foot}</div>']))
LOG = logslide('Jeffries 3: Game Log', 'Member Stats', 'His 9 Splits From Most Democrats',
    lrow('6/12/25', 'HALT Fentanyl Act', 'Permanently puts fentanyl-related drugs in the strictest drug category.', 'No', '104&ndash;103')
    + lrow('7/17/25', 'GENIUS Act', 'Sets federal rules for stablecoins, digital money meant to hold a steady value.', 'Yes', '102&ndash;110', shade=True)
    + lrow('11/19/25', 'Cory Mills Censure', 'Sent a resolution to censure Rep. Cory Mills to the Ethics Committee instead of voting on it.', 'No', '106&ndash;95', tag='Step')
    + lrow('11/21/25', 'Resolution Denouncing Socialism', 'Says Congress denounces socialism in all its forms.', 'Yes', '86&ndash;98', shade=True)
    + lrow('4/30/26', 'Crawford Farm Bill Amendment', 'Would let food assistance (SNAP) pay for hot rotisserie chicken.', 'No', '196&ndash;12'),
    'Since January 2025<br>See full details and terminology at floortherecord.com')
LOG2 = logslide('Jeffries 4: Game Log, Continued', 'Member Stats', '9 Splits: Continued',
    lrow('5/13/26', 'Nationwide Consumer And Fuel Retailer Choice Act', 'Would allow gasoline with 15 percent ethanol to be sold all year, and end some refinery exemptions.', 'Yes', '95&ndash;113')
    + lrow('5/14/26', 'Cashless Bail Reporting Act', 'Would have the Attorney General list, each year, places that release people charged with certain crimes without cash bail.', 'Yes', '96&ndash;114', shade=True)
    + lrow('7/14/26', 'Sunshine Protection Act', 'Would make daylight saving time permanent.', 'No', '114&ndash;95')
    + lrow('7/15/26', 'Massie Amendment On Aid To Israel', 'Would have barred a State Department funding bill&rsquo;s money from going to Israel and cut $3.3 billion in military aid.', 'No', '103&ndash;98', shade=True, res='Failed'),
    'Since January 2025<br>See full details and terminology at floortherecord.com')

def crow(yr, title, sub): return f'<div style="flex: 1; display: flex; align-items: center; gap: {G}px; border-top: 2px solid {LINE}"><div style="width: 170px; flex: none; {NUM}; font-size: 44px; color: {PURPLE}">{yr}</div><div style="display: flex; flex-direction: column; gap: 6px"><div style="{D}; font-weight: 700; font-size: 38px; line-height: 1.05; letter-spacing: -0.02em">{title}</div><div style="font-size: 30px; line-height: 1.25; color: {T2}">{sub}</div></div></div>'
CAREER = ('Jeffries 5: Career', 'Member Stats', '\n'.join([
    h1('Career', 76),
    f'<div style="flex: 1; min-height: 0; display: flex; flex-direction: column; border-bottom: 2px solid {LINE}">'
    + crow('2007', 'New York State Assembly', 'Served six years, through 2012.') + crow('2013', 'U.S. House', 'Sworn in for New York&rsquo;s 8th District.')
    + crow('2019', 'House Democratic Caucus Chair', 'Held the post for four years.') + crow('2023', 'House Minority Leader', 'Leader of House Democrats since January 3, 2023.')
    + crow('2026', 'Nominated For Speaker', 'House Democrats voted 251 to 11 on November 18.') + '</div>',
    f'<div style="{CARD}; padding: 24px 32px; display: flex; align-items: center; justify-content: space-between; gap: {G}px"><div style="display: flex; flex-direction: column; gap: 10px"><div style="{CAPS}; font-size: 24px; color: {PURPLE}">Next Up</div><div style="{D}; font-weight: 700; font-size: 40px; line-height: 1.05; letter-spacing: -0.02em">The Full House Votes For Speaker</div></div><div style="text-align: right; flex: none"><div style="{NUM}; font-size: 54px; line-height: 1">Jan 3</div><div style="font-size: 26px; color: {T2}; margin-top: 6px">2027</div></div></div>',
    f'<div style="{CARD}; padding: 24px 32px; background: #F7F3FF; display: flex; align-items: center; justify-content: space-between; gap: {G}px"><div style="display: flex; flex-direction: column; gap: 10px"><div style="{CAPS}; font-size: 24px; color: {PURPLE}">Record Book</div><div style="font-size: 31px; line-height: 1.25">Longest House floor speech on record,<br>July 3, 2025.</div></div><div style="{NUM}; font-size: 76px; line-height: 1; color: {PURPLE}; flex: none">8:44</div></div>',
]))

ACT = ('Jeffries 6: Look Up Your Own', 'Your Turn', '\n'.join([
    h1('Every Member Has A Stat Sheet', 70),
    lede('Look up the numbers for the people who represent you.'),
    f'<div style="flex: 1; min-height: 0; display: flex; flex-direction: column; border-bottom: 2px solid {LINE}">'
    + stepn(1, 'Go To floortherecord.com', 'It is free. You do not need an account.')
    + stepn(2, 'Enter Your ZIP Code', 'Find your two senators and your representative.')
    + stepn(3, 'Read Their Record', 'Votes cast, votes missed, and how often they vote with their party.') + '</div>',
    f'<div style="border-radius: 28px; background: {PURPLE}; color: #FFFFFF; padding: {G}px; display: flex; align-items: center; justify-content: space-between; gap: {G}px"><div style="{D}; font-weight: 700; font-size: 64px; line-height: 1; letter-spacing: -0.02em">floortherecord.com</div><div style="font-size: 30px; line-height: 1.2; font-weight: 600; text-align: right">Link in bio</div></div>',
]))
HOOK = ('Stat Card 1: Who Is Hakeem Jeffries', 'In The News',
        f'<div style="flex: 1; display: flex; flex-direction: column; justify-content: center; gap: {G}px">'
        f'<div style="{D}; font-weight: 700; font-size: 150px; line-height: 0.98; letter-spacing: -0.03em"><div style="color: {INK}">Who Is</div><div style="color: {PURPLE}">Hakeem<br>Jeffries?</div></div>'
        f'<p style="margin: 0; font-size: 38px; line-height: 1.3; color: {T2}">House Democrats just nominated him for Speaker.<br>Swipe to see his record, by the numbers.</p>'
        f'<div style="display: flex; align-items: center; gap: 16px; {CAPS}; font-size: 26px; color: {PURPLE}">Swipe For His Stat Sheet<span style="font-size: 34px; line-height: 1">&rarr;</span></div></div>')
SLIDES = {'JeffHook': HOOK, 'JeffCard': CARD1, 'JeffSplits': SPLITS, 'JeffLog': LOG, 'JeffLog2': LOG2, 'JeffCareer': CAREER, 'JeffAct': ACT}
if __name__ == '__main__':
    out = pathlib.Path(sys.argv[1])
    for k, (t, l, b) in SLIDES.items(): (out / f'{k}.dc.html').write_text(page(t, l, b))
    print('wrote', ', '.join(SLIDES))
