#!/usr/bin/env python3
"""Wöchentliche Marktbeobachtung über Apify (Hashtags + Konkurrenz-Profile).
Nur Standardbibliothek. Umgebungsvariable: APIFY_TOKEN. Konfiguration: watchlist.json.
Schreibt watch/<Datum>_hashtags.json, watch/<Datum>_profile.json und watch/<Datum>_uebersicht.md.
Aufruf: python apify_watch.py [--dry-run]"""
import datetime, json, os, sys, urllib.error, urllib.parse, urllib.request
from collections import Counter

API = "https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items"
HASHTAG_ACTOR = "apify~instagram-hashtag-scraper"
PROFILE_ACTOR = "apify~instagram-profile-scraper"


def run(actor, payload, token):
    req = urllib.request.Request(API.format(actor=actor) + "?" + urllib.parse.urlencode({"token": token}),
                                 data=json.dumps(payload).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=290) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"Apify-Fehler {e.code} bei {actor}: {e.read().decode(errors='replace')[:400]}")


def num(x):
    return x if isinstance(x, (int, float)) else 0


def main():
    cfg = json.load(open("watchlist.json", encoding="utf-8"))
    hashtags, profile = cfg["hashtags"], cfg["profile"]
    limit = int(cfg.get("beitraege_pro_hashtag", 25))
    est = len(hashtags) * limit + len(profile)
    print(f"{len(hashtags)} Hashtags x {limit} Beiträge + {len(profile)} Profile = ca. {est} Ergebnisse (ca. {est * 2.6 / 1000:.2f} $ im Free-Tarif)")
    if "--dry-run" in sys.argv:
        return
    token = os.environ.get("APIFY_TOKEN") or sys.exit("APIFY_TOKEN fehlt.")
    day = datetime.date.today().isoformat()
    os.makedirs("watch", exist_ok=True)

    posts = run(HASHTAG_ACTOR, {"hashtags": hashtags, "resultsType": "posts", "resultsLimit": limit}, token)
    json.dump(posts, open(f"watch/{day}_hashtags.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    profs = run(PROFILE_ACTOR, {"usernames": profile}, token)
    json.dump(profs, open(f"watch/{day}_profile.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # Übersicht (defensiv: Feldnamen können je nach Actor-Version abweichen; die Rohdaten bleiben gespeichert)
    L = [f"# Wochenübersicht {day}", "", f"Beiträge gelesen: {len(posts)} | Profile gelesen: {len(profs)}", ""]
    tags = Counter()
    likes, cnt = Counter(), Counter()
    for p in posts:
        for h in p.get("hashtags") or []:
            tags[str(h).lower()] += 1
        src = p.get("inputUrl") or p.get("hashtag") or ""
        likes[src] += num(p.get("likesCount"))
        cnt[src] += 1
    L += ["## Häufigste Begleit-Hashtags in den gefundenen Beiträgen", ""]
    L += [f"- #{t}: {n}x" for t, n in tags.most_common(20)] or ["- (keine Hashtag-Felder in den Daten)"]
    L += ["", "## Durchschnittliche Likes pro gesuchtem Hashtag", ""]
    L += [f"- {s}: {likes[s] / cnt[s]:.0f} Likes (n={cnt[s]})" for s in cnt if s] or ["- (keine Like-Zahlen verfügbar)"]
    L += ["", "## Profile", ""]
    for p in profs:
        L.append(f"- @{p.get('username')}: {p.get('followersCount', '?')} Follower, {p.get('postsCount', '?')} Beiträge")
    open(f"watch/{day}_uebersicht.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
