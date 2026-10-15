#!/usr/bin/env python3
"""capture.py — a brand kit from a live URL: what the promo is built from.
  capture.py <url> <out_dir> [--lang en-US] [--scheme dark|light]
→ out_dir/brand.json (name, title, description, headings, CTAs, nav, colours by role, fonts, logo candidates)
  out_dir/shots/desktop_hero@2x.png, desktop_full@2x.png (1440 wide), mobile_hero@3x.png, mobile_full@3x.png (390 wide),
  out_dir/shots/logo_*.png|svg, og.png. Real pixels only — nothing generated.
Needs playwright (optional): pip install playwright && python -m playwright install chromium"""
import json, os, re, sys, urllib.request, urllib.parse

JS_KIT = r"""
() => {
  const cs = (el) => el ? getComputedStyle(el) : null;
  const txt = (el) => (el && el.innerText || '').replace(/\s+/g, ' ').trim();
  const vis = (el) => { const r = el.getBoundingClientRect(); const s = cs(el);
    return r.width > 2 && r.height > 2 && s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity > 0.05; };
  const all = (sel) => [...document.querySelectorAll(sel)].filter(vis);
  const rgb = (c) => { const m = (c || '').match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const p = m[1].split(',').map(x => parseFloat(x)); if (p.length > 3 && p[3] < 0.5) return null;
    return '#' + p.slice(0, 3).map(v => Math.round(v).toString(16).padStart(2, '0')).join(''); };
  const tally = {}; const add = (c, w, role) => { if (!c) return; const k = role + '|' + c; tally[k] = (tally[k] || 0) + w; };
  for (const el of all('body, body *')) {
    const s = cs(el); const r = el.getBoundingClientRect(); const area = Math.min(r.width * r.height, 2e6);
    add(rgb(s.backgroundColor), area, 'bg');
    if (el.childNodes.length && [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()))
      add(rgb(s.color), txt(el).length, 'text');
  }
  for (const el of all('a, button, [role=button], .btn, [class*=button], [class*=cta]')) {
    const s = cs(el); add(rgb(s.backgroundColor), 4000, 'accent'); add(rgb(s.color), 200, 'link');
    add(rgb(s.borderColor), 300, 'accent');
  }
  const ranked = (role) => Object.entries(tally).filter(([k]) => k.startsWith(role + '|'))
    .sort((a, b) => b[1] - a[1]).slice(0, 6).map(([k, v]) => ({ hex: k.split('|')[1], weight: Math.round(v) }));
  const font = (el) => el ? cs(el).fontFamily : null;
  const h1 = all('h1')[0];
  const logos = [];
  for (const el of all('header img, nav img, a[href="/"] img, [class*=logo] img, img[alt*=logo i], img[src*=logo i], header svg, [class*=logo] svg, a[href="/"] svg')) {
    const r = el.getBoundingClientRect(); if (r.top > 260) continue;
    logos.push({ tag: el.tagName.toLowerCase(), src: el.currentSrc || el.src || null, alt: el.alt || null,
                 box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
                 svg: el.tagName.toLowerCase() === 'svg' ? el.outerHTML.slice(0, 60000) : null });
  }
  const meta = (n) => { const m = document.querySelector(`meta[name="${n}"], meta[property="${n}"]`); return m ? m.content : null; };
  return {
    title: document.title, description: meta('description') || meta('og:description'), og_image: meta('og:image'),
    site_name: meta('og:site_name'), theme_color: meta('theme-color'),
    h1: txt(h1), headings: all('h1, h2, h3').slice(0, 24).map(e => ({ tag: e.tagName.toLowerCase(), text: txt(e).slice(0, 160) })),
    ctas: [...new Set(all('a, button').map(txt).filter(t => t && t.length < 40))].slice(0, 30),
    nav: [...new Set(all('nav a, header a').map(txt).filter(t => t && t.length < 30))].slice(0, 16),
    paragraphs: all('p').map(txt).filter(t => t.length > 40).slice(0, 14).map(t => t.slice(0, 300)),
    colors: { background: ranked('bg'), text: ranked('text'), accent: ranked('accent'), link: ranked('link') },
    fonts: { heading: font(h1 || all('h2')[0]), body: font(all('p')[0] || document.body) },
    favicons: [...document.querySelectorAll('link[rel*=icon]')].map(l => l.href),
    logos, page_height: document.documentElement.scrollHeight,
  };
}
"""


def settle(page):
    page.wait_for_timeout(1200)
    # trigger lazy content and scroll-in animations, then go back to the top
    h = page.evaluate("document.documentElement.scrollHeight")
    for y in range(0, min(h, 24000), 700):
        page.evaluate(f"window.scrollTo(0,{y})"); page.wait_for_timeout(120)
    page.evaluate("window.scrollTo(0,0)"); page.wait_for_timeout(900)
    page.add_style_tag(content="*,*::before,*::after{animation-play-state:paused!important;transition:none!important;caret-color:transparent!important}")


