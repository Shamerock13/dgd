# DGD – Verlinkbare Marken- und Parfümeurprofile

Stand: 27. Juli 2026

## Ziel

Marken und Parfümeure sollen aus dem öffentlichen Katalog direkt geöffnet und als dauerhafte URL weitergegeben werden können. Browser-Zurück muss dabei wieder zur vorherigen Suche, Detailansicht oder Profilseite führen.

## URL-Zustand

Die öffentliche Katalogansicht verwendet weiterhin `/` und ergänzt Profilzustände über Query-Parameter:

```text
/?profile=brand&profile_id=<UUID>
/?profile=perfumer&profile_id=<PER-ID>
```

Zusätzliche Such- und Seitenparameter können in der URL erhalten bleiben. Beim Öffnen eines Profils wird ein eigener Eintrag in der Browser-Historie angelegt.

## Markenprofile

Markennamen sind in Duftkarten und Duftdetails anklickbar. Das Profil zeigt:

- Name und Beschreibung
- Herkunftsland
- Gründungsjahr
- Link zur offiziellen Website, falls hinterlegt
- paginierte Liste der zugeordneten Düfte

Die Duftliste wird über den vorhandenen Katalogendpunkt mit `brand_id` geladen.

## Parfümeurprofile

Ein Parfümeurname wird in der Duftdetailansicht verlinkt, wenn ein passendes Masterprofil vorhanden ist. Das Profil zeigt:

- Name und Profiltext
- Nationalität
- Geburtsjahr
- Stil
- paginierte Liste der exakt zugeordneten Kreationen

Der Katalogendpunkt unterstützt dafür den neuen exakten Filter `perfumer`.

## Verhalten bei fehlenden Daten

- Fehlt ein Profil, erscheint eine klare Nicht-gefunden-Anzeige.
- Ist zu einem Duft kein Masterprofil vorhanden, bleibt der Parfümeurname normaler Text.
- Profile ohne zugeordnete Düfte zeigen einen leeren, aber gültigen Zustand.

## Dev-Abnahme

Mindestens prüfen:

1. Markenname auf einer Duftkarte öffnet das richtige Markenprofil.
2. Markenname in der Duftdetailansicht öffnet dasselbe Profil.
3. Ein verlinkter Parfümeurname öffnet das passende Parfümeurprofil.
4. Profil-URLs funktionieren in einem neuen Tab.
5. Browser-Zurück führt exakt zur vorherigen Ansicht.
6. Profilseiten mit mehr als 24 Düften lassen sich paginieren.
7. Ein nicht vorhandenes Profil führt nicht zu einem leeren oder kaputten Bildschirm.
8. Der normale Katalog und das Admin-Center bleiben unverändert funktionsfähig.
