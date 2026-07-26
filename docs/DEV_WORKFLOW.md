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
- Projektentscheidungen, Ideen, abgeschlossene Pakete und nächste Schritte dauerhaft in `docs/` festhalten.
- Der Repository-Stand ist maßgeblich; wichtige Informationen dürfen nicht nur im Chat verbleiben.

## 1. Änderung vorbereiten

Vor Beginn eines Pakets:

1. `docs/PROJECT_CONTEXT.md` lesen.
2. `docs/ROADMAP.md` lesen.
3. Relevante Quell- und Konfigurationsdateien lesen.
4. Bestehende Architektur und Datenstrukturen weiterverwenden, statt parallele Lösungen einzubauen.
5. Umfang, Ziel und bewusst nicht enthaltene Punkte des Pakets festlegen.

Besonders wichtige Kern-Dateien:

- `frontend/src/main.jsx`
- `frontend/src/styles.css`
- `frontend/src/detail.css`, sofern vorhanden oder relevant
- `backend/app/main.py`
- `backend/app/models.py`
- `backend/app/schemas.py`
- `backend/app/migrations.py`
- Import-Services bei Änderungen am Master-Import

## 2. Änderung in GitHub umsetzen

- Für größere Pakete bevorzugt einen Feature-Branch verwenden.
- Zusammenhängende Änderungen gemeinsam umsetzen.
- Vorhandene Admin-, Import- und Produktionslogik nur verändern, wenn sie zum Paket gehört.
- Keine temporären Hilfs-, Trigger- oder Workflow-Dateien im finalen Diff belassen.
- Den finalen Diff vor dem Merge kontrollieren.
- Nach erfolgreicher Prüfung per sauberem Squash-Commit oder nachvollziehbarem Commit auf `main` bringen.

## 3. Technisch prüfen

Je nach Änderung mindestens prüfen:

### Frontend

```bash
cd frontend
npm install
npm run build
```

Hinweis: Solange keine `package-lock.json` vorhanden ist, funktioniert `npm ci` nicht. In diesem Projekt daher derzeit `npm install` für die Build-Prüfung verwenden.

Zusätzlich prüfen:

- Keine neuen Build-Fehler
- Keine offensichtlichen React- oder Importfehler
- Desktop-, Tablet- und Mobilansicht bei UI-Änderungen
- Bild-Fallbacks bei fehlenden und fehlerhaften Bild-URLs
- Navigation zwischen Übersichten und Detailansichten

### Backend

- Python-Syntax und Imports
- Betroffene API-Endpunkte
- Fehlerfälle und Statuscodes
- Bestehende Clients und Schemas
- Keine unbeabsichtigten Datenbankänderungen

### Datenbank

- Nur `DGD-Dev-PostgreSQL` verwenden.
- Niemals die produktive Datenbank anfassen.
- Migrationen müssen idempotent sein.
- Neue oder ältere Datenbanken müssen sicher gestartet werden können.
- Vor `UPDATE`- oder `ALTER COLUMN`-Anweisungen benötigte Legacy-Spalten mit `ADD COLUMN IF NOT EXISTS` absichern.
- Aktuelle Schema-Version über `/api/system/migrations` kontrollieren.

## 4. Projektdokumentation aktualisieren

Nach jedem größeren Paket und vor dem finalen Merge:

### `docs/PROJECT_CONTEXT.md`

Aktualisieren, wenn sich verändert haben:

- Architektur
- Technik oder Datenfluss
- wichtige Endpunkte
- umgesetzte Funktionen
- bekannte Besonderheiten oder Fehlerbehebungen
- aktuelles nächstes Paket

### `docs/ROADMAP.md`

Aktualisieren:

- abgeschlossenes Paket als umgesetzt markieren
- tatsächlich umgesetzten Umfang festhalten
- neue Ideen dem passenden Paket zuordnen
- nächste Priorität festlegen
- bewusst verschobene Punkte sichtbar lassen

### `docs/DEV_WORKFLOW.md`

Aktualisieren, wenn sich verändert haben:

- GitHub-Ablauf
- Build- oder Testbefehle
- Unraid-Deployment
- Dev-Container
- Datenbank- oder Migrationstests
- Sicherheits- und Produktionsregeln

Dokumentationsänderungen sollen möglichst im selben Paket oder direkt anschließend als eigener sauberer Dokumentations-Commit erfolgen.

## 5. Änderungen auf Unraid holen

Das lokale Repository befindet sich unter:

```text
/mnt/user/appdata/dgd-github
```

Aktuellen Stand von `main` laden:

```bash
cd /mnt/user/appdata/dgd-github
GIT_SSH_COMMAND='ssh -i /root/.ssh/dgd_github -o IdentitiesOnly=yes' git pull origin main
```

## 6. Dev-Container neu starten

Nach dem Pull Frontend und Backend neu starten:

```bash
docker restart DGD-Dev-Frontend DGD-Dev-Backend
```

Die Dev-Umgebung verwendet:

- Frontend: Port `15173`
- Backend: Port `18080`
- PostgreSQL: Port `55432`
- Docker-Netzwerk: `dgd-dev`

## 7. In der Dev-Umgebung testen