def fetch(url, dst):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r, open(dst, "wb") as f:
            f.write(r.read())
        return dst
    except Exception as e:
        return None


def main():
    if len(sys.argv) < 3 or sys.argv[1] in ("-h", "--help"):
        print(__doc__.strip()); sys.exit(0 if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help") else 2)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("capture.py needs playwright: pip install playwright && python -m playwright install chromium")
    url, out = sys.argv[1], sys.argv[2]
    os.makedirs(os.path.join(out, "shots"), exist_ok=True)
    kit = {"url": url}
    with sync_playwright() as p:
        b = p.chromium.launch()
        # the page in the promo's language, not the machine's: a default context gets the machine's locale
        lang = sys.argv[sys.argv.index("--lang") + 1] if "--lang" in sys.argv else "en-US"
        scheme = sys.argv[sys.argv.index("--scheme") + 1] if "--scheme" in sys.argv else "dark"
        loc = dict(locale=lang, timezone_id="UTC", extra_http_headers={"Accept-Language": f"{lang},{lang.split('-')[0]};q=0.9"})
        ctx = b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2, color_scheme=scheme, **loc,
                            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36")
        page = ctx.new_page()
        page.goto(url, wait_until="networkidle", timeout=60000)
        settle(page)
        kit.update(page.evaluate(JS_KIT))
        page.screenshot(path=os.path.join(out, "shots", "desktop_hero@2x.png"))
        page.screenshot(path=os.path.join(out, "shots", "desktop_full@2x.png"), full_page=True)
        for k, lg in enumerate(kit.get("logos", [])[:4]):
            x, y, w, h = lg["box"]
            if w * h > 0:
                page.screenshot(path=os.path.join(out, "shots", f"logo_{k}@2x.png"),
                                clip={"x": max(0, x - 4), "y": max(0, y - 4), "width": w + 8, "height": h + 8}, omit_background=True)
            if lg.get("svg"):
                open(os.path.join(out, "shots", f"logo_{k}.svg"), "w").write(lg["svg"]); lg["svg"] = f"shots/logo_{k}.svg"
        mctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True, has_touch=True, color_scheme=scheme, **loc,
                             user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1")
        mp = mctx.new_page(); mp.goto(url, wait_until="networkidle", timeout=60000); settle(mp)
        mp.screenshot(path=os.path.join(out, "shots", "mobile_hero@3x.png"))
        # a bar pinned to the bottom of the viewport (tab bars, cookie strips) gets baked into a full-page shot at the
        # first screen's height and then scrolls up through the content (YouTube's tab bar did): save it as its
        # own crop, hide it for the full-page shot, and record where it sits so a phone screen can pin it back
        fixed = mp.evaluate("""() => {
          const vh = innerHeight, hits = [];
          for (const el of document.querySelectorAll('body *')) {
            const s = getComputedStyle(el); if (s.position !== 'fixed' && s.position !== 'sticky') continue;
            const r = el.getBoundingClientRect(); if (r.height < 20 || r.width < innerWidth * 0.6) continue;
            if (r.bottom >= vh - 2 && r.top > vh * 0.6) { hits.push([r.top, r.bottom]); el.setAttribute('data-lv-hidden', s.visibility); }
          }
          if (!hits.length) return null;
          return { top: Math.min(...hits.map(h => h[0])), bottom: Math.max(...hits.map(h => h[1])) };
        }""")
        if fixed:
            mp.screenshot(path=os.path.join(out, "shots", "mobile_fixed_bottom@3x.png"),
                          clip={"x": 0, "y": fixed["top"], "width": 390, "height": fixed["bottom"] - fixed["top"]})
            mp.evaluate("() => document.querySelectorAll('[data-lv-hidden]').forEach(el => el.style.setProperty('visibility', 'hidden', 'important'))")
            kit["mobile_fixed_bottom"] = {"top": round(fixed["top"], 1), "height": round(fixed["bottom"] - fixed["top"], 1)}
        mp.screenshot(path=os.path.join(out, "shots", "mobile_full@3x.png"), full_page=True)
        b.close()
    if kit.get("og_image"):
        kit["og_file"] = fetch(urllib.parse.urljoin(url, kit["og_image"]), os.path.join(out, "shots", "og" + (os.path.splitext(urllib.parse.urlparse(kit["og_image"]).path)[1] or ".png")))
    json.dump(kit, open(os.path.join(out, "brand.json"), "w"), indent=1, ensure_ascii=False)
    print(f"{kit.get('title')!r} · h1 {kit.get('h1')!r}")
    print("bg", [c['hex'] for c in kit['colors']['background'][:4]], "text", [c['hex'] for c in kit['colors']['text'][:3]],
          "accent", [c['hex'] for c in kit['colors']['accent'][:4]])
    print("fonts", kit["fonts"], "· logos", len(kit.get("logos", [])), "· page", kit.get("page_height"), "px")


if __name__ == "__main__":
    main()
