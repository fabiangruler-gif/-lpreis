#!/usr/bin/env python3
"""Tägliches Ölpreis-Update: data.json -> post.html -> post.png (1080x1920).
Layout-Basis: 941x1672 CSS-px (Referenzbilder), Ausgabe skaliert auf 1080x1920."""
import json, html, sys, base64, pathlib, shutil, os

ROOT = pathlib.Path(__file__).parent
data = json.loads((ROOT / (sys.argv[1] if len(sys.argv) > 1 else "data.json")).read_text(encoding="utf-8"))
out_name = sys.argv[2] if len(sys.argv) > 2 else "post"
e = lambda s: html.escape(s).replace("\n", "<br>")

def svg(inner, vb="0 0 48 48"):
    return f'<svg viewBox="{vb}" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">{inner}</svg>'

ICONS = {
    "bank": svg('<path d="M6 18 24 8l18 10Z"/><path d="M10 22v14M18 22v14M30 22v14M38 22v14M6 40h36M8 36h32"/>'),
    "ship": svg('<path d="M4 30h40l-6 10H10Z"/><path d="M12 30V20h24v10M20 20v-6h8v6"/><path d="M2 44c4 2 8 2 11 0s8-2 11 0 8 2 11 0 8-2 11 0"/>'),
    "barrel": svg('<ellipse cx="24" cy="10" rx="13" ry="5"/><path d="M11 10v28c0 3 6 5 13 5s13-2 13-5V10"/><path d="M11 20c0 3 6 5 13 5s13-2 13-5M11 30c0 3 6 5 13 5s13-2 13-5"/>'),
    "chart": svg('<path d="M5 40h38"/><path d="M8 32l9-9 7 6 14-16"/><path d="M30 13h8v8"/>'),
    "hand": svg('<path d="M4 26l10-8 8 2 8-4 10 8-6 8-8 4-6-2-6 2z"/><path d="M14 18l-4 12M30 16l8 8"/>'),
    "clock": svg('<circle cx="24" cy="24" r="18"/><path d="M24 12v13l8 5"/>', ),
    "cal": svg('<rect x="6" y="9" width="36" height="32" rx="4"/><path d="M6 19h36M15 5v8M33 5v8"/><path d="M14 27h4M22 27h4M30 27h4M14 34h4M22 34h4"/>'),
    "drop": '<svg viewBox="0 0 40 52"><path fill="url(#gDrop)" d="M20 2C20 2 3 22 3 34a17 17 0 0 0 34 0C37 22 20 2 20 2Z"/><path d="M10 33c0-6 4-12 8-17" stroke="#fff" stroke-opacity=".7" stroke-width="3" fill="none" stroke-linecap="round"/><path d="M14 44a14 14 0 0 0 20-8" stroke="#06607c" stroke-opacity=".55" stroke-width="3" fill="none" stroke-linecap="round"/></svg>',
    "bulb": svg('<path d="M24 5c-8 0-14 6-14 13 0 5 3 8 5 11 1 2 1 4 1 6h16c0-2 0-4 1-6 2-3 5-6 5-11 0-7-6-13-14-13Z"/><path d="M18 40h12M20 45h8M24 0v0M5 12l-3-2M43 12l3-2M3 24H0M45 24h3"/>'),
}

def arrow(kind):
    if kind == "up":
        return '<span class="ar up">▲</span>'
    if kind == "down":
        return '<span class="ar down">▼</span>'
    return '<span class="ar flat">▶</span>'

def price(name, p):
    sign = "up" if p["dir"] == "up" else ("down" if p["dir"] == "down" else "flat")
    return f'''<div class="price">
      <div class="drop">{ICONS["drop"]}</div>
      <div class="pcol"><div class="pname">{name}</div><div class="pval">{e(p["preis"])} $</div></div>
      {arrow(sign)}
      <div class="pdiff {sign}"><div>{e(p["diff"])} $</div><div>{e(p["pct"])} %</div></div>
    </div>'''

def newsitem(n):
    return f'''<div class="news"><div class="nic">{ICONS[n["icon"]]}</div>
      <div><div class="nt">{e(n["titel"])}</div><div class="nx">{e(n["text"])}</div></div></div>'''

def watchitem(i, w):
    return f'''<div class="wrow"><span class="wn">{i}</span><span class="wl"><b>{e(w["titel"])}</b> – {e(w["text"])}</span></div>'''

