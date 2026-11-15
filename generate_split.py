#!/usr/bin/env python3
"""Tägliches Ölpreis-Update in 3 Stories: data.json -> <prefix>_1/2/3.png (1080x1920).
1 = Preise + Prognose, 2 = Nachrichten, 3 = Szenarien + Worauf achten + Einschätzung.
Aufruf: python3 generate_split.py data.json <prefix>"""
import json, html, sys, base64, pathlib, shutil, os

ROOT = pathlib.Path(__file__).parent
data = json.loads((ROOT / (sys.argv[1] if len(sys.argv) > 1 else "data.json")).read_text(encoding="utf-8"))
prefix = sys.argv[2] if len(sys.argv) > 2 else "split"
e = lambda s: html.escape(s).replace("\n", "<br>")


def svg(inner, vb="0 0 48 48"):
    return f'<svg viewBox="{vb}" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">{inner}</svg>'


ICONS = {
    "bank": svg('<path d="M6 18 24 8l18 10Z"/><path d="M10 22v14M18 22v14M30 22v14M38 22v14M6 40h36M8 36h32"/>'),
    "ship": svg('<path d="M4 30h40l-6 10H10Z"/><path d="M12 30V20h24v10M20 20v-6h8v6"/><path d="M2 44c4 2 8 2 11 0s8-2 11 0 8 2 11 0 8-2 11 0"/>'),
    "barrel": svg('<ellipse cx="24" cy="10" rx="13" ry="5"/><path d="M11 10v28c0 3 6 5 13 5s13-2 13-5V10"/><path d="M11 20c0 3 6 5 13 5s13-2 13-5M11 30c0 3 6 5 13 5s13-2 13-5"/>'),
    "chart": svg('<path d="M5 40h38"/><path d="M8 32l9-9 7 6 14-16"/><path d="M30 13h8v8"/>'),
    "clock": svg('<circle cx="24" cy="24" r="18"/><path d="M24 12v13l8 5"/>'),
    "cal": svg('<rect x="6" y="9" width="36" height="32" rx="4"/><path d="M6 19h36M15 5v8M33 5v8"/><path d="M14 27h4M22 27h4M30 27h4M14 34h4M22 34h4"/>'),
    "bulb": svg('<path d="M24 5c-8 0-14 6-14 13 0 5 3 8 5 11 1 2 1 4 1 6h16c0-2 0-4 1-6 2-3 5-6 5-11 0-7-6-13-14-13Z"/><path d="M18 40h12M20 45h8"/>'),
    "drop": '<svg viewBox="0 0 40 52"><path fill="url(#gDrop)" d="M20 2C20 2 3 22 3 34a17 17 0 0 0 34 0C37 22 20 2 20 2Z"/><path d="M10 33c0-6 4-12 8-17" stroke="#fff" stroke-opacity=".7" stroke-width="3" fill="none" stroke-linecap="round"/></svg>',
}
ICONS["link"] = svg('<path d="M20 28a8 8 0 0 0 11 0l7-7a8 8 0 0 0-11-11l-3 3"/><path d="M28 20a8 8 0 0 0-11 0l-7 7a8 8 0 0 0 11 11l3-3"/>')
ARROW = {"up": '<span class="ar up">▲</span>', "down": '<span class="ar down">▼</span>', "flat": '<span class="ar flat">▶</span>'}

