"""Thanksgiving 2026: why the holiday is the fourth Thursday in November. Facts from the National Archives,
Center for Legislative Archives, "Congress Establishes Thanksgiving" (H.J. Res. 41, 77th Congress)."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from race_carousel_example import page, h1, lede, INK, T2, MUTED, LINE, RED, PURPLE, BLUE, D, G, CARD, CAP
from weekly_recap_example import NUM, SWIPE, sc, crisp, pt
BIGH = f'{D}; font-weight: 700; letter-spacing: -0.03em'
SRC = f'<div style="font-size: 26px; line-height: 1.2; color: {MUTED}">Source: National Archives</div>'
HOOK = ('Thanksgiving 1: Why The Fourth Thursday', 'Happy Thanksgiving', '\n'.join([
    f'<div style="flex: 1; display: flex; flex-direction: column; justify-content: center; gap: {G}px"><div style="{BIGH}; font-size: 116px; line-height: 0.98">Why Is<br>Thanksgiving<br>Always <span style="color: {PURPLE}">The Fourth<br>Thursday?</span></div>'
    f'<div style="font-size: 46px; line-height: 1.2; font-weight: 600">Because Congress voted on it.</div></div>',
    SWIPE('Swipe For The Story'),
]))
def stepc(n, title, sub, hi=False):
    return (f'<div style="flex: 1; display: flex; align-items: center; gap: {G}px; border-top: 2px solid {LINE}"><div style="width: 84px; height: 84px; flex: none; border-radius: 50%; background: {PURPLE if hi else "#F1EAFE"}; color: {"#FFFFFF" if hi else PURPLE}; display: flex; align-items: center; justify-content: center; {D}; font-weight: 700; font-size: 46px">{n}</div>'
            f'<div style="display: flex; flex-direction: column; gap: 10px"><div style="{BIGH}; font-size: 50px; line-height: 1.04; letter-spacing: -0.02em">{title}</div><div style="font-size: 36px; line-height: 1.26">{sub}</div></div></div>')
BEFORE = ('Thanksgiving 2: It Used To Be The Last Thursday', 'Before 1939', '\n'.join([
    f'<div style="{CAP}; color: {MUTED}">First, the tradition</div>',
    f'<div style="{BIGH}; font-size: 92px; line-height: 0.98; margin-top: -12px">It Used To Be<br>The <span style="color: {PURPLE}">Last</span><br>Thursday</div>',
    f'<div style="flex: 1; min-height: 0; display: flex; flex-direction: column; justify-content: center; gap: 30px; border-top: 2px solid {LINE}; border-bottom: 2px solid {LINE}; font-size: 48px; line-height: 1.26">{pt("No law set the date.")}{pt("Each year, the President picked it.")}{pt("Since Abraham Lincoln, that almost always meant the last Thursday in November.")}</div>',
    SRC,
]))
def cal():
    days = ['S', 'M', 'T', 'W', 'T', 'F', 'S']; cells = [''] * 3 + [str(d) for d in range(1, 31)] + [''] * 2
    def cell(c):
        if c == '23': st = f'background: {PURPLE}; color: #FFFFFF'
        elif c == '30': st = f'background: #FFFFFF; color: {INK}; box-shadow: inset 0 0 0 5px {INK}'
        else: st = f'color: {INK if c else "transparent"}'
        return f'<div style="height: 60px; display: flex; align-items: center; justify-content: center; border-radius: 16px; {D}; font-weight: 700; font-size: 36px; {st}">{c or "0"}</div>'
    head = ''.join(f'<div style="height: 44px; display: flex; align-items: center; justify-content: center; {CAP}; font-size: 24px; color: {PURPLE if i == 4 else MUTED}">{d}</div>' for i, d in enumerate(days))
    return f'<div style="{CARD}; padding: 18px {G}px"><div style="{CAP}; color: {MUTED}; font-size: 26px; text-align: center; padding-bottom: 4px">November 1939</div><div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px 10px">{head}{"".join(cell(c) for c in cells)}</div></div>'
def key(color, ring, title, sub):
    dot = f'background: {color}' if not ring else f'background: #FFFFFF; box-shadow: inset 0 0 0 5px {INK}'
    return f'<div style="flex: 1; display: flex; align-items: center; gap: 18px"><div style="width: 56px; height: 56px; flex: none; border-radius: 16px; {dot}"></div><div style="display: flex; flex-direction: column; gap: 4px"><div style="{BIGH}; font-size: 36px; line-height: 1.05; letter-spacing: -0.02em">{title}</div><div style="font-size: 30px; line-height: 1.2">{sub}</div></div></div>'
MOVED = ('Thanksgiving 3: In 1939 The President Moved It', '1939', '\n'.join([
    f'<div style="{CAP}; color: {MUTED}">Then, 1939</div>',
    f'<div style="{BIGH}; font-size: 72px; line-height: 1; margin-top: -12px">The President<br>Moved It <span style="color: {PURPLE}">Up A Week</span></div>',
    f'<div style="font-size: 36px; line-height: 1.26">Franklin Roosevelt wanted a longer Christmas shopping season.</div>',
    cal(),
    f'<div style="flex: 1; min-height: 0; display: flex; align-items: center; gap: 24px">{key(PURPLE, False, "About Half The States", "Used the new date")}{key(INK, True, "About Half", "Kept the old date")}</div>',
    f'<div style="font-size: 36px; line-height: 1.26; font-weight: 600">America had two Thanksgivings,<br>in 1939 and again in 1940.</div>',
    SRC,
]))
SETTLED = ('Thanksgiving 4: In 1941 Congress Settled It', '1941', '\n'.join([
    f'<div style="{CAP}; color: {MUTED}">Finally, 1941</div>',
    f'<div style="{BIGH}; font-size: 92px; line-height: 0.98; margin-top: -12px">Congress<br><span style="color: {PURPLE}">Settled It</span></div>',
    f'<div style="flex: 1; min-height: 0; display: flex; flex-direction: column; border-bottom: 2px solid {LINE}">'
    + stepc(1, 'The House Voted', 'Make it the <strong>last</strong> Thursday, by law.')
    + stepc(2, 'The Senate Changed One Word', 'Make it the <strong>fourth</strong> Thursday,<br>since some Novembers have five.')
    + stepc(3, 'The House Agreed', 'The President signed it on December 26, 1941.<br>It has been the fourth Thursday ever since.', True) + '</div>',
    SRC,
]))
BYE = ('Thanksgiving 5: Happy Thanksgiving', 'Happy Thanksgiving', '\n'.join([
    f'<div style="flex: 1; display: flex; flex-direction: column; justify-content: center; gap: {G}px"><div style="{BIGH}; font-size: 128px; line-height: 0.98">Happy<br><span style="color: {PURPLE}">Thanksgiving</span></div>'
    f'<div style="font-size: 40px; line-height: 1.28">One more: George Washington&rsquo;s first Thanksgiving proclamation named<br><strong>Thursday, November 26</strong>, 1789.<br>Today is <strong>Thursday, November 26</strong>.</div></div>',
    f'<div style="border-radius: 28px; background: {PURPLE}; color: #FFFFFF; padding: {G}px; display: flex; flex-direction: column; gap: 14px"><div style="font-size: 30px; line-height: 1.2; font-weight: 600">How Congress votes, in plain English</div><div style="{D}; font-weight: 700; font-size: 64px; line-height: 1; letter-spacing: -0.02em">floortherecord.com</div></div>',
]))
SLIDES = {'ThanksHook': HOOK, 'ThanksBefore': BEFORE, 'ThanksMoved': MOVED, 'ThanksSettled': SETTLED, 'ThanksBye': BYE}
if __name__ == '__main__':
    out = pathlib.Path(sys.argv[1])
    for k, (t, l, b) in SLIDES.items(): (out / f'{k}.dc.html').write_text(crisp(page(t, l, b)))
    print('wrote', ', '.join(SLIDES))
