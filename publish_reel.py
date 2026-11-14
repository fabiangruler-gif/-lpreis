#!/usr/bin/env python3
"""Veröffentlicht ein Video als Instagram-Reel. Nur Standardbibliothek.
Env: IG_TOKEN, IG_USER_ID. Aufruf: python publish_reel.py --video-url URL --caption-file datei.txt"""
import argparse, json, os, sys, time, urllib.error, urllib.parse, urllib.request

VERSION = os.environ.get("IG_API_VERSION", "v27.0")
BASE = f"https://graph.facebook.com/{VERSION}"


def call(method, url, params=None):
    data = urllib.parse.urlencode(params).encode() if params and method == "POST" else None
    if params and method == "GET":
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"API-Fehler {e.code} bei {method} {url.split('?')[0]}: {e.read().decode(errors='replace')}")


ap = argparse.ArgumentParser()
ap.add_argument("--video-url", required=True)
ap.add_argument("--caption-file", required=True)
a = ap.parse_args()
token, ig_id = os.environ["IG_TOKEN"], os.environ["IG_USER_ID"]
caption = open(a.caption_file, encoding="utf-8").read().strip()

for _ in range(12):
    try:
        with urllib.request.urlopen(urllib.request.Request(a.video_url, method="HEAD"), timeout=20) as r:
            if r.status == 200:
                break
    except Exception:
        time.sleep(5)
else:
    sys.exit("Video-URL nicht öffentlich erreichbar.")

cont = call("POST", f"{BASE}/{ig_id}/media", {"media_type": "REELS", "video_url": a.video_url,
            "caption": caption, "share_to_feed": "true", "access_token": token})["id"]
print("Container:", cont)
for _ in range(60):
    st = call("GET", f"{BASE}/{cont}", {"fields": "status_code,status", "access_token": token})
    print("Status:", st)
    if st.get("status_code") == "FINISHED":
        break
    if st.get("status_code") in ("ERROR", "EXPIRED"):
        sys.exit("Container-Fehler, Reel nicht veröffentlicht.")
    time.sleep(10)
else:
    sys.exit("Timeout.")
res = call("POST", f"{BASE}/{ig_id}/media_publish", {"creation_id": cont, "access_token": token})
print("Reel veröffentlicht, Media-ID:", res.get("id"))
