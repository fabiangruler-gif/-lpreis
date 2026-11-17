#!/usr/bin/env python3
"""Baut ein Reel aus reels/specs/<slug>.json (6 Slides, Gold auf Schwarz, Sprecher per ElevenLabs).

Aufruf:
  python3 reels/build_reel.py <slug>                 # echte Vertonung (ELEVENLABS_API_KEY nötig)
  python3 reels/build_reel.py <slug> --fake-audio    # Testlauf ohne Ton-API (Stille nach Wortzahl)
  python3 reels/build_reel.py <slug> --cover-only    # nur das Profil-Vorschaubild
  python3 reels/build_reel.py <slug> --tts-test edge # Stimme testen (elevenlabs | edge | piper)
Ergebnis: out/reels/<slug>.mp4, <slug>_storyboard.jpg, <slug>_cover.jpg (Profil-Vorschau, wird per cover_url gesetzt)
"""
import hashlib, html, json, os, pathlib, re, shutil, subprocess, sys, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
FPS, GAP, TAIL, LEAD = 30, 0.28, 0.7, 0.15
# Nur echte Stille vorn/hinten kappen und je etwas Luft lassen, damit leise Wortanfänge/-enden nicht abgeschnitten werden
TRIM = ("silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.10,areverse,"
        "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.14,areverse")
VOICE = os.environ.get("ELEVENLABS_VOICE_ID") or "8aPaMtDocayOBFDFyWHp"  # Markus
MODEL = os.environ.get("ELEVENLABS_MODEL") or "eleven_multilingual_v2"


def sh(*a):
    subprocess.run([str(x) for x in a], check=True)


def dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


# ---------- Text-Helfer ----------
def gold(s):
    return re.sub(r"\*(.+?)\*", r'<span class="g">\1</span>', html.escape(s or "", quote=False))


def esc(s):
    return html.escape(s or "", quote=False)


ICONS = {
    "pie": '<circle cx="24" cy="24" r="21"/><path d="M24 24V3A21 21 0 0 1 43.6 31.5z" fill="#f5b22f"/>',
    "globe": '<circle cx="24" cy="24" r="21"/><ellipse cx="24" cy="24" rx="9" ry="21"/><path d="M3 24h42"/>',
    "chart": '<circle cx="24" cy="24" r="21"/><path d="M12 33l8-9 6 5 10-13"/><path d="M30 16h6v6"/>',
    "clock": '<circle cx="24" cy="24" r="21"/><path d="M24 11v14l9 6"/>',
    "warn": '<path d="M24 5L45 41H3z"/><path d="M24 18v12"/><circle cx="24" cy="35" r="1.5" fill="#f5b22f"/>',
    "drop": '<path d="M24 4C24 4 8 22 8 33a16 16 0 0 0 32 0C40 22 24 4 24 4Z"/>',
    "euro": '<circle cx="24" cy="24" r="21"/><path d="M31 15a10 10 0 1 0 0 18M13 21h14M13 27h14"/>',
}


def icon(name):
    return (f'<svg viewBox="0 0 48 48" fill="none" stroke="#f5b22f" stroke-width="2.6" stroke-linecap="round" '
            f'stroke-linejoin="round">{ICONS.get(name, ICONS["chart"])}</svg>')


# ---------- Slide-Typen ----------
def s_hook(d):
    return (f'<div class="photo"></div><div class="vig"></div>'
            f'<h1 class="txt">{gold(d["titel"])}</h1><div class="txt sub">{esc(d.get("sub"))}</div>'
            '<svg style="position:absolute;left:78px;top:1390px;background:rgba(0,12,19,.7);border-radius:50%;padding:10px" '
            'width="116" height="116" viewBox="0 0 48 48" fill="none" stroke="#f5b22f" stroke-width="2.4">'
            '<circle cx="24" cy="24" r="19"/><ellipse cx="24" cy="24" rx="8" ry="19"/><path d="M5 24h38M8 14h32M8 34h32"/></svg>'
            '<div class="line" style="left:220px;top:1446px;width:260px;height:5px"></div>')


def s_stat(d):
    return (f'<div class="photo"></div><div class="vig"></div><div class="bigflag flag">{d.get("emoji","⛽")}</div>'
            f'<div class="txt t"><div class="flag" style="font-size:84px">{d.get("emoji","⛽")}</div>'
            f'<div class="rank" style="margin-top:14px">{esc(d.get("label"))}</div>'
            f'<div class="nm">{esc(d["name"])}</div><div class="val">{esc(d["wert"])}</div>'
            f'<div class="unit">{esc(d.get("einheit"))}</div><div class="note">{esc(d.get("note"))}</div></div>')


