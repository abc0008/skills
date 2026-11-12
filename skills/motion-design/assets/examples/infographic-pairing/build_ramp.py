"""Worked example: builds ramp-5-lessons-infographic.html from the doc-to-infographic template
plus five motion-design explainer icons (Lucide objects).

  python3 build_ramp.py [output.html]

Needs lucide-static (see scripts/lucide.py) and the doc-to-infographic skill alongside this one.
"""
import sys, re, os
_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_here, '..', '..', '..', 'scripts'))
from lucide import lu, inner

T = os.environ.get('INFOGRAPHIC_TEMPLATE') or os.path.join(_here, '..', '..', '..', '..', 'doc-to-infographic', 'assets', 'template.html')
tpl = open(T).read()
head, rest = tpl.split('<div class="wrap">', 1)
_, script = rest.split('\n</div>\n\n<script>', 1)
script = '<script>' + script
head = head[:head.index('<!-- ===== ICON SPRITE')]            # sprite not needed: icons are Lucide, inlined

# ---------- rebrand the template to the editorial palette ----------
for a, b in [('--ink:#16202e;', '--ink:#191919;'), ('--muted:#5a6b7e;', '--muted:#5f594c;'), ('--faint:#8a98a8;', '--faint:#8d8676;'),
             ('--line:#e4e9f0;', '--line:#d9d2c2;'), ('--bg:#ffffff;', '--bg:#f4efe4;'), ('--panel:#f6f8fb;', '--panel:#ebe5d6;'),
             ('--accent:#1f4e79;', '--accent:#191919;'), ('--accent-soft:#e9f0f8;', '--accent-soft:#ebe5d6;'),
             ('--cat-imo:#9a5b2a;', '--cat-imo:#191919;'), ('--maxw:980px;', '--maxw:1000px;'),
             ('background:rgba(255,255,255,.92);', 'background:rgba(244,239,228,.94);'), ('border:1px solid #d4e2f0;', 'border:1px solid var(--line);'),
             ('<title>REPLACE — page title</title>', '<title>5 lessons from putting AI to work with enterprise finance teams</title>')]:
    assert a in head, a
    head = head.replace(a, b)