CSS = r'''
@font-face{font-family:'Poppins';src:url(assets/fonts/Poppins-Bold.ttf);font-weight:100 900}
@font-face{font-family:'Inter';src:url(assets/fonts/Inter-Regular.otf);font-weight:100 450;font-style:normal}
@font-face{font-family:'Inter';src:url(assets/fonts/Inter-Medium.otf);font-weight:451 599;font-style:normal}
@font-face{font-family:'Inter';src:url(assets/fonts/Inter-Bold.otf);font-weight:600 900;font-style:normal}
@font-face{font-family:'Inter';src:url(assets/fonts/Inter-Italic.otf);font-weight:100 900;font-style:italic}
*{box-sizing:border-box;margin:0;padding:0}
:root{--cyan:#2eeaf8;--yellow:#ffd34d;--green:#5cf28f;--red:#ff8480;--txt:#fff;--card:#04182b;--line:rgba(46,234,248,.7);--shadow:#000b15}
html,body{width:941px;height:1672px}
body{font-family:'Inter',sans-serif;color:var(--txt);position:relative;overflow:hidden;
 background:linear-gradient(180deg,#00223d 0%,#001426 50%,#001d36 100%)}
body::before{content:"";position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(25,217,234,.03) 0 1px,transparent 1px 40px),repeating-linear-gradient(90deg,rgba(25,217,234,.03) 0 1px,transparent 1px 40px)}
svg{display:block}
/* Kopf */
.head{position:absolute;left:0;top:0;width:941px;height:236px;overflow:hidden;background:linear-gradient(90deg,#000f1d 0%,#00203a 55%,transparent 100%)}
.head .ph{position:absolute;right:0;top:0;width:470px;height:236px;background:url(data:image/png;base64,%%PHOTO%%) center/cover;
 -webkit-mask-image:linear-gradient(90deg,transparent 0,#000 38%);mask-image:linear-gradient(90deg,transparent 0,#000 38%)}
.head::after{content:"";position:absolute;left:0;right:0;bottom:0;height:3px;background:linear-gradient(90deg,transparent,#14c8e0 20%,#14c8e0 80%,transparent);opacity:.7}
.dropH{position:absolute;left:40px;top:28px;width:28px;height:38px}
.t1{position:absolute;left:92px;top:30px;font:700 34px/1 Poppins;letter-spacing:1px;color:var(--cyan);text-shadow:0 2px 0 #06586b}
.t2{position:absolute;left:30px;top:72px;font:800 55px/1 Poppins;color:#fff;letter-spacing:.5px;text-shadow:0 3px 0 #0b5d7a}
.t3{position:absolute;left:30px;top:146px;font:700 18.5px/1 Poppins;color:var(--cyan);letter-spacing:.5px;white-space:nowrap}
.dt{position:absolute;left:30px;top:184px;display:flex;align-items:center;gap:12px;font:500 18px Inter;color:#fff}
.dt svg{width:36px;height:36px;color:var(--cyan)}
.headline{position:absolute;left:28px;top:246px;width:890px}
.headline h1{font:700 31px/1.15 Poppins;color:#fff}
.headline p{font:500 18.5px/1.25 Inter;color:#d7eef7;margin-top:6px}
/* Karten */
.card{position:absolute;left:17px;width:907px;background:var(--card);border:3px solid var(--cyan);border-radius:16px;box-shadow:0 5px 0 var(--shadow)}
.card h2{position:absolute;left:14px;top:9px;display:flex;align-items:center;gap:13px;font:700 26px Poppins;color:var(--cyan)}
.num{width:42px;height:42px;border-radius:50%;background:var(--cyan);color:#001726;font:700 25px Poppins;display:flex;align-items:center;justify-content:center;box-shadow:0 3px 0 #06607c}
/* 1 */
#c1{top:336px;height:166px}
.prices{position:absolute;left:0;right:0;top:54px;display:flex}
.price{flex:1;display:flex;align-items:center;gap:12px;padding:0 14px 0 26px;height:70px}
.price+.price{border-left:2px solid var(--line)}
.drop{width:40px;height:52px;flex:none}
.pname{font:700 22px Poppins;line-height:1}
.pval{font:800 44px/1.05 Poppins;white-space:nowrap}
.ar{font-size:24px;margin-left:4px}.up{color:var(--green)}.down{color:var(--red)}.flat{color:var(--yellow)}
.pdiff{font:700 21px/1.15 Poppins}
.phint{position:absolute;left:0;right:0;bottom:10px;text-align:center;font:500 15.5px Inter;display:flex;gap:8px;justify-content:center;align-items:center;white-space:nowrap}
.phint svg{width:20px;height:20px;color:var(--cyan)}
/* 2 */
#c2{top:516px;height:286px}
.ngrid{position:absolute;left:0;right:0;top:56px;height:224px;display:grid;grid-template-columns:1fr 1fr;grid-auto-rows:1fr}
.news{display:flex;gap:12px;padding:10px 16px 6px 18px;border-top:1.5px solid var(--line)}
.news:nth-child(even){border-left:1.5px solid var(--line)}.news:nth-child(-n+2){border-top:none}
.nic{width:50px;height:50px;flex:none;padding:9px;border-radius:13px;background:#0a3350;border:2px solid var(--cyan);box-shadow:0 3px 0 var(--shadow);color:#e9fcff}
.nt{font:700 19.5px/1.12 Poppins;color:var(--cyan);margin-bottom:4px}
.nx{font:400 17px/1.24 Inter}
/* 3 */
#c3{top:816px;height:234px}
.pg{position:absolute;left:0;right:0;top:68px;height:160px;display:grid;grid-template-columns:1fr 1fr}
.pc{padding:0 16px 0 22px}.pc+.pc{border-left:2px solid var(--line)}
.ph2{display:flex;align-items:center;gap:10px;font:600 17.5px Poppins;color:var(--cyan);height:40px;margin-bottom:10px;white-space:nowrap}
.ph2 svg{width:38px;height:38px;padding:7px;border-radius:11px;background:#0a3350;border:2px solid var(--cyan);box-shadow:0 3px 0 var(--shadow);color:#e9fcff}
.pill{display:inline-block;margin:0 0 12px 0;padding:2px 18px;border-radius:30px;background:var(--cyan);color:#001726;font:700 19.5px/1.2 Poppins;box-shadow:0 3px 0 #06607c}
.pill.green{background:var(--green);box-shadow:0 3px 0 #0f5f33}.pill.yellow{background:var(--yellow);box-shadow:0 3px 0 #7a5a0c}.pill.red{background:var(--red);box-shadow:0 3px 0 #77201e}
.pt{font:400 17.5px/1.25 Inter}
/* 4 */
#c4{top:1064px;height:196px}
.sg{position:absolute;left:0;right:0;top:68px;height:122px;display:grid;grid-template-columns:1fr 1fr 1fr}
.sc{padding:0 14px 0 18px}.sc+.sc{border-left:2px solid var(--line)}
.srow{display:flex;align-items:center;gap:12px;margin-bottom:12px}
.sic{width:40px;height:40px;border-radius:50%;flex:none;display:flex;align-items:center;justify-content:center;font:700 23px Inter;color:#04202f}
.sic.g{background:var(--green);box-shadow:0 3px 0 #0f5f33}.sic.y{background:var(--yellow);box-shadow:0 3px 0 #7a5a0c}.sic.r{background:var(--red);box-shadow:0 3px 0 #77201e}
.sl{font:700 21px/1 Poppins}.sl.g{color:var(--green)}.sl.y{color:var(--yellow)}.sl.r{color:var(--red)}
.sx{font:400 17px/1.24 Inter}
/* 5 */
#c5{top:1274px;height:192px}
.wl5{position:absolute;left:0;right:0;top:54px;padding:0 22px 0 20px}
.wrow{display:flex;align-items:center;gap:14px;height:33px;font:400 17.5px Inter;white-space:nowrap}
.wn{width:28px;height:28px;border-radius:50%;flex:none;background:var(--cyan);color:#001726;font:700 16px Poppins;display:flex;align-items:center;justify-content:center}
.wl b{font-weight:700;color:#fff}
/* Einschätzung */
.ein{position:absolute;left:17px;top:1480px;width:907px;height:126px;background:#0b1f2c;border:3px solid var(--yellow);border-radius:16px;box-shadow:0 5px 0 var(--shadow);padding:10px 22px 0 18px;display:flex;gap:18px;align-items:flex-start}
.ein .bi{width:54px;height:54px;color:var(--yellow);flex:none;margin-top:6px}
.ein h3{font:700 21px Poppins;color:var(--yellow);letter-spacing:.5px;margin-bottom:3px;text-transform:uppercase}
.ein p{font:600 19.5px/1.25 Inter}
.ein .dis2{position:absolute;left:18px;right:22px;bottom:6px;text-align:center;font:italic 13px Inter;color:#cfe4ee;border-top:1.5px solid rgba(255,211,77,.5);padding-top:4px}
.foot{position:absolute;left:0;top:1612px;width:941px;height:60px;padding:0 72px 0 20px;display:flex;align-items:center;gap:14px}
.foot .fd{width:24px;height:32px;flex:none}
.foot .q{font:400 12.4px/1.35 Inter;flex:1}

/* ===== FLACH: kein Glow, keine Schatten ===== */
.card,.ein,.num,.nic,.ph2 svg,.pill,.sic,.wn{box-shadow:none!important}
.t1,.t2,.t3,.headline h1,.card h2,.ein h3,.pval,.pdiff,.ar,.sl{text-shadow:none!important}
svg,.drop svg,.dropH svg,.fd svg,.nic svg,.ph2 svg,.ein .bi{filter:none!important}
'''
photo = base64.b64encode((ROOT / "assets/header_photo.png").read_bytes()).decode()
n = data["news"]; s = data["szenarien"]; k = data["prognose_kurz"]; m = data["prognose_mittel"]
page = f'''<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><style>
''' + CSS.replace("%%PHOTO%%", photo) + '''</style></head><body>
<svg width="0" height="0" style="position:absolute"><defs><linearGradient id="gDrop" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#a6f6ff"/><stop offset=".5" stop-color="#19d9ea"/><stop offset="1" stop-color="#0a7fa8"/></linearGradient></defs></svg>
'''

