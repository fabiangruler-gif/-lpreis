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
