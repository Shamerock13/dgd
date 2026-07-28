# DGD – Aktueller Projektstand

Stand: 28. Juli 2026

Diese Datei ist die kompakte, maßgebliche Übersicht über den tatsächlich auf `main` vorhandenen Funktionsstand. Änderungen in offenen Feature-Branches werden ausdrücklich als in Arbeit gekennzeichnet. Detailentscheidungen stehen zusätzlich in den jeweiligen Fachdateien unter `docs/`.

## Umgesetzte Pakete

1. Detailansicht & Duftzwillinge 2.0
2. Bildverwaltung & Bildquellen 1.0
3. Markenprofile 1.0
4. Quellen & Verifizierung 1.0
5. Parfümeurprofile 1.0
6. Datenqualität & redaktionelle Arbeitsliste 1.0
7. Lokaler Bildupload & Medienablage 1.0
8. Automatische Recherche & Import-Warteschlange 1.0
9. Recherchequellen & zeitgesteuerter Scanner 1.0
10. Quellenadapter & Mehrseiten-Scanner 1.0
11. Gemini-Recherche & Datenqualität 1.0
12. Gemini-Rechercheverlauf & Tokenkontrolle 1.0
13. Scanner-Betrieb & automatische Fälligkeit 1.0
14. Suche, Filter & Navigation 2.0
16.1 Strukturiertes Performance-Datenmodell
16.2 Performance-Karte im Duftprofil

## Paket 16.1 abgeschlossen

Das Datenmodell für Duftleistung ist auf `main` vorhanden. Erfasst werden unter anderem:

- Haltbarkeit als Stundenbereich und normalisierter Score
- Projektion, Sillage, Drydown und Gesamtperformance
- Projektion in der ersten Stunde und nach drei Stunden
- Quellenanzahl, Vertrauensgrad und Quellenabweichung
- Prüfstatus, Recherchedatum, Version und Produktionszeitraum
- persönliche Bewertung getrennt von Community-Daten

Das explizite DGD-Migrationsschema steht bei `0012`. Migration, Backendstart, API-Ausgabe und automatisierte Tests wurden in der Dev-Umgebung bestätigt. Ergebnis: `11 passed`, eine nicht blockierende FastAPI-Abschreibungswarnung.

## Paket 16.2 abgeschlossen

Die Performance-Karte wurde über PR #75 nach `main` übernommen. Die öffentliche Duftdetailansicht zeigt:

- Haltbarkeitsbereich und Score
- Gesamtleistung, Projektion, Sillage und Drydown
- zeitbezogene Projektionswerte
- Vertrauen, Quellenanzahl, Abweichung und Prüfstatus
- Version, Produktionszeitraum und Recherchedatum
- klar getrennte persönliche Bewertungen

Fehlende Werte werden als „Noch offen“ beziehungsweise „–“ dargestellt. Es werden keine Werte aus Legacy-Feldern hochgerechnet oder erfunden.

## Paket 16.3 in Arbeit

**Zeitlicher Duftverlauf** liegt im Branch `feature/performance-timeline`.

Die bestehende Performance-Karte wird ergänzt um:

- eine responsive Timeline für Opening, Herzphase und Drydown
- sichtbare Phasenwerte für erste Stunde, nach drei Stunden und Basisphase
- feste verbale Einordnungen von „sehr dezent“ bis „sehr stark“
- ein Stärke-Badge aus dem vorhandenen Gesamtperformance-Wert
- eine deterministische Kurzbeschreibung der Entwicklung
- saubere Platzhalter, wenn einzelne oder alle Phasenwerte fehlen

Die Timeline verwendet ausschließlich vorhandene Felder aus Migration `0012`. Sie erzeugt keine zusätzlichen Zwischenwerte und führt keine KI-Recherche aus. Dev-Abnahme und Merge stehen noch aus.

## Paket 15 in Arbeit

**Datenvalidierung & Importqualität 2.0** besitzt:

```text
POST /api/import/quality/preview
POST /api/import/quality/commit
GET  /api/import/quality/runs
```

Qualitätsvorschau, geschützter Commit, manuelle `REVIEW`-Entscheidungen und gespeicherte Importberichte wurden praktisch in Dev bestätigt. Offen bleibt die Absicherung des Master-Imports mit denselben Regeln.

## Paket 18 gestartet

**Preisbeobachtung & Händlervergleich 1.0** besitzt im ersten Backend-Baustein:

```text
GET  /api/prices/retailers
POST /api/prices/retailers
POST /api/prices/offers/check
GET  /api/prices/fragrances/{fragrance_id}?days=90
```

Neu sind getrennte Datenmodelle für Händler, aktuelle Angebote und unveränderliche Preisbeobachtungen. Der Duft-Endpunkt berechnet den günstigsten verfügbaren Gesamtpreis inklusive Versand, den Preis pro 100 ml, den historischen Bestpreis und den Verlauf für bis zu 1095 Tage.

Produktarten werden als Flakon, Tester, Set, Probe oder Refill getrennt gekennzeichnet. Ausverkaufte Angebote bleiben nachvollziehbar, zählen aber nicht zum aktuell günstigsten Preis.

Der erste Baustein liest noch keine Händlerseiten automatisch aus. Admin-Oberfläche, Händleradapter und tägliche Scannerläufe folgen getrennt.

## Scanner-Betrieb

Die Dev-Umgebung besitzt den getrennten Container `DGD-Dev-Scanner`. Der Worker verarbeitet ausschließlich aktive und fällige Recherchequellen, verhindert parallele Doppelläufe und veröffentlicht keine Treffer automatisch.

## Recherche- und Sicherheitsregeln

- nur öffentliche HTTP- und HTTPS-Ziele
- interne, private, reservierte und lokale Netzwerkziele bleiben blockiert
- keine automatische Veröffentlichung
- Dublettenprüfung vor Freigabe
- ähnliche Importkandidaten niemals automatisch zusammenführen
- Preise und Versand getrennt speichern und als Gesamtpreis vergleichen
- ausverkaufte Angebote nicht als günstigsten Preis anzeigen
- Duftnoten und Akkorde zentral normalisieren

## Datenbankstand

Das explizite DGD-Migrationsschema steht bei `0012`. Neue Tabellen für Importberichte und Preisbeobachtung werden idempotent über die registrierten SQLAlchemy-Modelle angelegt.

## Qualitätssicherung

Die GitHub-CI prüft:

```bash
python -m compileall -q backend/app
npm install
npm run build
```

Backendtests können in der aktuellen Dev-Image-Konfiguration ausgeführt werden, nachdem `backend/tests` in den Container kopiert wurde, da `backend/Dockerfile.dev` derzeit nur `app` übernimmt:

```bash
docker cp backend/tests DGD-Dev-Backend:/app/tests
docker exec -it DGD-Dev-Backend python -m pytest -q /app/tests
```

Neue Pakete gelten erst nach erfolgreichem Test in der separaten Dev-Umgebung als praktisch abgenommen.

## Nächster Schritt

**Paket 16.3 im Dev-Frontend bauen und visuell mit einem leeren sowie einem befüllten Performance-Datensatz prüfen. Danach PR zusammenführen. Parallel bleiben Paket 15 und Paket 18 als eigene Arbeitsstränge offen.**

## Dokumentationsregel

Nach jedem größeren Paket werden mindestens `CURRENT_STATUS`, `PROJECT_CONTEXT`, `ROADMAP`, die Fachdatei und bei Workflowänderungen `DEV_WORKFLOW` geprüft.

Der Chat ist nicht das Projektgedächtnis. Maßgeblich sind Repository und Dokumentation.
