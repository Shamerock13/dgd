# DGD 2.0 – Roadmap

Stand: 27. Juli 2026

Diese Roadmap zeigt den aktuellen Entwicklungsstand von DGD und die Reihenfolge der nächsten größeren Pakete. Maßgeblich für den tatsächlich auf `main` vorhandenen Funktionsstand bleibt zusätzlich `docs/CURRENT_STATUS.md`.

## Statusübersicht

### Abgeschlossen

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

### Als Nächstes

13. ⏭️ Scanner-Betrieb & automatische Fälligkeit 1.0

### Danach vorgesehen

14. ⬜ Suche, Filter & Navigation 2.0
15. ⬜ Datenvalidierung & Importqualität 2.0
16. ⬜ Admin-Bereich 2.0
17. ⬜ Vergleich & Bewertung 2.0
18. ⬜ Preisbeobachtung & Händlervergleich 1.0
19. ⬜ Spätere Benutzerfunktionen

---

## 1–12. Umgesetzte Pakete

### Detailansicht & Duftzwillinge 2.0

- eigene Duftdetailansicht statt Modal
- strukturierte Duftpyramide mit Freitext-Fallback
- direkte Anzeige verbundener Duftzwillinge
- Ähnlichkeit, Gemeinsamkeiten, Unterschiede und Quellenhinweise
- Preisabstand und Kennzeichnung des günstigeren Duftes
- responsive Darstellung und robuste Bild-Fallbacks

### Bildverwaltung & Bildquellen 1.0

- externe Bildpfade mit Quelle, Quellenlink und Prüfstatus
- gemeinsamer Bildbaustein für Karten, Admin und Detailseite
- belastbare Fallback-Logik für leere oder defekte Bildquellen

### Markenprofile 1.0

- eigenständige Markenseiten
- Herkunft, Gründungsjahr, Website und Beschreibung
- Verifizierungsstatus, Kennzahlen sowie Duftliste mit Suche und Sortierung

### Quellen & Verifizierung 1.0

- Quellenregister im Admin
- Zuordnung zu Marken, Düften, Duftzwillingen und allgemeinen Themen
- Vertrauens- und Nutzungsstatus
- Prüfnotizen, Quellentyp, Datum sowie URL oder Datei

### Parfümeurprofile 1.0

- eigene Profile mit Biografie, Nationalität, Stil und bekannten Werken
- Primärquelle und Artikelstatus
- direkte Verknüpfung aus Duftprofilen

### Datenqualität & redaktionelle Arbeitsliste 1.0

- dynamische Qualitätsprüfung ohne zusätzliche Datenduplikate
- priorisierte Aufgabenliste für Marken, Düfte, Bilder, Quellen und Twins
- Suche und Filter nach Priorität und Kategorie
- redaktioneller Qualitätswert und direkte Sprünge in den passenden Admin-Bereich

### Lokaler Bildupload & Medienablage 1.0

- persistenter Unraid-Medienordner
- Upload für JPEG, PNG und WebP bis 8 MB
- Prüfung von MIME-Typ und Dateisignatur
- kollisionsfreie Dateinamen sowie Ersetzen und Löschen lokaler Bilder

### Automatische Recherche & Import-Warteschlange 1.0

- manuelles Scannen öffentlicher Quellseiten
- Erkennung strukturierter JSON-LD-Produktdaten
- Import-Warteschlange mit Bearbeitung und Statusfiltern
- Dublettenprüfung und ausdrückliche Freigabe vor Datenbankübernahme
- SSRF-Schutz gegen interne Netzwerkziele

### Recherchequellen & zeitgesteuerter Scanner 1.0

- verwaltete Recherchequellen mit Aktivstatus und Scanintervall
- Speicherung von Scanläufen, Fehlern und Zeitpunkten
- Auswahl fälliger Quellen als Grundlage für einen späteren Worker

### Quellenadapter & Mehrseiten-Scanner 1.0

- Adaptertypen `SINGLE` und `LIST`
- Erkennung von Produktlinks auf Marken-, Kategorie- und Suchseiten
- Domainbegrenzung, Linkfilter und Höchstzahl pro Lauf
- Fehler einzelner Produktseiten brechen den gesamten Listenlauf nicht ab

### Gemini-Recherche & Datenqualität 1.0

- gezielte Recherche einzelner Düfte
- Suche nach weiteren Düften einer Marke
- gemeinsame Feld- und Zeichenlimits
- Ausschluss bekannter Feldwerte und Duftzwillinge
- Grounding-Pflicht für Twin-Vorschläge
- serverseitige Normalisierung von Duftnoten und Akkorden
- Prüflauf vor historischen Bereinigungen

