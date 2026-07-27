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

```bash
cd /mnt/user/appdata/dgd-github
GIT_SSH_COMMAND='ssh -i /root/.ssh/dgd_github -o IdentitiesOnly=yes -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no' \
git pull origin main
```

Bei Änderungen am Scanner-Worker oder Compose:

```bash
docker compose -f docker-compose.dev.yml up -d --build backend scanner-worker frontend
```

Nur bei reinen Backend-/Frontend-Änderungen ohne Compose-Anpassung genügt anschließend gegebenenfalls:

```bash
docker restart DGD-Dev-Backend DGD-Dev-Frontend
```

## Dev-Abnahme

Mindestens prüfen:

1. Frontend ist über Port `15173` erreichbar.
2. Backend antwortet über Port `18080`.
3. `/api/health` ist erfolgreich.
4. Browser-Konsole zeigt keine neuen Fehler.
5. Betroffene Funktion arbeitet wie erwartet.
6. Bei Datenbankänderungen Start mit bestehender und frischer Dev-Datenbank prüfen.
7. Produktion bleibt unberührt.

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

## Produktionsschutz

Diese Container dürfen durch den normalen Entwicklungsworkflow nicht verändert werden:

- `DGD-App`
- `DGD-PostgreSQL`
- `DGD-Updater`

Ein Produktions-Rollout ist immer ein eigener, ausdrücklich freizugebender Schritt.
