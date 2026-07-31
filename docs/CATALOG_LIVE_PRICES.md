# Live Händlerpreise im öffentlichen Katalog

Stand: 31. Juli 2026

Die öffentliche Duftdetailseite lädt zusätzlich zur Duft-API die Preisübersicht über:

```text
GET /api/prices/fragrances/{fragrance_id}?days=90
```

## Freigegebene Daten

Öffentlich berücksichtigt werden ausschließlich Angebote:

- mit `review_status = APPROVED`
- von aktiven Händlern
- die einer vorhandenen Preisquelle und einem vorhandenen Duft zugeordnet sind

Scannerstatus und Abrufart spielen für die Anzeige keine Rolle. Auch eine bewusst über den Browser-Connector aktualisierte Quelle kann öffentlich erscheinen, solange sie fachlich freigegeben ist.

## Variantenvergleich

Angebote werden nach drei Merkmalen gruppiert:

1. Produktart: Flakon, Tester, Set, Probe oder Nachfüllung
2. Größe in ml
3. Konzentration

Nur Angebote derselben Gruppe werden direkt miteinander verglichen. Ein Tester, Set oder Sample kann deshalb nicht als günstigster regulärer Flakon erscheinen. Fehlende Größen oder Konzentrationen bilden eine klar gekennzeichnete unvollständige Gruppe und werden nicht mit vollständig bestimmten Varianten vermischt.

Die Standardauswahl bevorzugt eine lieferbare reguläre Flakonvariante und danach die am besten durch Händlerangebote und Beobachtungen belegte Gruppe.

## Darstellung

Für die gewählte Variante zeigt das Duftprofil:

- günstigsten aktuellen Gesamtpreis inklusive Versand
- zugehörigen Händler und Produktlink
- Preis pro 100 ml, sofern die Größe bekannt ist
- historisches Tief derselben Variante
- absoluten und prozentualen Abstand zum Tiefpreis
- letzte Prüfung und Anzahl lieferbarer Angebote
- Zeitraumfilter für 30, 90 und 365 Tage
- täglichen günstigsten beobachteten Gesamtpreis als Verlaufsgrafik
- alle Händlerangebote der Variante, nach Gesamtpreis sortiert

Ausverkaufte Angebote bleiben sichtbar und im Rohverlauf erhalten, zählen aber nicht als aktuelles Bestangebot.

## Rückfallverhalten

Fehlen freigegebene Händlerangebote, bleibt der bisherige manuell gepflegte Duftpreis beziehungsweise „Nicht hinterlegt“ sichtbar. Andere Fachdaten werden nicht automatisch erfunden oder überschrieben.
