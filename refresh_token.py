#!/usr/bin/env python3
"""Verlängert das 60-Tage-Token (Instagram-Login). Das Token muss mindestens 24 h alt und noch gültig sein.
Gibt das neue Token auf stdout aus (nichts anderes), Meldungen gehen nach stderr."""
import json, os, sys, urllib.error, urllib.parse, urllib.request

token = os.environ.get("IG_TOKEN") or sys.exit("IG_TOKEN fehlt.")
url = "https://graph.instagram.com/refresh_access_token?" + urllib.parse.urlencode({"grant_type": "ig_refresh_token", "access_token": token})
try:
    with urllib.request.urlopen(url, timeout=60) as r:
        d = json.loads(r.read().decode())
except urllib.error.HTTPError as e:
    sys.exit(f"Refresh fehlgeschlagen {e.code}: {e.read().decode(errors='replace')}")
print(f"Neues Token gültig für {d.get('expires_in')} Sekunden.", file=sys.stderr)
print(d["access_token"])
