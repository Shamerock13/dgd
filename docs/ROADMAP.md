# DGD 2.0 – Roadmap

Stand: 27. Juli 2026

Diese Roadmap zeigt den aktuellen Entwicklungsstand. Maßgeblich für den tatsächlich auf `main` vorhandenen Funktionsstand bleibt zusätzlich `docs/CURRENT_STATUS.md`.

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
14. ✅ Suche, Filter & Navigation 2.0

## In Arbeit

15. 🚧 Datenvalidierung & Importqualität 2.0

Bereits praktisch in Dev bestätigt:

- Qualitätsvorschau `POST /api/import/quality/preview`
- konservative Normalisierung von Marken- und Duftnamen
- sichere Erkennung exakter und normalisierter Dubletten
- ähnliche Treffer nur als manuelle Prüfhinweise
- Entscheidungen `CREATE`, `DUPLICATE`, `REVIEW` und `BLOCK`
- Qualitätsanzeige im Admin-Center
- geschützter Commit über `POST /api/import/quality/commit`
- vollständiger Importstopp bei ungelösten oder blockierten Zeilen
- kein Teilschreibvorgang beim Abbruch

Aktueller Baustein, Dev-Abnahme offen:

- bewusste Auflösung von `REVIEW`-Zeilen
- neuer Duft, vorhandenen Kandidaten verwenden oder Zeile ausschließen
- bewusste Original-/Alternativzuordnung bei Duftzwillingen
- erneute serverseitige Prüfung aller Entscheidungen
- dauerhafte Importberichte über `GET /api/import/quality/runs`

Danach:

- Master-Import mit denselben Regeln absichern
- Paket 15 vollständig dokumentieren und abschließen

## Danach vorgesehen

16. ⬜ Admin-Bereich 2.0
17. ⬜ Vergleich & Bewertung 2.0
18. ⬜ Preisbeobachtung & Händlervergleich 1.0
19. ⬜ Spätere Benutzerfunktionen

## Für später vorgemerkt

- Tippfehler-Toleranz mit `pg_trgm`
- Autovervollständigung und Suchvorschläge
- Filterfacetten mit Trefferzahlen
- Mehrfachauswahl von Duftnoten mit UND-/ODER-Logik
- lesbare Slugs zusätzlich zu UUID-Links

## Dokumentationsregel

Nach jedem größeren Paket werden `CURRENT_STATUS`, `PROJECT_CONTEXT`, `ROADMAP`, die Fachdatei und bei Workflowänderungen `DEV_WORKFLOW` geprüft und aktualisiert.