CSS = r'''
  /* ============ motion-design base (explainer icons) ============ */
  :root{--paper:var(--bg);--mute:#c9c2b2;--mute-text:#8d8676;--hl:#ffd60a;--mark:#e5381c;
    --io:cubic-bezier(.645,.045,.355,1);--out:cubic-bezier(.165,.84,.44,1);--snap:cubic-bezier(.19,1,.22,1)}
  .mo{display:block;background:var(--paper);color:var(--ink);font-family:var(--font)}
  svg.mo{width:100%;height:auto;overflow:visible}
  .mo text{font-family:var(--font);fill:currentColor}
  .mo .ln{fill:none;stroke:currentColor;stroke-width:3;stroke-linecap:round;stroke-linejoin:round}
  .mo .pen{fill:none;stroke:var(--mark);stroke-width:3.5;stroke-linecap:round;stroke-linejoin:round}
  .xicon{--loop:5.5s}
  .xicon *{transform-box:view-box;transform-origin:0 0}
  .xicon .draw{stroke-dasharray:1;stroke-dashoffset:0;transition:none}
  .xicon .a-all{animation-name:x-all}
  @keyframes x-all{0%{opacity:0}4%,95%{opacity:1}100%{opacity:0}}
  .xicon .glyph{fill:var(--mark);font:800 26px/1 var(--font);transform-box:fill-box;transform-origin:50% 60%;text-anchor:middle}
  .xicon .c{transform-box:fill-box;transform-origin:50% 50%}
  .xicon [class*="a-"]{animation-duration:var(--loop);animation-iteration-count:infinite;animation-timing-function:linear;animation-fill-mode:both}
  .reveal:not(.in) .xicon [class*="a-"]{animation-play-state:paused}       /* icons wait until scrolled into view */
  .mo.static [class*="a-"]{animation:none!important}
  @media print,(prefers-reduced-motion:reduce){.mo [class*="a-"]{animation:none!important}}
  .xicon .lu{fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
  .xicon .plate{fill:var(--hl)}
  .xicon .off{color:var(--mute-text)}
  .xicon .hl{fill:var(--hl)}
  .xicon .lbl{font:800 8.5px/1 var(--font);letter-spacing:.05em;text-anchor:middle;fill:currentColor}
  .xicon .chip rect{fill:var(--mark)}.xicon .chip text{fill:var(--paper);font:800 9.5px/1 var(--font);text-anchor:middle}
  .xicon .chipo rect{fill:var(--paper);stroke:currentColor;stroke-width:2.5}.xicon .chipo text{fill:currentColor;font:800 9.5px/1 var(--font);text-anchor:middle}
  .xicon .box{fill:var(--paper);stroke:currentColor;stroke-width:2.5}
  .xicon .ck{stroke:var(--ink);stroke-width:3.5;stroke-linecap:round;stroke-linejoin:round;fill:none}

  /* ---- 1. the question: invoice = PO, but not the contract ---- */
  .q1 .eq{fill:var(--ink)}
  .q1 .a-eq{animation-name:q1-eq}.q1 .a-ct{animation-name:q1-ct}.q1 .a-pl{animation-name:q1-pl}.q1 .a-ne{animation-name:q1-ne}.q1 .a-inv{animation-name:q1-inv}.q1 .a-cl{animation-name:q1-cl}
  @keyframes q1-eq{0%,10%{opacity:0;transform:scale(.6);animation-timing-function:var(--out)}17%,100%{opacity:1;transform:scale(1)}}
  @keyframes q1-ct{0%,32%{opacity:0;transform:translate(0,-18px);animation-timing-function:var(--snap)}44%,100%{opacity:1;transform:translate(0,0)}}
  @keyframes q1-cl{0%,38%{opacity:0}46%,100%{opacity:1}}
  @keyframes q1-pl{0%,46%{opacity:0;transform:scale(.6);animation-timing-function:var(--snap)}53%,100%{opacity:1;transform:scale(1)}}
  @keyframes q1-ne{0%,58%{opacity:0;transform:scale(.6);animation-timing-function:var(--out)}65%,100%{opacity:1;transform:scale(1)}}
  @keyframes q1-inv{0%,60%{color:var(--ink)}68%,100%{color:var(--mark)}}

  /* ---- 2. definitions: three workbooks, one rule set, one CAC ---- */
  .d2 .v{opacity:0}.d2 .v rect{fill:var(--paper);stroke:var(--mark);stroke-width:2}.d2 .v text{fill:var(--mark);font:800 8.5px/1 var(--font);text-anchor:middle}
  .d2 .hlr{transform-box:fill-box;transform-origin:0 50%}
  .d2 .out{transform:translate(60px,102px)}
  .d2 .a-v1{animation-name:d2-v1}.d2 .a-v2{animation-name:d2-v2}.d2 .a-v3{animation-name:d2-v3}.d2 .a-bx{animation-name:d2-bx}.d2 .a-o{animation-name:d2-o}.d2 .a-hl{animation-name:d2-hl}.d2 .a-ck{animation-name:d2-ck}
  @keyframes d2-v1{0%,6%{transform:translate(24px,46px) rotate(-9deg);opacity:0}10%,16%{transform:translate(24px,46px) rotate(-9deg);opacity:1;animation-timing-function:var(--io)}28%{transform:translate(60px,70px) rotate(0deg);opacity:1}31%,100%{transform:translate(60px,70px);opacity:0}}
  @keyframes d2-v2{0%,6%{transform:translate(60px,46px) rotate(6deg);opacity:0}10%,24%{transform:translate(60px,46px) rotate(6deg);opacity:1;animation-timing-function:var(--io)}36%{transform:translate(60px,70px) rotate(0deg);opacity:1}39%,100%{transform:translate(60px,70px);opacity:0}}
  @keyframes d2-v3{0%,6%{transform:translate(96px,46px) rotate(-5deg);opacity:0}10%,32%{transform:translate(96px,46px) rotate(-5deg);opacity:1;animation-timing-function:var(--io)}44%{transform:translate(60px,70px) rotate(0deg);opacity:1}47%,100%{transform:translate(60px,70px);opacity:0}}
  @keyframes d2-bx{0%,44%{transform:scale(1)}50%{transform:scale(1.12)}56%,100%{transform:scale(1)}}
  @keyframes d2-o{0%,54%{transform:translate(60px,74px);opacity:0}57%{transform:translate(60px,74px);opacity:1;animation-timing-function:var(--snap)}68%,100%{transform:translate(60px,102px);opacity:1}}
  @keyframes d2-hl{0%,68%{transform:scaleX(0);animation-timing-function:var(--io)}76%,100%{transform:scaleX(1)}}
  @keyframes d2-ck{0%,76%{stroke-dashoffset:1;visibility:hidden}77%{stroke-dashoffset:1;visibility:visible;animation-timing-function:var(--io)}84%,100%{stroke-dashoffset:0;visibility:visible}}

  /* ---- 3. evidence: the rejected option shows its reason; a person approves ---- */
  .e3 .a-top{animation-name:e3-top}.e3 .a-x{animation-name:e3-x}.e3 .a-rs{animation-name:e3-rs}.e3 .a-pl{animation-name:e3-pl}.e3 .a-ln{animation-name:e3-ln}.e3 .a-us{animation-name:e3-us}.e3 .a-st{animation-name:e3-st}
  .e3 .rsn{transform:translate(78px,30px)}
  @keyframes e3-top{0%,16%{color:var(--ink)}24%,100%{color:var(--mute-text)}}
  @keyframes e3-x{0%,16%{stroke-dashoffset:1;visibility:hidden}17%{stroke-dashoffset:1;visibility:visible}24%,100%{stroke-dashoffset:0;visibility:visible}}
  @keyframes e3-rs{0%,28%{transform:translate(40px,30px);opacity:0}31%{transform:translate(40px,30px);opacity:1;animation-timing-function:var(--snap)}42%,100%{transform:translate(78px,30px);opacity:1}}
  @keyframes e3-pl{0%,46%{opacity:0;transform:scale(.6);animation-timing-function:var(--snap)}53%,100%{opacity:1;transform:scale(1)}}
  @keyframes e3-ln{0%,54%{stroke-dashoffset:1;visibility:hidden}55%{stroke-dashoffset:1;visibility:visible;animation-timing-function:var(--io)}63%,100%{stroke-dashoffset:0;visibility:visible}}
  @keyframes e3-us{0%,60%{opacity:0;transform:scale(.6);animation-timing-function:var(--snap)}67%,100%{opacity:1;transform:scale(1)}}
  @keyframes e3-st{0%,70%{opacity:0;transform:translate(34px,-24px) scale(1.6);animation-timing-function:var(--snap)}80%,100%{opacity:1;transform:translate(0,0) scale(1)}}

  /* ---- 4. work left behind: the pile for the accountant ---- */
  .w4 .row{stroke-width:4}
  .w4 .a-r1{animation-name:w4-r1}.w4 .a-r2{animation-name:w4-r2}.w4 .a-r3{animation-name:w4-r3}.w4 .a-r4{animation-name:w4-r4}.w4 .a-r5{animation-name:w4-r5}.w4 .a-r6{animation-name:w4-r6}
  .w4 .a-keep{animation-name:w4-keep}.w4 .a-clip{animation-name:w4-clip}.w4 .a-bot{animation-name:w4-bot}
  .w4 .gone{opacity:0}
  @keyframes w4-bot{0%,8%{transform:scale(1)}11%{transform:scale(1.12)}14%,16%{transform:scale(1)}19%{transform:scale(1.12)}22%,24%{transform:scale(1)}27%{transform:scale(1.12)}30%,32%{transform:scale(1)}35%{transform:scale(1.12)}38%,100%{transform:scale(1)}}
  @keyframes w4-r1{0%,8%{opacity:0;transform:translate(-34px,-30px);stroke:var(--ink)}14%,40%{opacity:1;transform:translate(0,0);stroke:var(--ink)}46%,62%{stroke:var(--mark)}70%,100%{opacity:1;transform:translate(0,0);stroke:var(--ink)}}
  @keyframes w4-r2{0%,13%{opacity:0;transform:translate(-34px,-24px);stroke:var(--ink)}19%,40%{opacity:1;transform:translate(0,0);stroke:var(--ink)}46%,62%{stroke:var(--mark)}70%,100%{opacity:1;transform:translate(0,0);stroke:var(--ink)}}
  @keyframes w4-r3{0%,18%{opacity:0;transform:translate(-34px,-18px);stroke:var(--ink)}24%,40%{opacity:1;transform:translate(0,0);stroke:var(--ink)}46%,62%{opacity:1;stroke:var(--mark);transform:translate(0,0)}72%,100%{opacity:0;stroke:var(--mark);transform:translate(0,14px)}}
  @keyframes w4-r4{0%,23%{opacity:0;transform:translate(-34px,-12px);stroke:var(--ink)}29%,40%{opacity:1;transform:translate(0,0);stroke:var(--ink)}46%,62%{opacity:1;stroke:var(--mark);transform:translate(0,0)}72%,100%{opacity:0;stroke:var(--mark);transform:translate(0,20px)}}
  @keyframes w4-r5{0%,28%{opacity:0;transform:translate(-34px,-6px);stroke:var(--ink)}34%,40%{opacity:1;transform:translate(0,0);stroke:var(--ink)}46%,62%{opacity:1;stroke:var(--mark);transform:translate(0,0)}72%,100%{opacity:0;stroke:var(--mark);transform:translate(0,26px)}}
  @keyframes w4-r6{0%,33%{opacity:0;transform:translate(-34px,0);stroke:var(--mark)}39%,62%{opacity:1;transform:translate(0,0);stroke:var(--mark)}72%,100%{opacity:0;stroke:var(--mark);transform:translate(0,32px)}}
  @keyframes w4-clip{0%,52%{opacity:0;transform:scale(1.8);animation-timing-function:var(--snap)}60%,100%{opacity:1;transform:scale(1)}}

  /* ---- 5. rule change: the right case changes, the others do not ---- */
  .r5 .xm{stroke:var(--mark);stroke-width:3.5;stroke-linecap:round;fill:none;opacity:0}
  .r5 .v1{opacity:0}
  .r5 .sweep{stroke:var(--mark);stroke-width:2;stroke-dasharray:.1 5;stroke-linecap:round;opacity:0}
  .r5 .a-v1{animation-name:r5-v1}.r5 .a-v2{animation-name:r5-v2}.r5 .a-rb{animation-name:r5-rb}.r5 .a-sw{animation-name:r5-sw}.r5 .a-x{animation-name:r5-x}.r5 .a-k{animation-name:r5-k}.r5 .a-pl{animation-name:r5-pl}.r5 .a-kb{animation-name:r5-kb}.r5 .a-kc{animation-name:r5-kc}
  @keyframes r5-v1{0%,22%{opacity:1}28%,100%{opacity:0}}
  @keyframes r5-v2{0%,22%{opacity:0}28%,100%{opacity:1}}
  @keyframes r5-rb{0%,22%{transform:scale(1)}27%{transform:scale(1.14)}32%,100%{transform:scale(1)}}
  @keyframes r5-sw{0%,36%{opacity:0;transform:translateY(0)}38%{opacity:1;transform:translateY(0)}64%{opacity:1;transform:translateY(64px)}68%,100%{opacity:0;transform:translateY(64px)}}
  @keyframes r5-x{0%,4%{opacity:0}8%,44%{opacity:1}48%,100%{opacity:0}}
  @keyframes r5-k{0%,47%{stroke-dashoffset:1;visibility:hidden}48%{stroke-dashoffset:1;visibility:visible}55%,100%{stroke-dashoffset:0;visibility:visible}}
  @keyframes r5-pl{0%,54%{opacity:0;transform:scale(.6);animation-timing-function:var(--snap)}61%,100%{opacity:1;transform:scale(1)}}
  @keyframes r5-kb{0%,52%{transform:scale(1)}56%{transform:scale(1.25)}60%,100%{transform:scale(1)}}
  @keyframes r5-kc{0%,60%{transform:scale(1)}64%{transform:scale(1.25)}68%,100%{transform:scale(1)}}

  /* ============ page-level additions ============ */
  h1{font-weight:800;letter-spacing:-.02em;font-size:38px;line-height:1.1}
  .takeaway{font-weight:800;letter-spacing:-.015em;font-size:25px;line-height:1.15}
  .eyebrow{color:var(--mute-text)}
  .lesson{display:grid;grid-template-columns:200px 1fr;gap:30px;align-items:center;margin-bottom:18px}
  .lesson .icw{width:200px}
  .lesson .lead{margin:6px 0 0}
  .ichip.ai{background:var(--ink);color:var(--bg)} .ichip.hu{background:var(--hl);color:var(--ink)}
  .ichip.doc{background:var(--panel);color:var(--ink)} .ichip.old{background:transparent;color:var(--faint);border:1px dashed var(--faint)}
  .rnode{background:var(--bg);font-size:13px;padding:6px 10px}
  .redge{flex:0 1 84px}
  .rel.tight .redge{flex:0 1 54px;min-width:44px}
  [data-branch].decided .br-off{opacity:.62;filter:none}
  .rnode.old{color:var(--faint);box-shadow:none;border-style:dashed}
  .rnode.flag{border-color:var(--mark);color:var(--mark)}
  .rnode.hu{border-color:var(--ink);background:#fff7cf}
  .redge.miss::before{color:var(--mark)} .redge.miss .shaft{background:var(--mark)} .redge.miss .shaft::after{border-left-color:var(--mark)}
  .rows{display:grid;gap:14px}
  .rowlab{font-size:11.5px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--faint);margin:0 0 6px}
  .fork{display:grid;grid-template-columns:auto 1fr;gap:10px 8px;align-items:center}
  table.cmp{border-collapse:collapse;width:100%;font-size:14.5px}
  table.cmp th{font-size:11.5px;text-transform:uppercase;letter-spacing:.06em;text-align:left;color:var(--faint);padding:8px 14px;border-bottom:3px solid var(--ink)}
  table.cmp td{padding:11px 14px;border-bottom:1px solid var(--line);vertical-align:top}
  table.cmp td:first-child{font-weight:700;white-space:nowrap}
  table.cmp td.old{color:var(--faint)} table.cmp td.new{font-weight:600}
  table.cmp .hu{background:#fff7cf}
  mark.h{background:var(--hl);color:var(--ink);padding:1px 5px}
  @media (max-width:720px){.lesson{grid-template-columns:1fr}.lesson .icw{width:170px}}
</style>
</head>
<body>
<!-- Icons: Lucide (ISC) -->
'''
head = head.replace('</style>\n</head>\n<body>\n', CSS)
assert 'Icons: Lucide' in head

