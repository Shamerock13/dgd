# Datenlücken-Recherche & Dublettenbelege 1.0

## Ziel

DGD prüft vorhandene Düfte auf fehlende Fakten und erzeugt daraus gezielte Rechercheaufträge. Mögliche Dubletten werden nicht nur markiert, sondern mit nachvollziehbaren Quellen belegt.

## Erkannte Datenlücken

- Erscheinungsjahr
- Konzentration
- Parfümeur
- Beschreibung
- Bild
- Quelle
- strukturierte oder freie Duftpyramide

`POST /api/enrichment/scan-gaps` aktualisiert die Arbeitsaufträge. `GET /api/enrichment/tasks` liefert die offenen oder abgeschlossenen Aufgaben.

## Quellen für mögliche Dubletten

Zu jedem Dublettenverdacht können mehrere Belege gespeichert werden:

- Quellenname und URL
- gefundene Schreibweise von Marke und Duft
- gefundenes Jahr
- gefundene Konzentration
- Klassifikation
- Begründung
- Trefferqualität

Erlaubte Klassifikationen:

- `LIKELY_SAME`
- `CONCENTRATION_VARIANT`
- `FLANKER`
- `POSSIBLE_DUPLICATE`
- `SIMILAR_NAME`

API:

- `POST /api/enrichment/dupe-evidence`
- `GET /api/enrichment/dupe-evidence`

## Sicherheits- und Qualitätsregeln

- Quellen bleiben auch nach Ablehnung oder späterem Zusammenführen nachvollziehbar.
- Unterschiedliche Konzentrationen und Flanker gelten nicht automatisch als Dublette.
- Widersprüchliche Quellen müssen redaktionell geprüft werden.
- Automatisches Zusammenführen wird erst in einem späteren Paket ergänzt und darf nur mit belastbarer Quellenlage erfolgen.
- Fremde redaktionelle Texte werden nicht ungeprüft übernommen.

## Nächster Schritt

Quellenadapter für gezielte Suche nach Marke und Duftname, Vorschläge für fehlende Felder sowie eine Admin-Oberfläche zum Vergleichen, Freigeben und Ablehnen der gefundenen Werte.
