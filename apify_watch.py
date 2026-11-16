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
    good = [p for p in posts if not p.get("error")]
    L = [f"# Wochenübersicht {day}", "", f"Hashtag-Beiträge: {len(good)} brauchbar von {len(posts)} Zeilen | Profile: {len(profs)}", ""]
    L += ["## Hashtags", ""]
    if not good:
        L += ["Der Hashtag-Scraper lieferte keine Beiträge (Fehler: " + ", ".join(sorted({str(p.get('error')) for p in posts})) + ").",
              "Mögliche Gründe: Instagram blockiert Hashtag-Seiten ohne Login, oder das Free-Limit greift. Rohdaten prüfen."]
    else:
        tags, likes, cnt = Counter(), Counter(), Counter()
        for p in good:
            for h in p.get("hashtags") or []:
                tags[str(h).lower()] += 1
            src = p.get("inputUrl") or ""
            likes[src] += num(p.get("likesCount"))
            cnt[src] += 1
        L += [f"- #{t}: {n}x" for t, n in tags.most_common(20)]
        L += ["", "Durchschnittliche Likes je gesuchtem Hashtag:"]
        L += [f"- {s_.rsplit('/', 1)[-1]}: {likes[s_] / cnt[s_]:.0f} Likes (n={cnt[s_]})" for s_ in cnt if s_]
    L += ["", "## Konkurrenz-Profile (letzte Beiträge)", "",
          "| Profil | Follower | Ø Likes | Ø Kommentare | Interaktion | Beiträge/Woche | Formate |", "|---|---|---|---|---|---|---|"]
    for p in sorted(profs, key=lambda x: -num(x.get("followersCount"))):
        ps = p.get("latestPosts") or []
        lk = [q["likesCount"] for q in ps if isinstance(q.get("likesCount"), int) and q["likesCount"] >= 0]
        cm = [num(q.get("commentsCount")) for q in ps]
        ts = sorted(q["timestamp"][:10] for q in ps if q.get("timestamp"))
        days = max((datetime.date.fromisoformat(ts[-1]) - datetime.date.fromisoformat(ts[0])).days + 1, 1) if len(ts) > 1 else 0
        fol = num(p.get("followersCount"))
        al = sum(lk) / len(lk) if lk else 0
        ac = sum(cm) / len(cm) if cm else 0
        rate = f"{(al + ac) / fol * 100:.2f} %" if fol else "?"
        wk = f"{len(ps) / days * 7:.1f}" if days else "?"
        fm = ", ".join(f"{k} {v}" for k, v in Counter(q.get("type") for q in ps).most_common())
        L.append(f"| @{p.get('username')} | {format(fol, ',').replace(',', '.')} | {al:.0f} | {ac:.0f} | {rate} | {wk} | {fm} |")
    open(f"watch/{day}_uebersicht.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
