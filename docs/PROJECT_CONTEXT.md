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

Lokales Repository:

```text
/mnt/user/appdata/dgd-github
```

Lokale Medien:

```text
/mnt/user/appdata/dgd-dev-media
```

## Technik

- Backend: FastAPI, SQLAlchemy, PostgreSQL
- Frontend: React, Vite
- Vite baut drei HTML-Einstiege: `index.html`, `admin.html` und den Weiterleitungs-Einstieg `catalog.html`
- `/` ist die öffentliche Katalogansicht
- `/admin.html` enthält das bestehende Admin-Center
- Datenbankzugriff über `DATABASE_URL`
- explizites DGD-Migrationsschema aktuell bis `0011`
- zusätzliche Recherche-, Scanner-, Gemini- und Verlaufsstrukturen werden idempotent angelegt

## Aktueller Funktionsstand

Abgeschlossen sind alle Pakete bis einschließlich:

13. **Scanner-Betrieb & automatische Fälligkeit 1.0**

Paket 14 **Suche, Filter & Navigation 2.0** ist in Arbeit. Der paginierte Katalog ist als öffentliche Hauptansicht integriert und in Dev bestätigt. Suche, Filter, Sortierung, Seite und Duftdetail bleiben in der URL erhalten.

Die Admin-Listen für Düfte und Marken besitzen eine getrennte, DOM-basierte Such- und Pagination-Schicht. Sie verändert weder React-Formulare noch Verwaltungsendpunkte. Suchtext und Seite bleiben in `sessionStorage`; nach dem Bearbeiten wird zum vorherigen Listeneintrag zurückgesprungen. Diese Funktionen wurden praktisch in Dev bestätigt.

Der Scanner-Worker läuft getrennt von API und Frontend. Er prüft ausschließlich aktive und fällige Quellen, meldet einen Heartbeat, speichert den letzten Zyklusstatus und verhindert parallele Doppelläufe derselben Quelle über PostgreSQL-Advisory-Locks.

Die Automatik wird im Bereich **Recherche & Anreicherung** gesteuert. Der Worker veröffentlicht keine Treffer automatisch; neue Produkte bleiben in der Import-Warteschlange.

Wichtige Endpunkte:

```text
GET /api/catalog/fragrances
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
- Feldvorschläge und Produkte landen zunächst in Prüf- beziehungsweise Import-Warteschlangen
- Gemini-Twins benötigen eine konkrete brauchbare Grounding-Quelle
- bekannte Feldwerte und Twin-Kandidaten werden ausgeschlossen
- Duftnoten und Akkorde werden zentral normalisiert
- Gemini-Läufe protokollieren Status, Quellen, Treffer und Tokenverbrauch

## Arbeitsweise

- vor jedem größeren Paket zuerst `PROJECT_CONTEXT`, `ROADMAP` und `DEV_WORKFLOW` lesen
- danach aktuellen Code und relevante Konfigurationen prüfen
- Änderungen auf einem Feature-Branch im GitHub-Repository umsetzen
- GitHub-CI muss Backend-Compile und Frontend-Build erfolgreich abschließen
- anschließend per sauberem Squash-Commit nach `main` mergen
- Tests ausschließlich in der Dev-Umgebung
- Produktion nicht verändern
- Dokumentation im selben Paket aktualisieren

## Dev-Aktualisierung

```bash
cd /mnt/user/appdata/dgd-github
GIT_SSH_COMMAND='ssh -i /root/.ssh/dgd_github -o IdentitiesOnly=yes -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no' \
git pull origin main

docker restart DGD-Dev-Frontend
```

## Nächster Schritt

**Dauerhaft verlinkbare Marken- und Parfümeuransichten umsetzen und danach Paket 14 abschließen.**

Produktion wird erst nach erfolgreicher Dev-Abnahme in einem eigenen, ausdrücklich freigegebenen Schritt vorbereitet.