M = 'var(--mark)'
def ic(name):            # small Lucide icon for a chip
    return f'<svg class="ic" viewBox="0 0 24 24">{inner(name)}</svg>'
def rn(icon, text, kind='doc', cls=''):
    return f'<span class="rnode {cls}"><span class="ichip {kind}">{ic(icon)}</span>{text}</span>'
def ed(verb, cls=''):
    return f'<span class="redge {cls}" data-verb="{verb}"><i class="shaft"></i></span>'
def icon(name, cls, label, body):
    return f'<div class="icw reveal"><svg class="mo xicon {cls}" data-name="{name}" viewBox="0 0 120 120" role="img" aria-label="{label}"><g class="a-all">{body}</g></svg></div>'

# ---------------- icons ----------------
i1 = icon('ramp1_question', 'q1', 'An invoice and a purchase order match. Then the contract appears, is highlighted, and a not-equal sign shows the invoice does not match it.',
    f'<g class="a-inv">{lu("receipt-text", 30, 32, 34)}</g>' + lu('file-text', 86, 32, 34)
    + '<text class="glyph eq a-eq" x="58" y="40">=</text>'
    + '<text class="lbl" x="30" y="60">INVOICE</text><text class="lbl" x="86" y="60">PO</text>'
    + '<g style="transform:translate(64px,90px)"><rect class="plate c a-pl" x="-19" y="-19" width="38" height="38" rx="7"/></g>'
    + f'<g class="a-ct">{lu("scroll-text", 64, 90, 32)}</g>'
    + '<text class="lbl a-cl" x="64" y="118">CONTRACT</text>'
    + '<text class="glyph a-ne" x="30" y="98">&#8800;</text>')

