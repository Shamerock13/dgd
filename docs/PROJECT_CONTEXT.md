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
- Duftdetails werden als eigene Ansicht innerhalb der App dargestellt.
- Strukturierte Duftnoten werden über `GET /api/fragrances/{fragrance_id}/notes` geladen.

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
- Eigene Duftdetailansicht statt Modal
- Zurück-Navigation zur vorherigen Übersicht
- Strukturierte Kopf-, Herz- und Basisnoten
- Freitext-Fallback für noch nicht strukturierte Duftnoten
- Duftcharakter mit Haltbarkeit, Projektion, Süße und Frische
- Zugehörige Duftzwillinge direkt am Duft
- Ähnlichkeit, Gemeinsamkeiten, Unterschiede und Quellenhinweise
- Preisabstand und Kennzeichnung des günstigeren Duftes
- Responsive Detailansicht
- Bild-Fallback bei fehlenden oder fehlerhaften Bildquellen

## Zielbild DGD 2.0

DGD soll sich von einer einfachen Datenbankoberfläche zu einem hochwertigen Parfum- und Duftzwillinge-Lexikon entwickeln.

Langfristig geplant:

- Bessere Bildverwaltung und einheitliche Bildquellen
- Markenprofile
- Parfümeurprofile
- Sichtbare Quellen und Verifizierungsstatus
- Bessere Admin-Suche und Pagination
- Saubere Datenvalidierung
- Master-Import als zentrale Datenquelle
- Erweiterter Vergleich und nachvollziehbare Ähnlichkeitsbewertung
- Später eventuell Benutzerbewertungen, Favoriten und Sammlungen

## Arbeitsweise

- Änderungen zuerst direkt im GitHub-Repository durchführen.
- Größere zusammenhängende Pakete statt vieler kleiner Änderungen umsetzen.
- Vor jeder Änderung den aktuellen Code lesen.
- Änderungen möglichst als sauberen Commit auf `main` einspielen.
- Keine Produktionscontainer verändern.
- Keine produktive Datenbank anfassen.
- Nach jedem größeren Paket Projektstand, Entscheidungen, neue Ideen und nächste Schritte in den Dateien unter `docs/` dokumentieren.
- Der Chat ist kein dauerhafter Projektspeicher; maßgeblich ist die Dokumentation im Repository.

Danach werden Änderungen auf Unraid geholt mit:

```bash
cd /mnt/user/appdata/dgd-github
GIT_SSH_COMMAND='ssh -i /root/.ssh/dgd_github -o IdentitiesOnly=yes' git pull origin main
docker restart DGD-Dev-Frontend DGD-Dev-Backend
```

## Zuletzt abgeschlossenes Paket

**Detailansicht & Duftzwillinge 2.0**

Umgesetzt in:

- `frontend/src/main.jsx`
- `frontend/src/detail.css`

Validiert mit:

```bash
cd frontend
npm install
npm run build
```

## Nächstes größeres Paket

**Bildverwaltung & Bildquellen**

Geplante Schwerpunkte:

- Einheitliche Strategie für externe und spätere lokale Bilder
- Robuste Fehlerbehandlung bei ungültigen Bild-URLs
- Wiederverwendbare Bildkomponente für Karten und Detailseiten
- Bessere Platzhalter und Fallbacks
- Prüfung, wie Bildquellen und Bildstatus im Master-Import gepflegt werden sollen

Vor Beginn insbesondere lesen:

- `frontend/src/main.jsx`
- `frontend/src/styles.css`
- `frontend/src/detail.css`
- `backend/app/main.py`
- `backend/app/models.py`
- `backend/app/schemas.py`
- `backend/app/migrations.py`
- `backend/app/master_import_service.py`

## Aktueller Stand: Bildverwaltung & Bildquellen 1.0

Die Bildverwaltung wird bewusst in zwei Stufen umgesetzt. Stufe 1 verwaltet externe oder künftig lokale Bildpfade samt Quelle, Nutzungsnotiz und Prüfstatus. Ein echter Upload folgt erst mit einem klaren Unraid-Speicher-, Backup- und Löschkonzept.

Umgesetzt in diesem Paket:

- Migration `0007` für Bildmetadaten
- Bildquelle, Quellenlink und Nutzungs-/Rechtehinweis je Duft
- Status `OPEN`, `VERIFIED` oder `BROKEN`
- einheitlicher Bildbaustein für Karten, Admin und Detailseite
- belastbarer Fallback bei leerer oder defekter Bild-URL
- Import-Unterstützung für die neuen Bildfelder
- Vorbereitung auf spätere lokale Pfade wie `/media/...`

## Aktueller Stand: Markenprofile 1.0

Umgesetzt sind eigenständige Markenseiten mit Herkunft, Gründungsjahr, offizieller Website, Beschreibung und Verifizierungsstatus. Jede Markenseite zeigt Kennzahlen sowie alle zugeordneten Düfte mit eigener Suche und Sortierung. Von Duftdetailseiten kann direkt zum Markenprofil gewechselt werden. Schema-Version ist nun `0008`.


## Aktueller Stand: Quellen & Verifizierung 1.0

Das bestehende `master_sources`-Register ist jetzt über die App nutzbar. Quellen können Marken, Düften, Duftzwillingen oder allgemeinen Themen zugeordnet werden. Vertrauensstatus (`OPEN`, `REVIEW`, `TRUSTED`, `REJECTED`) und Nutzungsstatus (`OPEN`, `ALLOWED`, `RESTRICTED`, `INTERNAL`) bilden den redaktionellen Prüfprozess ab. Schema-Version ist nun `0009`.

## Aktueller Stand: Parfümeurprofile 1.0

Die vorhandene Tabelle `master_perfumers` ist jetzt vollständig über die App nutzbar. Profile enthalten Biografie, Nationalität, Geburtsjahr, Stil, bekannte Werke, Primärquelle, redaktionelle Notiz und Artikelstatus. Duftdetailseiten verlinken direkt auf passende Profile. Schema-Version ist `0010`.
