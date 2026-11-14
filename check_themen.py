#!/usr/bin/env python3
"""Prüft reels/themen.md: Struktur, doppelte Titel, Status, Länge. Gibt die offenen Themen aus.
Exit-Code 1 bei Fehlern."""
import re, sys

STATUS = {"neu", "in arbeit", "vorschau", "geplant", "veröffentlicht"}
TYPEN = {"reel", "karussell"}
text = open(sys.argv[1] if len(sys.argv) > 1 else "reels/themen.md", encoding="utf-8").read()
liste = text.split("\n---", 1)[1] if "\n---" in text else text
blocks = re.split(r"(?m)^## ", liste)[1:]

fehler, warn, themen, titel_seen = [], [], [], set()
for b in blocks:
    zeilen = b.strip().splitlines()
    titel = zeilen[0].strip()
    status, typ, punkte = "neu", "reel", []
    for z in zeilen[1:]:
        z = z.strip()
        if z.startswith("-") and z[1:].strip().lower().startswith(("status:", "typ:")):
            z = z[1:].strip()
        if z.lower().startswith("status:"):
            status = z.split(":", 1)[1].strip().lower()
        elif z.lower().startswith("typ:"):
            typ = z.split(":", 1)[1].strip().lower()
        elif z.startswith("-") and z[1:].strip():
            punkte.append(z[1:].strip())
    if not titel:
        fehler.append("Block ohne Titel")
        continue
    if titel.lower() in titel_seen:
        fehler.append(f"Doppelter Titel: {titel}")
    titel_seen.add(titel.lower())
    if len(titel) > 70:
        warn.append(f"Titel sehr lang (>70): {titel}")
    if status not in STATUS:
        fehler.append(f"{titel}: unbekannter Status '{status}' (erlaubt: {', '.join(sorted(STATUS))})")
    if typ not in TYPEN:
        fehler.append(f"{titel}: unbekannter Typ '{typ}' (erlaubt: Reel, Karussell)")
    if not punkte:
        warn.append(f"{titel}: keine Stichpunkte, ich recherchiere frei")
    themen.append((titel, status, typ, len(punkte)))

print(f"{len(themen)} Themen gefunden")
for t, s, ty, n in themen:
    print(f"  [{s}] {t} ({ty}, {n} Stichpunkte)")
for w in warn:
    print("Hinweis:", w)
for f in fehler:
    print("FEHLER:", f)
if not themen:
    print("FEHLER: keine Themen gefunden (Blöcke mit '## Titel' nach der Linie '---')")
    sys.exit(1)
sys.exit(1 if fehler else 0)