sheets = ''.join(lu('file-spreadsheet', x, 20, 26, cls='off') for x in (24, 60, 96))
i2 = icon('ramp2_definitions', 'd2', 'Three workbooks each produce a different version of CAC. The three go into one agreed rule set and a single CAC comes out, highlighted and checked.',
    sheets
    + '<g style="transform:translate(60px,72px)"><g class="c a-bx"><rect class="box" x="-25" y="-9" width="50" height="18" rx="3"/><text class="lbl" y="3.2">RULES</text></g></g>'
    + ''.join(f'<g class="v a-v{k}"><rect x="-13" y="-7.5" width="26" height="15" rx="7.5"/><text y="3">CAC</text></g>' for k in (1, 2, 3))
    + '<rect class="hl hlr a-hl" x="40" y="92" width="40" height="20"/>'
    + '<g class="chipo out a-o"><rect x="-15" y="-9" width="30" height="18" rx="9"/><text y="3.4">CAC</text></g>'
    + '<path class="pen draw a-ck" pathLength="1" d="M88 100l5 5 9-11"/>')

i3 = icon('ramp3_evidence', 'e3', 'Two funding options. The cheaper one is struck out and a reason slides out beside it. The other is highlighted, handed to an approver, and stamped.',
    f'<g class="a-top">{lu("banknote", 24, 30, 32)}</g>'
    + '<path class="pen draw a-x" pathLength="1" d="M10 42L38 18"/>'
    + '<g class="chipo rsn a-rs"><rect x="-23" y="-9" width="46" height="18" rx="9"/><text y="3.4">REASON</text></g>'
    + '<g style="transform:translate(24px,84px)"><rect class="plate c a-pl" x="-20" y="-15" width="40" height="30" rx="6"/></g>'
    + lu('banknote', 24, 84, 32)
    + '<path class="ln draw a-ln" pathLength="1" d="M48 84H72" style="stroke-width:2.5"/>'
    + f'<g style="transform:translate(92px,80px)"><g class="c a-us">{lu("user-round", 0, 0, 30)}<text class="lbl" x="0" y="26">APPROVER</text></g></g>'
    + f'<g style="transform:translate(44px,66px)"><g class="a-st">{lu("stamp", 0, 0, 24, color=M)}</g></g>')