def _blk(d, cls, top):
    return (f'<div class="bigflag flag" style="top:{top+10}px">{d.get("emoji","")}</div>'
            f'<div class="txt blk {cls}"><div class="fl flag">{d.get("emoji","")}</div>'
            f'<div class="rank">{esc(d.get("label"))}</div><div class="nm">{esc(d["name"])}</div>'
            f'<div class="val">{esc(d["wert"])}</div><div class="unit">{esc(d.get("einheit"))}</div></div>')


def s_compare(d):
    return ('<div class="photo cold"></div><div class="photo"></div><div class="vig"></div>'
            + _blk(d["a"], "b1", 290)
            + '<div class="line" style="left:78px;right:78px;top:925px;width:924px"></div>'
            + _blk(d["b"], "b2", 960)
            + f'<div class="txt foot">{esc(d.get("foot"))}</div>')


def s_list(d):
    rows = d["zeilen"][:4]
    n, step = len(rows), (210 if len(rows) == 4 else 250)
    out = f'<img class="map" src="{{MAP}}"><h1 class="txt">{gold(d["titel"])}</h1>'
    for i, r in enumerate(rows):
        top = 640 + i * step
        wert = f'<div class="v">{esc(r["wert"])}</div>' if r.get("wert") else ""
        namecls = "n" if r.get("wert") else "n big2"
        out += (f'<div class="row" style="top:{top}px"><div class="fl flag">{r.get("emoji","•")}</div>'
                f'<div><div class="{namecls}">{esc(r["name"])}</div>{wert}</div></div>')
        if i < n - 1:
            out += f'<div class="line sep" style="top:{top+step-35}px"></div>'
    out += (f'<div class="foot"><svg width="52" height="68" viewBox="0 0 40 52"><path fill="none" stroke="#f5b22f" '
            f'stroke-width="3" d="M20 3C20 3 4 22 4 34a16 16 0 0 0 32 0C36 22 20 3 20 3Z"/></svg>{esc(d.get("foot"))}</div>')
    return out.replace('class="foot"', f'class="foot" style="top:{640+(n-1)*step+215}px"')


def s_points(d):
    cols = "".join(f'<div class="col">{icon(p.get("icon"))}<div>{esc(p["text"])}</div></div>' for p in d["punkte"][:3])
    return f'<h1 class="txt">{gold(d["titel"])}</h1><img class="map" src="{{MAP}}"><div class="cols">{cols}</div>'


BARRELS = ('<svg class="barrels" viewBox="0 0 1080 420"><defs><linearGradient id="bl" x1="0" x2="1"><stop offset="0" stop-color="#0b0f12"/>'
           '<stop offset=".45" stop-color="#2a3238"/><stop offset="1" stop-color="#05080a"/></linearGradient></defs>'
           '<g><rect x="130" y="60" width="400" height="330" rx="30" fill="url(#bl)"/><rect x="130" y="110" width="400" height="12" fill="#06090b"/>'
           '<rect x="130" y="320" width="400" height="12" fill="#06090b"/><ellipse cx="330" cy="62" rx="200" ry="26" fill="#1b2227" stroke="#f5b22f" stroke-width="3"/>'
           '<path d="M330 150c0 0-52 62-52 98a52 52 0 0 0 104 0c0-36-52-98-52-98z" fill="url(#gd)"/></g>'
           '<g><rect x="560" y="150" width="270" height="240" rx="24" fill="url(#bl)"/><rect x="560" y="190" width="270" height="9" fill="#06090b"/>'
           '<rect x="560" y="340" width="270" height="9" fill="#06090b"/><ellipse cx="695" cy="152" rx="135" ry="20" fill="#1b2227" stroke="#f5b22f" stroke-width="3"/>'
           '<path d="M695 225c0 0-30 36-30 57a30 30 0 0 0 60 0c0-21-30-57-30-57z" fill="url(#gd)"/></g>'
           '<g><rect x="850" y="210" width="190" height="180" rx="20" fill="url(#bl)"/><ellipse cx="945" cy="212" rx="95" ry="15" fill="#1b2227" stroke="#f5b22f" stroke-width="3"/>'
           '<path d="M945 262c0 0-22 26-22 41a22 22 0 0 0 44 0c0-15-22-41-22-41z" fill="url(#gd)"/></g></svg>')


