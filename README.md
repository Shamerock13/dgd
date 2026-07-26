# DGD

**Das Große Parfum- & Duftzwillinge-Lexikon**

DGD ist eine Webanwendung zur strukturierten Verwaltung von Parfums,
Marken, Duftzwillingen, Parfümeuren und Quellen.

## Technischer Aufbau

- Backend: FastAPI
- Frontend: React und Vite
- Datenbank: PostgreSQL
- Betrieb: Docker auf Unraid

## Verzeichnisstruktur

```text
backend/    FastAPI-Anwendung und Importdienste
frontend/   React-Frontend
docs/       Projektdokumentation
tests/      Automatisierte Tests
docker/     Docker-Konfiguration
set -e

WORK="/mnt/user/appdata/dgd-github"

echo "=== README und Projektdokumente fertigstellen ==="

cat > "$WORK/README.md" <<'EOF'
# DGD

**Das Große Parfum- & Duftzwillinge-Lexikon**

DGD ist eine Webanwendung zur strukturierten Verwaltung von Parfums,
Marken, Duftzwillingen, Parfümeuren und Quellen.

## Technischer Aufbau

- Backend: FastAPI
- Frontend: React und Vite
- Datenbank: PostgreSQL
- Betrieb: Docker auf Unraid

## Verzeichnisstruktur

- `backend/` – FastAPI-Anwendung und Importdienste
- `frontend/` – React-Frontend
- `docs/` – Projektdokumentation
- `tests/` – Automatisierte Tests
- `docker/` – Docker-Konfiguration

## Aktueller Stand

Die stabile Produktionsversion ist DGD 1.2.0.

Die Entwicklung in diesem Repository erfolgt getrennt von der laufenden
Produktionsinstallation.