rows = ''.join(f'<path class="ln row {"gone" if k > 2 else ""} a-r{k}" d="M70 {96 - 9 * k}H100"/>' for k in range(1, 7))
i4 = icon('ramp4_work_left', 'w4', 'An agent sends six proposed matches into an accountant\'s tray; the pile turns red. A paperclip of evidence is attached and the pile shrinks to two.',
    f'<g style="transform:translate(22px,30px)"><g class="c a-bot">{lu("bot", 0, 0, 28, color=M)}</g></g>'
    + lu('user-round', 22, 96, 28)
    + lu('inbox', 85, 102, 34)
    + rows
    + f'<g style="transform:translate(108px,74px)"><g class="c a-clip">{lu("paperclip", 0, 0, 20)}</g></g>'
    + '<text class="lbl" x="85" y="24">TO CHECK</text>')

def case(y, letter, extra):
    return (f'<g class="chipo" style="transform:translate(22px,{y}px)"><rect x="-10" y="-9" width="20" height="18" rx="9"/><text y="3.4">{letter}</text></g>'
            + lu('receipt-text', 52, y, 22) + extra)
i5 = icon('ramp5_rule_change', 'r5', 'A rule moves from version one to version two and three clients\' cases are rerun. Client A\'s wrong rejection becomes a pass; clients B and C stay as they were.',
    '<g style="transform:translate(60px,16px)"><g class="c a-rb"><rect class="box" x="-27" y="-9" width="54" height="18" rx="9"/>'
    '<text class="lbl v1 a-v1" y="3.2">RULE V1</text><text class="lbl a-v2" y="3.2">RULE V2</text></g></g>'
    + '<path class="ln sweep a-sw" d="M10 38H110"/>'
    + case(52, 'A', '<g style="transform:translate(88px,52px)"><rect class="plate c a-pl" x="-13" y="-12" width="26" height="24" rx="5"/></g>'
                    '<path class="xm a-x" d="M83 47l10 10M93 47l-10 10"/><path class="ck draw a-k" pathLength="1" d="M82 52l4.5 4.5 8-10"/>')
    + case(76, 'B', '<g style="transform:translate(88px,76px)"><g class="c a-kb"><path class="ck" d="M-6 0l4.5 4.5 8-10"/></g></g>')
    + case(100, 'C', '<g style="transform:translate(88px,100px)"><g class="c a-kc"><path class="ck" d="M-6 0l4.5 4.5 8-10"/></g></g>'))

