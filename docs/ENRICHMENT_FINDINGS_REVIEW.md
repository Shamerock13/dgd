# Feldbezogene Datenfunde & Prüfung 1.0

## Ziel

Gefundene Angaben werden nicht mehr nur als allgemeiner Recherchetreffer behandelt. DGD speichert jeden Fund bezogen auf einen konkreten Duft und ein konkretes Feld.

## Unterstützte Felder

- Erscheinungsjahr
- Konzentration
- Parfümeur
- Beschreibung
- Bild-URL
- Kopf-, Herz- und Basisnoten
- Akkorde

## Datenmodell

Die Tabelle `enrichment_findings` speichert Duft, Feld, vorgeschlagenen Wert, Quelle, Textausschnitt, Vertrauenswert und Prüfstatus. Mehrfache identische Fundstellen werden über Duft, Feld und URL zusammengeführt.

## Prüfablauf

Unter **Quellen & Prüfung** werden aktueller und gefundener Wert nebeneinander angezeigt.

- **Übernehmen** schreibt den Wert nur, wenn das Zielfeld leer ist oder bereits denselben Wert enthält.
- **Konflikt** markiert eine abweichende Angabe zur manuellen Klärung.
- **Ablehnen** verwirft den Vorschlag, ohne Duftdaten zu verändern.

Bei einer Übernahme wird zusätzlich ein Eintrag im Quellenregister angelegt. Bestehende abweichende Werte werden nicht automatisch überschrieben.

## API

- `POST /api/enrichment/findings`
- `GET /api/enrichment/findings?status=PENDING`
- `POST /api/enrichment/findings/{id}/approve`
- `POST /api/enrichment/findings/{id}/conflict`
- `POST /api/enrichment/findings/{id}/reject`

## Nächster Schritt

Die Quellenadapter sollen strukturierte Angaben aus eindeutigen Fundstellen automatisch als `enrichment_findings` ablegen. Die Freigabelogik bleibt davon getrennt.
