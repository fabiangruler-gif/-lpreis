#!/usr/bin/env python3
"""Reel-Plan: reels/plan.json verwaltet, welches Reel an welchem Tag veröffentlicht wird.
Nur Standardbibliothek.
  python3 reel_plan.py heute [YYYY-MM-DD]     gibt den Slug aus, wenn für den Tag ein Reel mit Status "bereit" vorliegt
  python3 reel_plan.py status <slug> <status>  setzt den Status (bereit|veröffentlicht|stopp) und passt reels/themen.md an
  python3 reel_plan.py add <datum> <slug> "<Thema>"   trägt ein neues Reel mit Status "bereit" ein
  python3 reel_plan.py liste                   zeigt den Plan
Veröffentlichungstage: Di, Do, Fr, So. Status "stopp" hält ein Reel zurück (zum Prüfen/Korrigieren)."""
import datetime, json, re, sys, zoneinfo

PLAN, THEMEN = "reels/plan.json", "reels/themen.md"
TAGE = {1, 3, 4, 6}  # Mo=0 ... So=6 -> Di, Do, Fr, So
THEMEN_STATUS = {"bereit": "geplant", "veröffentlicht": "veröffentlicht"}


def load():
    return json.load(open(PLAN, encoding="utf-8"))


def save(d):
    json.dump(d, open(PLAN, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    open(PLAN, "a").write("\n")


def themen_status(thema, status):
    """Setzt in reels/themen.md die Status-Zeile des Blocks mit diesem Titel."""
    text = open(THEMEN, encoding="utf-8").read()
    pat = re.compile(r"(?m)^(## " + re.escape(thema) + r"\s*\n)(Status:[^\n]*\n)?")
    if not pat.search(text):
        print(f"Hinweis: Thema '{thema}' nicht in {THEMEN} gefunden.", file=sys.stderr)
        return
    open(THEMEN, "w", encoding="utf-8").write(pat.sub(lambda m: f"{m.group(1)}Status: {status}\n", text, count=1))


def heute(tag=None):
    tag = tag or datetime.datetime.now(zoneinfo.ZoneInfo("Europe/Berlin")).date().isoformat()
    for r in load()["reels"]:
        if r["datum"] == tag:
            if r["status"] == "bereit":
                print(r["slug"])
            else:
                print(f"Reel {r['slug']} für {tag} hat Status '{r['status']}', wird nicht veröffentlicht.", file=sys.stderr)
            return
    print(f"Für {tag} ist kein Reel eingeplant.", file=sys.stderr)


def main():
    a = sys.argv[1:] or ["liste"]
    if a[0] == "heute":
        heute(a[1] if len(a) > 1 else None)
    elif a[0] == "status":
        d = load()
        r = next((x for x in d["reels"] if x["slug"] == a[1]), None) or sys.exit(f"Slug {a[1]} nicht im Plan.")
        r["status"] = a[2]
        save(d)
        if a[2] in THEMEN_STATUS:
            themen_status(r["thema"], THEMEN_STATUS[a[2]])
    elif a[0] == "add":
        datum, slug, thema = a[1], a[2], a[3]
        wd = datetime.date.fromisoformat(datum).weekday()
        if wd not in TAGE:
            sys.exit(f"{datum} ist kein Veröffentlichungstag (Di, Do, Fr, So).")
        d = load()
        d["reels"] = [x for x in d["reels"] if x["datum"] != datum and x["slug"] != slug]
        d["reels"].append({"datum": datum, "slug": slug, "thema": thema, "status": "bereit"})
        d["reels"].sort(key=lambda x: x["datum"])
        save(d)
        themen_status(thema, "geplant")
    else:
        for r in load()["reels"]:
            print(r["datum"], r["status"].ljust(14), r["slug"])


if __name__ == "__main__":
    main()
