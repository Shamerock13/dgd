# DGD – Aktueller Projektstand

Stand: 27. Juli 2026

Diese Datei ist die kompakte, maßgebliche Übersicht über den tatsächlich auf `main` vorhandenen Funktionsstand. Detailentscheidungen stehen zusätzlich in den jeweiligen Fachdateien unter `docs/`.

## Umgesetzte Pakete

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
13. Scanner-Betrieb & automatische Fälligkeit 1.0
14. Suche, Filter & Navigation 2.0

## Paket 14 abgeschlossen

**Suche, Filter & Navigation 2.0** umfasst:

- den paginierten Backend-Endpunkt `GET /api/catalog/fragrances`,
- gewichtete Suche und serverseitige Filter,
- den Katalog 2.0 als öffentliche Hauptansicht unter `/`,
- das bestehende Admin-Center getrennt unter `/admin.html`,
- 24 Ergebnisse pro Katalogseite,
- URL-basierte Filter, Sortierung und Seitennummer,
- dauerhaft verlinkbare Duftdetails,
- Browser-Historie für Ergebnis-, Detail- und Profilnavigation,
- verzögerte Texteingabe und Schutz gegen verspätete Antworten,
- Suche und Pagination in den Admin-Listen für Düfte und Marken,
- dauerhaft verlinkbare Markenprofile mit Stammdaten und Duftliste,
- dauerhaft verlinkbare Parfümeurprofile mit exakter Zuordnung ihrer Kreationen.

Die praktische Dev-Abnahme ist vollständig erfolgreich. Bestätigt wurden Suche, Filter, Pagination, Direktlinks, responsive Darstellung, Browser-Zurück, Admin-Suche, Rücksprung zum bearbeiteten Datensatz sowie Marken- und Parfümeurprofile einschließlich direkt aufrufbarer Profil-URLs.

## Scanner-Betrieb

Die Dev-Umgebung besitzt den getrennten Container `DGD-Dev-Scanner`. Der Worker:

- läuft unabhängig von Frontend und API,
- prüft ausschließlich aktive und fällige Recherchequellen,
- verwendet PostgreSQL-Advisory-Locks gegen parallele Doppelläufe derselben Quelle,
- speichert Heartbeat, letzten Zyklusstatus und Fehler,
- kann im Bereich **Recherche & Anreicherung** ein- oder ausgeschaltet werden,
- zeigt pro Quelle den nächsten geplanten Lauf,
- legt Treffer weiterhin ausschließlich in der Import-Warteschlange ab.

API-Endpunkte:

```text
GET /api/research/scanner/status
PUT /api/research/scanner/status
```

Der Worker wird über folgenden Moduleinstieg gestartet:

```text
python -m app.scanner_worker
```

## Recherche- und Sicherheitsregeln

- nur öffentliche HTTP- und HTTPS-Ziele
- interne, private, reservierte und lokale Netzwerkziele bleiben blockiert
- `SINGLE`- und `LIST`-Adapter
- höchstens 100 Produktseiten pro Mehrseitenlauf
- keine automatische Veröffentlichung
- Dublettenprüfung vor Freigabe
- Gemini-Twins nur mit konkreter Grounding-Quelle
- bekannte Feldwerte und Twin-Kandidaten werden ausgeschlossen
- Duftnoten und Akkorde werden zentral normalisiert

## Datenbankstand

Das explizite DGD-Migrationsschema bleibt bei `0011`. Recherche-, Scanner-, Gemini- und Verlaufsstrukturen werden idempotent über registrierte SQLAlchemy-Modelle und abgesicherte SQL-Anweisungen angelegt.

## Qualitätssicherung

Die GitHub-CI prüft:

```bash
python -m compileall -q backend/app
npm install
npm run build
```

Neue Pakete gelten erst nach erfolgreichem Test in der separaten Dev-Umgebung als praktisch abgenommen.

## Nächster Schritt

**Paket 15 – Datenvalidierung & Importqualität 2.0 beginnen.**

## Dokumentationsregel

Nach jedem größeren Paket werden mindestens geprüft:

- `docs/CURRENT_STATUS.md`
- `docs/PROJECT_CONTEXT.md`
- `docs/ROADMAP.md`
- die jeweilige technische Fachdatei
- `docs/DEV_WORKFLOW.md`, falls sich Arbeitsweise, Container oder Tests ändern

Der Chat ist nicht das Projektgedächtnis. Maßgeblich sind Repository und Dokumentation.