# DGD 2.0 – Roadmap

Stand: 27. Juli 2026

Diese Roadmap zeigt den aktuellen Entwicklungsstand und die Reihenfolge der nächsten größeren Pakete. Maßgeblich für den tatsächlich auf `main` vorhandenen Funktionsstand bleibt zusätzlich `docs/CURRENT_STATUS.md`.

## Abgeschlossen

1. ✅ Detailansicht & Duftzwillinge 2.0
2. ✅ Bildverwaltung & Bildquellen 1.0
3. ✅ Markenprofile 1.0
4. ✅ Quellen & Verifizierung 1.0
5. ✅ Parfümeurprofile 1.0
6. ✅ Datenqualität & redaktionelle Arbeitsliste 1.0
7. ✅ Lokaler Bildupload & Medienablage 1.0
8. ✅ Automatische Recherche & Import-Warteschlange 1.0
9. ✅ Recherchequellen & zeitgesteuerter Scanner 1.0
10. ✅ Quellenadapter & Mehrseiten-Scanner 1.0
11. ✅ Gemini-Recherche & Datenqualität 1.0
12. ✅ Gemini-Rechercheverlauf & Tokenkontrolle 1.0
13. ✅ Scanner-Betrieb & automatische Fälligkeit 1.0

## In Arbeit

14. 🚧 Suche, Filter & Navigation 2.0

Bereits umgesetzt:

- paginierter Katalogendpunkt `GET /api/catalog/fragrances`
- gewichtete Suche nach Duftname, Marke, strukturierter Duftnote, Akkorden, Parfümeur und Beschreibung
- serverseitige Filter für Marke, Zielgruppe, Konzentration, Duftnote, Jahr, Preis und Haltbarkeit
- definierte Sortierungen und begrenzte Seitengröße
- Facetten für Konzentrationen und Jahresbereich
- eigener Dev-Katalog unter `/catalog.html`
- echte Pagination mit 24 Ergebnissen pro Seite
- URL-basierte Filter, Sortierung und Seitennummer
- verlinkbare Duftdetails und Browser-Historie
- verzögerte Suche und Schutz gegen verspätete Antworten

Noch offen:

- praktische Dev-Abnahme des neuen Katalogs
- Entscheidung über Ablösung oder Integration der bisherigen öffentlichen Ansicht
- dauerhaft verlinkbare Marken- und Parfümeuransichten
- stabilere Admin-Suche

Für später vorgemerkt:

- Tippfehler-Toleranz mit `pg_trgm`
- Autovervollständigung und Suchvorschläge
- Filterfacetten mit Trefferzahlen
- Mehrfachauswahl von Duftnoten mit UND-/ODER-Logik
- lesbare Slugs zusätzlich zu UUID-Links

## Danach vorgesehen

15. ⬜ Datenvalidierung & Importqualität 2.0
16. ⬜ Admin-Bereich 2.0
17. ⬜ Vergleich & Bewertung 2.0
18. ⬜ Preisbeobachtung & Händlervergleich 1.0
19. ⬜ Spätere Benutzerfunktionen

## Paket 13 – umgesetzter Umfang

- eigener Dev-Container `DGD-Dev-Scanner`
- Workerstart über `python -m app.scanner_worker`
- automatische Auswahl ausschließlich aktiver und fälliger Quellen
- PostgreSQL-Advisory-Lock pro Quelle gegen parallele Doppelläufe
- sichtbarer Heartbeat und letzter Zyklusstatus
- Ein-/Ausschalter und Prüfintervall im Recherchebereich
- sichtbarer nächster Lauf pro Quelle
- Fehler stoppen den Worker nicht dauerhaft
- weiterhin keine automatische Freigabe von Treffern

## Spätere Pakete

### Datenvalidierung & Importqualität 2.0

- strengere Backend-Validierung
- robustere Dublettenerkennung bei Schreibvarianten
- klarere Konflikte und Fehlerberichte

### Admin-Bereich 2.0

- Suche, Filter und Pagination in großen Listen
- klarere Formulare und bessere mobile Bedienung

### Vergleich & Bewertung 2.0

- nachvollziehbare Ähnlichkeitskriterien
- getrennte Betrachtung von Duftverlauf, Noten, Haltbarkeit und Projektion

### Preisbeobachtung & Händlervergleich 1.0

- getrennt von der KI betriebene Händlerabfragen
- günstigstes belastbares Angebot und Preisverlauf
- Zuordnung nach Duft, Größe und Konzentration

## Dokumentationsregel

Nach jedem größeren Paket werden `CURRENT_STATUS`, `PROJECT_CONTEXT`, `ROADMAP`, die Fachdatei und bei Workflowänderungen `DEV_WORKFLOW` geprüft und aktualisiert.