# ---------------- sections ----------------
def lesson(sid, n, icon_html, takeaway, lead, diagram, notice, more):
    return f'''
  <section id="{sid}">
    <div class="lesson">
      {icon_html}
      <div><p class="eyebrow">Lesson {n}</p><h2 class="takeaway">{takeaway}</h2><p class="lead">{lead}</p></div>
    </div>
    <div class="reveal">{diagram}</div>
    <p class="caption"><strong>What to notice:</strong> {notice}</p>
    <details class="more"><summary>The case behind it</summary><div class="body"><p class="caption" style="margin-top:0">{more}</p></div></details>
  </section>'''

s1 = lesson('s1', 1, i1, 'Start from the business question, not the data that happens to match',
    'A specific question tells the workflow which evidence it needs for the decision.',
    '<div class="rows" data-branch><div class="br-off"><p class="rowlab">The check that passed</p><div class="rel">'
    + rn('receipt-text', 'Invoice', 'old', 'old') + ed('matches', 'seq') + rn('file-text', 'Purchase order', 'old', 'old') + ed('lets through', 'miss') + rn('triangle-alert', 'Outdated rate on both', 'old', 'flag')
    + '</div></div><div class="br-on"><p class="rowlab">The question: are suppliers charging the negotiated price?</p><div class="rel">'
    + rn('receipt-text', 'Each invoice line') + ed('linked to') + rn('scroll-text', 'Contract term') + ed('recalculates') + rn('list-checks', 'Review queue', 'ai')
    + ed('hands to', 'handoff') + rn('user-round', 'Buyer decides', 'hu', 'hu') + '</div></div></div>',
    'the invoice-to-PO match was not wrong, it answered a different question. Tying each line to the contract is what surfaces the discrepancy, and the decision to pursue it stays with the buyer.',
    'A distributor\'s procurement team wanted to know whether suppliers were charging negotiated prices. Invoices matched purchase orders, but an outdated rate could appear on both and pass. The workflow linked each invoice line to its contract terms; the review queue showed a recalculated amount and the supporting term for each possible discrepancy. Buyers checked the flags and prepared questions for suppliers.')