def s_cta(d):
    if d.get("stil") == "ruhig":
        # Ruhiger Abschluss (jedes zweite Reel): Kernaussage statt Frage, kein Folge-Button.
        hint = d.get("hinweis", "Täglich das Ölpreis-Update")
        return ('<div class="photo"></div><div class="vig"></div>'
                f'<h1 class="txt">{gold(d["titel"])}</h1>{BARRELS}'
                f'<div class="txt calm"><span class="dot"></span>@oil_preis_daily<span class="sepd">•</span>{esc(hint)}</div>'
                f'<div class="txt src">{esc(d.get("quelle"))}</div>')
    return ('<div class="photo"></div><div class="vig"></div>'
            f'<h1 class="txt">{gold(d["titel"])}</h1>{BARRELS}'
            '<div class="txt cmt"><svg width="86" height="86" viewBox="0 0 48 48" fill="none" stroke="#f5b22f" stroke-width="2.6" stroke-linejoin="round">'
            '<path d="M6 10h36v24H22l-10 8v-8H6z"/><circle cx="16" cy="22" r="1.6" fill="#f5b22f"/><circle cx="24" cy="22" r="1.6" fill="#f5b22f"/>'
            f'<circle cx="32" cy="22" r="1.6" fill="#f5b22f"/></svg>{esc(d.get("kommentar","Schreib es in die Kommentare!"))}</div>'
            '<div class="btn"><svg width="80" height="80" viewBox="0 0 48 48" fill="none" stroke="#0a1218" stroke-width="3.2" stroke-linecap="round">'
            '<circle cx="20" cy="15" r="8"/><path d="M5 42c1-10 7-15 15-15s12 4 13 9"/><path d="M38 20v12M32 26h12"/></svg>Folge für das tägliche<br>Ölpreis-Update.</div>'
            f'<div class="txt src">{esc(d.get("quelle"))}</div>')


def cover_data(spec):
    """Daten für das Profil-Vorschaubild. Optional in der Spec unter "cover": {titel, emoji, zahl, einheit}."""
    c = dict(spec.get("cover") or {})
    hook = spec["slides"][0]
    c.setdefault("titel", hook.get("titel") or spec.get("titel", ""))
    first = next((x for x in spec["slides"] if x["typ"] in ("stat", "compare")), None)
    if first:
        src = first["a"] if first["typ"] == "compare" else first
        c.setdefault("emoji", src.get("emoji", "🛢️"))
        c.setdefault("zahl", src.get("wert", ""))
        c.setdefault("einheit", src.get("einheit", ""))
    c.setdefault("emoji", "🛢️")
    return c


def s_cover(d):
    n = len(re.sub(r"\*", "", d["titel"]))
    size = 124 if n <= 30 else 108 if n <= 46 else 92
    zahl = (f'<div class="cz{" long" if len(d["zahl"]) > 8 else ""}">{esc(d["zahl"])}</div><div class="ce">{esc(d.get("einheit"))}</div>' if d.get("zahl") else "")
    return ('<div class="photo"></div><div class="vig"></div>'
            '<div class="txt brand"><svg width="46" height="60" viewBox="0 0 40 52"><path fill="#f5b22f" d="M20 3C20 3 4 22 4 34a16 16 0 0 0 32 0C36 22 20 3 20 3Z"/></svg>ÖLPREIS DAILY</div>'
            f'<h1 class="txt ct" style="font-size:{size}px">{gold(d["titel"])}</h1>'
            f'<div class="txt cbox"><div class="flag cf">{d["emoji"]}</div><div>{zahl}</div></div>')


TYPES = {"hook": s_hook, "stat": s_stat, "compare": s_compare, "list": s_list, "points": s_points, "cta": s_cta}