body_html = f"""
<div class="head"><div class="ph"></div>
  <div class="dropH">{ICONS["drop"]}</div>
  <div class="t1">TÄGLICHES</div><div class="t2">ÖLPREIS-UPDATE</div>
  <div class="t3">BRENT &amp; WTI • NEWS • ANALYSE • PROGNOSE</div>
  <div class="dt">{ICONS["cal"]}<span>{e(data["datum"])}</span></div></div>

<div class="headline"><h1>{e(data["headline"])}</h1><p>{e(data["subline"])}</p></div>

<div class="card" id="c1"><h2><span class="num">1</span>Aktuelle Ölpreise</h2>
  <div class="prices">{price("Brent", data["brent"])}{price("WTI", data["wti"])}</div>
  <div class="phint">{ICONS["clock"]}<span>{e(data["preis_hinweis"])}</span></div></div>

<div class="card" id="c2"><h2><span class="num">2</span>Die wichtigsten Nachrichten</h2>
  <div class="ngrid">{"".join(newsitem(x) for x in n[:4])}</div></div>

<div class="card" id="c3"><h2><span class="num">3</span>Prognose</h2>
  <div class="pg">
    <div class="pc"><div class="ph2">{ICONS["clock"]}<span>Kurzfristig – nächste 24 bis 72 Stunden</span></div>
      <div class="pill {k.get("farbe","")}">{e(k["label"])}</div><div class="pt">{e(k["text"])}</div></div>
    <div class="pc"><div class="ph2">{ICONS["cal"]}<span>Mittelfristig – nächste 1 bis 4 Wochen</span></div>
      <div class="pill {m.get("farbe","")}">{e(m["label"])}</div><div class="pt">{e(m["text"])}</div></div></div></div>

<div class="card" id="c4"><h2><span class="num">4</span>Mögliche Szenarien</h2>
  <div class="sg">
    <div class="sc"><div class="srow"><div class="sic g">↑</div><div class="sl g">AUFWÄRTS</div></div><div class="sx">{e(s["up"])}</div></div>
    <div class="sc"><div class="srow"><div class="sic y">↔</div><div class="sl y">SEITWÄRTS</div></div><div class="sx">{e(s["side"])}</div></div>
    <div class="sc"><div class="srow"><div class="sic r">↓</div><div class="sl r">ABWÄRTS</div></div><div class="sx">{e(s["down"])}</div></div></div></div>

<div class="card" id="c5"><h2><span class="num">5</span>Worauf ich als Nächstes achten würde</h2>
  <div class="wl5">{"".join(watchitem(i+1, w) for i, w in enumerate(data["watch"][:4]))}</div></div>

<div class="ein"><div class="bi">{ICONS["bulb"]}</div><div><h3>Meine Einschätzung für heute</h3><p>{e(data["einschaetzung"])}</p></div>
  <div class="dis2">Markteinschätzung, keine sichere Vorhersage und keine Anlageberatung.</div></div>

<div class="foot"><div class="fd">{ICONS["drop"]}</div><div class="q">{e(data["quellen"])}</div></div>
</body></html>"""
page = page + body_html

(ROOT / f"{out_name}.html").write_text(page, encoding="utf-8")

from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    chrome = os.environ.get("CHROME_PATH") or next((shutil.which(c) for c in ("google-chrome","google-chrome-stable","chromium","chromium-browser","chrome") if shutil.which(c)), None)
    b = p.chromium.launch(executable_path=chrome, args=["--no-sandbox"]) if chrome else p.chromium.launch(args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 941, "height": 1672}, device_scale_factor=1080/941)
    pg.goto(f"file://{ROOT}/{out_name}.html")
    pg.wait_for_timeout(400)
    pg.screenshot(path=str(ROOT / f"{out_name}.png"))
    b.close()
from PIL import Image
Image.open(ROOT / f"{out_name}.png").convert("RGB").resize((1080,1920),Image.LANCZOS).save(ROOT / f"{out_name}.png")
Image.open(ROOT / f"{out_name}.png").convert("RGB").save(ROOT / f"{out_name}.jpg", "JPEG", quality=92, optimize=True)
print("ok", out_name)