s2 = lesson('s2', 2, i2, 'Give AI the definitions finance has agreed, or it will reproduce the disagreement',
    'Finance work leaves almost no room for error, so the agent needs the team\'s own rules for what counts and how shared costs are split.',
    '<table class="cmp"><thead><tr><th></th><th>Before: each workbook decides</th><th>After: finance decides once</th></tr></thead><tbody>'
    '<tr><td>Shared costs</td><td class="old">Allocated differently in each workbook</td><td class="new hu">One approved split, agreed by finance</td></tr>'
    '<tr><td>Customer identity</td><td class="old">Sales and finance use different identifiers</td><td class="new">Reconciled as part of the agreed rules</td></tr>'
    '<tr><td>The calculation</td><td class="old">Rebuilt by hand; data in separate systems</td><td class="new">Agent applies the approved rules; repeatable and explainable</td></tr>'
    '<tr><td>When a number looks off</td><td class="old">Hard to say which assumption caused it</td><td class="new">Traced to its inputs, corrected, rerun</td></tr>'
    '</tbody></table>',
    'the agent did not invent a definition of customer acquisition cost. Finance agreed one, and the agent\'s job was to apply it the same way every time and show its working.',
    'A software company\'s finance team was comparing customer acquisition cost across products. Workbooks allocated shared costs differently, the data sat in separate systems, and sales and finance used different customer identifiers. Finance agreed which costs belonged in the comparison and how to split shared costs, then gave those rules to the agent. In review, finance traced an unexpected difference to a shared-cost assumption, corrected it and reran the comparison.')

s3 = lesson('s3', 3, i3, 'An approval needs evidence and a named approver. "Be careful" is not a control.',
    'Reviewers need to see which constraints a recommendation meets and why the alternatives were rejected.',
    '<div class="rows" data-branch><div class="br-off"><p class="rowlab">The alternative</p><div class="rel">'
    + rn('banknote', 'Lower-cost funding option', 'old', 'old') + ed('excluded because', 'miss') + rn('file-text', 'Why each asset qualified or failed', 'ai')
    + '</div></div><div class="br-on"><p class="rowlab">The recommendation</p><div class="rel">'
    + rn('calculator', 'Scenarios + remaining capacity', 'ai') + ed('traced by') + rn('search', 'Treasury review', 'hu', 'hu')
    + ed('approves', 'handoff') + rn('stamp', 'Named approver', 'hu', 'hu') + ed('executes', 'handoff') + rn('landmark', 'Authorized staff', 'hu', 'hu')
    + '</div></div></div>',
    'three separate human roles follow the AI step: review, approval and execution. The workflow names who holds each one instead of relying on a cautious prompt.',
    'In a treasury review, the team needed to understand why a lower-cost funding option had been excluded. Analysts had been combining asset data with agreements, eligibility rules and facility limits by hand. The workflow prepared scenarios with reviewed calculations, remaining facility capacity and an explanation of why each asset qualified or failed, so treasury could trace exclusions, check feasible alternatives and route the recommendation for approval.')

s4 = lesson('s4', 4, i4, 'Judge a workflow by the work it leaves behind, not the output it produces',
    'The value is in how much checking, correction and follow-up remains for the team.',
    '<div class="rows"><div><p class="rowlab">What changed in the reconciliation</p><div class="rel">'
    + rn('link-2', 'Entries grouped, evidence attached', 'ai') + ed('separates') + rn('clock', 'Routine timing differences', 'doc')
    + '</div><div class="rel" style="margin-top:10px">' + rn('link-2', 'Same proposed matches', 'ai') + ed('leaves', 'handoff') + rn('inbox', 'Smaller exception queue', 'hu', 'hu') + '</div></div>'
    '<div><p class="rowlab">What still has to be measured</p><div class="rel tight">'
    + rn('search', 'Checking', 'hu') + ed('plus', 'seq') + rn('pencil-line', 'Correcting', 'hu') + ed('plus', 'seq') + rn('send', 'Follow-up', 'hu') + ed('plus', 'seq') + rn('cpu', 'Cost to run', 'ai')
    + ed('equals') + rn('scale', 'True cost', 'doc') + '</div></div></div>',
    'matching on amounts alone produced plenty of output and sent accountants back into the records, including for cases they had already closed. The improvement was a shorter, better-supported queue. The article reports no time-saved figure; the team says that measurement is still to do.',
    'In bank reconciliation for a multi-entity services business, too many proposed matches needed rechecking. Amount-only matching missed timing differences and payments that covered several entries. The team grouped related ledger entries, attached supporting evidence, and separated routine timing differences from unexplained discrepancies, so accepted matches could be traced to source records. Testing with accountants showed which steps still required investigation.')

