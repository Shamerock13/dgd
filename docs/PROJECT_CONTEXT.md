# DGD – Projektkontext

Stand: 28. Juli 2026

Wir arbeiten am Repository `Shamerock13/dgd`. Ergänzend gelten `docs/CURRENT_STATUS.md`, `docs/ROADMAP.md` und `docs/DEV_WORKFLOW.md`.

## Architektur

### Produktion auf Unraid

- `DGD-App`
- `DGD-PostgreSQL`
- `DGD-Updater`
- stabile Produktionsversion: `dgd-core:1.2.0`
- Produktion und produktive Datenbank werden niemals direkt für Entwicklung oder Tests verwendet.

### Separate Dev-Umgebung

- `DGD-Dev-Frontend`
- `DGD-Dev-Backend`
- `DGD-Dev-Scanner`
- `DGD-Dev-PostgreSQL`
- Docker-Netzwerk: `dgd-dev`
- Frontend-Port: `15173`
- Backend-Port: `18080`
- PostgreSQL-Port: `55432`

Lokales Repository: `/mnt/user/appdata/dgd-github`

Lokale Medien: `/mnt/user/appdata/dgd-dev-media`

## Technik

- Backend: FastAPI, SQLAlchemy, PostgreSQL
- Frontend: React, Vite
- `/` ist die öffentliche Katalogansicht
- `/admin.html` enthält das bestehende Admin-Center
- Datenbankzugriff über `DATABASE_URL`
- explizites DGD-Migrationsschema aktuell bis `0011`

## Aktueller Funktionsstand

Abgeschlossen sind alle Pakete bis einschließlich Paket 14 **Suche, Filter & Navigation 2.0**.

Paket 15 **Datenvalidierung & Importqualität 2.0** besitzt Qualitätsvorschau, geschützten Commit, manuelle `REVIEW`-Entscheidungen und gespeicherte Importberichte. Diese Abläufe wurden praktisch in Dev bestätigt. Der Master-Import muss noch mit denselben Regeln abgesichert werden.

Paket 18 **Preisbeobachtung & Händlervergleich 1.0** wurde auf Nutzerpriorität vorgezogen. Der erste Backend-Baustein trennt Händler, aktuelle Angebote und unveränderliche Preisbeobachtungen. Angebote speichern Warenpreis, Versand, Größe, Produktart, Verfügbarkeit und Prüfzeitpunkt. Der Preis-Endpunkt berechnet günstigstes verfügbares Angebot, Preis pro 100 ml, historischen Bestpreis und Verlauf.

Die Preislogik führt noch keine externen Abrufe aus. Händleradapter und tägliche Preisprüfungen werden später an den getrennten Scanner-Worker angebunden.

Der öffentliche Katalog unterstützt serverseitige Suche, Filter, Pagination und dauerhaft verlinkbare Duft-, Marken- und Parfümeuransichten. Die Admin-Listen für Düfte und Marken besitzen Suche und Pagination.

Der Scanner-Worker läuft getrennt von API und Frontend. Er prüft ausschließlich aktive und fällige Quellen und veröffentlicht keine Treffer automatisch.

## Wichtige Endpunkte

```text
GET  /api/catalog/fragrances
POST /api/import/quality/preview
POST /api/import/quality/commit
GET  /api/import/quality/runs
GET  /api/prices/retailers
POST /api/prices/retailers
POST /api/prices/offers/check
GET  /api/prices/fragrances/{fragrance_id}
GET  /api/research/sources
POST /api/research/sources/{source_id}/scan
POST /api/research/sources/scan-active
GET  /api/research/scan-runs
GET  /api/research/scanner/status
PUT  /api/research/scanner/status
```

## Recherche- und Prüfprinzipien

- nur öffentliche HTTP- und HTTPS-Ziele
- private, lokale, reservierte und Link-Local-Ziele bleiben blockiert
- keine automatische Veröffentlichung
- ähnliche Importkandidaten niemals automatisch zusammenführen
- manuelle Importentscheidungen nur gegen unmittelbar neu berechnete Kandidaten akzeptieren
- blockierte Zeilen können nicht manuell freigegeben werden
- Preis und Versand getrennt speichern; Gesamtpreis vergleichen
- ausverkaufte Angebote nicht als günstigsten aktuellen Preis anzeigen
- Händlerseiten später nur über kontrollierte Adapter abrufen
- Duftnoten und Akkorde zentral normalisieren

## Arbeitsweise

- vor jedem größeren Paket zuerst `PROJECT_CONTEXT`, `ROADMAP` und `DEV_WORKFLOW` lesen
- danach aktuellen Code und relevante Konfigurationen prüfen
- Änderungen auf einem Feature-Branch umsetzen
- GitHub-CI muss Backend-Compile und Frontend-Build erfolgreich abschließen
- anschließend per Squash nach `main` mergen
- Tests ausschließlich in der Dev-Umgebung
- Produktion nicht verändern
- Dokumentation im selben Paket aktualisieren

## Dev-Aktualisierung

```bash
cd /mnt/user/appdata/dgd-github
GIT_SSH_COMMAND='ssh -i /root/.ssh/dgd_github -o IdentitiesOnly=yes -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no' \
git pull origin main

docker restart DGD-Dev-Backend DGD-Dev-Frontend
```

## Nächster Schritt

**Preis-Backend in Dev mit Händler und mehreren Preisbeobachtungen testen; anschließend Admin-Oberfläche ergänzen.**

Produktion wird erst nach erfolgreicher Dev-Abnahme in einem eigenen, ausdrücklich freizugebenden Schritt vorbereitet.