CSS = r'''
@font-face{font-family:'Poppins';src:url(assets/fonts/Poppins-Bold.ttf);font-weight:100 900}
@font-face{font-family:'Inter';src:url(assets/fonts/Inter-Regular.otf);font-weight:100 450}
@font-face{font-family:'Inter';src:url(assets/fonts/Inter-Medium.otf);font-weight:451 599}
@font-face{font-family:'Inter';src:url(assets/fonts/Inter-Bold.otf);font-weight:600 900}
*{box-sizing:border-box;margin:0;padding:0}
:root{--cyan:#2eeaf8;--yellow:#ffd34d;--green:#5cf28f;--red:#ff8480;--txt:#fff;--card:#04182b;--line:rgba(46,234,248,.7)}
html,body{width:941px;height:1672px}
body{font-family:'Inter',sans-serif;color:var(--txt);position:relative;overflow:hidden;background:linear-gradient(180deg,#00223d 0%,#001426 50%,#001d36 100%)}
body::before{content:"";position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(25,217,234,.03) 0 1px,transparent 1px 40px),repeating-linear-gradient(90deg,rgba(25,217,234,.03) 0 1px,transparent 1px 40px)}
svg{display:block}
.head{position:absolute;left:0;top:0;width:941px;height:236px;overflow:hidden;background:linear-gradient(90deg,#000f1d 0%,#00203a 55%,transparent 100%)}
.head .ph{position:absolute;right:0;top:0;width:470px;height:236px;background:url(data:image/png;base64,%%PHOTO%%) center/cover;-webkit-mask-image:linear-gradient(90deg,transparent 0,#000 38%);mask-image:linear-gradient(90deg,transparent 0,#000 38%)}
.head::after{content:"";position:absolute;left:0;right:0;bottom:0;height:3px;background:linear-gradient(90deg,transparent,#14c8e0 20%,#14c8e0 80%,transparent);opacity:.7}
.dropH{position:absolute;left:40px;top:28px;width:28px;height:38px}
.t1{position:absolute;left:92px;top:30px;font:700 34px/1 Poppins;letter-spacing:1px;color:var(--cyan)}
.t2{position:absolute;left:30px;top:72px;font:800 55px/1 Poppins;color:#fff;letter-spacing:.5px}
.t3{position:absolute;left:30px;top:146px;font:700 22px/1 Poppins;color:var(--cyan);white-space:nowrap}
.dt{position:absolute;left:30px;top:184px;display:flex;align-items:center;gap:12px;font:500 18px Inter;color:#fff}
.dt svg{width:36px;height:36px;color:var(--cyan)}
.part{position:absolute;right:30px;top:28px;display:flex;gap:10px}
.part i{width:16px;height:16px;border-radius:50%;background:rgba(255,255,255,.3)}.part i.on{background:var(--cyan)}
.headline{position:absolute;left:28px;top:254px;width:890px}
.headline h1{font:700 40px/1.15 Poppins;color:#fff}
.headline p{font:500 24px/1.28 Inter;color:#d7eef7;margin-top:10px}
.card{position:absolute;left:17px;width:907px;background:var(--card);border:3px solid var(--cyan);border-radius:16px}
.card h2{position:absolute;left:16px;top:12px;display:flex;align-items:center;gap:14px;font:700 30px Poppins;color:var(--cyan)}
.num{width:46px;height:46px;border-radius:50%;background:var(--cyan);color:#001726;font:700 27px Poppins;display:flex;align-items:center;justify-content:center}
.ic{width:70px;height:70px;flex:none;padding:13px;border-radius:16px;background:#0a3350;border:2px solid var(--cyan);color:#e9fcff}
/* Frame 1 */
#a1{top:470px;height:380px}
.prow{position:absolute;left:0;right:0;height:130px;display:flex;align-items:center;gap:20px;padding:0 24px}
.prow .dr{width:56px;height:74px;flex:none}
.pn{font:700 30px Poppins;width:130px}
.pv{font:800 70px/1 Poppins;white-space:nowrap;flex:1}
.ar{font-size:36px}.up{color:var(--green)}.down{color:var(--red)}.flat{color:var(--yellow)}
.pd{font:700 28px/1.15 Poppins;text-align:right;width:170px}
.hint{position:absolute;left:0;right:0;bottom:14px;text-align:center;font:500 20px Inter;display:flex;gap:10px;justify-content:center;align-items:center;white-space:nowrap}
.hint svg{width:26px;height:26px;color:var(--cyan)}
#a2{top:870px;height:700px}
.pb{position:absolute;left:0;right:0;padding:0 26px}
.pb+.pb{border-top:2px solid var(--line)}
.ph2{display:flex;align-items:center;gap:14px;font:600 24px Poppins;color:var(--cyan);margin-bottom:14px}
.ph2 svg{width:50px;height:50px;padding:9px;border-radius:13px;background:#0a3350;border:2px solid var(--cyan);color:#e9fcff}
.pill{display:inline-block;margin-bottom:14px;padding:4px 24px;border-radius:40px;background:var(--cyan);color:#001726;font:700 32px/1.25 Poppins}
.pill.green{background:var(--green)}.pill.yellow{background:var(--yellow)}.pill.red{background:var(--red)}
.pt{font:400 30px/1.3 Inter}
/* Frame 2 */
.nc{position:absolute;left:17px;width:907px;height:280px;background:var(--card);border:3px solid var(--cyan);border-radius:16px;display:flex;gap:26px;align-items:center;padding:0 28px 0 26px}
.nc .ic{width:104px;height:104px;padding:20px;border-radius:22px}
.nt{font:700 36px/1.15 Poppins;color:var(--cyan);margin-bottom:10px}
.nx{font:400 31px/1.3 Inter}
/* Frame 3 */
#s1{top:262px;height:600px}
.sg{position:absolute;left:0;right:0;top:74px}
.sr{display:flex;gap:20px;align-items:center;padding:0 24px;height:172px}
.sr+.sr{border-top:2px solid var(--line)}
.sic{width:62px;height:62px;border-radius:50%;flex:none;display:flex;align-items:center;justify-content:center;font:700 34px Inter;color:#04202f}
.sic.g{background:var(--green)}.sic.y{background:var(--yellow)}.sic.r{background:var(--red)}
.sl{font:700 28px/1 Poppins;margin-bottom:8px}.sl.g{color:var(--green)}.sl.y{color:var(--yellow)}.sl.r{color:var(--red)}
.sx{font:400 24px/1.28 Inter}
.vt{display:inline-block;margin-top:8px;padding:3px 14px;border-radius:30px;background:rgba(255,255,255,.1);font:600 19px Inter;color:#d7eef7}
.vt b{font-weight:800}.vt .up{color:var(--green)}.vt .down{color:var(--red)}.vt .flat{color:var(--yellow)}
.h3s{position:absolute;left:33px;top:256px;display:flex;align-items:center;gap:14px;font:700 30px Poppins;color:var(--cyan)}
.qs{margin-top:12px;font:400 18px Inter;color:#9fc3d1;display:flex;align-items:center;gap:8px}.qs b{font-weight:700;color:#d7eef7}.qs svg{width:20px;height:20px;color:var(--cyan)}
.srcs{position:absolute;left:30px;right:30px;font:400 15px/1.4 Inter;color:#9fc3d1}
#w1{top:876px;height:400px}
.wl5{position:absolute;left:0;right:0;top:70px;padding:0 24px}
.wrow{display:flex;align-items:center;gap:18px;height:82px;font:400 25px/1.25 Inter}
.wrow+.wrow{border-top:1.5px solid var(--line)}
.wn{width:40px;height:40px;border-radius:50%;flex:none;background:var(--cyan);color:#001726;font:700 22px Poppins;display:flex;align-items:center;justify-content:center}
.wl b{font-weight:700}
.ein{position:absolute;left:17px;top:1290px;width:907px;height:300px;background:#0b1f2c;border:3px solid var(--yellow);border-radius:16px;padding:20px 26px 0 24px;display:flex;gap:22px;align-items:flex-start}
.ein .bi{width:70px;height:70px;color:var(--yellow);flex:none;margin-top:6px}
.ein h3{font:700 27px Poppins;color:var(--yellow);margin-bottom:10px;text-transform:uppercase}
.ein p{font:600 29px/1.3 Inter}
.ein .dis2{position:absolute;left:24px;right:26px;bottom:14px;text-align:center;font:italic 18px Inter;color:#cfe4ee;border-top:1.5px solid rgba(255,211,77,.5);padding-top:8px}
.foot{position:absolute;left:0;top:1612px;width:941px;height:60px;padding:0 72px 0 20px;display:flex;align-items:center;gap:14px}
.foot .fd{width:24px;height:32px;flex:none}.foot .q{font:400 13px/1.35 Inter;flex:1}
.next{position:absolute;right:30px;bottom:12px;font:700 22px Poppins;color:var(--cyan)}
'''

