#!/usr/bin/env python3
"""Veröffentlicht ein JPEG als Instagram-Story (Instagram API mit Instagram-Login).
Nur Standardbibliothek. Umgebungsvariablen: IG_TOKEN (Pflicht), IG_USER_ID (Pflicht bei graph.facebook.com), IG_API_HOST und IG_API_VERSION (optional).
Aufruf: python publish_story.py --image-url https://.../story.jpg [--dry-run]"""
import argparse, json, os, sys, time, urllib.error, urllib.parse, urllib.request

VERSION = os.environ.get("IG_API_VERSION", "v27.0")
# graph.instagram.com = Instagram-Login-Token; graph.facebook.com = Unified-Login / Facebook-Login-Token (z. B. Systemnutzer-Token)
HOST = os.environ.get("IG_API_HOST") or ""   # leer = automatisch erkennen
BASE = ""


def call(method, url, params=None, tries=4):
    """API-Aufruf mit Wiederholung bei Netzwerk-/Serverfehlern (5xx, 429). Exit-Code 2 = Token/Konto-Problem."""
    data = urllib.parse.urlencode(params).encode() if params and method == "POST" else None
    if params and method == "GET":
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    for i in range(1, tries + 1):
        req = urllib.request.Request(url, data=data, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            if (e.code >= 500 or e.code == 429) and i < tries:
                print(f"API-Fehler {e.code}, neuer Versuch {i}/{tries - 1} ...", flush=True)
                time.sleep(10 * i)
                continue
            code = 2 if ('"code":190' in body.replace(" ", "") or "OAuthException" in body) else 1
            print(f"API-Fehler {e.code} bei {method} {url.split('?')[0]}: {body}", file=sys.stderr)
            sys.exit(code)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if i < tries:
                print(f"Netzwerkfehler ({e}), neuer Versuch {i}/{tries - 1} ...", flush=True)
                time.sleep(10 * i)
                continue
            sys.exit(f"Netzwerkfehler bei {method} {url.split('?')[0]}: {e}")


def try_get(url, params):
    """Gibt (Daten, Fehlertext) zurück; der Fehlertext von Meta wird im Log gezeigt."""
    for i in range(3):
        try:
            with urllib.request.urlopen(url + "?" + urllib.parse.urlencode(params), timeout=30) as r:
                return json.loads(r.read().decode()), None
        except urllib.error.HTTPError as e:
            err = f"{e.code}: {e.read().decode(errors='replace')[:400]}"
            if e.code < 500 and e.code != 429:
                return None, err
        except Exception as e:
            err = str(e)
        time.sleep(5)
    return None, err


def detect_host(token, ig_id):
    """Findet heraus, zu welchem Host das Token gehört (Instagram-Login- oder Facebook/Unified-Token)."""
    if ig_id:
        d, e1 = try_get(f"https://graph.facebook.com/{VERSION}/{ig_id}", {"fields": "username", "access_token": token})
        if d and d.get("username"):
            return "graph.facebook.com", ig_id
    else:
        e1 = "keine IG_USER_ID gesetzt"
    d, e2 = try_get(f"https://graph.instagram.com/{VERSION}/me", {"fields": "user_id,username", "access_token": token})
    if d and d.get("user_id"):
        return "graph.instagram.com", d["user_id"]
    print(f"graph.facebook.com: {e1}\ngraph.instagram.com: {e2}", file=sys.stderr)
    print("Token passt weder zu graph.facebook.com noch zu graph.instagram.com "
          "(abgelaufen, falsche Rechte, Konto nicht zugewiesen oder Meta verlangt eine Verifizierung).", file=sys.stderr)
    sys.exit(2)


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
    global HOST, BASE
    ap = argparse.ArgumentParser()
    ap.add_argument("--image-url", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true", help="nur prüfen, ob das Token funktioniert (veröffentlicht nichts)")
    a = ap.parse_args()

    token = os.environ.get("IG_TOKEN")
    if not token:
        sys.exit("IG_TOKEN fehlt (Zugriffstoken).")
    if a.check:
        h, i = detect_host(token, os.environ.get("IG_USER_ID"))
        print(f"Token OK ({h}, Konto-ID {i}).")
        return
    if not a.image_url:
        sys.exit("--image-url fehlt.")
    if a.dry_run:
        BASE_D = f"https://{HOST or '<automatisch erkannt>'}/{VERSION}"
        print("DRY RUN – würde ausführen:")
        print(f"  1. POST {BASE_D}/<IG_ID>/media  media_type=STORIES image_url={a.image_url}")
        print(f"  2. GET  {BASE_D}/<CONTAINER>?fields=status_code  (bis FINISHED)")
        print(f"  3. POST {BASE_D}/<IG_ID>/media_publish  creation_id=<CONTAINER>")
        return

    wait_for_url(a.image_url)
    ig_id = os.environ.get("IG_USER_ID")
    if HOST:
        if not ig_id and HOST == "graph.instagram.com":
            ig_id = call("GET", f"https://{HOST}/{VERSION}/me", {"fields": "user_id,username", "access_token": token}).get("user_id")
    else:
        HOST, ig_id = detect_host(token, ig_id)
    BASE = f"https://{HOST}/{VERSION}"
    print("Host:", HOST, "| Konto-ID:", ig_id)
    if not ig_id:
        sys.exit("IG_USER_ID fehlt.")

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
