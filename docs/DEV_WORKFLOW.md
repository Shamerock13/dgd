# DGD – Entwicklungsworkflow

Dieser Ablauf gilt für Änderungen an `Shamerock13/dgd`.

## Grundregeln

- Änderungen zuerst im GitHub-Repository durchführen.
- Vor jeder Änderung den aktuellen Code lesen.
- Größere zusammenhängende Pakete bevorzugen.
- Änderungen sauber committen.
- Produktion niemals direkt verändern.
- Produktive Container und die produktive Datenbank nicht für Tests verwenden.
- Tests ausschließlich in der separaten Dev-Umgebung durchführen.

## 1. Änderung in GitHub

Relevante Dateien im Repository lesen und anschließend die Änderung umsetzen.

Besonders wichtige Kern-Dateien:

- `frontend/src/main.jsx`
- `frontend/src/styles.css`
- `backend/app/main.py`
- `backend/app/models.py`
- `backend/app/schemas.py`
- `backend/app/migrations.py`

Die Änderung anschließend als nachvollziehbaren Commit auf `main` bringen.

## 2. Änderungen auf Unraid holen

Das lokale Repository befindet sich unter:

```text
/mnt/user/appdata/dgd-github
```

Aktuellen Stand von `main` laden:

```bash
cd /mnt/user/appdata/dgd-github
GIT_SSH_COMMAND='ssh -i /root/.ssh/dgd_github -o IdentitiesOnly=yes' git pull origin main
```

## 3. Dev-Container neu starten

Nach dem Pull Frontend und Backend neu starten:

```bash
docker restart DGD-Dev-Frontend DGD-Dev-Backend
```

Die Dev-Umgebung verwendet:

- Frontend: Port `15173`
- Backend: Port `18080`
- PostgreSQL: Port `55432`
- Docker-Netzwerk: `dgd-dev`

## 4. Testen

Nach dem Neustart prüfen:

1. Frontend ist über Port `15173` erreichbar.
2. Backend antwortet über Port `18080`.
3. `/api/health` meldet einen erfolgreichen Status.
4. Browser-Konsole enthält keine neuen Fehler.
5. API-Aufrufe über den Vite-Proxy `/api` funktionieren.
6. Die betroffene Funktion arbeitet wie erwartet.
7. Mobile Darstellung und Navigation prüfen, wenn Frontend-Code geändert wurde.
8. Bei Datenbankänderungen Migrationen und Start mit einer frischen Dev-Datenbank prüfen.

## 5. Datenbank- und Migrationstests

- Nur `DGD-Dev-PostgreSQL` verwenden.
- Niemals die produktive Datenbank anfassen.
- Migrationen müssen idempotent sein.
- Neue oder ältere Datenbanken müssen sicher gestartet werden können.
- Vor `UPDATE`- oder `ALTER COLUMN`-Anweisungen benötigte Legacy-Spalten mit `ADD COLUMN IF NOT EXISTS` absichern.
- Aktuelle Schema-Version über `/api/system/migrations` kontrollieren.

## 6. Master-Import testen

Master-Import ausschließlich in der Dev-Umgebung prüfen:

```text
POST /api/import/master/preview
POST /api/import/master/commit
GET  /api/import/master/runs
```

Dabei kontrollieren:

- Vorschau und Validierungsfehler
- Anzahl der Marken, Düfte, Duftzwillinge und Quellen
- Dubletten und fehlerhafte Zuordnungen
- Importhistorie
- Verhalten bei einer frischen Datenbank

## 7. Produktionsschutz

Die folgenden Container dürfen durch diesen Workflow nicht verändert oder für Tests verwendet werden:

- `DGD-App`
- `DGD-PostgreSQL`
- `DGD-Updater`

Die stabile Produktionsversion ist `dgd-core:1.2.0`.

Ein späterer Produktions-Rollout ist ein eigener, bewusst freizugebender Schritt und gehört nicht zum normalen GitHub → Unraid → Neustart → Test-Ablauf.
