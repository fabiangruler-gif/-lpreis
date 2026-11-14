#!/usr/bin/env python3
"""Veröffentlicht ein JPEG als Instagram-Story (Instagram API mit Instagram-Login).
Nur Standardbibliothek. Umgebungsvariablen: IG_TOKEN (Pflicht), IG_USER_ID (optional), IG_API_VERSION (optional).
Aufruf: python publish_story.py --image-url https://.../story.jpg [--dry-run]"""
import argparse, json, os, sys, time, urllib.error, urllib.parse, urllib.request

VERSION = os.environ.get("IG_API_VERSION", "v27.0")
BASE = f"https://graph.instagram.com/{VERSION}"


def call(method, url, params=None):
    data = urllib.parse.urlencode(params).encode() if params and method == "POST" else None
    if params and method == "GET":
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        sys.exit(f"API-Fehler {e.code} bei {method} {url.split('?')[0]}: {body}")


def wait_for_url(url, tries=12):
    """Meta lädt das Bild selbst herunter – es muss öffentlich erreichbar sein."""
    for i in range(tries):
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=20) as r:
                if r.status == 200:
                    return
        except Exception:
            pass
        time.sleep(5)
    sys.exit(f"Bild-URL nicht öffentlich erreichbar: {url}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image-url", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    token = os.environ.get("IG_TOKEN")
    if not token:
        sys.exit("IG_TOKEN fehlt (Zugriffstoken).")
    if a.dry_run:
        print("DRY RUN – würde ausführen:")
        print(f"  1. POST {BASE}/<IG_ID>/media  media_type=STORIES image_url={a.image_url}")
        print(f"  2. GET  {BASE}/<CONTAINER>?fields=status_code  (bis FINISHED)")
        print(f"  3. POST {BASE}/<IG_ID>/media_publish  creation_id=<CONTAINER>")
        return

    wait_for_url(a.image_url)
    ig_id = os.environ.get("IG_USER_ID") or call("GET", f"{BASE}/me", {"fields": "user_id,username", "access_token": token}).get("user_id")
    if not ig_id:
        sys.exit("Konnte IG_USER_ID nicht ermitteln.")

    cont = call("POST", f"{BASE}/{ig_id}/media", {"media_type": "STORIES", "image_url": a.image_url, "access_token": token})["id"]
    print("Container:", cont)

    for _ in range(30):  # max. ~5 Minuten
        st = call("GET", f"{BASE}/{cont}", {"fields": "status_code", "access_token": token}).get("status_code")
        print("Status:", st)
        if st == "FINISHED":
            break
        if st in ("ERROR", "EXPIRED"):
            sys.exit(f"Container-Status {st} – Story nicht veröffentlicht.")
        time.sleep(10)
    else:
        sys.exit("Timeout beim Warten auf FINISHED.")

    res = call("POST", f"{BASE}/{ig_id}/media_publish", {"creation_id": cont, "access_token": token})
    print("Story veröffentlicht, Media-ID:", res.get("id"))


if __name__ == "__main__":
    main()