CSS = r'''
@font-face{font-family:'Poppins';src:url({A}/fonts/Poppins-Bold.ttf);font-weight:100 900}
@font-face{font-family:'Inter';src:url({A}/fonts/Inter-Regular.otf);font-weight:100 450}
@font-face{font-family:'Inter';src:url({A}/fonts/Inter-Medium.otf);font-weight:451 599}
@font-face{font-family:'Inter';src:url({A}/fonts/Inter-Bold.otf);font-weight:600 900}
*{box-sizing:border-box;margin:0;padding:0}
:root{--gold:#f5b22f;--bg:#000c13;--white:#fefefe;--mut:#d3dce1}
html,body{width:1080px;height:1920px;background:var(--bg);font-family:'Inter',sans-serif;color:var(--white);overflow:hidden}
.slide{position:absolute;inset:0;overflow:hidden;display:none;background:radial-gradient(900px 700px at 80% 0%,#07202c 0%,#000c13 70%)}
.g{color:var(--gold)}
h1,.big{font-family:'Poppins',sans-serif;font-weight:700}
.flag{font-family:'Noto Color Emoji';line-height:1}
.photo{position:absolute;left:0;right:0;bottom:0;background:url({A}/header_photo.png) center/cover;
 filter:grayscale(1) sepia(1) saturate(3.2) hue-rotate(-14deg) brightness(.82) contrast(1.25);
 -webkit-mask-image:linear-gradient(180deg,transparent 0,#000 38%);mask-image:linear-gradient(180deg,transparent 0,#000 38%)}
.photo.cold{filter:grayscale(1) sepia(1) saturate(1.6) hue-rotate(150deg) brightness(.7) contrast(1.2)}
.vig{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,12,19,.55) 0,rgba(0,12,19,0) 30%,rgba(0,12,19,0) 70%,rgba(0,12,19,.7) 100%)}
.txt{position:absolute;left:78px;right:78px;text-shadow:0 3px 14px rgba(0,0,0,.65)}
.line{position:absolute;height:4px;background:var(--gold);border-radius:2px}
.map{position:absolute;left:-60px;width:1200px}
.s-hook .photo{height:1050px}.s-hook h1{font-size:98px;line-height:1.08;top:300px}
.s-hook .sub{top:700px;font:500 54px/1.25 'Inter';color:var(--white)}
.s-stat .photo{height:860px}
.rank{font:700 58px 'Poppins';color:var(--gold)}
.s-stat .t{top:330px}
.s-stat .bigflag{position:absolute;right:50px;top:330px;font-size:270px;transform:rotate(-6deg);filter:drop-shadow(0 8px 14px rgba(0,0,0,.6))}
.s-stat .nm{font:700 150px/1 'Poppins';margin-top:6px}
.s-stat .val{font:700 158px/1 'Poppins';color:var(--gold);margin-top:34px}
.s-stat .unit{font:600 62px 'Inter';margin-top:16px}
.s-stat .note{font:400 40px 'Inter';color:var(--mut);margin-top:12px}
.s-compare .photo{height:900px;opacity:.38}
.s-compare .photo.cold{top:150px;bottom:auto;height:700px;opacity:.5;-webkit-mask-image:linear-gradient(180deg,transparent 0,#000 40%,transparent 100%);mask-image:linear-gradient(180deg,transparent 0,#000 40%,transparent 100%)}
.blk .fl{font-size:84px}.blk .rank{font-size:54px;margin-top:10px}
.blk .nm{font:700 92px/1.05 'Poppins';margin-top:4px}
.blk .val{font:700 128px/1 'Poppins';color:var(--gold);margin-top:22px}
.blk .unit{font:600 50px 'Inter';margin-top:10px}
.s-compare .b1{top:290px}.s-compare .b2{top:960px}
.s-compare .bigflag{position:absolute;right:50px;font-size:190px;transform:rotate(-5deg);filter:drop-shadow(0 8px 14px rgba(0,0,0,.6))}
.s-compare .foot{top:1500px;font:500 42px/1.3 'Inter'}
.s-list .map{top:700px;opacity:.55;-webkit-mask-image:radial-gradient(closest-side,#000 55%,transparent 100%);mask-image:radial-gradient(closest-side,#000 55%,transparent 100%)}
.s-list h1{font-size:82px;line-height:1.1;top:300px}
.row{position:absolute;left:78px;right:78px;display:flex;align-items:center;gap:36px}
.row .fl{font-size:104px;width:150px;text-align:center}
.row .n{font:600 52px/1.15 'Inter'}.row .n.big2{font:600 58px/1.2 'Inter'}
.row .v{font:700 76px/1.05 'Poppins';color:var(--gold)}
.s-list .sep{left:78px;width:640px;height:3px;background:rgba(245,178,47,.7)}
.s-list .foot{position:absolute;left:78px;display:flex;align-items:center;gap:22px;font:400 38px 'Inter';color:var(--mut)}
.s-points h1{font-size:80px;line-height:1.1;top:300px}
.s-points .map{top:680px;opacity:.95;-webkit-mask-image:radial-gradient(closest-side,#000 62%,transparent 100%);mask-image:radial-gradient(closest-side,#000 62%,transparent 100%)}
.cols{position:absolute;left:60px;right:60px;top:1330px;display:flex}
.col{flex:1;text-align:center;padding:0 16px;border-left:3px solid rgba(245,178,47,.55)}
.col:first-child{border-left:none}
.col svg{width:112px;height:112px;margin:0 auto 16px;display:block}
.col div{font:600 33px/1.25 'Inter'}
.s-cta .photo{height:760px;opacity:.5}
.s-cta h1{font-size:90px;line-height:1.1;top:300px}
.s-cta .barrels{position:absolute;left:0;right:0;top:830px;height:420px}
.cmt{top:1290px;display:flex;align-items:center;gap:24px;font:700 48px 'Poppins'}
.btn{position:absolute;left:78px;right:78px;top:1390px;height:150px;border-radius:30px;background:var(--gold);color:#0a1218;display:flex;align-items:center;gap:30px;padding:0 44px;font:700 46px/1.2 'Poppins'}
.calm{top:1400px;left:78px;right:78px;display:flex;align-items:center;gap:18px;font:600 36px 'Inter';color:var(--gold)}
.calm .dot{width:14px;height:14px;border-radius:50%;background:var(--gold);flex:none}.calm .sepd{opacity:.6}
.src{left:78px;right:78px;top:1580px;font:400 29px/1.35 'Inter';color:var(--mut)}
/* Profil-Vorschaubild: wichtiger Inhalt liegt in der Mitte (Raster zeigt ca. 3:4, Reels-Tab 4:5) */
.s-cover{display:block;opacity:1}
.s-cover .photo{height:1100px}
.s-cover .brand{top:340px;display:flex;align-items:center;gap:18px;font:700 40px 'Poppins';color:var(--gold);letter-spacing:3px}
.s-cover .ct{top:430px;line-height:1.06}
.s-cover .cbox{top:1120px;display:flex;align-items:center;gap:34px;padding:34px 44px;border-radius:36px;
 background:rgba(0,12,19,.82);border:3px solid var(--gold);text-shadow:none}
.s-cover .cf{font-size:150px}
.s-cover .cz{font:700 112px/1 'Poppins';color:var(--gold);white-space:nowrap}
.s-cover .cz.long{font-size:84px}
.s-cover .ce{font:600 44px/1.2 'Inter';margin-top:10px}
'''

