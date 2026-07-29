# DGD – Projektkontext

Stand: 29. Juli 2026

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
- explizites DGD-Migrationsschema aktuell bis `0013`

## Aktueller Funktionsstand

Abgeschlossen sind alle Pakete bis einschließlich Paket 14 **Suche, Filter & Navigation 2.0**, die Performance-Pakete 16.1 bis 16.3 sowie Paket 16.4.1 **Duft-DNA-Datenmodell und API**.

Paket 16.1 ergänzt strukturierte Performance-Daten. Paket 16.2 zeigt diese Werte in einer eigenständigen Performance-Karte. Paket 16.3 ergänzt den zeitlichen Verlauf für Opening, Herzphase und Drydown, ohne zusätzliche Messpunkte zu erfinden.

Paket 16.4.1 ergänzt 16 optionale Duft-DNA-Dimensionen, Herkunft, Prüfstatus, Quellenqualität und getrennte persönliche Werte. Migration `0013`, Backendstart, Endpunkte und `17 passed, 1 warning` wurden in Dev bestätigt.

Paket 16.4.2 **Duft-DNA-Karte** wird im Branch `feature/fragrance-dna-card` entwickelt. Die Karte liest den eigenen DNA-Endpunkt, sortiert vorhandene Dimensionen nach Stärke und zeigt persönliche Wahrnehmung getrennt. Fehlende Werte bleiben leer.

Paket 15 **Datenvalidierung & Importqualität 2.0** besitzt Qualitätsvorschau, geschützten Commit, manuelle `REVIEW`-Entscheidungen und gespeicherte Importberichte. Der Master-Import muss noch mit denselben Regeln abgesichert werden.

Paket 18 **Preisbeobachtung & Händlervergleich 1.0** trennt Händler, aktuelle Angebote und unveränderliche Preisbeobachtungen. Händleradapter und tägliche Preisprüfungen folgen später am getrennten Scanner-Worker.

Der öffentliche Katalog unterstützt serverseitige Suche, Filter, Pagination und dauerhaft verlinkbare Duft-, Marken- und Parfümeuransichten. Die Admin-Listen für Düfte und Marken besitzen Suche und Pagination.

## Wichtige Endpunkte

```text
GET  /api/catalog/fragrances
GET  /api/fragrances/{fragrance_id}
GET  /api/fragrances/{fragrance_id}/dna
PUT  /api/fragrances/{fragrance_id}/dna
PUT  /api/fragrances/{fragrance_id}/dna/personal
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
- Performance-Werte nur strukturiert und mit sichtbarem Prüfstatus darstellen
- zeitliche Performance-Texte nur aus vorhandenen Phasenwerten ableiten
- Duft-DNA nur aus strukturierten Feldern darstellen
- fehlende DNA-Werte nicht als `0` behandeln
- persönliche DNA niemals mit aggregierter Recherche-DNA vermischen
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
git fetch origin
git switch <feature-branch>
git pull --ff-only origin <feature-branch>
```

Geänderte Dienste anschließend gezielt bauen und ersetzen. Bei einem festen Docker-Containernamen muss der bestehende Dev-Container gegebenenfalls vorher gestoppt und entfernt werden. Datenbankvolumes und Produktion bleiben dabei unberührt.

## Nächster Schritt

**Paket 16.4.2 im Dev-Frontend bauen und die Duft-DNA-Karte mit leerem, partiellem und persönlichem Profil visuell prüfen.**

Produktion wird erst nach erfolgreicher Dev-Abnahme in einem eigenen, ausdrücklich freizugebenden Schritt vorbereitet.