photo = base64.b64encode((ROOT / "assets/header_photo.png").read_bytes()).decode()
n, s, k, m = data["news"], data["szenarien"], data["prognose_kurz"], data["prognose_mittel"]


def head(i, label):
    dots = "".join(f'<i class="{"on" if j == i else ""}"></i>' for j in (1, 2, 3))
    return (f'<div class="head"><div class="ph"></div><div class="dropH">{ICONS["drop"]}</div>'
            f'<div class="t1">TÄGLICHES</div><div class="t2">ÖLPREIS-UPDATE</div>'
            f'<div class="t3">TEIL {i} VON 3 • {label}</div>'
            f'<div class="dt">{ICONS["cal"]}<span>{e(data["datum"])}</span></div><div class="part">{dots}</div></div>')


def prow(name, p, top):
    d = p["dir"] if p["dir"] in ARROW else "flat"
    return (f'<div class="prow" style="top:{top}px"><div class="dr">{ICONS["drop"]}</div><div class="pn">{name}</div>'
            f'<div class="pv">{e(p["preis"])} $</div>{ARROW[d]}<div class="pd {d}"><div>{e(p["diff"])} $</div><div>{e(p["pct"])} %</div></div></div>')


def foot(txt=None):
    q = txt if txt is not None else ""
    return f'<div class="foot"><div class="fd">{ICONS["drop"]}</div><div class="q">{e(q)}</div></div>'