JS = r'''
const TL=__TL__;
const SEL='h1,.sub,.rank,.nm,.val,.unit,.note,.fl,.bigflag,.line,.row,.foot,.col,.barrels,.cmt,.btn,.src,.blk>*,.t>*';
const slides=[...document.querySelectorAll('.slide')];
const E=x=>1-Math.pow(1-Math.min(1,Math.max(0,x)),3);
const items=slides.map(sl=>{const els=[...sl.querySelectorAll(SEL)].filter(e=>!e.closest('.photo'));
  return els.map(e=>({e,cnt:e.matches('.val,.v')?e.textContent:null}));});
function fmt(txt,p){const m=txt.match(/^([\d,]+)(.*)$/);if(!m)return txt;const dec=(m[1].split(',')[1]||'').length;
  const v=parseFloat(m[1].replace(',','.'))*p;return v.toFixed(dec).replace('.',',')+m[2];}
window.seek=function(t){
 slides.forEach((sl,i)=>{const [a,b]=TL[i];const u=t-a;const d0=b-a;
  const inn=E(u/0.2),out=1-E((u-(d0-0.2))/0.25);
  const vis=(t>=a-0.001&&t<b+0.3);
  sl.style.display=vis?'block':'none'; if(!vis)return;
  sl.style.opacity=Math.min(inn,i===slides.length-1?1:out);
  sl.querySelectorAll('.photo,.map').forEach(p=>{p.style.transform='scale('+(1+0.07*Math.min(1,u/d0))+')';p.style.transformOrigin='50% 60%'});
  items[i].forEach((o,k)=>{const d=0.04+Math.min(k,8)*0.11;const p=E((u-d)/0.5);
    o.e.style.opacity=p;o.e.style.transform=(o.e.classList.contains('bigflag')?'rotate(-6deg) ':'')+'translateY('+(1-p)*45+'px)';
    if(o.cnt!==null){o.e.textContent=fmt(o.cnt,E((u-d)/1.1));}});
 });
};
const q=new URLSearchParams(location.search).get('s');
if(q){slides.forEach(x=>x.style.display='none');const el=document.getElementById('s'+q);el.style.display='block';el.style.opacity=1;}
'''