Nach dem Neustart prüfen:

1. Frontend ist über Port `15173` erreichbar.
2. Backend antwortet über Port `18080`.
3. `/api/health` meldet einen erfolgreichen Status.
4. Browser-Konsole enthält keine neuen Fehler.
5. API-Aufrufe über den Vite-Proxy `/api` funktionieren.
6. Die betroffene Funktion arbeitet wie erwartet.
7. Navigation zurück zur vorherigen Ansicht funktioniert.
8. Mobile Darstellung und Navigation funktionieren, wenn Frontend-Code geändert wurde.
9. Fehlende oder ungültige Bild-URLs führen nicht zu einer kaputten Ansicht.
10. Bei Datenbankänderungen Migrationen und Start mit einer frischen Dev-Datenbank prüfen.

## 8. Master-Import testen

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
- Neue Datenfelder und Verknüpfungen, sofern das Paket sie betrifft

## 9. Abnahme und Fehlerbehandlung

- Erst nach erfolgreichem Test in der Dev-Umgebung gilt ein Paket als abgeschlossen.
- Gefundene Fehler werden wieder zuerst im GitHub-Repository behoben.
- Keine spontane Korrektur direkt im laufenden Dev- oder Produktionscontainer.
- Nach einer Korrektur erneut Pull, Neustart und Test durchführen.
- Erkenntnisse aus Fehlern oder Sonderfällen in den Projektdokumenten ergänzen.

## 10. Produktionsschutz

Die folgenden Container dürfen durch diesen Workflow nicht verändert oder für Tests verwendet werden:

- `DGD-App`
- `DGD-PostgreSQL`
- `DGD-Updater`

Die stabile Produktionsversion ist `dgd-core:1.2.0`.

Ein späterer Produktions-Rollout ist ein eigener, bewusst freizugebender Schritt und gehört nicht zum normalen GitHub → Unraid → Neustart → Test-Ablauf.

## Bildänderungen testen

Bei Änderungen an Bildfeldern oder der Bilddarstellung zusätzlich prüfen:

- leere Bild-URL zeigt den DGD-Fallback
- nicht erreichbare Bild-URL fällt nach `onError` auf den Fallback zurück
- Bildstatus und Quellenhinweise werden im Admin korrekt gespeichert
- externe Links öffnen mit `target="_blank"` und `rel="noreferrer"`
- relative Pfade wie `/media/...` bleiben für den späteren lokalen Upload zulässig
- keine externen Bilder automatisch herunterladen oder in Produktion kopieren

## Markenprofile testen

Bei Änderungen an Marken zusätzlich prüfen:

- Markenkarte öffnet das eigene Profil statt nur einen Filter zu setzen
- Herkunft, Gründungsjahr, Website und Status werden korrekt gespeichert
- Duftliste enthält ausschließlich Düfte der gewählten Marke
- Suche und Sortierung innerhalb der Marke funktionieren
- Navigation Duftdetail → Marke → Duft funktioniert ohne veralteten Zustand
- externe Website öffnet sicher mit `target="_blank"` und `rel="noreferrer"`


## Quellen und Verifizierung testen

- Quelle anlegen, bearbeiten und löschen
- Zuordnung zu Marke, Duft und Duftzwilling prüfen
- Vertrauensfilter im Quellenregister prüfen
- externe Quellenlinks nur mit `target="_blank"` und `rel="noreferrer"` öffnen
- Statuswerte außerhalb der definierten Enum-Werte müssen vom Backend abgelehnt werden
- Prüfübersicht muss nach Änderungen neu geladen werden

## Parfümeurprofile testen

- Profil anlegen, bearbeiten und löschen
- Löschschutz bei zugeordneten Düften prüfen
- Namenszuordnung zwischen Duft und Profil prüfen
- Navigation Duftdetail → Parfümeurprofil → Duft prüfen
- Primärquellen nur sicher extern öffnen
- Frontend-Build und Backend-Compile ausführen


## Datenqualität und Arbeitsliste testen

- `/api/quality/worklist` liefert Summary, Kategorien und Aufgaben
- fehlendes Bild, fehlende Quelle und fehlende Duftpyramide werden erkannt
- exakt vorhandene Parfümeurprofile werden nicht fälschlich beanstandet
- Prioritäts-, Kategorie- und Textfilter funktionieren gemeinsam
- Schaltfläche `Bearbeiten` öffnet den passenden Admin-Bereich
- erneute Prüfung aktualisiert die Arbeitsliste nach Änderungen
- Qualitätswert ausdrücklich nur als redaktionellen Fortschrittsindikator behandeln


## Lokale Medien testen und sichern

- Upload mit JPEG, PNG und WebP testen
- falsche Dateiendung beziehungsweise ungültige Signatur muss abgelehnt werden
- Größenlimit von 8 MB prüfen
- Ersetzen entfernt die vorherige lokale Datei
- Löschen ist nur für lokale `/media/fragrances/...`-Dateien erlaubt
- `/mnt/user/appdata/dgd-dev-media` muss in das Unraid-Backup aufgenommen werden
- Datenbank und Medienordner immer gemeinsam sichern und wiederherstellen
