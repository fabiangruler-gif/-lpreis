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

def watchitem(w):
    return f'''<div class="watch"><div class="wic">{ICONS[w["icon"]]}</div>
      <div class="wt">{e(w["titel"])}</div><div class="wx">{e(w["text"])}</div></div>'''

photo = base64.b64encode((ROOT / "assets/header_photo.png").read_bytes()).decode()
n = data["news"]; s = data["szenarien"]; k = data["prognose_kurz"]; m = data["prognose_mittel"]

page = f'''<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><style>
@font-face{{font-family:'Poppins';src:url(assets/fonts/Poppins-Bold.ttf);font-weight:100 900}}
@font-face{{font-family:'Inter';src:url(assets/fonts/Inter-Regular.otf);font-weight:100 450;font-style:normal}}
@font-face{{font-family:'Inter';src:url(assets/fonts/Inter-Medium.otf);font-weight:451 599;font-style:normal}}
@font-face{{font-family:'Inter';src:url(assets/fonts/Inter-Bold.otf);font-weight:600 900;font-style:normal}}
@font-face{{font-family:'Inter';src:url(assets/fonts/Inter-Italic.otf);font-weight:100 900;font-style:italic}}
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{--cyan:#19d9ea;--bgc:#021f38;--yellow:#f7d25b;--green:#4ade80;--red:#fb6e6b;--txt:#e9f4fb}}
html,body{{width:941px;height:1672px;background:#001a30}}
body{{font-family:'Inter',sans-serif;color:var(--txt);position:relative;overflow:hidden;
  background:linear-gradient(180deg,#00223d 0%,#001b33 45%,#00213b 100%)}}
.head{{position:absolute;left:0;top:0;width:941px;height:236px;overflow:hidden;
  background:linear-gradient(90deg,#001c34 0%,#01213c 45%,transparent 100%)}}
.head .ph{{position:absolute;right:0;top:0;width:470px;height:236px;background:url(data:image/png;base64,{photo}) center/cover;
  -webkit-mask-image:linear-gradient(90deg,transparent 0,#000 38%);mask-image:linear-gradient(90deg,transparent 0,#000 38%)}}
.head::after{{content:"";position:absolute;left:0;right:0;bottom:0;height:3px;background:linear-gradient(90deg,transparent,#14c8e0 20%,#14c8e0 80%,transparent);opacity:.6}}
.t1{{position:absolute;left:92px;top:30px;font:700 34px/1 Poppins;letter-spacing:1px;color:var(--cyan)}}
.dropH{{position:absolute;left:40px;top:28px;width:28px;height:38px;color:var(--cyan)}}
.t2{{position:absolute;left:30px;top:72px;font:800 55px/1 Poppins;color:#fff;letter-spacing:.5px}}
.t3{{position:absolute;left:30px;top:146px;font:700 18.5px/1 Poppins;color:var(--cyan);letter-spacing:.5px;white-space:nowrap}}
.dt{{position:absolute;left:30px;top:184px;display:flex;align-items:center;gap:12px;font:500 17.5px Inter;color:#fff}}
.dt svg{{width:36px;height:36px;color:var(--cyan)}}
.headline{{position:absolute;left:28px;top:250px;width:885px}}
.headline h1{{font:700 27.5px/1.15 Poppins;color:#fff}}
.headline p{{font:400 16.2px/1.3 Inter;color:#dcebf5;margin-top:6px}}
.card{{position:absolute;left:17px;width:907px;border:2.5px solid #19d9ea;border-radius:18px;background:rgba(2,31,56,.92);
  box-shadow:0 0 14px rgba(25,217,234,.35),inset 0 0 18px rgba(25,217,234,.10)}}
.card h2{{position:absolute;left:14px;top:10px;display:flex;align-items:center;gap:14px;font:700 23.5px Poppins;color:var(--cyan)}}
.num{{width:42px;height:42px;border-radius:50%;background:#14d4e8;color:#032235;font:700 24px Poppins;display:flex;align-items:center;justify-content:center;
  box-shadow:0 0 12px rgba(20,212,232,.7)}}
/* 1 */
#c1{{top:338px;height:182px}}
.prices{{position:absolute;left:0;right:0;top:54px;display:flex}}
.price{{flex:1;display:flex;align-items:center;gap:14px;padding:0 20px 0 30px;height:84px}}
.price + .price{{border-left:2px solid rgba(25,217,234,.5)}}
.drop{{width:46px;height:60px;color:var(--cyan)}}
.pname{{font:700 22px Poppins;color:#fff;line-height:1}}
.pval{{font:800 40px/1.05 Poppins;color:#fff;white-space:nowrap}}
.ar{{font-size:22px;margin-left:6px}} .ar.up{{color:var(--green)}} .ar.down{{color:var(--red)}} .ar.flat{{color:var(--yellow)}}
.pdiff{{font:700 20px/1.15 Poppins}} .pdiff.up{{color:var(--green)}} .pdiff.down{{color:var(--red)}} .pdiff.flat{{color:var(--yellow)}}
.phint{{position:absolute;left:0;right:0;bottom:12px;text-align:center;font:400 14.2px Inter;white-space:nowrap;color:#e6f2f9;display:flex;gap:10px;justify-content:center;align-items:center}}
.phint svg{{width:24px;height:24px;color:var(--cyan)}}
/* 2 */
#c2{{top:540px;height:337px}}
.ngrid{{position:absolute;left:0;right:0;top:56px;display:grid;grid-template-columns:1fr 1fr;grid-auto-rows:1fr;height:270px}}
.news{{display:flex;gap:14px;padding:10px 18px 6px 20px;border-top:1.5px solid rgba(25,217,234,.45)}}
.news:nth-child(even){{border-left:1.5px solid rgba(25,217,234,.45)}}
.news:nth-child(-n+2){{border-top:none}}
.nic{{width:50px;height:50px;flex:none;color:#6fd3ee;margin-top:2px}}
.nt{{font:700 17px/1.15 Poppins;color:var(--cyan);margin-bottom:5px}}
.nx{{font:400 14.4px/1.27 Inter;color:#eef6fb}}
/* 3 */
#c3{{top:896px;height:204px}}
.pg{{position:absolute;left:0;right:0;top:50px;display:grid;grid-template-columns:1fr 1fr;height:150px}}
.pc{{padding:0 20px 0 28px;position:relative}}
.pc + .pc{{border-left:2px solid rgba(25,217,234,.5)}}
.ph2{{display:flex;align-items:center;gap:10px;font:600 15px Poppins;white-space:nowrap;color:var(--cyan);height:34px}}
.ph2 svg{{width:38px;height:38px;margin-left:-6px}}
.pill{{display:inline-block;margin:2px 0 8px 0;padding:2px 22px;border-radius:30px;background:#16d3e6;color:#06233a;font:700 18px Poppins;white-space:nowrap;text-decoration:underline;text-underline-offset:3px;margin-left:54px}}
.pc:nth-child(2) .ph2{{margin-left:6px}} .pc:nth-child(2) .pill{{margin-left:62px}}
.pt{{font:400 14.6px/1.28 Inter;color:#eef6fb}}
/* 4 */
#c4{{top:1119px;height:156px}}
.sg{{position:absolute;left:0;right:0;top:54px;display:grid;grid-template-columns:1fr 1fr 1fr;height:96px}}
.sc{{display:flex;gap:10px;padding:0 10px 0 18px}} .sc + .sc{{border-left:2px solid rgba(25,217,234,.5)}}
.sic{{width:46px;height:46px;border-radius:50%;flex:none;display:flex;align-items:center;justify-content:center;font:700 25px Inter;color:#04202f}}
.sic.g{{background:#4ade80}} .sic.y{{background:#f7d25b}} .sic.r{{background:#fb6e6b}}
.sl{{font:700 19.5px/1 Poppins;margin:2px 0 5px}} .sl.g{{color:#4ade80}} .sl.y{{color:#f7d25b}} .sl.r{{color:#fb6e6b}}
.sx{{font:400 13.6px/1.25 Inter;color:#eef6fb}}
/* 5 */
#c5{{top:1283px;height:192px}}
.wg{{position:absolute;left:0;right:0;top:56px;display:grid;grid-template-columns:repeat(4,1fr);height:128px}}
.watch{{padding:0 16px 0 20px}} .watch + .watch{{border-left:2px solid rgba(25,217,234,.5)}}
.wic{{height:34px;width:46px;color:#6fd3ee;margin-bottom:2px}} .wic svg{{width:100%;height:100%}}
.wt{{font:700 15.2px/1.1 Poppins;color:var(--cyan);margin-bottom:4px}}
.wx{{font:400 13.4px/1.25 Inter;color:#eef6fb}}
.watch:nth-child(4) .wic{{display:none}} .watch:nth-child(4){{padding-top:0}} .watch:nth-child(4) .wt{{margin-top:2px}}
/* Einschätzung */
.ein{{position:absolute;left:17px;top:1486px;width:907px;height:94px;border:3px solid #f7d25b;border-radius:16px;background:rgba(14,36,50,.95);
  box-shadow:0 0 16px rgba(247,210,91,.4),inset 0 0 18px rgba(247,210,91,.08);display:flex;align-items:center;gap:22px;padding:0 24px 0 20px}}
.ein .bi{{width:62px;height:62px;color:#f7d25b;flex:none}}
.ein h3{{font:700 19px Poppins;color:#f7d25b;letter-spacing:.5px;margin-bottom:3px;text-transform:uppercase}}
.ein p{{font:500 16.2px/1.3 Inter;color:#fff}}
.foot{{position:absolute;left:0;top:1596px;width:941px;height:76px;padding:0 26px 0 20px;display:flex;align-items:center;gap:14px}}
.foot .fd{{width:26px;height:34px;color:var(--cyan);flex:none}}
.foot .q{{font:400 11.4px/1.4 Inter;color:#e7f2f9;flex:1}}
.foot .dis{{border-left:1.5px solid rgba(25,217,234,.5);padding-left:16px;font:italic 11.4px/1.35 Inter;color:#e7f2f9;text-align:right;width:150px}}

/* ===== PRO: Ebenen, 3D, Abstände ===== */
body::before{{content:"";position:absolute;inset:0;background:
 radial-gradient(620px 380px at 86% 14%,rgba(255,140,40,.20),transparent 70%),
 radial-gradient(720px 520px at 8% 58%,rgba(20,200,230,.11),transparent 70%),
 radial-gradient(520px 420px at 92% 88%,rgba(20,200,230,.14),transparent 70%),
 repeating-linear-gradient(0deg,rgba(25,217,234,.04) 0 1px,transparent 1px 38px),
 repeating-linear-gradient(90deg,rgba(25,217,234,.04) 0 1px,transparent 1px 38px)}}
.head::before{{content:"";position:absolute;right:0;top:0;width:520px;height:236px;z-index:2;pointer-events:none;
 background:linear-gradient(180deg,transparent 55%,rgba(0,26,48,.6) 100%),radial-gradient(circle at 62% 70%,rgba(255,170,60,.28),transparent 55%);mix-blend-mode:screen}}
.t1{{text-shadow:0 1px 0 #0aa0b3,0 2px 0 #087c8f,0 3px 0 #06586b,0 7px 10px rgba(0,0,0,.6),0 0 18px rgba(25,217,234,.45)}}
.t2{{text-shadow:0 1px 0 #d5edf7,0 2px 0 #a6d6e8,0 3px 0 #62adcc,0 4px 0 #2f84ab,0 5px 0 #17607f,0 6px 0 #0b3f5c,0 12px 14px rgba(0,0,0,.65),0 0 30px rgba(25,217,234,.35)}}
.t3{{text-shadow:0 2px 0 #06586b,0 0 12px rgba(25,217,234,.5)}}
.headline h1{{text-shadow:0 2px 0 rgba(0,0,0,.45),0 0 20px rgba(25,217,234,.28)}}
.card{{background:linear-gradient(180deg,rgba(9,58,92,.96) 0%,rgba(2,33,58,.96) 36%,rgba(1,21,41,.98) 100%);border-color:#22e3f2;
 box-shadow:0 14px 26px rgba(0,0,0,.55),0 0 18px rgba(25,217,234,.42),inset 0 2px 0 rgba(255,255,255,.20),inset 0 -12px 26px rgba(0,0,0,.38),inset 0 0 24px rgba(25,217,234,.12)}}
.card::before{{content:"";position:absolute;left:0;right:0;top:0;height:46%;border-radius:16px 16px 60% 60%/16px 16px 22px 22px;
 background:linear-gradient(180deg,rgba(255,255,255,.075),transparent);pointer-events:none}}
.card h2{{text-shadow:0 2px 0 #06556b,0 5px 8px rgba(0,0,0,.55),0 0 14px rgba(25,217,234,.35)}}
.num{{width:44px;height:44px;background:radial-gradient(circle at 32% 26%,#c5f9ff 0,#19d9ea 40%,#0a8fb0 100%);color:#02263a;
 box-shadow:0 5px 0 #06607c,0 9px 14px rgba(0,0,0,.55),0 0 16px rgba(20,212,232,.7),inset 0 2px 3px rgba(255,255,255,.75)}}
/* Abstände Überschrift -> Inhalt */
#c1{{top:336px;height:182px}} #c1 .prices{{top:62px}}
#c2{{top:534px;height:322px}} #c2 .ngrid{{top:66px;height:248px}}
#c3{{top:872px;height:218px}} #c3 .pg{{top:62px;height:150px}}
#c4{{top:1104px;height:172px}} #c4 .sg{{top:64px;height:104px}}
#c5{{top:1290px;height:208px}} #c5 .wg{{top:62px;height:140px}}
.ein{{top:1508px;height:86px}}
.foot{{top:1602px;height:70px;padding:0 78px 0 20px}} .foot .q{{font-size:10.6px}} .foot .dis{{width:156px}} .wx{{font-size:13px}} .sx{{font-size:13.2px}}
/* Preise */
.price{{background:linear-gradient(180deg,rgba(25,217,234,.08),transparent)}}
.pval{{text-shadow:0 1px 0 #c3e2ee,0 2px 0 #6aa6c0,0 3px 0 #2d6784,0 8px 10px rgba(0,0,0,.6),0 0 20px rgba(25,217,234,.3)}}
.pdiff{{text-shadow:0 0 12px currentColor,0 3px 4px rgba(0,0,0,.5)}}
.ar{{text-shadow:0 0 14px currentColor,0 3px 3px rgba(0,0,0,.5)}}
.drop svg,.dropH svg,.fd svg{{filter:drop-shadow(0 0 8px rgba(25,217,234,.8)) drop-shadow(0 5px 4px rgba(0,0,0,.55))}}
.drop{{width:46px;height:60px}}
/* Icon-Kacheln */
.nic,.wic{{width:56px;height:56px;padding:10px;border-radius:15px;color:#c4f4ff;margin-top:0;
 background:linear-gradient(145deg,rgba(45,150,190,.5),rgba(4,36,62,.92));border:1.5px solid rgba(111,211,238,.6);
 box-shadow:0 5px 0 rgba(1,16,30,.95),0 9px 14px rgba(0,0,0,.5),inset 0 1px 0 rgba(255,255,255,.4),0 0 12px rgba(25,217,234,.28)}}
.wic{{width:40px;height:40px;padding:7px;border-radius:11px;margin-bottom:6px;box-shadow:0 4px 0 rgba(1,16,30,.95),0 7px 10px rgba(0,0,0,.5),inset 0 1px 0 rgba(255,255,255,.4),0 0 10px rgba(25,217,234,.28)}}
.nic svg,.wic svg{{filter:drop-shadow(0 0 5px rgba(25,217,234,.8))}}
.nic{{flex:none}} .nt{{margin-top:2px}}
.ph2{{height:42px}} .ph2 svg{{width:42px;height:42px;padding:7px;margin-left:-8px;border-radius:12px;color:#c4f4ff;
 background:linear-gradient(145deg,rgba(45,150,190,.5),rgba(4,36,62,.92));border:1.5px solid rgba(111,211,238,.6);
 box-shadow:0 4px 0 rgba(1,16,30,.95),0 7px 10px rgba(0,0,0,.5),inset 0 1px 0 rgba(255,255,255,.4)}}
.wt{{margin-top:2px}}
.watch:nth-child(4) .wt{{margin-top:0}}
/* Prognose-Pillen */
.pill{{background:linear-gradient(180deg,#6af2ff 0%,#16d3e6 46%,#0aa3be 100%);margin-bottom:13px;
 box-shadow:0 4px 0 #066a85,0 8px 12px rgba(0,0,0,.5),0 0 14px rgba(22,211,230,.5),inset 0 1px 0 rgba(255,255,255,.65)}}
/* Szenarien */
.sic{{width:48px;height:48px}}
.sic.g{{background:radial-gradient(circle at 32% 26%,#dcffe9,#4ade80 46%,#17884a);box-shadow:0 4px 0 #0f5f33,0 8px 10px rgba(0,0,0,.5),0 0 14px rgba(74,222,128,.6),inset 0 2px 2px rgba(255,255,255,.6)}}
.sic.y{{background:radial-gradient(circle at 32% 26%,#fff3c4,#f7d25b 46%,#b8891a);box-shadow:0 4px 0 #7a5a0c,0 8px 10px rgba(0,0,0,.5),0 0 14px rgba(247,210,91,.6),inset 0 2px 2px rgba(255,255,255,.6)}}
.sic.r{{background:radial-gradient(circle at 32% 26%,#ffd3d1,#fb6e6b 46%,#b53330);box-shadow:0 4px 0 #77201e,0 8px 10px rgba(0,0,0,.5),0 0 14px rgba(251,110,107,.6),inset 0 2px 2px rgba(255,255,255,.6)}}
.sl{{text-shadow:0 0 12px currentColor,0 3px 3px rgba(0,0,0,.5)}}
.sc:nth-child(1){{background:linear-gradient(90deg,rgba(74,222,128,.13),transparent 80%)}}
.sc:nth-child(2){{background:linear-gradient(90deg,rgba(247,210,91,.12),transparent 80%)}}
.sc:nth-child(3){{background:linear-gradient(90deg,rgba(251,110,107,.13),transparent 80%)}}
.sc{{padding-top:6px}}
/* Einschätzung */
.ein{{background:linear-gradient(180deg,rgba(40,48,40,.96),rgba(10,30,44,.97) 55%,rgba(6,22,34,.98));
 box-shadow:0 14px 24px rgba(0,0,0,.55),0 0 20px rgba(247,210,91,.45),inset 0 2px 0 rgba(255,255,255,.18),inset 0 -10px 22px rgba(0,0,0,.35),inset 0 0 20px rgba(247,210,91,.08)}}
.ein h3{{text-shadow:0 2px 0 #7a5a0c,0 5px 8px rgba(0,0,0,.5),0 0 14px rgba(247,210,91,.4)}}
.ein .bi{{filter:drop-shadow(0 0 10px rgba(247,210,91,.85)) drop-shadow(0 4px 4px rgba(0,0,0,.5))}}
.corner{{position:absolute;right:0;bottom:0;width:70px;height:70px;background:linear-gradient(135deg,transparent 50%,#19d9ea 50% 62%,transparent 62% 69%,#1b7fd0 69%);filter:drop-shadow(0 0 8px rgba(25,217,234,.7))}}

/* ===== LESBAR: große Schrift, weniger Inhalt (Handy-Story) ===== */
.headline{{top:248px;width:890px}} .headline h1{{font:700 35px/1.18 Poppins}}
.card h2{{font:700 29px Poppins;top:12px;left:16px}} .num{{width:46px;height:46px;font-size:27px}}
/* 1 Preise */
#c1{{top:344px;height:196px}} #c1 .prices{{top:70px}}
.price{{height:92px;gap:14px;padding:0 14px 0 26px}}
.pname{{font:700 26px Poppins}} .pval{{font:800 50px/1.05 Poppins}}
.pdiff{{font:700 23px/1.15 Poppins}} .ar{{font-size:26px}}
.drop{{width:48px;height:62px}}
.phint{{font:500 16.5px Inter;bottom:10px;white-space:normal;padding:0 20px;line-height:1.25}}
.phint svg{{width:22px;height:22px;flex:none}}
/* 2 News */
#c2{{top:556px;height:412px}} #c2 .ngrid{{top:68px;height:336px;grid-template-columns:1fr}}
.news{{border-left:none!important;border-top:1.5px solid rgba(25,217,234,.45)!important;padding:10px 22px 8px 20px;gap:18px;align-items:center}}
.news:first-child{{border-top:none!important}}
.nic{{width:64px;height:64px;padding:12px}}
.nt{{font:700 26px/1.1 Poppins;margin-bottom:5px}} .nx{{font:400 22.5px/1.26 Inter}}
/* 3 Prognose */
#c3{{top:982px;height:268px}} #c3 .pg{{top:64px;height:196px}}
.pc{{padding:0 18px 0 22px}}
.ph2{{font:600 19.5px Poppins;height:44px}} .ph2 svg{{width:42px;height:42px}}
.pill{{font:700 22px Poppins;margin:4px 0 9px 0!important;padding:2px 20px;white-space:normal;line-height:1.2}}
.pc:nth-child(2) .ph2{{margin-left:0}}
.pt{{font:400 21.5px/1.25 Inter}}
/* 4 Szenarien */
#c4{{top:1264px;height:238px}} #c4 .sg{{top:62px;height:170px;grid-template-columns:1fr}}
.sc{{align-items:center;padding:0 24px 0 20px;gap:16px;background-size:100% 100%}}
.sc+.sc{{border-left:none;border-top:1.5px solid rgba(25,217,234,.4)}}
.sc>div:last-child{{display:flex;align-items:center;gap:18px}}
.sic{{width:42px;height:42px;font-size:24px}}
.sl{{font:700 23px/1 Poppins;width:158px;flex:none;margin:0}} .sx{{font:400 21px/1.2 Inter}}
/* Einschätzung + Fuß */
.ein{{top:1516px;height:98px;gap:18px;padding:0 22px 0 18px}} .ein .bi{{width:56px;height:56px}}
.ein h3{{font:700 19px Poppins;margin-bottom:2px}} .ein p{{font:600 21.5px/1.22 Inter}}
.foot{{top:1622px;height:50px;padding:0 60px 0 18px}} .foot .fd{{display:none}}
.foot .q{{font-size:11.6px;line-height:1.3}} .foot .dis{{font-size:11.6px;width:110px;padding-left:12px}}

/* ===== KLARE KANTEN + KONTRAST ===== */
body{{background:#000f1d!important}} body::before{{background:repeating-linear-gradient(0deg,rgba(25,217,234,.025) 0 1px,transparent 1px 40px),repeating-linear-gradient(90deg,rgba(25,217,234,.025) 0 1px,transparent 1px 40px)!important}}
.head{{background:linear-gradient(90deg,#000f1d 0%,#00203a 55%,transparent 100%)!important}}
.head::before{{display:none}}
.t1,.t3,.t2,.headline h1,.card h2,.ein h3,.pval,.pdiff,.ar,.sl{{text-shadow:0 2px 0 rgba(0,0,0,.85)!important}}
.t2{{text-shadow:0 3px 0 #0b5d7a!important}}
.card{{background:#04182b!important;border:3px solid #2eeaf8!important;border-radius:16px!important;box-shadow:0 5px 0 #000b15!important}}
.card::before{{display:none}}
.ein{{background:#0b1f2c!important;border:3px solid #ffd34d!important;box-shadow:0 5px 0 #000b15!important}}
.num{{background:#2eeaf8!important;color:#001726!important;box-shadow:0 3px 0 #06607c!important}}
.price{{background:none!important}} .price+.price,.pc+.pc,.sc+.sc,.news{{border-color:rgba(46,234,248,.7)!important}}
.nic,.wic,.ph2 svg{{background:#0a3350!important;border:2px solid #2eeaf8!important;box-shadow:0 3px 0 #000b15!important;color:#e9fcff!important}}
.nic svg,.wic svg,.drop svg,.dropH svg{{filter:none!important}}
.pill{{background:#2eeaf8!important;color:#001726!important;box-shadow:0 3px 0 #06607c!important;text-decoration:none!important}}
.sic.g{{background:#4ade80!important;box-shadow:0 3px 0 #0f5f33!important}}
.sic.y{{background:#ffd34d!important;box-shadow:0 3px 0 #7a5a0c!important}}
.sic.r{{background:#ff7570!important;box-shadow:0 3px 0 #77201e!important}}
.sc{{background:none!important}}
.nt,.card h2,.ph2{{color:#2eeaf8!important}} .nx,.pt,.sx,.ein p,.phint,.foot .q,.foot .dis{{color:#ffffff!important}}
.sl.g,.pdiff.up,.ar.up{{color:#5cf28f!important}} .sl.r,.pdiff.down,.ar.down{{color:#ff8480!important}} .sl.y{{color:#ffd34d!important}}
.corner{{display:none}}

/* Feinschliff */
#c1{{top:332px;height:216px}} #c1 .prices{{top:66px}} .phint{{bottom:12px;font-size:17px}}
#c2{{top:562px;height:410px}}
#c3{{top:986px;height:232px}} #c3 .pg{{top:62px;height:164px}} .pt{{font-size:24px}} .pill{{font-size:23px}} .ph2{{font-size:20px}}
#c4{{top:1232px;height:244px}} #c4 .sg{{top:64px;height:174px}} .sx{{font-size:23px}} .sl{{font-size:24px;width:172px}}
.ein{{top:1490px;height:106px}} .ein p{{font-size:23px}}
.foot{{top:1608px;height:64px}}
</style></head><body>
<svg width="0" height="0" style="position:absolute"><defs><linearGradient id="gDrop" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#a6f6ff"/><stop offset=".5" stop-color="#19d9ea"/><stop offset="1" stop-color="#0a7fa8"/></linearGradient></defs></svg><div class="corner"></div>
<div class="head"><div class="ph"></div>
  <div class="dropH">{ICONS["drop"]}</div>
  <div class="t1">TÄGLICHES</div><div class="t2">ÖLPREIS-UPDATE</div>
  <div class="t3">BRENT &amp; WTI • NEWS • ANALYSE • PROGNOSE</div>
  <div class="dt">{ICONS["cal"]}<span>{e(data["datum"])}</span></div></div>

<div class="headline"><h1>{e(data["headline"])}</h1></div>

<div class="card" id="c1"><h2><span class="num">1</span>Aktuelle Ölpreise</h2>
  <div class="prices">{price("Brent", data["brent"])}{price("WTI", data["wti"])}</div>
  <div class="phint">{ICONS["clock"]}<span>{e(data["preis_hinweis"])}</span></div></div>

<div class="card" id="c2"><h2><span class="num">2</span>Das bewegt den Markt</h2>
  <div class="ngrid">{"".join(newsitem(x) for x in n[:3])}</div></div>

<div class="card" id="c3"><h2><span class="num">3</span>Prognose</h2>
  <div class="pg">
    <div class="pc"><div class="ph2">{ICONS["clock"]}<span>Kurzfristig · 24–72 Std.</span></div>
      <div class="pill">{e(k["label"])}</div><div class="pt">{e(k["text"])}</div></div>
    <div class="pc"><div class="ph2">{ICONS["cal"]}<span>Mittelfristig · 1–4 Wochen</span></div>
      <div class="pill">{e(m["label"])}</div><div class="pt">{e(m["text"])}</div></div></div></div>

<div class="card" id="c4"><h2><span class="num">4</span>Szenarien</h2>
  <div class="sg">
    <div class="sc"><div class="sic g">↑</div><div><div class="sl g">AUFWÄRTS</div><div class="sx">{e(s["up"])}</div></div></div>
    <div class="sc"><div class="sic y">↔</div><div><div class="sl y">SEITWÄRTS</div><div class="sx">{e(s["side"])}</div></div></div>
    <div class="sc"><div class="sic r">↓</div><div><div class="sl r">ABWÄRTS</div><div class="sx">{e(s["down"])}</div></div></div></div></div>

<div class="ein"><div class="bi">{ICONS["bulb"]}</div><div><h3>Einschätzung</h3><p>{e(data["einschaetzung"])}</p></div></div>

<div class="foot"><div class="fd">{ICONS["drop"]}</div><div class="q">{e(data["quellen"])}</div>
  <div class="dis">Keine<br>Anlageberatung.</div></div>
</body></html>'''

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
