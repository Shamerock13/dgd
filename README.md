# DGD

**Das Große Parfum- & Duftzwillinge-Lexikon**

DGD ist eine Webanwendung zur strukturierten Verwaltung von Parfums, Marken, Duftzwillingen, Parfümeuren, Quellen, Preisen und recherchierten Duftdaten.

## Technischer Aufbau

- Backend: FastAPI
- Frontend: React und Vite
- Datenbank: PostgreSQL
- Betrieb: Docker auf Unraid

## Verzeichnisstruktur

- `backend/` – FastAPI-Anwendung, Datenmodelle, Migrationen und Importdienste
- `frontend/` – öffentlicher Duftkatalog und Admin Center
- `docs/` – Projektdokumentation
- `backend/tests/` – automatisierte Backend-Tests
- `docker-compose.dev.yml` – getrennte Entwicklungsumgebung

## Performance-Daten

Seit Paket 16 unterstützt DGD strukturierte und vergleichbare Performance-Daten je Duft:

- Haltbarkeit als Stundenbereich und normalisierter Score
- Projektion, Sillage, Drydown und Gesamtperformance
- Projektion in der ersten Stunde und nach drei Stunden
- Quellenanzahl, Vertrauensgrad und Quellenabweichung
- Prüfstatus, Recherchedatum, Version und Produktionszeitraum
- persönliche Bewertungen getrennt von recherchierten Community-Werten

Die öffentliche Detailansicht stellt diese Angaben in einer eigenen Performance-Karte dar. Fehlende Werte bleiben ausdrücklich als offen gekennzeichnet; DGD erzeugt keine geschätzten Ersatzwerte aus Legacy-Feldern.

Weitere technische Details stehen in [`docs/performance-data.md`](docs/performance-data.md).

## Entwicklung und Produktion

Die Entwicklung erfolgt getrennt von der laufenden Produktionsinstallation. Änderungen werden zuerst auf Feature-Branches in der Dev-Umgebung getestet und anschließend per Pull Request nach `main` übernommen.

Aktueller Dev-Aufruf:

```bash
cd /mnt/user/appdata/dgd-github
docker compose -f docker-compose.dev.yml up -d
```

## Tests

Backend-Tests liegen unter `backend/tests/`.

```bash
python -m pytest -q backend/tests
```