s5 = lesson('s5', 5, i5, 'Test a rule change on the cases it should move and the ones it should leave alone',
    'A fix is only safe when the right decisions change and unrelated ones stay the same.',
    '<div class="rows"><div><p class="rowlab">Should change</p><div class="rel">'
    + rn('git-branch', 'Updated allowance: one client, one date', 'ai') + ed('applies to') + rn('receipt-text', 'Eligible requests') + ed('rerun', 'seq') + rn('check', 'Decision changes', 'hu', 'hu')
    + '</div></div><div><p class="rowlab">Should not change</p><div class="rel">'
    + rn('history', 'Other clients\' policies', 'doc') + ed('still govern') + rn('receipt-text', 'Their requests') + ed('rerun', 'seq') + rn('equal', 'Decision unchanged', 'doc')
    + '</div></div></div>',
    'the rerun checks both rows. Versioned rules, with each recommendation linked to its policy evidence, are what make it possible to change one client\'s allowance without touching anyone else\'s.',
    'A services company handled expenses and supplier invoices under client-specific policies, amendments and exceptions. A reviewer caught an expense rejection based on an outdated allowance that applied to one client and one effective date. The team had converted approved guidance into versioned rules, so the rejection could be traced to its source and the right version updated. They then reran previously reviewed cases: the amendment applied to eligible requests and other clients stayed under their own policies.')

matrix = '''
  <section id="who">
    <p class="eyebrow">Across all five</p>
    <h2 class="takeaway">In every case the AI prepares the evidence and a person keeps the decision</h2>
    <p class="lead">Read across: the same division of labour shows up in procurement, FP&amp;A, treasury, accounting and expense policy.</p>
    <div class="reveal scroller"><table class="cmp"><thead><tr><th>Lesson</th><th>Team</th><th>What the workflow prepares</th><th>What a person still decides</th></tr></thead><tbody>
      <tr><td>1. The question</td><td>Procurement</td><td>A recalculated amount and the supporting contract term for each flag</td><td class="hu">Whether a charge warrants recovery</td></tr>
      <tr><td>2. Definitions</td><td>Finance</td><td>A repeatable calculation, traceable to its inputs</td><td class="hu">Which costs count and how shared costs are split</td></tr>
      <tr><td>3. Evidence</td><td>Treasury</td><td>Scenarios, remaining capacity, and why each asset qualified or failed</td><td class="hu">Approval, then execution by authorized staff</td></tr>
      <tr><td>4. Work left</td><td>Accounting</td><td>Grouped entries with evidence; a smaller exception queue</td><td class="hu">Investigating the unexplained discrepancies</td></tr>
      <tr><td>5. Rule changes</td><td>Expense policy</td><td>Recommendations linked to versioned policy; a rerun of past cases</td><td class="hu">Catching the outdated allowance and approving the guidance</td></tr>
    </tbody></table></div>
    <div class="legend"><span><span class="dot" style="background:var(--ink)"></span>Prepared by the AI workflow</span><span><span class="dot" style="background:var(--hl)"></span>Decided or done by a person</span><span><span class="dot" style="background:var(--mark)"></span>The gap or failure the lesson is about</span></div>
    <p class="caption"><strong>What to notice:</strong> none of the five workflows makes the final call. Each one is built to shorten the path to a human decision and to make that decision checkable.</p>
  </section>'''

body = f'''<div class="wrap">
  <header class="doc">
    <p class="eyebrow">Applied AI in finance &middot; visual summary</p>
    <h1>5 lessons from putting AI to work with enterprise finance teams</h1>
    <p class="dek">What separates a finance AI workflow that gets used from one that creates more checking, drawn from Ramp's first months of client engagements.</p>
    <div class="meta"><span>Source: Ori Daniel, Head of Applied AI Solutions, Ramp</span><span>Published October 26, 2026</span></div>
  </header>

  <nav class="toc" aria-label="Sections">
    <a href="#summary" class="active">Summary</a><a href="#s1">1 Question</a><a href="#s2">2 Definitions</a><a href="#s3">3 Evidence</a><a href="#s4">4 Work left</a><a href="#s5">5 Rule changes</a><a href="#who">Who decides</a>
  </nav>

  <section id="summary">
    <div class="summary reveal">
      <h2>The bottom line</h2>
      <p>The workflows that held up were built around a <mark class="h">specific question</mark>, used <mark class="h">definitions finance had already agreed</mark>, showed <mark class="h">evidence a reviewer could check</mark>, were judged by the <mark class="h">work they left for the team</mark>, and were <mark class="h">tested when rules changed</mark>. In all five, the AI prepares the case and a named person makes the decision. The article offers these as directional guidance and reports no time-saved or ROI figures.</p>
    </div>
  </section>
{s1}{s2}{s3}{s4}{s5}{matrix}

  <footer style="margin-top:56px;padding-top:18px;border-top:1px solid var(--line);font-size:12.5px;color:var(--faint)">
    Generated from "5 Lessons From Putting AI to Work With Enterprise Finance Teams" (Ramp, October 26, 2026). Wording is paraphrased; no figures are shown because the source gives none beyond the five lessons. Icons: Lucide (ISC).
  </footer>
</div>

'''
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(_here, 'ramp-5-lessons-infographic.html')
open(out, 'w').write(head + body + script)
print('written', len(head + body + script) // 1024, 'KB')
