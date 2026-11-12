"""Frame sheets and GIFs for motion graphics (.mo / .xicon elements) in an HTML page.

  python3 mo_frames.py page.html outdir [--gif] [--fps 12] [--width 960] [--hold 4]

Looping graphics (infinite iterations) export as looping GIFs.
Play-once graphics export as a GIF that plays once and rests on the final frame for --hold seconds.
"""
import sys, os, io
from playwright.sync_api import sync_playwright
from PIL import Image

page_path, outdir = sys.argv[1], sys.argv[2]
def opt(flag, default):
    return type(default)(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default
want_gif = '--gif' in sys.argv
fps, width, hold = opt('--fps', 12), opt('--width', 960), opt('--hold', 4.0)
only = opt('--only', '')            # substring filter on data-name
phase, lead = opt('--phase', 0.9), opt('--lead', 0.7)   # GIFs open on the finished frame
loops, rest = opt('--loops', 3), opt('--rest', 2.5)   # icons: play N times (0 = forever), resting on the finished frame between plays
os.makedirs(outdir, exist_ok=True)

SEL = '.mo, .xicon'
INFO = """(i)=>{const el=document.querySelectorAll('%s')[i];
  const an=el.getAnimations({subtree:true});
  const t=an.map(a=>a.effect.getComputedTiming());
  const loops=t.some(x=>x.iterations===Infinity);
  const total=loops?Math.max(0,...t.map(x=>x.duration)):Math.max(0,...t.map(x=>x.endTime));
  return {loops,total,count:an.length,name:el.dataset.name||[...el.classList].find(c=>!['mo','xicon','static'].includes(c))||('mo'+i)}}""" % SEL
SEEK = """([i,t])=>{document.querySelectorAll('%s')[i].getAnimations({subtree:true}).forEach(a=>{a.pause();a.currentTime=t;});}""" % SEL

def shared_palette(frames, colors=48, bg=None):
    """Quantize all frames to one small palette (flat graphics need few colours) and keep the
    background colour exact, so the GIF is small and its box does not show against the slide."""
    n = len(frames); w, h = frames[0].size
    strip = Image.new('RGB', (w * 2, h)); strip.paste(frames[0], (0, 0)); strip.paste(frames[n // 2], (w, 0))
    pal = strip.quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.Dither.NONE)
    bg = bg or frames[0].getpixel((2, 2)); p = pal.getpalette()[:colors * 3]
    k = min(range(len(p) // 3), key=lambda i: sum((p[i * 3 + c] - bg[c]) ** 2 for c in range(3))); p[k * 3:k * 3 + 3] = list(bg); pal = Image.new('P', (1, 1)); pal.putpalette(p + p[:3] * (256 - len(p) // 3))
    return [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]

def fix_gif_background(path, bg, tol=3):
    """Set every palette entry within `tol` of `bg` to exactly `bg`, in the global
    and every local colour table. Pillow's GIF writer can shift palette values by one step; an exact
    background keeps the GIF's box invisible against a slide of the same colour."""
    b = bytearray(open(path, 'rb').read())
    def patch(off, size):
        for i in range(size // 3):
            if max(abs(b[off + i * 3 + c] - bg[c]) for c in range(3)) <= tol: b[off + i * 3:off + i * 3 + 3] = bytes(bg)
    def skip_sub(p):
        while b[p]: p += b[p] + 1
        return p + 1
    p = 13
    if b[10] & 0x80:
        n = 3 * 2 ** ((b[10] & 7) + 1); patch(13, n); p += n
    while p < len(b):
        if b[p] == 0x21: p = skip_sub(p + 2)
        elif b[p] == 0x2C:
            f = b[p + 9]; p += 10
            if f & 0x80:
                n = 3 * 2 ** ((f & 7) + 1); patch(p, n); p += n
            p = skip_sub(p + 1)
        else: break
    open(path, 'wb').write(b)

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1200, 'height': 900}, device_scale_factor=2)
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('file://' + os.path.abspath(page_path)); pg.wait_for_timeout(300)
    els = pg.locator(SEL)
    for i in range(els.count()):
        el = els.nth(i); info = pg.evaluate(INFO, i); name, total = info['name'], info['total']
        if only and only not in name: continue
        def shot(t):
            pg.evaluate(SEEK, [i, t]); return Image.open(io.BytesIO(el.screenshot())).convert('RGB')
        last = total if not info['loops'] else total * 7 / 8
        fr = [shot(min(total * k / 7, last) if not info['loops'] else total * k / 8 + 1) for k in range(8)]
        w, h = fr[0].size; sheet = Image.new('RGB', (w * 4, h * 2), 'white')
        for k, im in enumerate(fr): sheet.paste(im, ((k % 4) * w, (k // 4) * h))
        sheet.thumbnail((2000, 1400)); sheet.save(f'{outdir}/{name}_sheet.png')
        print(name, 'loops' if info['loops'] else 'once', round(total), 'ms,', info['count'], 'animations')
        if want_gif:
            n = max(2, int(round(total / 1000 * fps)))
            hgt = round(width * h / w)
            if info['loops']:
                # start the loop at the held payoff so frame 1 (what PowerPoint's editor, thumbnails and previews show) is the finished icon
                frames = [shot((phase * total + total * k / n) % total).resize((width, hgt), Image.LANCZOS) for k in range(n)]
                dur = [int(1000 / fps)] * n; dur[0] = int(rest * 1000)      # rest on the finished icon before each play
                kw = dict(save_all=True, append_images=frames[1:], duration=dur, optimize=False)
                if loops == 0: kw['loop'] = 0
                elif loops > 1: kw['loop'] = loops - 1
            else:
                # play-once: open on the finished frame for `lead` seconds, then build, then hold
                final = shot(total).resize((width, hgt), Image.LANCZOS)
                frames = [final] + [shot(total * k / n).resize((width, hgt), Image.LANCZOS) for k in range(n + 1)]
                dur = [int(lead * 1000)] + [int(1000 / fps)] * (n + 1); dur[-1] = int(hold * 1000)
                kw = dict(save_all=True, append_images=frames[1:], duration=dur, optimize=False)
            css_bg = pg.evaluate("(i)=>getComputedStyle(document.querySelectorAll('%s')[i]).backgroundColor" % SEL, i)
            m = __import__('re').findall(r'\d+', css_bg)[:3]; bg = tuple(int(v) for v in m) if len(m) == 3 else None
            frames = shared_palette(frames, bg=bg); kw['append_images'] = frames[1:]; kw['optimize'] = True; kw['disposal'] = 1
            frames[0].save(f'{outdir}/{name}.gif', **kw)
            if bg: fix_gif_background(f'{outdir}/{name}.gif', bg)
            pg.evaluate("(i)=>document.querySelectorAll('%s')[i].classList.add('static')" % SEL, i)
            Image.open(io.BytesIO(el.screenshot())).convert('RGB').resize((width, hgt), Image.LANCZOS).save(f'{outdir}/{name}_static.png')
            pg.evaluate("(i)=>document.querySelectorAll('%s')[i].classList.remove('static')" % SEL, i)
            print('   gif', os.path.getsize(f'{outdir}/{name}.gif') // 1024, 'KB,', len(frames), 'frames')
    print('errors', errs)
    b.close()
