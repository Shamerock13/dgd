# DGD – Projektkontext

Stand: 31. Juli 2026

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
- Frontend: React, Vite plus bestehende Admin- und Katalog-Skripte
- öffentlicher Katalog: `/`
- Admin-Center: `/admin.html`
- lokale Medien: `/media/fragrances`
- explizites Migrationsschema bis `0017`
- Preis-Worker als separater Container
- lokaler Manifest-v3-Browser-Connector für Chrome und Edge

## Aktueller Funktionsstand

Abgeschlossen sind die Pakete bis 14, Performance 16.1 bis 16.3, Duft-DNA 16.4, Admin 16.5.1 bis 16.5.3, Performance-Recherche 16.6.1 sowie KI-Export und Rückimport 16.7.1 bis 16.7.6.

Preisquellen werden kontrolliert importiert, im Admin geprüft und separat für Scannerläufe freigegeben. Neue Händler bleiben zunächst deaktiviert. Neue oder geänderte Quellen starten mit `PENDING_REVIEW` und `scanner_active = false`.

## KI-Export und Rückimport

```text
GET  /api/ai-research-export/xlsx
POST /api/ai-research-import/preview
POST /api/ai-research-import/apply
```

Der Export erzeugt eine KI-taugliche XLSX-Datei mit neun Tabellenblättern. Persönliche Performance- und DNA-Werte werden nicht exportiert. Die Vorschau zeigt neue Werte und Konflikte ohne Datenbankänderung. Nur ausdrücklich ausgewählte Änderungen werden übernommen; Konflikte benötigen eine zusätzliche Bestätigung und werden vor dem Speichern erneut gegen den aktuellen Datenbankstand geprüft.

Duft-DNA akzeptiert ausschließlich die 16 numerischen Dimensionen von 0 bis 10. Beschreibende Merkmale wie Jahreszeit, Anlass oder Duftfamilie gehören künftig in ein separates Datenmodell.

## Preisquellen, Scanner und Browser-Connector

```text
GET  /api/prices/review/offers
POST /api/prices/review/offers/{offer_id}/decision
POST /api/prices/review/offers/{offer_id}/scanner
POST /api/prices/review/offers/{offer_id}/test
GET  /api/prices/browser-connector/health
POST /api/prices/browser-connector/import
GET  /api/prices/browser-connector/extension.zip
GET  /api/prices/fragrances/{fragrance_id}
```

Scannerläufe berücksichtigen nur freigegebene und ausdrücklich aktivierte Quellen aktiver Händler. Blockieren Händler sowohl HTTP als auch serverseitiges Chromium, wird die Quelle auf `BROWSER_REQUIRED` gesetzt. Der Nutzer kann Preis und Lieferbarkeit dann über die bewusst ausgelöste Chrome-/Edge-Erweiterung an die lokale DGD-Instanz übertragen.

Der öffentliche Preis-Endpunkt liefert aktuelle Angebote und Preisbeobachtungen. Paket 18.1 erweitert ihn um Variantengruppen nach Produktart, Größe und Konzentration, damit Tester, Sets, Proben und abweichende Größen nicht als direkte Alternativen verglichen werden.

## Wichtige Sicherheitsregeln

- leere Zellen bedeuten keine Löschung
- persönliche Werte bleiben strikt getrennt
- ungeprüfte KI-Werte werden nicht automatisch veröffentlicht
- Konflikte werden nicht vorausgewählt
- Preisquellen bleiben bis zur manuellen Freigabe inaktiv
- Scanner werden durch Importe niemals automatisch aktiviert
- öffentliche Preise stammen nur aus freigegebenen Quellen aktiver Händler
- jeder erfolgreiche Übernahmelauf, Scannertest und Browserimport wird protokolliert
- CAPTCHA-, Proxy- und Bot-Schutz-Umgehungen sind ausgeschlossen
- Fehler führen zum Rollback der Transaktion
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

## Aktuelles Paket

Paket 18.1 / Issue #101 / Draft-PR #102 ergänzt Preisverlauf und Variantenvergleich im öffentlichen Duftprofil. Danach sind Preisalarme oder die weitere Absicherung des Master-Imports die nächsten sinnvollen größeren Schritte.
