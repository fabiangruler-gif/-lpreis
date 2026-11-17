# Reel-Rhythmus

**Veröffentlichung:** Di, Do, Fr und So um 09:00 Uhr (Berlin), automatisch durch den Workflow „Reel veröffentlichen (Plan Di/Do/Fr/So)“.
**Bauen:** am Vortag (Mo, Mi, Do, Sa), damit Zahlen aktuell sind und du das Reel prüfen kannst.

## Ablauf
1. Am Vortag um etwa 10:00 wählt Claude das nächste Thema aus `reels/themen.md` (erstes mit `Status: neu`), recherchiert aktuelle Zahlen, schreibt `reels/specs/<slug>.json`, baut Video, Ton und Cover.
2. Das Ergebnis liegt in `out/reels/`: `<slug>.mp4` (Video), `<slug>_storyboard.jpg` (alle 6 Slides auf einen Blick), `<slug>_cover.jpg` (Profil-Vorschau), `<slug>.txt` (Beschreibung). Du bekommst eine Push-Nachricht.
3. In `reels/plan.json` steht das Reel mit Status `bereit` und seinem Veröffentlichungsdatum.
4. Am Veröffentlichungstag um 09:00 Uhr geht es automatisch online.

## Prüfen und eingreifen
- **Zurückhalten:** in `reels/plan.json` den Status des Reels von `bereit` auf `stopp` setzen. Dann wird nichts veröffentlicht.
- **Korrigieren:** `reels/specs/<slug>.json` bzw. die Beschreibung ändern und den Workflow „Reel bauen“ mit dem Slug neu starten, danach den Status wieder auf `bereit` setzen.
- **Anderes Thema:** das Wunschthema in `reels/themen.md` ganz nach oben schieben (Status `neu`).
- **Fehlt ein Reel**, legt der Workflow ein GitHub-Issue „Heute kein Reel veröffentlicht“ an.

## Status in der Themenliste
`neu` → `geplant` (im Plan, wartet auf den Tag) → `veröffentlicht`. `in arbeit` und `vorschau` setzt du selbst, diese Themen überspringt die automatische Auswahl.

## Letzte Folie: abwechselnd Frage oder ruhiger Abschluss
- **Jedes zweite Reel** bekommt einen ruhigen Abschluss: in der Spec bei der letzten Folie (`typ: "cta"`) `"stil": "ruhig"` setzen. Statt Frage und gelbem Folge-Button steht dort eine Kernaussage als Titel (Schlüsselwort in `*Sternchen*` wird gold) und klein darunter „@oil_preis_daily • Täglich das Ölpreis-Update“ (Text anpassbar mit `"hinweis"`).
- **Automatisch:** `reels/build_reel.py` wählt beim Bauen selbst: war das vorige Reel im Plan mit Frage und Button, wird das neue ruhig, und umgekehrt. Die Wahl wird als `"stil"` in der Spec gespeichert (ein erneutes Bauen ändert sie nicht). Wer einen bestimmten Abschluss will, trägt `"stil": "ruhig"` oder `"stil": "frage"` selbst ein.
- Bei ruhigen Reels lässt das Skript in der Beschreibung die Kommentar-Frage und die „Folge @…“-Zeile automatisch weg.
