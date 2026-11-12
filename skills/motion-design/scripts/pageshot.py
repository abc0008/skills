import sys
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1100,'height':900}); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e))); pg.goto('file://'+sys.argv[1])
    h=pg.evaluate('document.body.scrollHeight')
    for y in range(0,h,500): pg.evaluate(f'scrollTo(0,{y})'); pg.wait_for_timeout(120)
    pg.evaluate("document.querySelectorAll('.xicon').forEach(e=>e.classList.add('static'))"); pg.wait_for_timeout(1500)
    pg.evaluate('scrollTo(0,0)'); pg.screenshot(path=sys.argv[2],full_page=True)
    print('height',h,'errors',errs,'hidden reveals',pg.evaluate("[...document.querySelectorAll('.reveal')].filter(e=>getComputedStyle(e).opacity<0.99).length")); b.close()
