# Tägliche Öl-Story automatisch auf Instagram

## Wie es funktioniert
1. `data.json` bekommt die Tagesdaten (Kurse, News, Prognose).
2. Der Push von `data.json` startet bei GitHub den Workflow **Tägliche Öl-Story**.
3. Der Workflow rendert das Bild (1080×1920, JPEG), legt es im öffentlichen Repo ab und
   veröffentlicht es über die Instagram-API als **Story**.
4. Alle ~2 Wochen verlängert der Workflow **Token verlängern** das 60-Tage-Token automatisch.

## Einmalige Einrichtung

### 1. Instagram-Account
- Profil → Einstellungen → Kontotyp → auf **Creator** oder **Business** wechseln
  (Professional-Account ist Pflicht).
- Eine Facebook-Seite scheint beim Instagram-Login-Weg nicht nötig zu sein (laut Meta-Doku
  nicht gefordert). Falls Meta später doch danach fragt, verknüpfe eine.

### 2. Meta-App (developers.facebook.com)
- App erstellen, Typ **Business**.
- Im Dashboard: **Instagram → API-Einrichtung mit Instagram-Business-Login**.
- Neben deinem Account auf **Token generieren** klicken, einloggen, Token kopieren.
  Dieses Token ist 60 Tage gültig. Falls Meta verlangt, dass dein Account vorher als
  „Instagram-Tester“ unter App-Rollen eingetragen wird, tu das zuerst.
- Berechtigungen: `instagram_business_basic` und `instagram_business_content_publish`.

### 3. GitHub
- Neues **öffentliches** Repo anlegen (Meta muss das Bild per URL laden können).
- Den Inhalt dieses Ordners (`vorlage`) ins Repo kopieren. Die beiden Dateien aus `github-workflows/`
  müssen im Repo im Pfad `.github/workflows/` liegen (auf github.com: *Add file → Create new file*,
  Pfad `.github/workflows/daily-story.yml` eintippen und den Inhalt einfügen; ebenso `refresh-token.yml`).
- Repo → Settings → Secrets and variables → Actions:
  - Secret **IG_TOKEN** = das kopierte Token
  - Secret **IG_USER_ID** = (optional) deine Instagram-User-ID; ohne sie wird sie automatisch ermittelt
  - Secret **GH_PAT** = (nur für die Token-Verlängerung) Personal Access Token mit Recht
    „Secrets: Read and write“ nur für dieses Repo
  - Variable **AUTO_PUBLISH** = `true`, sobald du dem Ablauf vertraust (siehe unten)

### 4. Erster Test
- Actions → **Tägliche Öl-Story** → *Run workflow*. Das erzeugt das Bild und veröffentlicht es sofort.
- Das Bild findest du zusätzlich als Artefakt **story-vorschau** im Lauf.

## Prüfschritt vor dem Veröffentlichen (empfohlen am Anfang)
Solange `AUTO_PUBLISH` nicht auf `true` steht, rendert ein Push nur die Vorschau.
Du prüfst Kurse und Texte im Artefakt und startest dann *Run workflow*.
Erst wenn die Qualität über Wochen stimmt, setze `AUTO_PUBLISH=true`.

## Grenzen
- Stories verschwinden nach 24 Stunden; Sticker (Link, Umfrage) sind über die API nicht möglich.
- Das Bild muss JPEG sein (max. 8 MB) und öffentlich erreichbar – beides ist eingebaut.
- Der Token-Refresh-Endpunkt ist noch ungetestet; erster Lauf manuell starten und Log prüfen.
- Stimmt etwas mit den Zahlen nicht, ist das Bild trotzdem öffentlich. Quellenangabe und
  „keine Anlageberatung“ stehen deshalb im Bild.
