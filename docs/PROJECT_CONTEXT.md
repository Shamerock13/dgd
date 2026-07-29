# DGD – Projektkontext

Stand: 29. Juli 2026

Repository: `Shamerock13/dgd`. Maßgeblich sind außerdem `docs/CURRENT_STATUS.md`, `docs/ROADMAP.md` und `docs/DEV_WORKFLOW.md`.

## Umgebungen

Produktion auf Unraid:
- `DGD-App`
- `DGD-PostgreSQL`
- `DGD-Updater`

Separate Dev-Umgebung:
- `DGD-Dev-Frontend` auf Port `15173`
- `DGD-Dev-Backend` auf Port `18080`
- `DGD-Dev-Scanner`
- `DGD-Dev-PostgreSQL` auf Port `55432`

Lokales Repository: `/mnt/user/appdata/dgd-github`

Produktion und produktive Datenbank werden niemals direkt für Entwicklung oder Tests verwendet.

## Technik

- Backend: FastAPI, SQLAlchemy, PostgreSQL
- Frontend: React, Vite
- öffentlicher Katalog: `/`
- Admin-Center: `/admin.html`
- explizites Migrationsschema bis `0013`

## Aktueller Funktionsstand

Abgeschlossen sind die Pakete bis 14, Performance 16.1 bis 16.3 sowie Duft-DNA 16.4.1 und 16.4.2.

Paket 16.4.3 liegt in `feature/fragrance-dna-admin` und PR #81. Der Admin-Editor für alle 16 DNA-Dimensionen ist in Dev praktisch bestätigt. Aggregierte und persönliche Werte lassen sich getrennt laden, speichern, erneut laden und gezielt leeren. Fehlende Werte bleiben leer. Der Router-Fix stellt sicher, dass DNA-Endpunkte vor dem SPA-Fallback greifen.

Kontrollierte Recherchevorschläge und deren Freigabe folgen getrennt. Ungeprüfte KI-Werte werden nicht automatisch veröffentlicht.

## Wichtige DNA-Endpunkte

```text
GET  /api/fragrances/{fragrance_id}/dna
PUT  /api/fragrances/{fragrance_id}/dna
PUT  /api/fragrances/{fragrance_id}/dna/personal
```

## Arbeitsweise

- Feature-Branch pro Paket
- GitHub-CI für Backend-Compile und Frontend-Build
- praktische Tests ausschließlich in Dev
- Dokumentation im selben Paket aktualisieren
- anschließend Squash-Merge nach `main`
- Produktion nicht verändern

## Dev-Aktualisierung

```bash
cd /mnt/user/appdata/dgd-github
git fetch origin
git switch <feature-branch>
git pull --ff-only origin <feature-branch>
```

Geänderte Dienste gezielt bauen und mit `--no-deps` ersetzen, wenn bestehende Dev-Abhängigkeiten nicht neu angelegt werden sollen.

## Nächster Schritt

PR #81 mergen und anschließend die kontrollierte Recherche- und Freigabelogik als eigenen Baustein starten.
