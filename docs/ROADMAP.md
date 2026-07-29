# DGD 2.0 – Roadmap

Stand: 29. Juli 2026

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
16.3 ✅ Zeitlicher Duftverlauf
16.4.1 ✅ Duft-DNA-Datenmodell und API

## In Arbeit

15. 🚧 Datenvalidierung & Importqualität 2.0

Praktisch in Dev bestätigt:

- Qualitätsvorschau und konservative Dublettenerkennung
- Entscheidungen `CREATE`, `DUPLICATE`, `REVIEW` und `BLOCK`
- Qualitätsanzeige im Admin-Center
- geschützter Commit ohne Teilschreibvorgang
- bewusste Auflösung von `REVIEW`-Zeilen
- gespeicherte Importberichte

Noch offen:

- Master-Import mit denselben Regeln absichern
- Paket 15 vollständig abschließen

16.4.2 🚧 Duft-DNA-Karte

Im Branch `feature/fragrance-dna-card` umgesetzt:

- responsive Balkendarstellung aller vorhandenen DNA-Dimensionen
- stärkste Werte zuerst
- Signatur aus den drei prägendsten vorhandenen Dimensionen
- Herkunft und Prüfstatus sichtbar
- Vertrauen, Quellenanzahl, Quellenabweichung und Datenstand
- persönliche DNA optisch und fachlich getrennt
- Leerzustände ohne erfundene Werte
- Fachdatei, Projektstatus, Projektkontext und Roadmap aktualisiert

Noch offen:

- Frontend-Build in Dev
- Prüfung eines Duftes ohne DNA
- Prüfung eines partiellen Profils und persönlicher DNA
- Desktop- und Mobilabnahme
- PR zusammenführen

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

16.4.3 ⬜ Pflege und Recherche der Duft-DNA

Nach der sichtbaren Karte folgen getrennt:

- Admin-Eingabe für manuelle DNA-Werte
- kontrollierte Recherchevorschläge
- Prüf- und Freigabeworkflow
- keine automatische Veröffentlichung ungeprüfter KI-Werte

16. ⬜ Admin-Bereich 2.0
17. ⬜ Vergleich & Bewertung 2.0
19. ⬜ Spätere Benutzerfunktionen

## Für später vorgemerkt

- optionales Radar-Diagramm zusätzlich zur Balkendarstellung
- feinere Performance-Zeitpunkte mit eigenem Datenmodell
- Tippfehler-Toleranz mit `pg_trgm`
- Autovervollständigung und Suchvorschläge
- Filterfacetten mit Trefferzahlen
- Mehrfachauswahl von Duftnoten mit UND-/ODER-Logik
- lesbare Slugs zusätzlich zu UUID-Links

## Dokumentationsregel

Nach jedem größeren Paket werden `CURRENT_STATUS`, `PROJECT_CONTEXT`, `ROADMAP`, die Fachdatei und bei Workflowänderungen `DEV_WORKFLOW` geprüft und aktualisiert.
