"""Option: a box score slide for the shutdown bill (H.R. 5371). Numbers from the Senate and House roll calls."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from race_carousel_example import page, h1, lede, INK, T2, MUTED, LINE, RED, PURPLE, BLUE, D, G, CARD, CAP
GREY = '#8A93A3'
NUM = f"{D}; font-weight: 700; font-variant-numeric: tabular-nums; letter-spacing: -0.01em"
def dot(c): return f'<span style="display: inline-block; width: 14px; height: 14px; border-radius: 50%; background: {c}; margin-right: 8px"></span>'
def head(cols): return f'<div style="display: flex; align-items: center; padding: 0 {G}px 14px"><div style="flex: 1"></div>' + ''.join(f'<div style="width: 150px; text-align: center; white-space: nowrap; {CAP}; font-size: 20px; color: {MUTED}">{c}</div>' for c in cols) + '</div>'
def line(label, vals, bold_last=True, top=True):
    cells = ''.join(f'<div style="width: 150px; text-align: center; {NUM}; font-size: 42px; line-height: 1; color: {INK if i == len(vals) - 1 else T2}">{v}</div>' for i, v in enumerate(vals))
    return f'<div style="display: flex; align-items: center; padding: 17px {G}px; border-top: 2px solid {LINE}"><div style="flex: 1; {D}; font-weight: 700; font-size: 38px; line-height: 1; letter-spacing: -0.02em">{label}</div>{cells}</div>'
def box(name, date, cols, rows):
    return (f'<div style="border: 2px solid {LINE}; border-radius: 28px; overflow: hidden; display: flex; flex-direction: column; flex: none">'
            f'<div style="background: {INK}; color: #FFFFFF; display: flex; align-items: center; justify-content: space-between; padding: 18px {G}px"><div style="{CAP}">{name}</div><div style="{CAP}; font-size: 20px; opacity: 0.75">{date}</div><div style="{CAP}; background: {PURPLE}; border-radius: 999px; padding: 9px 16px; font-size: 19px">Final</div></div>'
            f'<div style="padding-top: 18px">{head(cols)}{"".join(line(l, v) for l, v in rows)}</div></div>')
def stat(n, label): return f'<div style="flex: 1; {CARD}; padding: 22px; display: flex; flex-direction: column; gap: 8px"><div style="{NUM}; font-size: 54px; line-height: 1; color: {PURPLE}">{n}</div><div style="font-size: 22px; line-height: 1.25; color: {T2}">{label}</div></div>'
R, Dm, I = dot(RED) + 'Rep', dot(BLUE) + 'Dem', dot(GREY) + 'Ind'
BOX = ('Shutdown 6: Box Score', 'Box Score', '\n'.join([
    h1('The Bill That Ended The Shutdown', 62),
    f'<div style="flex: 1; min-height: 0; display: flex; flex-direction: column; justify-content: space-between; gap: {G}px">'
    + box('Senate', 'Nov 10, 2025', [R, Dm, I, 'Total'], [('Yes', [52, 7, 1, 60]), ('No', [1, 38, 1, 40])])
    + box('House', 'Nov 12, 2025', [R, Dm, 'Total'], [('Yes', [216, 6, 222]), ('No', [2, 207, 209]), ('Did Not Vote', [1, 1, 2])])
    + f'<div style="display: flex; gap: 20px">{stat(43, "days the government was shut down")}{stat(14, "Senate votes that fell short first")}{stat(60, "Senate votes needed to move forward")}{stat(16, "members who broke with their party")}</div></div>',
]))
if __name__ == '__main__':
    out = pathlib.Path(sys.argv[1]); t, l, b = BOX
    (out / 'ShutBox.dc.html').write_text(page(t, l, b)); print('wrote ShutBox')