### Gemini-Rechercheverlauf & Tokenkontrolle 1.0

- Rechercheverlauf pro Duft
- Anzeige von Zeitpunkt, Quellen, Treffern und Tokenverbrauch
- Protokollierung erfolgreicher und fehlgeschlagener Läufe
- 15-minütiger Schutz vor versehentlichen Wiederholungen
- bewusster Neustart über „Trotzdem erneut suchen“

---

## 13. Scanner-Betrieb & automatische Fälligkeit 1.0 – nächstes Paket

Ziel ist ein zuverlässiger automatischer Betrieb der bereits vorhandenen Recherchequellen und Scannerlogik.

Geplante Schwerpunkte:

- eigener Scanner-Dienst beziehungsweise Worker in der Dev-Umgebung
- regelmäßiger Abruf ausschließlich fälliger und aktiver Quellen
- Sperre gegen parallele Doppelläufe derselben Quelle
- ein klarer Ein-/Ausschalter für den automatischen Betrieb
- Laufzeit-, Fehler- und Erfolgskennzahlen
- sichtbarer letzter und nächster geplanter Lauf
- kontrollierte Wiederholungsstrategie bei temporären Fehlern
- keine automatische Freigabe von Warteschlangen-Treffern
- dokumentierte Neustart-, Betriebs-, Backup- und Wiederherstellungsregeln

Abnahmekriterien:

- der Worker läuft getrennt von Frontend und API
- nicht fällige oder deaktivierte Quellen werden übersprungen
- parallele Läufe derselben Quelle sind ausgeschlossen
- Fehler eines Laufs stoppen den Dienst nicht dauerhaft
- jeder Lauf bleibt im Admin nachvollziehbar
- Produktion wird erst nach erfolgreichem Dev-Test vorbereitet

---

## 14. Suche, Filter & Navigation 2.0

- verbesserte Volltextsuche und Treffergewichtung
- erweiterte Filter für Duftfamilie, Noten, Marke, Jahr und Konzentration
- Pagination statt vollständigem Laden großer Datenmengen
- stabilere Admin-Suche
- dauerhaft verlinkbare Detailseiten und URL-basierte Navigation
- zuverlässige Browser-Zurück-Navigation

## 15. Datenvalidierung & Importqualität 2.0

- strengere Backend-Validierung
- klarere Warnungen und Konflikte in der Importvorschau
- robustere Dublettenerkennung bei Schreibvarianten
- konsistente Pflichtfelder und Datenformate
- Validierung von Bildern, Quellen und Verknüpfungen
- nachvollziehbare Fehlerberichte und Importhistorie

## 16. Admin-Bereich 2.0

- Suche, Filter und Pagination in großen Verwaltungslisten
- klarere Bearbeitungsformulare
- bessere Zuordnung und Sortierung von Duftnoten
- zentrale Übersicht für Quellen-, Bild- und Verifizierungsstatus
- detaillierte Import- und Recherchehistorie
- bessere mobile Bedienbarkeit

## 17. Vergleich & Bewertung 2.0

- detaillierter Vergleich zwischen Original und Alternative
- nachvollziehbare Kriterien für die Ähnlichkeitsbewertung
- getrennte Betrachtung von Duftverlauf, Noten, Haltbarkeit und Projektion
- Darstellung von Gemeinsamkeiten und Unterschieden
- Preis- und Ersparnisdarstellung

## 18. Preisbeobachtung & Händlervergleich 1.0

- getrennt von der KI-Recherche betriebene Händlerabfragen
- regelmäßige Preisaktualisierung bekannter Händler
- Zuordnung nach Duft, Größe und Konzentration
- Anzeige des aktuell günstigsten belastbaren Angebots
- Preisverlauf über einen wählbaren Zeitraum
- Kennzeichnung von Versandkosten, Lieferstatus und veralteten Treffern
- keine automatische Veröffentlichung unklarer Produktzuordnungen

## 19. Spätere Benutzerfunktionen

Diese Funktionen bleiben bewusst nachgelagert:

- Benutzerbewertungen
- Favoriten und Merklisten
- eigene Sammlungen
- persönliche Duftprofile
- Benachrichtigungen bei neuen Twins oder Preisänderungen

---

## Dokumentationsregel

Nach jedem größeren Paket werden mindestens geprüft und bei Bedarf aktualisiert:

- `docs/CURRENT_STATUS.md`
- `docs/PROJECT_CONTEXT.md`
- `docs/ROADMAP.md`
- die jeweilige technische Fachdatei
- `docs/DEV_WORKFLOW.md`, falls sich Arbeitsweise oder Tests ändern

Der Chat ist nicht das Projektgedächtnis. Maßgeblich sind Repository und Dokumentation.