def build_html(spec, TL, path):
    A = (ROOT / "assets").as_uri()
    body = ""
    for i, s in enumerate(spec["slides"]):
        t = s["typ"]
        body += f'<section class="slide s-{t}" id="s{i+1}">{TYPES[t](s)}</section>\n'
    body = body.replace("{MAP}", f"{A}/map_crop.png")
    doc = ('<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><style>' + CSS.replace("{A}", A) + '</style></head><body>'
           '<svg width="0" height="0" style="position:absolute"><defs><linearGradient id="gd" x1="0" y1="0" x2="1" y2="1">'
           '<stop offset="0" stop-color="#ffd27a"/><stop offset="1" stop-color="#f5a211"/></linearGradient></defs></svg>'
           + body + '<script>' + JS.replace("__TL__", json.dumps(TL)) + '</script></body></html>')
    path.write_text(doc, encoding="utf-8")


# ---------- Ton ----------
# Stimmen-Reihenfolge: ElevenLabs (beste Qualität, Gratis-Kontingent begrenzt) -> Edge-TTS (kostenlos, Microsoft-Stimmen)
# -> Piper (kostenlos, offline, Open Source). Pro Reel wird EINE Stimme für alle Sätze verwendet (keine Mischung).
# Erzwingen: TTS_PROVIDER=edge  oder  TTS_PROVIDER=elevenlabs,edge,piper (Reihenfolge)
EDGE_VOICE = os.environ.get("EDGE_VOICE") or "de-DE-ChristophNeural"
PIPER_VOICE = os.environ.get("PIPER_VOICE") or "de_DE-thorsten-medium"
PROVIDERS = [x.strip() for x in (os.environ.get("TTS_PROVIDER") or "elevenlabs,edge,piper").split(",") if x.strip()]


class TTSError(Exception):
    pass


