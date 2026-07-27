# DGD – Projektkontext

Stand: 27. Juli 2026

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

Abgeschlossen sind alle Pakete bis einschließlich:

14. **Suche, Filter & Navigation 2.0**

Paket 15 **Datenvalidierung & Importqualität 2.0** ist in Arbeit. Die Qualitätsprüfung und der geschützte Commit wurden in Dev bestätigt. Relevante Endpunkte:

```text
POST /api/import/quality/preview
POST /api/import/quality/commit
GET  /api/import/quality/runs
```

Die Qualitätslogik verwendet die vorhandenen CSV-/XLSX-Parser und Zeilenvalidatoren, ergänzt jedoch eine konservative Identitätsnormalisierung und Kandidatensuche. Exakte sowie sicher normalisierte Treffer werden als Dubletten erkannt. Ähnliche Treffer bleiben zunächst `REVIEW` und werden niemals automatisch zusammengeführt.

Der aktuelle Baustein erlaubt für `REVIEW`-Zeilen bewusste Entscheidungen: neuen Duft anlegen, einen angebotenen vorhandenen Kandidaten verwenden oder die Zeile ausschließen. Bei Duftzwillingen werden Original und Alternative ausdrücklich gewählt. Der Server analysiert dieselbe Datei direkt vor dem Schreiben erneut und akzeptiert ausschließlich Kandidaten, die weiterhin zur aktuellen Prüfung gehören.

Importversuche und Entscheidungen werden in `import_quality_runs` als JSON-Bericht gespeichert. Die Tabelle wird idempotent über die registrierten SQLAlchemy-Modelle angelegt.

Der öffentliche Katalog unterstützt serverseitige Suche, Filter, Pagination und dauerhaft verlinkbare Duft-, Marken- und Parfümeuransichten. Die Admin-Listen für Düfte und Marken besitzen Suche und Pagination. Paket 14 wurde vollständig in Dev bestätigt.

Der Scanner-Worker läuft getrennt von API und Frontend. Er prüft ausschließlich aktive und fällige Quellen und veröffentlicht keine Treffer automatisch.

## Wichtige Endpunkte

```text
GET /api/catalog/fragrances
POST /api/import/quality/preview
POST /api/import/quality/commit
GET /api/import/quality/runs
GET /api/research/sources
POST /api/research/sources/{source_id}/scan
POST /api/research/sources/scan-active
GET /api/research/scan-runs
GET /api/research/scanner/status
PUT /api/research/scanner/status
```

## Recherche- und Prüfprinzipien

- nur öffentliche HTTP- und HTTPS-Ziele
- private, lokale, reservierte und Link-Local-Ziele bleiben blockiert
- keine automatische Veröffentlichung
- ähnliche Importkandidaten niemals automatisch zusammenführen
- manuelle Importentscheidungen nur gegen die unmittelbar neu berechneten Kandidaten akzeptieren
- blockierte Zeilen können nicht manuell freigegeben werden
- Feldvorschläge und Produkte landen zunächst in Prüf- beziehungsweise Import-Warteschlangen
- Gemini-Twins benötigen eine konkrete brauchbare Grounding-Quelle
- Duftnoten und Akkorde werden zentral normalisiert

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

**Manuelle REVIEW-Entscheidungen und gespeicherte Importberichte in Dev testen.**

Produktion wird erst nach erfolgreicher Dev-Abnahme in einem eigenen, ausdrücklich freizugebenden Schritt vorbereitet.
