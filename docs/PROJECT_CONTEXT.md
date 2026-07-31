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
- explizites Migrationsschema bis `0018`
- Preis-Worker als separater Container
- lokaler Manifest-v3-Browser-Connector für Chrome und Edge

## Aktueller Funktionsstand

Abgeschlossen sind die Pakete bis 14, Performance 16.1 bis 16.3, Duft-DNA 16.4, Admin 16.5.1 bis 16.5.3, Performance-Recherche 16.6.1, KI-Export und Rückimport 16.7.1 bis 16.7.6 sowie Preisverlauf, Variantenvergleich und Preisalarme 18.1 bis 18.2.

Preisquellen werden kontrolliert importiert, im Admin geprüft und separat für Scannerläufe freigegeben. Neue Händler bleiben zunächst deaktiviert. Neue oder geänderte Quellen starten mit `PENDING_REVIEW` und `scanner_active = false`.

## KI-Export und Rückimport

```text
GET  /api/ai-research-export/xlsx
POST /api/ai-research-import/preview
POST /api/ai-research-import/apply
```

Der Export erzeugt eine KI-taugliche XLSX-Datei mit neun Tabellenblättern. Persönliche Performance- und DNA-Werte werden nicht exportiert. Die Vorschau zeigt neue Werte und Konflikte ohne Datenbankänderung. Nur ausdrücklich ausgewählte Änderungen werden übernommen; Konflikte benötigen eine zusätzliche Bestätigung und werden vor dem Speichern erneut gegen den aktuellen Datenbankstand geprüft.

Duft-DNA akzeptiert ausschließlich die 16 numerischen Dimensionen von 0 bis 10. Beschreibende Merkmale wie Jahreszeit, Anlass oder Duftfamilie gehören künftig in ein separates Datenmodell.

## Preisquellen, Scanner, Verlauf und Alarme

```text
GET    /api/prices/review/offers
POST   /api/prices/review/offers/{offer_id}/decision
POST   /api/prices/review/offers/{offer_id}/scanner
POST   /api/prices/review/offers/{offer_id}/test
GET    /api/prices/browser-connector/health
GET    /api/prices/browser-connector/queue
POST   /api/prices/browser-connector/import
GET    /api/prices/browser-connector/extension.zip
GET    /api/prices/fragrances/{fragrance_id}
GET    /api/prices/fragrances/{fragrance_id}/alerts
PUT    /api/prices/fragrances/{fragrance_id}/alerts/{variant_key}
DELETE /api/prices/fragrances/{fragrance_id}/alerts/{variant_key}
```

Scannerläufe berücksichtigen nur freigegebene und ausdrücklich aktivierte Quellen aktiver Händler. Blockieren Händler sowohl HTTP als auch serverseitiges Chromium, wird die Quelle auf `BROWSER_REQUIRED` gesetzt. Der Nutzer kann Preis und Lieferbarkeit dann über die bewusst ausgelöste Chrome-/Edge-Erweiterung an die lokale DGD-Instanz übertragen.

Der öffentliche Preis-Endpunkt liefert Variantengruppen nach Produktart, Größe und Konzentration. Bestpreis, historisches Tief und Verlauf werden nur innerhalb derselben Variante berechnet.

Lokale Preisalarme sind eindeutig an `fragrance_id` und `variant_key` gebunden. Sie akzeptieren einen Zielpreis inklusive Versand, einen maximalen prozentualen Abstand zum historischen Tief oder beide Regeln. Jede neue `price_observations`-Zeile stößt innerhalb derselben Datenbanktransaktion eine Neubewertung an.

## Browser-Prüfrunde 18.3

Der Queue-Endpunkt liefert ausschließlich freigegebene Quellen mit `trust_status = BROWSER_REQUIRED`, deaktiviertem Server-Scanner und aktivem Händler. Die letzte manuelle Prüfung wird aus dem jüngsten Audit-Ereignis `BROWSER_IMPORT_SUCCESS` ermittelt.

Statuswerte:

```text
NEVER_CHECKED
DUE
CURRENT
```

Die Fälligkeit orientiert sich an `scan_interval`. Bekannte Stunden-, Tages-, Wochen- und Monatswerte werden normalisiert; unbekannte Werte verwenden sicher 24 Stunden. Nie geprüfte Quellen stehen zuerst, anschließend die am längsten nicht manuell geprüften Quellen.

Der Admin startet die Prüfrunde bewusst mit der ersten fälligen Produktseite. Nach einem erfolgreichen Browserimport fragt die Erweiterung die Queue erneut ab und bietet die nächste fällige Seite über einen eigenen Knopf an. Ohne diesen Klick findet keine Navigation statt. Die Queue besitzt keine Sitzung und bleibt dadurch auch nach Browser- oder Containerneustarts konsistent.

## Wichtige Sicherheitsregeln

- leere Zellen bedeuten keine Löschung
- persönliche Werte bleiben strikt getrennt
- ungeprüfte KI-Werte werden nicht automatisch veröffentlicht
- Konflikte werden nicht vorausgewählt
- Preisquellen bleiben bis zur manuellen Freigabe inaktiv
- Scanner werden durch Importe niemals automatisch aktiviert
- öffentliche Preise stammen nur aus freigegebenen Quellen aktiver Händler
- Preisalarme ignorieren ausverkaufte, ungeprüfte und inaktive Quellen
- Browser-Prüfrunden enthalten keine ungeprüften Quellen oder inaktiven Händler
- jede Produktseite wird ausschließlich nach einer bewussten Nutzeraktion geöffnet und übertragen
- jeder erfolgreiche Übernahmelauf, Scannertest und Browserimport wird protokolliert
- CAPTCHA-, Proxy- und Bot-Schutz-Umgehungen sind ausgeschlossen
- Fehler führen zum Rollback der Transaktion
- normale Admin-Formulare senden nur ihre erlaubten Felder

## Arbeitsweise

- Feature-Branch pro Paket
- GitHub-CI für Backend-Compile, Erweiterungsprüfung und Frontend-Build
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

Paket 18.3 / Issue #105 / Draft-PR #106 ergänzt eine fälligkeitsbasierte, bewusst gesteuerte Prüfrunde für Browser-Preisquellen. Parallel bleibt Paket 15 zur weiteren Importvalidierung offen.