f1 = head(1, "PREISE &amp; PROGNOSE") + f'''
<div class="headline"><h1>{e(data["headline"])}</h1><p>{e(data["subline"])}</p></div>
<div class="card" id="a1"><h2><span class="num">1</span>Aktuelle Ölpreise</h2>
 {prow("Brent", data["brent"], 74)}{prow("WTI", data["wti"], 200)}
 <div class="hint">{ICONS["clock"]}<span>{e(data["preis_hinweis"])}</span></div></div>
<div class="card" id="a2"><h2><span class="num">2</span>Prognose</h2>
 <div class="pb" style="top:76px;height:300px"><div class="ph2">{ICONS["clock"]}<span>Kurzfristig – 24 bis 72 Stunden</span></div>
   <div class="pill {k.get("farbe","")}">{e(k["label"])}</div><div class="pt">{e(k["text"])}</div></div>
 <div class="pb" style="top:384px;height:300px;padding-top:22px"><div class="ph2">{ICONS["cal"]}<span>Mittelfristig – 1 bis 4 Wochen</span></div>
   <div class="pill {m.get("farbe","")}">{e(m["label"])}</div><div class="pt">{e(m["text"])}</div></div></div>
<div class="next">Weiter: Nachrichten →</div>
''' + foot(data['quellen'].split('\n')[-1])

news = "".join(
    f'<div class="nc" style="top:{322 + i * 292}px"><div class="ic">{ICONS[x["icon"]]}</div><div><div class="nt">{e(x["titel"])}</div><div class="nx">{e(x["text"])}</div><div class="qs">Quelle: <b>{e(x.get("quelle",""))}</b> ({e(x.get("quelle_datum",""))}) • {ICONS["link"]}<span>{e(x.get("link_anzeige",""))}</span></div></div></div>'
    for i, x in enumerate(n[:4]))
