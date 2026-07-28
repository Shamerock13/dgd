# DGD 2.0 – Roadmap

Stand: 28. Juli 2026

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
16.1 ✅ Strukturiertes Performance-Datenmodell
16.2 ✅ Performance-Karte im Duftprofil

## In Arbeit

15. 🚧 Datenvalidierung & Importqualität 2.0

Praktisch in Dev bestätigt:

- Qualitätsvorschau und konservative Dublettenerkennung
- Entscheidungen `CREATE`, `DUPLICATE`, `REVIEW` und `BLOCK`
- Qualitätsanzeige im Admin-Center
- geschützter Commit ohne Teilschreibvorgang
- bewusste Auflösung von `REVIEW`-Zeilen
- neuer Duft, vorhandenen Kandidaten verwenden oder Zeile ausschließen
- gespeicherte Importberichte

Noch offen:

- Master-Import mit denselben Regeln absichern
- Paket 15 vollständig abschließen

16.3 🚧 Zeitlicher Duftverlauf

Im Branch `feature/performance-timeline` umgesetzt:

- drei sichtbare Phasen: Opening, Herzphase und Drydown
- Nutzung der bestehenden Felder `projection_first_hour`, `projection_after_three_hours` und `drydown_strength`
- responsive Balkendarstellung pro Phase
- feste Stärke-Bezeichnungen statt freier oder erfundener Texte
- Stärke-Badge aus dem vorhandenen Gesamtperformance-Score
- deterministische Kurzbeschreibung der Entwicklung
- sichtbare Leerzustände für fehlende Phasenwerte
- aktualisierte Fach- und Projektdokumentation

Noch offen:

- Frontend-Build und Browserprüfung in Dev
- Prüfung mit leerem und befülltem Performance-Datensatz
- visuelle Abnahme und Merge

18. 🚧 Preisbeobachtung & Händlervergleich 1.0

Erster Backend-Baustein:

- Händlerstammdaten
- aktuelle Angebote pro Duft, Händler und Produkt-URL
- getrennte Speicherung von Warenpreis und Versand
- Größen und Produktarten wie Flakon, Tester, Set, Probe und Refill
- unveränderliche Preisbeobachtungen für den Verlauf
- günstigster verfügbarer Gesamtpreis
- Preis pro 100 ml
- historischer Bestpreis und Verlauf für bis zu 1095 Tage

Danach:

- Admin-Oberfläche für Händler und Testangebote
- Händleradapter
- tägliche automatische Preisprüfung im Scanner-Worker
- Preisbox und Verlauf in der Duftdetailansicht
- Preisalarm

## Als Nächstes vorgesehen

16.4 ⬜ Duft-DNA

Geplant ist eine visuelle Charakterdarstellung, beispielsweise für:

- frisch und zitrisch
- holzig und würzig
- süß und gourmandig
- rauchig und ledrig
- grün, pudrig oder animalisch

Vor der Umsetzung muss festgelegt werden, welche Dimensionen gespeichert, recherchiert und persönlich bewertet werden. Ein Radar- oder Balkendiagramm darf nur auf strukturierten Werten beruhen.

16. ⬜ Admin-Bereich 2.0
17. ⬜ Vergleich & Bewertung 2.0
19. ⬜ Spätere Benutzerfunktionen

## Für später vorgemerkt

- feinere Performance-Zeitpunkte mit eigenem Datenmodell
- Tippfehler-Toleranz mit `pg_trgm`
- Autovervollständigung und Suchvorschläge
- Filterfacetten mit Trefferzahlen
- Mehrfachauswahl von Duftnoten mit UND-/ODER-Logik
- lesbare Slugs zusätzlich zu UUID-Links

## Dokumentationsregel

Nach jedem größeren Paket werden `CURRENT_STATUS`, `PROJECT_CONTEXT`, `ROADMAP`, die Fachdatei und bei Workflowänderungen `DEV_WORKFLOW` geprüft und aktualisiert.
