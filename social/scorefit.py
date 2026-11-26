"""Measure, in a real browser, the blank space between a score's digits and its dash, so both sides can be made equal.
Run from /home/claude/racecheck (fonts). Writes score_gaps.json: {"401-0": [left_em, right_em], ...} with zero margins."""
import json, sys, pathlib
from playwright.sync_api import sync_playwright
from PIL import Image
import io
PAIRS = [(32,16),(401,0),(62,33),(48,51),(51,46),(52,46),(49,43),(49,41),(398,0),(396,14),(365,36)]
PX = 400
faces = "@font-face{font-family:\"Inter Tight\";font-weight:700;src:url(node_modules/@fontsource/inter-tight/files/inter-tight-latin-700-normal.woff2) format('woff2')}"
def html(y, n):
    return (f'<!doctype html><meta charset="utf-8"><style>body{{margin:40px;background:#fff}}{faces}</style>'
            f'<span id="s" style="font-family:\'Inter Tight\';font-weight:700;font-size:{PX}px;line-height:1;display:inline-flex;align-items:center;letter-spacing:-0.02em;font-variant-numeric:proportional-nums">'
            f'<span style="color:#f00">{y}</span><span style="display:inline-block;width:0.34em;height:0.085em;background:#0f0"></span><span style="color:#00f">{n}</span></span>')
out = {}
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_context(viewport={'width': 2400, 'height': 600}).new_page()
    for y, n in PAIRS:
        pathlib.Path('fit.html').write_text(html(y, n)); pg.goto('file://' + str(pathlib.Path('fit.html').resolve())); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(250)
        im = Image.open(io.BytesIO(pg.screenshot())).convert('RGB'); w, h = im.size; px = im.load()
        isg = lambda c: c[1] > 200 and c[0] < 80 and c[2] < 80
        rows = [yy for yy in range(h) if any(isg(px[x, yy]) for x in range(0, w, 3))]
        band = range(max(0, min(rows) - int(0.13 * PX)), min(h, max(rows) + int(0.13 * PX)))   # judge the gap where the eye does: around the dash's height
        def cols(test): return [x for x in range(w) if any(test(px[x, yy]) for yy in band)]
        red = cols(lambda c: c[0] > 200 and c[1] < 80 and c[2] < 80); grn = cols(lambda c: c[1] > 200 and c[0] < 80 and c[2] < 80); blu = cols(lambda c: c[2] > 200 and c[0] < 80 and c[1] < 80)
        out[f'{y}-{n}'] = [round((min(grn) - max(red) - 1) / PX, 4), round((min(blu) - max(grn) - 1) / PX, 4)]
    b.close()
json.dump(out, open('/home/claude/social/score_gaps.json', 'w'), indent=1); print(out)
