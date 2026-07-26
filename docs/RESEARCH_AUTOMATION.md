# DGD Rechercheautomatisierung

## Zielbild

Die Recherche soll sich wie ein Plex-Scan bedienen lassen, ohne ungeprüfte Inhalte direkt in die Duftdatenbank zu schreiben. Der Ablauf bleibt deshalb immer zweistufig:

1. Quellen werden gescannt und erzeugen Vorschläge.
2. Vorschläge werden in der Import-Warteschlange geprüft, bearbeitet, übernommen oder abgelehnt.

## Umgesetzter Stand

### Automatische Recherche & Import-Warteschlange 1.0

- manueller Scan einer öffentlichen HTML-Seite
- Erkennung von JSON-LD-Produktdaten und Seitentitel-Fallback
- Speicherung von Quelle, Rohdaten und Trefferqualität
- Dublettenprüfung über normalisierte Marke und Duftname
- keine automatische Veröffentlichung
- Schutz vor privaten, lokalen und internen Netzwerkzielen

### Recherchequellen & zeitgesteuerter Scanner 1.0

- feste Recherchequellen mit Name, URL, Notiz und Aktivstatus
- frei wählbares Scanintervall von 1 bis 8.760 Stunden
- manueller Scan einer einzelnen Quelle
- Sammelscan aller aktiven Quellen
- Sammelscan nur der laut Intervall fälligen Quellen
- Speicherung von letztem Lauf, Status und Fehlermeldung
- separate Scan-Historie mit Fund-, Neu- und Dublettenzahlen
- Quellen können pausiert, bearbeitet oder gelöscht werden

## Datenmodell

### `research_sources`

Speichert die dauerhaft gepflegten Quellenprofile. Wichtige Felder:

- `name`
- `url`
- `interval_hours`
- `active`
- `note`
- `last_run_at`
- `last_status`
- `last_error`

### `research_scan_runs`

Protokolliert jeden Lauf einer festen Quelle:

- Quelle
- Start und Ende
- Status `RUNNING`, `SUCCESS` oder `FAILED`
- gefundene Treffer
- neu angelegte Vorschläge
- mögliche Dubletten
- Fehlermeldung

Die Tabellen werden beim Start über die registrierten SQLAlchemy-Modelle idempotent angelegt. Das bestehende Migrationsschema bleibt in diesem Paket bei `0011`.

## Sicherheitsentscheidungen

- ausschließlich vollständige HTTP- und HTTPS-Adressen
- DNS-Auflösung vor dem Abruf
- Sperre privater, lokaler, reservierter und Link-Local-Adressen
- Antwort muss HTML sein
- maximale Verarbeitung von 2 MB HTML je Abruf
- maximal 50 Vorschläge pro Seite
- keine automatische Übernahme in `fragrances`

## Bedienung

Unter `Admin → Recherche` stehen jetzt drei Ebenen bereit:

1. feste Recherchequellen verwalten
2. Einzelscan einer beliebigen öffentlichen Seite
3. Import-Warteschlange prüfen

Mit **Alle aktiven scannen** werden alle aktiven Quellen sofort geprüft. Mit **Nur fällige scannen** werden nur Quellen ausgeführt, deren Intervall seit dem letzten Lauf abgelaufen ist.

## Betrieb und Tests

Vor einem Merge prüfen:

- Backend mit `python -m compileall -q backend/app`
- Frontend mit `npm install && npm run build`
- Quelle anlegen, bearbeiten, pausieren und löschen
- Einzel- und Sammelscan testen
- fällige und noch nicht fällige Quellen unterscheiden
- Fehlerlauf in Quelle und Scan-Historie sichtbar machen
- identische Treffer nicht erneut anlegen
- Dubletten weiterhin nur markieren

Die zentrale CI unter `.github/workflows/ci.yml` führt Backend-Compile und Frontend-Build künftig bei Pull Requests sowie nach Änderungen auf `main` automatisch aus.

## Nächste sinnvolle Ausbaustufe

**Quellenadapter & Mehrseiten-Scanner 1.0**

Geplant:

- quellenspezifische Adapter statt ausschließlich generischer JSON-LD-Erkennung
- Listen- und Suchseiten mit mehreren Produktlinks
- begrenztes Folgen interner Produktlinks derselben Domain
- Seitennavigation mit klarer Maximalzahl
- robots.txt-, Rate-Limit- und Pausenregeln je Quelle
- Vorschau eines Scanplans vor dem Start
