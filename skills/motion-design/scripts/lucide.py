"""Lucide helper. Needs the icon files: `npm install lucide-static` (in the working directory,
next to this script, or in ~/iconsets), or set LUCIDE_STATIC to the package folder.

  python3 lucide.py find lock permission     -> icon names matching the words (names + tags)
  python3 lucide.py g lock --at 60,46 --size 28 [--cls "a-x"] [--color "var(--mark)"]
                                              -> an inline <g> centred at x,y, ready to paste into an .xicon svg
"""
import sys, os, re, json
_here = os.path.dirname(os.path.abspath(__file__))
ROOTS = [os.environ.get('LUCIDE_STATIC', ''), os.path.join(os.getcwd(), 'node_modules/lucide-static'),
         os.path.join(_here, 'node_modules/lucide-static'), os.path.expanduser('~/iconsets/node_modules/lucide-static')]
ROOT = next((r for r in ROOTS if r and os.path.isdir(r)), None)
if ROOT is None: raise SystemExit('lucide-static not found: run `npm install lucide-static` or set LUCIDE_STATIC')

def inner(name):
    p = f'{ROOT}/icons/{name}.svg'
    if not os.path.exists(p): raise SystemExit(f'no Lucide icon named {name!r}; try: lucide.py find <words>')
    s = open(p).read()
    s = re.sub(r'<!--.*?-->', '', s, flags=re.S); s = re.sub(r'<svg[^>]*>', '', s, flags=re.S).replace('</svg>', '')
    return ''.join(l.strip() for l in s.strip().splitlines())

def lu(name, x, y, size=28, cls='', color='', anim=''):
    """<g> centred at (x,y) in the 120 viewBox. `anim` = class for an inner group that can be animated (translate/scale) freely."""
    s = size / 24
    col = f';color:{color}' if color else ''
    body = f'<g class="lu {cls}" style="transform:scale({s:.3f}) translate(-12px,-12px){col}">{inner(name)}</g>'
    if anim: body = f'<g class="{anim}">{body}</g>'
    return f'<g style="transform:translate({x}px,{y}px)">{body}</g>'

if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == 'find':
        tags = json.load(open(f'{ROOT}/tags.json')); words = [w.lower() for w in a[1:]]
        hits = []
        for n, t in tags.items():
            hay = n + ' ' + ' '.join(t); sc = sum((3 if w in n else 1) for w in words if w in hay)
            if sc: hits.append((-sc, n))
        print(' '.join(n for _, n in sorted(hits)[:40]))
    elif a and a[0] == 'g':
        def opt(f, d): return a[a.index(f) + 1] if f in a else d
        x, y = [float(v) for v in opt('--at', '60,60').split(',')]
        print(lu(a[1], x, y, float(opt('--size', 28)), opt('--cls', ''), opt('--color', '')))
    else: print(__doc__)
