"""Weekly recap, scoreboard style: the week of November 16, 2026. Counts from House and Senate roll calls."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from race_carousel_example import page, h1, lede, INK, T2, MUTED, LINE, RED, PURPLE, BLUE, D, G, CARD, CAP
NUM = f'{D}; font-weight: 700; letter-spacing: -0.04em; font-variant-numeric: tabular-nums'
import json
GAPS = json.loads((pathlib.Path(__file__).parent / 'score_gaps.json').read_text())   # measured by scorefit.py
def sc(yes, no, c1=None, c2=None, dash=None, gap=0.085):
    """A score with exactly the same blank space on both sides of the dash (digits differ in built-in side space)."""
    l, r = GAPS[f'{yes}-{no}']
    return (f'<span style="display: inline-flex; align-items: center; letter-spacing: -0.02em; font-variant-numeric: proportional-nums"><span style="color: {c1 or PURPLE}">{yes}</span>'
            f'<span style="display: inline-block; width: 0.34em; height: 0.085em; margin: 0 {gap - r:.4f}em 0 {gap - l:.4f}em; background: {dash or MUTED}"></span><span style="color: {c2 or INK}">{no}</span></span>')
SWIPE = lambda t: f'<div style="display: flex; align-items: center; gap: 16px; {CAP}; color: {PURPLE}">{t}<span style="font-size: 34px; line-height: 1">&rarr;</span></div>'
def trio(n, label, color): return f'<div style="flex: 1; display: flex; align-items: center; gap: {G}px; border-top: 2px solid {LINE}"><div style="{NUM}; font-size: 190px; line-height: 0.9; color: {color}; width: 300px; flex: none">{n}</div><div style="{D}; font-weight: 700; font-size: 58px; line-height: 1.02; letter-spacing: -0.02em">{label}</div></div>'
HOOK = ('Recap 1: Last Week In Congress', 'The Scoreboard', '\n'.join([
    f'<div style="{D}; font-weight: 700; font-size: 104px; line-height: 0.98; letter-spacing: -0.03em">Last Week<br><span style="color: {PURPLE}">In Congress</span></div>',
    f'<div style="flex: 1; min-height: 0; display: flex; flex-direction: column; border-bottom: 2px solid {LINE}">' + trio('14', 'Real<br>Votes', INK) + trio('2', 'Nail-<br>Biters', RED) + trio('1', 'Giant<br>Energy Bill', PURPLE) + '</div>',
    SWIPE('Swipe For The Scores'),
]))
def score(title, tag, yes, no, verdict, name, line, extra=''):
    return (title, tag, '\n'.join([
        f'<div style="{D}; font-weight: 700; font-size: 84px; line-height: 1; letter-spacing: -0.03em">{tag}</div>',
        f'<div style="flex: 1; min-height: 0; display: flex; flex-direction: column; justify-content: center; gap: 20px"><div style="display: flex; align-items: baseline; gap: 26px; {NUM}; font-size: 300px; line-height: 0.86"><span style="color: {PURPLE}">{yes}</span><span style="font-size: 150px; color: {MUTED}">&ndash;</span><span style="color: {INK}">{no}</span></div>'
        f'<div style="display: flex; gap: 14px"><span style="{CAP}; color: #FFFFFF; background: {INK}; border-radius: 999px; padding: 10px 22px">{verdict}</span></div></div>',
        f'<div style="display: flex; flex-direction: column; gap: 14px; border-top: 2px solid {LINE}; padding-top: {G}px"><div style="{D}; font-weight: 700; font-size: 54px; line-height: 1.04; letter-spacing: -0.02em">{name}</div><div style="font-size: 34px; line-height: 1.3; color: {T2}">{line}</div>{extra}</div>',
    ]))
def blk(label, body, grow=1): return f'<div style="flex: {grow} 1 0; display: flex; flex-direction: column; gap: 20px; border-top: 2px solid {LINE}; padding-top: {G}px"><div style="{CAP}; color: {PURPLE}; font-size: 28px">{label}</div><div style="font-size: 45px; line-height: 1.26; color: {INK}">{body}</div></div>'
def pt(t): return f'<div style="display: flex; gap: 16px"><span style="color: {PURPLE}; font-weight: 700">&ndash;</span><span>{t}</span></div>'
def story(title, tag, yes, no, verdict, name, what, means):
    return (title, tag, '\n'.join([
        f'<div style="display: flex; align-items: flex-end; justify-content: space-between; gap: 24px"><div style="display: flex; flex-direction: column; gap: 16px"><div style="{CAP}; color: {MUTED}">{tag}</div><div style="{D}; font-weight: 700; font-size: 60px; line-height: 1.02; letter-spacing: -0.025em">{name}</div></div>'
        f'<div style="flex: none; display: flex; flex-direction: column; align-items: flex-end; gap: 12px"><div style="{NUM}; font-size: 120px; line-height: 0.86; white-space: nowrap">{sc(yes, no)}</div><span style="{CAP}; color: #FFFFFF; background: {INK}; border-radius: 999px; padding: 8px 18px; font-size: 22px">{verdict}</span></div></div>',
        f'<div style="flex: 1; min-height: 0; display: flex; flex-direction: column">' + blk('What it is', what) + blk('What it means', f'<div style="display: flex; flex-direction: column; gap: 26px">{means}</div>', 1.3) + '</div>',
    ]))
BIG = story('Recap 2: The Big One', 'The Big One', 62, 33, 'Senate · Passed', 'The Energy<br>Permitting Bill',
            'A bill to make federal permits for power lines, pipelines, and other energy projects faster to get and harder to undo.',
            pt('Agencies get new and shorter deadlines to review projects.') + pt('Lawsuits over those reviews must be filed within 150 days.') + pt('It is not law yet. The House votes next.'))
CLOSE = story('Recap 3: The Closest One', 'The Nail-Biter', 48, 51, 'Senate · Failed', 'Ending Hostilities<br>Against Iran',
              'A resolution directing the President to pull U.S. forces out of hostilities against Iran unless Congress approves them.',
              pt('It lost by 3 votes, so it goes no further.') + pt('The House had passed it in September.') + pt('3 Republicans voted yes.<br>1 Democrat voted no.'))
SHUT = story('Recap 4: The Shutout', 'The Shutout', 401, 0, 'House · Passed', 'Preventive Health<br>Savings Act',
             'A bill about how Congress counts costs. It lets committee leaders ask Congress&rsquo;s budget office to estimate longer-term savings from preventive health care.',
             pt('Those savings could appear in a bill&rsquo;s official cost report.') + pt('They are extra information. They cannot be used to get around budget rules.') + pt('It is not law yet. The Senate is next.'))
def row(name, sub, s, verdict='Confirmed'):
    return f'<div style="flex: 1; display: flex; align-items: center; gap: 24px; border-top: 2px solid {LINE}"><div style="flex: 1; display: flex; flex-direction: column; gap: 8px"><div style="{D}; font-weight: 700; font-size: 46px; line-height: 1.04; letter-spacing: -0.02em">{name}</div><div style="font-size: 30px; line-height: 1.25; color: {T2}">{sub}</div></div><div style="flex: none; text-align: right"><div style="{NUM}; font-size: 76px; line-height: 1; color: {PURPLE}; white-space: nowrap">{s}</div></div></div>'
BENCH = ('Recap 5: The Bench', 'The Bench', '\n'.join([
    f'<div style="{D}; font-weight: 700; font-size: 84px; line-height: 1; letter-spacing: -0.03em">The Bench</div>',
    lede('The Senate confirmed four federal judges.'),
    f'<div style="flex: 1; min-height: 0; display: flex; flex-direction: column; border-bottom: 2px solid {LINE}">' + row('Daniel Domenico', 'Appeals court, Tenth Circuit', sc(51, 46, PURPLE, PURPLE, PURPLE)) + row('Anna St. John', 'Appeals court, Fifth Circuit', sc(52, 46, PURPLE, PURPLE, PURPLE)) + row('Richard Bennett', 'District court, Southern Texas', sc(49, 43, PURPLE, PURPLE, PURPLE)) + row('Courtney Coker', 'District court, Northern Texas', sc(49, 41, PURPLE, PURPLE, PURPLE)) + '</div>',
]))
REST = ('Recap 6: The Rest Of The Board', 'Also On The Board', '\n'.join([
    f'<div style="{D}; font-weight: 700; font-size: 84px; line-height: 1; letter-spacing: -0.03em">Also On<br>The Board</div>',
    lede('Three more bills passed the House.'),
    f'<div style="flex: 1; min-height: 0; display: flex; flex-direction: column; border-bottom: 2px solid {LINE}">' + row('Barona Band Land Transfer', 'Puts land in trust for a California tribe.', sc(398, 0, PURPLE, PURPLE, PURPLE)) + row('Earth MRI Reauthorization', 'Extends a federal mineral mapping program.', sc(396, 14, PURPLE, PURPLE, PURPLE)) + row('Thomas Paine Memorial', 'Approves a spot near the National Mall.', sc(365, 36, PURPLE, PURPLE, PURPLE)) + '</div>',
]))
ACT = ('Recap 7: How Did Yours Vote', 'Your Turn', '\n'.join([
    f'<div style="flex: 1; display: flex; flex-direction: column; justify-content: center; gap: {G}px"><div style="{D}; font-weight: 700; font-size: 132px; line-height: 0.98; letter-spacing: -0.03em">How Did<br><span style="color: {PURPLE}">Yours</span><br>Vote?</div>' + lede('Every vote, every member, in plain English.') + '</div>',
    f'<div style="border-radius: 28px; background: {PURPLE}; color: #FFFFFF; padding: {G}px; display: flex; flex-direction: column; gap: 14px"><div style="font-size: 30px; line-height: 1.2; font-weight: 600">Look up your representative and senators</div><div style="{D}; font-weight: 700; font-size: 64px; line-height: 1; letter-spacing: -0.02em">floortherecord.com</div></div>',
]))
def crisp(html):
    """Make every slide hold up when someone zooms in on Instagram, which stores posts 1080 pixels wide:
    one near-navy text color (no greys), medium weight for large sentences, semibold for anything 34px or smaller."""
    import re
    html = (html.replace('color: #14213D; font-family: Inter, sans-serif;', 'color: #14213D; font-family: Inter, sans-serif; font-weight: 500;')
                .replace('#3B4A66', '#14213D').replace('#5A6473', '#2A3550'))
    def small(m):
        st = m.group(1); z = re.search(r'font-size: (\d+)px', st)
        if z and int(z.group(1)) <= 34 and 'font-weight' not in st: st += '; font-weight: 600'
        if z and int(z.group(1)) <= 26: st = st.replace('font-weight: 500', 'font-weight: 600')
        return f'style="{st}"'
    return re.sub(r'style="([^"]*)"', small, html)
SLIDES = {'RecapHook': HOOK, 'RecapBig': BIG, 'RecapClose': CLOSE, 'RecapShut': SHUT, 'RecapBench': BENCH, 'RecapRest': REST, 'RecapAct': ACT}
if __name__ == '__main__':
    out = pathlib.Path(sys.argv[1])
    for k, (t, l, b) in SLIDES.items(): (out / f'{k}.dc.html').write_text(crisp(page(t, l, b)))
    print('wrote', ', '.join(SLIDES))
