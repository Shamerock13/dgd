# DGD – Projektkontext

Stand: 30. Juli 2026

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
- Frontend: React, Vite plus bestehende Admin-Skripte
- öffentlicher Katalog: `/`
- Admin-Center: `/admin.html`
- lokale Medien: `/media/fragrances`
- explizites Migrationsschema bis `0015`

## Aktueller Funktionsstand

Abgeschlossen sind die Pakete bis 14, Performance 16.1 bis 16.3, Duft-DNA 16.4, Admin 16.5.1 bis 16.5.3, Performance-Recherche 16.6.1 sowie KI-Export und Rückimport 16.7.1 bis 16.7.3.

Paket 16.7.3 ergänzt die feldweise Freigabe und kontrollierte Datenbankübernahme für geprüfte Excel-Rückimporte. Die Dev-Abnahme einschließlich DNA-Validierung, lokalem Bild-Upload, Media-Auslieferung und normalem Duft-Speichern war erfolgreich.

## KI-Export und Rückimport

```text
GET  /api/ai-research-export/xlsx
POST /api/ai-research-import/preview
POST /api/ai-research-import/apply
```

Der Export erzeugt eine KI-taugliche XLSX-Datei mit neun Tabellenblättern. Persönliche Performance- und DNA-Werte werden nicht exportiert. Die Vorschau zeigt neue Werte und Konflikte ohne Datenbankänderung. Nur ausdrücklich ausgewählte Änderungen werden übernommen; Konflikte benötigen eine zusätzliche Bestätigung und werden vor dem Speichern erneut gegen den aktuellen Datenbankstand geprüft.

Duft-DNA akzeptiert ausschließlich die 16 numerischen Dimensionen von 0 bis 10. Beschreibende Merkmale wie Jahreszeit, Anlass oder Duftfamilie gehören künftig in ein separates Datenmodell.

Bildquellen können als Prüfinformation übernommen werden. Geprüfte Bilder werden lokal gespeichert; externe Produktseiten werden nicht automatisch als Bild eingebettet. Preisquellen und Scanner bleiben bis Paket 16.7.4 separat und inaktiv.

## Wichtige Sicherheitsregeln

- leere Zellen bedeuten keine Löschung
- persönliche Werte bleiben strikt getrennt
- ungeprüfte KI-Werte werden nicht automatisch veröffentlicht
- Konflikte werden nicht vorausgewählt
- Preisquellen bleiben bis zur separaten Scanner-Integration inaktiv
- jeder erfolgreiche Übernahmelauf wird protokolliert
- Fehler führen zum Rollback der gesamten Transaktion
- normale Admin-Formulare senden nur ihre erlaubten Felder

## Arbeitsweise

- Feature-Branch pro Paket
- GitHub-CI für Backend-Compile und Frontend-Build
- praktische Tests ausschließlich in Dev
- Dokumentation im selben Paket aktualisieren
- erst nach Nutzerabnahme auf „Ready for review“ setzen
- anschließend Merge nach `main`
- Produktion nicht verändern

## Dev-Aktualisierung

```bash
cd /mnt/user/appdata/dgd-github
git fetch origin
git switch <feature-branch>
git pull --ff-only origin <feature-branch>
docker compose -f docker-compose.dev.yml up -d --build
```

## Nächster Schritt

Paket 16.7.4 für validierte Preisquellen und kontrollierte spätere Scanner-Aktivierung.