def tts_eleven(text, prev, nxt, out):
    token = os.environ.get("ELEVENLABS_API_KEY")
    if not token:
        raise TTSError("ELEVENLABS_API_KEY fehlt")
    body = {"text": text, "model_id": MODEL}
    if prev:
        body["previous_text"] = prev
    if nxt:
        body["next_text"] = nxt
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}?output_format=mp3_44100_128",
                                 data=json.dumps(body).encode(), method="POST",
                                 headers={"xi-api-key": token, "Content-Type": "application/json", "Accept": "audio/mpeg"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            out.write_bytes(r.read())
    except urllib.error.HTTPError as e:
        raise TTSError(f"ElevenLabs-Fehler {e.code}: {e.read().decode(errors='replace')[:300]}")
    except Exception as e:
        raise TTSError(f"ElevenLabs nicht erreichbar: {e}")


def tts_edge(text, prev, nxt, out):
    try:
        subprocess.run([sys.executable, "-m", "edge_tts", "--voice", EDGE_VOICE, "--text", text, "--write-media", str(out)],
                       check=True, capture_output=True, text=True, timeout=120)
    except Exception as e:
        raise TTSError(f"Edge-TTS fehlgeschlagen: {getattr(e, 'stderr', None) or e}"[:300])
    if not out.exists() or out.stat().st_size < 1000:
        raise TTSError("Edge-TTS lieferte keine Audiodatei")


def tts_piper(text, prev, nxt, out):
    d = ROOT / "_work" / "piper"; d.mkdir(parents=True, exist_ok=True)
    try:
        if not (d / f"{PIPER_VOICE}.onnx").exists():
            subprocess.run([sys.executable, "-m", "piper.download_voices", PIPER_VOICE, "--download-dir", str(d)],
                           check=True, capture_output=True, text=True, timeout=300)
        wav = out.with_suffix(".piper.wav")
        subprocess.run([sys.executable, "-m", "piper", "-m", PIPER_VOICE, "--data-dir", str(d), "-f", str(wav)],
                       input=text, check=True, capture_output=True, text=True, timeout=180)
        sh("ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-q:a", "2", out)
    except Exception as e:
        raise TTSError(f"Piper fehlgeschlagen: {getattr(e, 'stderr', None) or e}"[:300])


TTS_FUNCS = {"elevenlabs": tts_eleven, "edge": tts_edge, "piper": tts_piper}


def tts(provider, text, prev, nxt, out, cache):
    voice = {"elevenlabs": f"{VOICE}|{MODEL}", "edge": EDGE_VOICE, "piper": PIPER_VOICE}[provider]
    key = hashlib.sha1(f"{provider}|{voice}|{text}".encode()).hexdigest()[:12]
    c = cache / f"{key}.mp3"
    if c.exists():
        shutil.copy(c, out)
        return
    TTS_FUNCS[provider](text, prev, nxt, out)
    shutil.copy(out, c)


def synth_all(sents, work, cache):
    """Vertont alle Sätze mit der ersten funktionierenden Stimme. Gibt (Dateien, Anbieter) zurück."""
    fehler = []
    for provider in PROVIDERS:
        try:
            raw = []
            for i, t in enumerate(sents):
                p = work / f"seg{i}.mp3"
                tts(provider, t, sents[i - 1] if i else "", sents[i + 1] if i + 1 < len(sents) else "", p, cache)
                raw.append(p)
            print(f"Stimme: {provider}" + (f" (Ersatz, weil: {fehler[-1]})" if fehler else ""))
            return raw, provider, fehler
        except TTSError as e:
            print(f"WARNUNG {provider}: {e}", file=sys.stderr)
            fehler.append(f"{provider}: {e}")
    sys.exit("Keine Stimme verfügbar:\n" + "\n".join(fehler))


STIMME = ""


def make_audio(spec, work, fake):
    sents = [s["sprech"] for s in spec["slides"]]
    raw = []
    cache = work / "cache"; cache.mkdir(exist_ok=True)
    if fake:
        for i, t in enumerate(sents):
            p = work / f"seg{i}.mp3"
            sh("ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
               "-t", f"{max(1.2, len(t.split()) * 0.36):.2f}", "-q:a", "5", p)
            raw.append(p)
        provider, fehler = "fake", []
    else:
        raw, provider, fehler = synth_all(sents, work, cache)
    global STIMME
    STIMME = provider + (" | Ersatzstimme, weil: " + " ; ".join(fehler) if fehler else "")
    trimmed = []
    for i, p in enumerate(raw):
        t = work / f"trim{i}.wav"
        sh("ffmpeg", "-y", "-loglevel", "error", "-i", p, "-filter:a", "anull" if fake else TRIM, "-ar", "44100", "-ac", "1", t)
        trimmed.append(t)
    natural = sum(dur(p) for p in trimmed) + GAP * (len(raw) - 1) + LEAD + TAIL
    ziel = float(spec.get("ziel_sekunden", 27))
    f = min(1.2, max(1.0, natural / ziel))
    print(f"Sprechdauer natürlich {natural:.1f}s, Ziel {ziel:.0f}s -> Tempo x{f:.2f}")
    segs, durs = [], []
    for i, p in enumerate(trimmed):
        w = work / f"seg{i}.wav"
        sh("ffmpeg", "-y", "-loglevel", "error", "-i", p, "-filter:a", f"atempo={f:.4f}", "-ar", "44100", "-ac", "1", w)
        segs.append(w); durs.append(dur(w))
    gap = work / "gap.wav"; lead = work / "lead.wav"
    for g, t in ((gap, GAP), (lead, LEAD)):
        sh("ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", t, g)
    lst = work / "list.txt"
    parts = [lead]
    for i, w in enumerate(segs):
        parts.append(w)
        if i < len(segs) - 1:
            parts.append(gap)
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    joined = work / "joined.wav"
    sh("ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined)
    # Slide-Grenzen: Mitte der Pausen
    starts, t = [], LEAD
    for d in durs:
        starts.append(t); t += d + GAP
    ends = [starts[i + 1] - GAP / 2 for i in range(len(starts) - 1)] + [starts[-1] + durs[-1] + TAIL]
    TL = [[0 if i == 0 else round(starts[i] - GAP / 2, 3), round(ends[i], 3)] for i in range(len(starts))]
    return joined, TL, ends[-1]


# ---------- Video ----------
def chrome():
    return next((shutil.which(c) for c in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser") if shutil.which(c)), None)


def render(htmlp, total, frames, storyboard):
    from playwright.sync_api import sync_playwright
    shutil.rmtree(frames, ignore_errors=True); frames.mkdir(parents=True)
    with sync_playwright() as p:
        c = chrome()
        b = p.chromium.launch(executable_path=c, args=["--no-sandbox"]) if c else p.chromium.launch(args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto(htmlp.as_uri()); pg.wait_for_timeout(700)
        n = int(total * FPS)
        for i in range(n):
            pg.evaluate(f"seek({i / FPS})")
            pg.screenshot(path=str(frames / f"f{i:04d}.jpg"), type="jpeg", quality=93)
        # Storyboard: je Slide ein Standbild kurz vor Ende
        shots = []
        for k, (a, bnd) in enumerate(json.loads(pg.evaluate("JSON.stringify(TL)"))):
            pg.evaluate(f"seek({a + (bnd - a) * 0.85})"); f = frames.parent / f"sb{k}.png"
            pg.screenshot(path=str(f)); shots.append(f)
        b.close()
    from PIL import Image
    ims = [Image.open(f).convert("RGB").resize((540, 960), Image.LANCZOS) for f in shots]
    sheet = Image.new("RGB", (540 * 3 + 40, 960 * 2 + 30), (255, 255, 255))
    for i, im in enumerate(ims):
        sheet.paste(im, (10 + (i % 3) * 550, 10 + (i // 3) * 970))
    sheet.save(storyboard, quality=88)


def build_cover(spec, work, outfile):
    """Rendert das Profil-Vorschaubild (1080x1920 JPEG) für cover_url der Instagram-API."""
    from playwright.sync_api import sync_playwright
    A = (ROOT / "assets").as_uri()
    doc = ('<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><style>' + CSS.replace("{A}", A) + '</style></head><body>'
           f'<section class="slide s-cover">{s_cover(cover_data(spec))}</section></body></html>')
    h = work / "cover.html"; h.write_text(doc, encoding="utf-8")
    with sync_playwright() as p:
        c = chrome()
        b = p.chromium.launch(executable_path=c, args=["--no-sandbox"]) if c else p.chromium.launch(args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto(h.as_uri()); pg.wait_for_timeout(800)
        pg.screenshot(path=str(outfile), type="jpeg", quality=92)
        b.close()
    print("Cover:", outfile)


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    fake = "--fake-audio" in sys.argv
    if not a:
        sys.exit(__doc__)
    slug = a[0]
    spec = json.loads((ROOT / "reels" / "specs" / f"{slug}.json").read_text(encoding="utf-8"))
    assert len(spec["slides"]) == 6, "Genau 6 Slides erwartet"
    work = ROOT / "_work" / slug; work.mkdir(parents=True, exist_ok=True)
    out = ROOT / "out" / "reels"; out.mkdir(parents=True, exist_ok=True)
    if "--tts-test" in sys.argv:
        prov = sys.argv[sys.argv.index("--tts-test") + 1]
        t = work / f"test_{prov}.mp3"
        TTS_FUNCS[prov]("Warum ist die Straße von Hormus so wichtig? Hier fließen täglich rund zwanzig Millionen Barrel Öl durch.", "", "", t)
        print(f"OK {prov}: {t.stat().st_size} Bytes, {dur(t):.1f} s")
        return
    if "--cover-only" in sys.argv:
        build_cover(spec, work, out / f"{slug}_cover.jpg")
        return
    audio, TL, total = make_audio(spec, work, fake)
    print("Timeline:", TL, "Gesamt:", round(total, 2))
    htmlp = work / "slides.html"; build_html(spec, TL, htmlp)
    render(htmlp, total, work / "frames", out / f"{slug}_storyboard.jpg")
    silent = work / "silent.mp4"
    sh("ffmpeg", "-y", "-loglevel", "error", "-framerate", FPS, "-i", work / "frames" / "f%04d.jpg", "-c:v", "libx264",
       "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-r", FPS, silent)
    af = f"loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=out:st={total-0.5:.2f}:d=0.5,apad"
    sh("ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", audio, "-filter_complex", f"[1:a]{af}[a]", "-map", "0:v", "-map", "[a]",
       "-t", f"{total:.2f}", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", out / f"{slug}.mp4")
    build_cover(spec, work, out / f"{slug}_cover.jpg")
    (out / f"{slug}_stimme.txt").write_text(STIMME + "\n", encoding="utf-8")
    (out / f"{slug}.txt").write_text(spec["caption"].strip() + "\n", encoding="utf-8")
    print("fertig:", out / f"{slug}.mp4")


if __name__ == "__main__":
    main()
