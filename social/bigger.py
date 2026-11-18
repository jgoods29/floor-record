"""Readable-on-a-phone pass: raises every small text size on a 1080x1350 slide. Big headlines stay as they are."""
import re
SIZES = {20: 24, 22: 26, 23: 26, 24: 26, 25: 27, 27: 30, 28: 30, 29: 31, 34: 36, 40: 42}
def bigger(html):
    head, sep, rest = html.partition('</helmet>')
    def f(m):
        n = int(m.group(1)); return f'font-size: {SIZES.get(n, n)}px'
    rest = re.sub(r'font-size: (\d+)px', f, rest)
    # keep the brand line and its pill at their set sizes
    rest = rest.replace("font-size: 26px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; line-height: 1; color: #6D28D9; border: 2px solid #DCCBFB", "font-size: 24px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; line-height: 1; color: #6D28D9; border: 2px solid #DCCBFB")
    return head + sep + rest
