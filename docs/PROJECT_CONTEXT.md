# DGD – Projektkontext

Wir arbeiten am Repository `Shamerock13/dgd`.

## Aktuelle Architektur

### Produktion auf Unraid

- `DGD-App`
- `DGD-PostgreSQL`
- `DGD-Updater`
- Stabile Produktionsversion: `dgd-core:1.2.0`
- Die Produktion darf niemals direkt verändert oder für Tests verwendet werden.

### Separate Dev-Umgebung

- `DGD-Dev-Frontend`
- `DGD-Dev-Backend`
- `DGD-Dev-PostgreSQL`
- Eigenes Docker-Netzwerk: `dgd-dev`
- Frontend-Port: `15173`
- Backend-Port: `18080`
- PostgreSQL-Port: `55432`

### Lokales Repository auf Unraid

```text
/mnt/user/appdata/dgd-github
```

## Technik

### Backend

- FastAPI
- SQLAlchemy
- PostgreSQL
- Datenbankzugriff über `DATABASE_URL`
- `Base.metadata.create_all()` plus eigene Migrationen
- Schema-Migrationen bis `0006`

### Frontend

- React
- Vite
- Relative API-Aufrufe über `/api`
- Vite-Proxy zeigt auf `DGD-Dev-Backend:8080`

## Datenbestand

Nach Master-Import ungefähr:

- 52 Marken
- 253 Düfte
- 135 Duftzwillinge
- 2 Quellen
- Aktuell keine Parfümeure aus der Quelldatei; die Struktur dafür ist vorhanden.

## Datenbank und Import

Vorhandene Tabellen und Strukturen:

- `brands`
- `fragrances`
- `twin_matches`
- Duftnoten und Zuordnungen
- `master_sources`
- `master_import_runs`
- `master_perfumers`
- `dgd_schema_migrations`

Der Master-Import läuft über:

```text
POST /api/import/master/preview
POST /api/import/master/commit
GET  /api/import/master/runs
```

Eine frische Datenbank zeigte einen Fehler in Migration `0005`. Dieser wurde behoben, indem Legacy-Spalten mit `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` vor den `UPDATE`-Anweisungen angelegt werden.

## Bereits umgesetzt

- Isolierte Dev-Umgebung
- GitHub-Repository-Struktur
- Moderne Startseite
- Neue Duftkarten
- Entdecken-Seite mit begrenzter Auswahl
- Markenbereich
- Suche
- Filter
- Sortierung
- Mobile Navigation
- Aktive Filter-Chips

## Zielbild DGD 2.0

DGD soll sich von einer einfachen Datenbankoberfläche zu einem hochwertigen Parfum- und Duftzwillinge-Lexikon entwickeln.

Langfristig geplant:

- Moderne Duftdetailseiten
- Echte Notenpyramide
- Verwandte Duftzwillinge direkt am Duft
- Preisvergleich und Ersparnis
- Ähnlichkeitsbewertung
- Bessere Bildverwaltung und Fallbacks
- Markenprofile
- Parfümeurprofile
- Sichtbare Quellen und Verifizierungsstatus
- Bessere Admin-Suche und Pagination
- Saubere Datenvalidierung
- Master-Import als zentrale Datenquelle
- Später eventuell Benutzerbewertungen, Favoriten und Sammlungen

## Arbeitsweise

- Änderungen zuerst direkt im GitHub-Repository durchführen.
- Größere zusammenhängende Pakete statt vieler kleiner Änderungen umsetzen.
- Vor jeder Änderung den aktuellen Code lesen.
- Änderungen möglichst als sauberen Commit auf `main` einspielen.
- Keine Produktionscontainer verändern.
- Keine produktive Datenbank anfassen.

Danach werden Änderungen auf Unraid geholt mit:

```bash
cd /mnt/user/appdata/dgd-github
GIT_SSH_COMMAND='ssh -i /root/.ssh/dgd_github -o IdentitiesOnly=yes' git pull origin main
docker restart DGD-Dev-Frontend DGD-Dev-Backend
```

## Nächstes größeres Paket

**Detailansicht & Duftzwillinge 2.0**

Vor Beginn insbesondere lesen:

- `frontend/src/main.jsx`
- `frontend/src/styles.css`
- `backend/app/main.py`
- `backend/app/models.py`
- `backend/app/schemas.py`
- `backend/app/migrations.py`
