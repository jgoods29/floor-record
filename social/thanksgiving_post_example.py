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
SPLIT = ('Thanksgiving 2: Two Thanksgivings', '1939', '\n'.join([
    f'<div style="{CAP}; color: {MUTED}">1939</div>',
    f'<div style="{BIGH}; font-size: 88px; line-height: 1; margin-top: -12px">Two<br>Thanksgivings</div>',
    f'<div style="flex: 1; min-height: 0; display: flex; flex-direction: column; justify-content: center; gap: 22px; border-top: 2px solid {LINE}; border-bottom: 2px solid {LINE}"><div style="{NUM}; font-size: 250px; line-height: 0.86">{sc(32, 16)}</div><div style="{CAP}; color: {PURPLE}; font-size: 28px">States that moved it &nbsp;&middot;&nbsp; States that did not</div></div>',
    f'<div style="display: flex; flex-direction: column; gap: 22px; font-size: 40px; line-height: 1.26">{pt("President Roosevelt moved the holiday<br>up a week, for a longer Christmas<br>shopping season.")}{pt("For two years, the country celebrated<br>on two different days.")}</div>',
    SRC,
]))
def side(who, when, word, color):
    return (f'<div style="flex: 1; {CARD}; padding: {G}px; display: flex; flex-direction: column; gap: 18px"><div style="display: flex; align-items: center; gap: 14px"><span style="{CAP}; color: #FFFFFF; background: {INK}; border-radius: 999px; padding: 8px 18px; font-size: 24px">{who}</span><span style="font-size: 28px; font-weight: 600; color: {MUTED}">{when}</span></div>'
            f'<div style="{BIGH}; font-size: 92px; line-height: 0.98">The <span style="color: {color}">{word}</span><br>Thursday</div></div>')
VERSUS = ('Thanksgiving 3: House Says Last, Senate Says Fourth', '1941', '\n'.join([
    f'<div style="{CAP}; color: {MUTED}">1941: Congress steps in</div>',
    f'<div style="{BIGH}; font-size: 70px; line-height: 1.02; margin-top: -12px">The House Said &ldquo;Last.&rdquo;<br>The Senate Said &ldquo;Fourth.&rdquo;</div>',
    f'<div style="flex: 1; min-height: 0; display: flex; flex-direction: column; gap: 24px">{side("House", "October 6, 1941", "Last", INK)}{side("Senate", "December 9, 1941", "Fourth", PURPLE)}</div>',
    f'<div style="font-size: 38px; line-height: 1.26"><strong>Why it matters:</strong> some Novembers<br>have five Thursdays.</div>',
    SRC,
]))
LAW = ('Thanksgiving 4: Signed December 26, 1941', 'The Final Score', '\n'.join([
    f'<div style="{CAP}; color: {MUTED}">The final step</div>',
    f'<div style="{BIGH}; font-size: 88px; line-height: 1; margin-top: -12px">Fourth<br><span style="color: {PURPLE}">Wins</span></div>',
    f'<div style="flex: 1; min-height: 0; display: flex; flex-direction: column; justify-content: center; gap: 26px; border-top: 2px solid {LINE}; border-bottom: 2px solid {LINE}; font-size: 42px; line-height: 1.26">{pt("The House agreed to the Senate&rsquo;s<br>one-word change.")}{pt("President Roosevelt signed it<br>on December 26, 1941.")}{pt("It has been the fourth Thursday ever since.")}</div>',
    f'<div style="{CARD}; background: #F7F3FF; padding: {G}px; display: flex; flex-direction: column; gap: 14px"><div style="{CAP}; color: {PURPLE}; font-size: 26px">Sound familiar?</div><div style="font-size: 36px; line-height: 1.28">Both chambers have to pass the same words.<br>Last week&rsquo;s energy permitting bill is at this exact step: back to the House.</div></div>',
    SRC,
]))
BYE = ('Thanksgiving 5: Happy Thanksgiving', 'Happy Thanksgiving', '\n'.join([
    f'<div style="flex: 1; display: flex; flex-direction: column; justify-content: center; gap: {G}px"><div style="{BIGH}; font-size: 128px; line-height: 0.98">Happy<br><span style="color: {PURPLE}">Thanksgiving</span></div>'
    f'<div style="font-size: 40px; line-height: 1.28">One more: George Washington&rsquo;s first Thanksgiving proclamation named<br><strong>Thursday, November 26</strong>, 1789.<br>Today is <strong>Thursday, November 26</strong>.</div></div>',
    f'<div style="border-radius: 28px; background: {PURPLE}; color: #FFFFFF; padding: {G}px; display: flex; flex-direction: column; gap: 14px"><div style="font-size: 30px; line-height: 1.2; font-weight: 600">How Congress votes, in plain English</div><div style="{D}; font-weight: 700; font-size: 64px; line-height: 1; letter-spacing: -0.02em">floortherecord.com</div></div>',
]))
SLIDES = {'ThanksHook': HOOK, 'ThanksSplit': SPLIT, 'ThanksVersus': VERSUS, 'ThanksLaw': LAW, 'ThanksBye': BYE}
if __name__ == '__main__':
    out = pathlib.Path(sys.argv[1])
    for k, (t, l, b) in SLIDES.items(): (out / f'{k}.dc.html').write_text(crisp(page(t, l, b)))
    print('wrote', ', '.join(SLIDES))