src = data["quellen"].split("\n")
f2 = (head(2, "DIE WICHTIGSTEN NACHRICHTEN") + '<div class="h3s"><span class="num">3</span>Die wichtigsten Nachrichten</div>' + news +
      '<div class="next" style="bottom:20px">Weiter: Ausblick →</div>')

watch = "".join(
    f'<div class="wrow"><span class="wn">{i+1}</span><span class="wl"><b>{e(w["titel"])}</b> – {e(w["text"])}</span></div>'
    for i, w in enumerate(data["watch"][:4]))
vg = data.get("szenarien_vergleich", {})
def vt(key):
    v = vg.get(key)
    if not v: return ""
    sym = {"more": ("▲", "up"), "less": ("▼", "down"), "same": ("=", "flat")}[v.get("trend", "same")]
    return f'<div class="vt"><b class="{sym[1]}">{sym[0]}</b> Vortag: {e(v["text"])}</div>'
f3 = head(3, "AUSBLICK") + f'''
<div class="card" id="s1"><h2><span class="num">4</span>Mögliche Szenarien</h2><div class="sg">
 <div class="sr"><div class="sic g">↑</div><div><div class="sl g">AUFWÄRTS</div><div class="sx">{e(s["up"])}</div>{vt("up")}</div></div>
 <div class="sr"><div class="sic y">↔</div><div><div class="sl y">SEITWÄRTS</div><div class="sx">{e(s["side"])}</div>{vt("side")}</div></div>
 <div class="sr"><div class="sic r">↓</div><div><div class="sl r">ABWÄRTS</div><div class="sx">{e(s["down"])}</div>{vt("down")}</div></div></div></div>
<div class="card" id="w1"><h2><span class="num">5</span>Worauf ich als Nächstes achten würde</h2><div class="wl5">{watch}</div></div>
<div class="ein"><div class="bi">{ICONS["bulb"]}</div><div><h3>Meine Einschätzung für heute</h3><p>{e(data["einschaetzung"])}</p></div>
 <div class="dis2">Markteinschätzung, keine sichere Vorhersage und keine Anlageberatung.</div></div>
''' + foot('Stand ' + data['quellen'].split('Stand ')[-1])

PRE = ('<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><style>' + CSS.replace("%%PHOTO%%", photo) +
       '</style></head><body><svg width="0" height="0" style="position:absolute"><defs><linearGradient id="gDrop" x1="0" y1="0" x2="1" y2="1">'
       '<stop offset="0" stop-color="#a6f6ff"/><stop offset=".5" stop-color="#19d9ea"/><stop offset="1" stop-color="#0a7fa8"/></linearGradient></defs></svg>')

from playwright.sync_api import sync_playwright
from PIL import Image
with sync_playwright() as p:
    chrome = os.environ.get("CHROME_PATH") or next((shutil.which(c) for c in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome") if shutil.which(c)), None)
    b = p.chromium.launch(executable_path=chrome, args=["--no-sandbox"]) if chrome else p.chromium.launch(args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 941, "height": 1672}, device_scale_factor=1080 / 941)
    for i, body in enumerate((f1, f2, f3), 1):
        (ROOT / f"{prefix}_{i}.html").write_text(PRE + body + "</body></html>", encoding="utf-8")
        pg.goto(f"file://{ROOT}/{prefix}_{i}.html"); pg.wait_for_timeout(400)
        pg.screenshot(path=str(ROOT / f"{prefix}_{i}.png"))
        im = Image.open(ROOT / f"{prefix}_{i}.png").convert("RGB").resize((1080, 1920), Image.LANCZOS)
        im.save(ROOT / f"{prefix}_{i}.png"); im.save(ROOT / f"{prefix}_{i}.jpg", "JPEG", quality=92, optimize=True)
    b.close()
print("ok", prefix)
