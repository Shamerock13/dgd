# DGD – Entwicklungsworkflow

Dieser Ablauf gilt für Änderungen an `Shamerock13/dgd`.

## Grundregeln

- Vor jedem größeren Paket zuerst `docs/PROJECT_CONTEXT.md`, `docs/ROADMAP.md` und `docs/DEV_WORKFLOW.md` lesen.
- Danach aktuellen Code und relevante Konfigurationen prüfen.
- Änderungen zuerst im GitHub-Repository auf einem Feature-Branch durchführen.
- Produktion niemals direkt verändern oder für Tests verwenden.
- Tests ausschließlich in der separaten Dev-Umgebung.
- Projektentscheidungen und nächste Schritte dauerhaft in `docs/` festhalten.

## Technische Prüfung

Backend:

```bash
python -m compileall -q backend/app
```

Frontend:

```bash
cd frontend
npm install
npm run build
```

Datenbankänderungen müssen idempotent sein. Neue und ältere Dev-Datenbanken müssen sicher starten können.

## GitHub-Ablauf

1. Feature-Branch von `main` erstellen.
2. Bestehende Architektur weiterverwenden.
3. Zusammengehörige Änderungen gemeinsam umsetzen.
4. Finalen Diff kontrollieren.
5. GitHub-CI abwarten.
6. Nach grüner CI per Squash nach `main` mergen.
7. Dokumentation im selben Paket aktualisieren.

## Dev-Umgebung

Container:

- `DGD-Dev-Frontend`
- `DGD-Dev-Backend`
- `DGD-Dev-Scanner`
- `DGD-Dev-PostgreSQL`

Ports:

- Frontend `15173`
- Backend `18080`
- PostgreSQL `55432`

Netzwerk: `dgd-dev`

## Änderungen auf Unraid holen

HTTPS ist für die Dev-Installation der bevorzugte Remote-Zugriff:

```bash
cd /mnt/user/appdata/dgd-github
git remote set-url origin https://github.com/Shamerock13/dgd.git
git fetch origin
git switch <feature-branch>
git pull --ff-only origin <feature-branch>
```

Für `main` entsprechend:

```bash
cd /mnt/user/appdata/dgd-github
git switch main
git pull --ff-only origin main
```

## Container gezielt neu bauen

Nur die betroffene Komponente neu bauen und die übrigen Dev-Dienste unangetastet lassen.

Backend:

```bash
docker compose -f docker-compose.dev.yml build backend
docker compose -f docker-compose.dev.yml up -d --no-deps --force-recreate backend
```

Frontend:

```bash
docker compose -f docker-compose.dev.yml build frontend
docker compose -f docker-compose.dev.yml up -d --no-deps --force-recreate frontend
```

Scanner-Worker:

```bash
docker compose -f docker-compose.dev.yml build scanner-worker
docker compose -f docker-compose.dev.yml up -d --no-deps --force-recreate scanner-worker
```

## Docker-Namenskonflikte

Falls Compose meldet, dass ein Dev-Containername bereits verwendet wird, ausschließlich den betroffenen Dev-Container entfernen und anschließend neu erstellen. Beispiel Frontend:

```bash
docker stop DGD-Dev-Frontend
docker rm DGD-Dev-Frontend
docker compose -f docker-compose.dev.yml up -d --no-deps --force-recreate frontend
```

Beispiel Backend:

```bash
docker stop DGD-Dev-Backend
docker rm DGD-Dev-Backend
docker compose -f docker-compose.dev.yml up -d --no-deps --force-recreate backend
```

PostgreSQL darf bei reinen Frontend- oder Backend-Tests nicht neu erstellt oder entfernt werden.

## Backendtests im Dev-Container

`backend/Dockerfile.dev` kopiert derzeit nur `backend/app` nach `/app/app`. Deshalb ist `/app/tests` im gebauten Container nicht automatisch vorhanden.

Tests vorübergehend in den laufenden Dev-Backend-Container kopieren:

```bash
cd /mnt/user/appdata/dgd-github
docker cp backend/tests DGD-Dev-Backend:/app/tests
docker exec -it DGD-Dev-Backend python -m pytest -q /app/tests
```

Erst ein späteres eigenes Workflow-Paket soll entscheiden, ob Tests dauerhaft ins Dev-Image aufgenommen werden. Produktionsimages sollen dadurch nicht unnötig vergrößert werden.

## Dev-Abnahme

Mindestens prüfen:

1. Frontend ist über Port `15173` erreichbar.
2. Backend antwortet über Port `18080`.
3. `/api/health` ist erfolgreich.
4. Browser-Konsole zeigt keine neuen Fehler.
5. Betroffene Funktion arbeitet wie erwartet.
6. Bei Datenbankänderungen Start mit bestehender und frischer Dev-Datenbank prüfen.
7. Relevante Tests ausführen und Ergebnis dokumentieren.
8. Dokumentation, Projektstatus und Roadmap prüfen.
9. Produktion bleibt unberührt.

## Scanner-Worker testen

Nach einem Worker-Paket zusätzlich prüfen:

- `DGD-Dev-Scanner` läuft dauerhaft und startet nach Neustart wieder.
- `GET /api/research/scanner/status` zeigt einen aktuellen Heartbeat.
- ausgeschaltete Automatik startet keine Quellenläufe.
- aktive und fällige Quellen werden verarbeitet.
- deaktivierte oder nicht fällige Quellen werden übersprungen.
- zwei gleichzeitige Starts derselben Quelle führen nicht zu zwei Läufen.
- letzter und nächster Lauf werden im Recherchebereich angezeigt.
- Fehler eines Quellenlaufs stoppen den Worker nicht dauerhaft.
- Treffer bleiben in der Import-Warteschlange und werden nicht automatisch freigegeben.
- Scanläufe bleiben über `/api/research/scan-runs` nachvollziehbar.

Nützliche Befehle:

```bash
docker logs --tail 100 DGD-Dev-Scanner
docker restart DGD-Dev-Scanner
```

## Dokumentation

Nach jedem größeren Paket mindestens prüfen und gegebenenfalls aktualisieren:

- `docs/CURRENT_STATUS.md`
- `docs/PROJECT_CONTEXT.md`
- `docs/ROADMAP.md`
- technische Fachdatei
- `docs/DEV_WORKFLOW.md`, wenn sich Container, Tests oder Deployment ändern

Ein Paket ist dokumentarisch erst vollständig, wenn Projektstatus und Roadmap den tatsächlichen Stand von `main` beziehungsweise eines ausdrücklich genannten offenen Feature-Branches korrekt unterscheiden.

## Produktionsschutz

Diese Container dürfen durch den normalen Entwicklungsworkflow nicht verändert werden:

- `DGD-App`
- `DGD-PostgreSQL`
- `DGD-Updater`

Ein Produktions-Rollout ist immer ein eigener, ausdrücklich freizugebender Schritt.