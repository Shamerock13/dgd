# DGD – Projektkontext

Stand: 27. Juli 2026

Wir arbeiten am Repository `Shamerock13/dgd`. Diese Datei beschreibt Architektur, Betriebsregeln, zentrale Datenflüsse und den aktuell maßgeblichen Entwicklungsstand. Ergänzend gelten `docs/CURRENT_STATUS.md`, `docs/ROADMAP.md` und `docs/DEV_WORKFLOW.md`.

## Aktuelle Architektur

### Produktion auf Unraid

- `DGD-App`
- `DGD-PostgreSQL`
- `DGD-Updater`
- stabile Produktionsversion: `dgd-core:1.2.0`
- Produktion und produktive Datenbank werden niemals direkt für Entwicklung oder Tests verwendet.

### Separate Dev-Umgebung

- `DGD-Dev-Frontend`
- `DGD-Dev-Backend`
- `DGD-Dev-PostgreSQL`
- Docker-Netzwerk: `dgd-dev`
- Frontend-Port: `15173`
- Backend-Port: `18080`
- PostgreSQL-Port: `55432`

Das lokale Repository auf Unraid liegt unter:

```text
/mnt/user/appdata/dgd-github
```

Lokale Medien der Dev-Umgebung liegen persistent unter:

```text
/mnt/user/appdata/dgd-dev-media
```

## Technik

### Backend

- FastAPI
- SQLAlchemy
- PostgreSQL
- Datenbankzugriff über `DATABASE_URL`
- `Base.metadata.create_all()` plus eigene idempotente Migrationen
- explizites DGD-Migrationsschema aktuell bis `0011`
- zusätzliche Recherche-, Scanner-, Gemini- und Verlaufsstrukturen werden idempotent über registrierte Modelle beziehungsweise `CREATE TABLE IF NOT EXISTS` und abgesicherte `ALTER TABLE`-Anweisungen angelegt.

### Frontend

- React
- Vite
- relative API-Aufrufe über `/api`
- Vite-Proxy auf `DGD-Dev-Backend:8080`
- eigene Duft-, Marken- und Parfümeuransichten innerhalb der App
- Admin-Bereiche für Datenpflege, Quellen, Recherche, Import und Qualitätssicherung

## Zentrale Datenbereiche

Vorhanden sind unter anderem:

- Marken und Düfte
- Duftzwillinge und Twin-Prüfvorschläge
- strukturierte Duftnoten und Freitextfelder
- Quellen- und Verifizierungsregister
- Parfümeurprofile
- Bildmetadaten und lokale Medienpfade
- Master-Import und Importhistorie
- Recherchekandidaten und Import-Warteschlange
- verwaltete Recherchequellen und Scanläufe
- Ergänzungsaufträge und Feldfunde
- Gemini-Rechercheverlauf mit Token- und Ergebniskennzahlen

Der Master-Import läuft über:

```text
POST /api/import/master/preview
POST /api/import/master/commit
GET  /api/import/master/runs
```

## Aktueller Funktionsstand

Umgesetzt sind:

1. Detailansicht & Duftzwillinge 2.0
2. Bildverwaltung & Bildquellen 1.0
3. Markenprofile 1.0
4. Quellen & Verifizierung 1.0
5. Parfümeurprofile 1.0
6. Datenqualität & redaktionelle Arbeitsliste 1.0
7. Lokaler Bildupload & Medienablage 1.0
8. Automatische Recherche & Import-Warteschlange 1.0
9. Recherchequellen & zeitgesteuerter Scanner 1.0
10. Quellenadapter & Mehrseiten-Scanner 1.0
11. Gemini-Recherche & Datenqualität 1.0
12. Gemini-Rechercheverlauf & Tokenkontrolle 1.0

Die detaillierte Statusbeschreibung steht in `docs/CURRENT_STATUS.md`; die Reihenfolge weiterer Pakete in `docs/ROADMAP.md`.

## Recherche- und Prüfprinzipien

- öffentliche Rechercheziele dürfen nur über HTTP oder HTTPS angesprochen werden
- private, lokale, reservierte und Link-Local-Ziele bleiben blockiert
- Recherchetreffer werden nicht automatisch veröffentlicht
- neue Produkte landen zunächst in der Import-Warteschlange
- Feldvorschläge landen zunächst in der Prüfliste
- Duftzwillinge aus Gemini benötigen eine konkrete brauchbare Grounding-Quelle
- bereits offene, übernommene, abgelehnte oder konfliktbehaftete Feldwerte werden nicht erneut vorgeschlagen
- bereits bekannte oder geprüfte Twin-Kandidaten werden ausgeschlossen
- Duftnoten und Akkorde werden zentral normalisiert
- historische Bereinigungen verwenden zuerst einen nicht schreibenden Prüflauf
- Gemini-Läufe protokollieren Zeitpunkt, Status, Modell, Quellen, Treffer und Tokenverbrauch
- ein 15-minütiger Schutz verhindert versehentliche direkte Wiederholungen; ein bewusster Neustart bleibt möglich

Wichtige Fachdateien:

```text
docs/RESEARCH_AUTOMATION.md
docs/SOURCE_ADAPTERS.md
docs/GEMINI_RESEARCH_AND_DATA_QUALITY.md
```

## Arbeitsweise

- vor jedem größeren Paket zuerst `docs/PROJECT_CONTEXT.md`, `docs/ROADMAP.md` und `docs/DEV_WORKFLOW.md` lesen
- danach den aktuellen Code und relevante Konfigurationen prüfen
- Änderungen zuerst im GitHub-Repository auf einem passenden Branch umsetzen
- zusammengehörige Änderungen gemeinsam entwickeln
- zentrale GitHub-CI muss Backend-Compile und Frontend-Build erfolgreich abschließen
- anschließend per sauberem Squash-Commit nach `main` mergen
- Tests ausschließlich in der separaten Dev-Umgebung durchführen
- Produktion nicht verändern
- nach jedem größeren Paket Status, Roadmap, Projektkontext und technische Fachdateien aktualisieren
- der Chat ist kein dauerhaftes Projektgedächtnis; maßgeblich ist das Repository

Aktuellen Stand auf Unraid holen:

```bash
cd /mnt/user/appdata/dgd-github
GIT_SSH_COMMAND='ssh -i /root/.ssh/dgd_github -o IdentitiesOnly=yes -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no' \
git pull origin main
```

Je nach Paket anschließend die betroffenen Dev-Container neu starten. Frontend und Backend gemeinsam:

```bash
docker restart DGD-Dev-Backend DGD-Dev-Frontend
```

## Nächstes größeres Paket

**Scanner-Betrieb & automatische Fälligkeit 1.0**

Ziele:

- eigener Scanner-Worker getrennt von Frontend und API
- regelmäßiger Abruf ausschließlich fälliger aktiver Quellen
- Sperre gegen parallele Doppelläufe derselben Quelle
- klarer Ein-/Ausschalter für den automatischen Betrieb
- Laufzeit-, Fehler- und Erfolgskennzahlen
- sichtbarer letzter und nächster geplanter Lauf
- kontrollierte Wiederholung temporärer Fehler
- keine automatische Freigabe von Warteschlangen-Treffern
- dokumentierte Betriebs-, Neustart-, Backup- und Wiederherstellungsregeln

Produktion wird für dieses Paket erst nach erfolgreicher Dev-Abnahme in einem eigenen, ausdrücklich freigegebenen Schritt vorbereitet.