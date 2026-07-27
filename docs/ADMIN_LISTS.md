# DGD – Admin-Listen: Suche und Pagination

Stand: 27. Juli 2026

## Ziel

Die bestehenden Verwaltungsformulare bleiben unverändert. Große Listen im Admin-Center sollen trotzdem schnell durchsuchbar und übersichtlich sein.

## Umfang

Die Zusatzschicht gilt zunächst für:

- vorhandene Düfte
- vorhandene Marken

Sie ergänzt:

- lokale Suche über die sichtbaren Datensätze
- 20 Einträge pro Seite
- Seitennavigation mit Vor-, Zurück- und kompakten Seitenzahlen
- Trefferanzeige `gefiltert von gesamt`
- Speicherung von Suchtext und Seite in `sessionStorage`
- Rücksprung zum bearbeiteten Eintrag nach dem Speichern

## Technische Umsetzung

`frontend/src/admin-list-tools.js` beobachtet ausschließlich die beiden unterstützten `.admin-list`-Bereiche und erweitert sie nach dem React-Rendern. Die React-Formulare, API-Aufrufe und Datenmodelle werden nicht verändert.

`frontend/src/admin-list-tools.css` enthält nur die Darstellung der neuen Such- und Paginationselemente.

Die Dateien werden ausschließlich über `frontend/admin.html` geladen und beeinflussen die öffentliche Katalogansicht nicht.

## Grenzen

- Die Suche arbeitet auf den bereits vom Admin-Center geladenen Datensätzen.
- Speziallisten wie Duftnoten, Duftzwillinge, Quellen und Recherche erhalten in diesem Paket keine zusätzliche Pagination.
- Serverseitige Admin-Pagination bleibt Bestandteil eines späteren Admin-Pakets, falls die Datenmenge das vollständige Laden im Browser unpraktisch macht.

## Dev-Abnahme

Mindestens prüfen:

1. Duftsuche findet nach Duft- und Markennamen.
2. Markensuche findet nach Markenname und Land.
3. Bei mehr als 20 Treffern erscheint die Seitennavigation.
4. Seitenwechsel zeigt keine doppelten oder fehlenden Datensätze.
5. Suchtext und Seite bleiben beim Wechsel zwischen Admin-Bereichen erhalten.
6. Nach Bearbeiten und Speichern wird der vorherige Eintrag wieder sichtbar.
7. Löschen und Neuanlegen aktualisieren Trefferzahl und Seiten korrekt.
8. Die übrigen Admin-Bereiche bleiben unverändert.
