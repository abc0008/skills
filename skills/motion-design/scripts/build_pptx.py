"""python3 build_pptx.py page.html gifdir out.pptx  -> one slide per .card / .wide block, GIF placed as a picture."""
import sys, re
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from PIL import Image
page, gifdir, out = sys.argv[1:4]
html = open(page).read()
blocks = re.findall(r'<div class="(card|wide)">(.*?)</(?:svg|table)>', html, re.S)
prs = Presentation(); prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
ink = RGBColor(0x19,0x19,0x19); mute = RGBColor(0x5f,0x59,0x4c)
for kind, b in blocks:
    k = re.search(r'<p class="k">(.*?)</p>', b, re.S); h = re.search(r'<h2>(.*?)</h2>', b, re.S); d = re.search(r'<p class="d">(.*?)</p>', b, re.S)
    name = re.search(r'data-name="(.*?)"', b).group(1)
    s = prs.slides.add_slide(prs.slide_layouts[6]); s.background.fill.solid(); s.background.fill.fore_color.rgb = RGBColor(0xF4,0xEF,0xE4)
    w0, h0 = Image.open(f'{gifdir}/{name}.gif').size
    wide = kind == 'wide' or w0 > h0 * 1.3
    tb = s.shapes.add_textbox(Inches(.8), Inches(.7 if wide else 1.1), Inches(11.5 if wide else 6.6), Inches(2 if wide else 5)); tf = tb.text_frame; tf.word_wrap = True
    items = ([(k.group(1).upper(), 14, True, mute)] if k else []) + [(h.group(1), 34 if wide else 40, True, ink)] + ([(d.group(1), 18 if wide else 20, False, mute)] if d else [])
    for i, (txt, sz, bold, col) in enumerate(items):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); r = para.add_run(); r.text = re.sub(r'&quot;', '"', txt)
        r.font.size = Pt(sz); r.font.bold = bold; r.font.color.rgb = col; r.font.name = 'Helvetica Neue'; para.space_after = Pt(10)
    g = f'{gifdir}/{name}.gif'; w, hgt = Image.open(g).size
    if wide:
        ph = 4.4; pw = ph * w / hgt; s.shapes.add_picture(g, Inches((13.333 - pw) / 2), Inches(2.8), Inches(pw), Inches(ph))
    else:
        s.shapes.add_picture(g, Inches(7.9), Inches(1.25), Inches(5), Inches(5))
prs.save(out); print(len(prs.slides), 'slides ->', out)
