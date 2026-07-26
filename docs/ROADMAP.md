# DGD 2.0 – Roadmap

Diese Roadmap bündelt die größeren Entwicklungspakete für den Ausbau von DGD zu einem hochwertigen Parfum- und Duftzwillinge-Lexikon.

## Statusübersicht

- ✅ Detailansicht & Duftzwillinge 2.0
- ⏭️ Bildverwaltung & Bildquellen
- ⬜ Markenprofile
- ⬜ Parfümeurprofile
- ⬜ Quellen & Verifizierung
- ⬜ Suche, Filter & Navigation 2.0
- ⬜ Datenvalidierung & Importqualität
- ⬜ Admin-Bereich 2.0
- ⬜ Vergleich & Bewertung 2.0
- ⬜ Spätere Benutzerfunktionen

## 1. Detailansicht & Duftzwillinge 2.0 – abgeschlossen

Umgesetzt:

- Eigene Duftdetailansicht statt Modal
- Klare Darstellung von Marke, Duft, Jahr, Konzentration, Parfümeur und Beschreibung
- Strukturierte Notenpyramide aus den vorhandenen Duftnotenzuordnungen
- Freitext-Fallback für ältere oder noch nicht strukturierte Daten
- Duftzwillinge direkt am jeweiligen Duft
- Ähnlichkeitswert, Gemeinsamkeiten und Unterschiede
- Quellen- und Prüfhinweise
- Preisvergleich, Preisabstand und Kennzeichnung des günstigeren Duftes
- Saubere Bilddarstellung mit Fallback
- Direkte Navigation zwischen verbundenen Düften
- Responsive Darstellung für Desktop, Tablet und Smartphone

Technische Hauptdateien:

- `frontend/src/main.jsx`
- `frontend/src/detail.css`

Validierung:

```bash
cd frontend
npm install
npm run build
```

## 2. Bildverwaltung & Bildquellen – nächstes Paket

- Einheitliche Bildquellen und klare Prioritätslogik
- Wiederverwendbare Bildkomponente für Duftkarten, Detailseiten und spätere Profile
- Robuste Fallback-Logik bei fehlenden oder ungültigen Bildern
- Platzhalter für fehlende Bilder
- Fehlerbehandlung bei nicht erreichbaren externen Bild-URLs
- Prüfung und Kennzeichnung der Bildquelle
- Vorbereitung auf lokale oder verwaltete Bilder
- Klärung, wie Bilddaten im Master-Import gepflegt und validiert werden

## 3. Markenprofile

- Eigene Markenseiten
- Beschreibung, Herkunft und Hintergrund
- Liste aller zugeordneten Düfte
- Filter- und Sortiermöglichkeiten innerhalb einer Marke
- Sichtbarer Verifizierungsstatus
- Bild beziehungsweise Logo mit Fallback

## 4. Parfümeurprofile

- Nutzung der vorhandenen Struktur `master_perfumers`
- Profil, Nationalität, Stil und bekannte Werke
- Verknüpfung mit Düften
- Quellen und Artikelstatus sichtbar machen
- Eigene Profilansicht

## 5. Quellen & Verifizierung

- Quellen direkt an relevanten Datensätzen anzeigen
- Vertrauens- und Nutzungsstatus sichtbar machen
- Verifizierungsstatus für Marken, Düfte und Duftzwillinge
- Nachvollziehbare Herkunft importierter Daten
- Quellenhinweise der Duftzwillinge vereinheitlichen

## 6. Suche, Filter & Navigation 2.0

- Verbesserte Volltextsuche
- Bessere Treffergewichtung
- Erweiterte Filter
- Pagination statt vollständigem Laden großer Datenmengen
- Stabilere Admin-Suche
- Direkte, dauerhaft verlinkbare Detailseiten
- Browser-Zurück-Navigation und später URL-basierte Routen

## 7. Datenvalidierung & Importqualität

- Strengere Validierung im Backend
- Bessere Fehlerberichte beim Master-Import
- Vorschau mit klaren Warnungen und Konflikten
- Dubletten-Erkennung
- Konsistente Pflichtfelder
- Master-Import als zentrale Datenquelle
- Validierung von Bildquellen und Verknüpfungen

## 8. Admin-Bereich 2.0

- Suche und Pagination
- Klarere Bearbeitungsformulare
- Bessere Zuordnung und Sortierung von Duftnoten
- Verwaltung von Quellen und Verifizierungsstatus
- Importhistorie mit Details und Fehlerberichten
- Bildverwaltung und Bildstatus

## 9. Vergleich & Bewertung 2.0

- Detaillierter Vergleich zwischen Original und Alternative
- Preis- und Ersparnisdarstellung
- Ähnlichkeitsbewertung nach nachvollziehbaren Kriterien
- Darstellung von Gemeinsamkeiten und Unterschieden
- Spätere Aufteilung der Ähnlichkeit nach Duftverlauf, Noten, Haltbarkeit und Projektion

## 10. Spätere Benutzerfunktionen

Diese Funktionen sind bewusst nachgelagert:

- Benutzerbewertungen
- Favoriten
- Eigene Sammlungen
- Merklisten
- Persönliche Duftprofile

## Dokumentationsregel

Nach jedem größeren Paket werden mindestens diese Dateien geprüft und aktualisiert:

- `docs/PROJECT_CONTEXT.md`
- `docs/ROADMAP.md`
- `docs/DEV_WORKFLOW.md`, falls sich die Arbeitsweise oder Teststrategie verändert

Neue Ideen werden sofort dem passenden Roadmap-Paket zugeordnet, auch wenn ihre Umsetzung erst später erfolgt.

## Aktuelle Priorität

Als nächstes wird das Paket **Bildverwaltung & Bildquellen** vorbereitet. Danach folgen voraussichtlich Markenprofile sowie Quellen und Verifizierung.

## Fortschritt: Bildverwaltung & Bildquellen 1.0

**Status: umgesetzt**

Enthalten sind externe Bildpfade, Bildquelle, Quellenlink, Nutzungsnotiz, Prüfstatus, Admin-Vorschau und ein gemeinsamer Fallback-Baustein.

### Nachgelagertes Paket: Lokaler Bildupload

- dauerhaft gemountetes Unraid-Verzeichnis
- erlaubte Dateitypen und Größenbegrenzung
- sichere Dateinamen und Dublettenstrategie
- Thumbnail-/Optimierungsstrategie
- Backup- und Löschregeln
- Migration bestehender externer Bilder nur nach bewusster Freigabe

**Nächstes größeres Paket:** Markenprofile 1.0.

## Fortschritt: Markenprofile 1.0

**Status: umgesetzt**

- eigenständige Markenseiten
- Herkunft, Gründungsjahr und Website
- Beschreibung und Verifizierungsstatus
- Markenkennzahlen
- Duftliste mit Suche und Sortierung
- direkte Navigation zwischen Duft- und Markenprofil

**Nächstes größeres Paket:** Quellen & Verifizierung 1.0.


## Fortschritt: Quellen & Verifizierung 1.0

**Status: umgesetzt**

- Quellenregister im Admin
- Zuordnung zu Marken, Düften und Duftzwillingen
- Vertrauens- und Nutzungsstatus
- Prüfnotizen, Quellentyp, Datum sowie URL/Datei
- Verifizierungsübersicht mit offenen Datensätzen

**Nächstes größeres Paket:** Parfümeurprofile 1.0.

## Fortschritt: Parfümeurprofile 1.0

**Status: umgesetzt**

- eigene Parfümeurprofile
- Biografie, Herkunft und Geburtsjahr
- Stil und bekannte Werke
- Primärquelle und Artikelstatus
- Werkverzeichnis aus zugeordneten Düften
- direkte Navigation aus Duftprofilen

**Nächstes größeres Paket:** Datenqualität & redaktionelle Arbeitsliste 1.0.


## Fortschritt: Datenqualität & redaktionelle Arbeitsliste 1.0

**Status: umgesetzt**

- dynamische Qualitätsprüfung ohne zusätzliche Datenduplikate
- priorisierte Aufgabenliste für Marken, Düfte, Bilder und Quellen
- Prüfung fehlender Duftpyramiden und Parfümeurprofile
- Prüfung unvollständiger oder unbelegter Duftzwillinge
- Suche sowie Filter nach Priorität und Kategorie
- direkter Sprung in den passenden Admin-Bereich
- redaktioneller Qualitätswert und Aufgabenkennzahlen

**Nächstes größeres Paket:** Lokaler Bildupload & Medienablage 1.0.


## Fortschritt: Lokaler Bildupload & Medienablage 1.0

**Status: umgesetzt**

- persistenter Unraid-Medienordner
- Upload für JPEG, PNG und WebP bis 8 MB
- Prüfung von MIME-Typ und Dateisignatur
- automatische kollisionsfreie Dateinamen
- Ersetzen und Löschen lokaler Duftbilder
- weiterhin Unterstützung externer Bild-URLs
- dokumentierte Backup- und Speicherregeln

**Nächstes größeres Paket:** Automatische Recherche & Import-Warteschlange 1.0.


## Fortschritt: Automatische Recherche & Import-Warteschlange 1.0

**Status: umgesetzt**

- manuelles Scannen öffentlicher Quellseiten
- Erkennung strukturierter JSON-LD-Produktdaten
- Import-Warteschlange mit Bearbeitung und Statusfiltern
- Dublettenprüfung gegen Marke und Duftname
- Freigabe oder Ablehnung vor Datenbankübernahme
- Quellenlink, Trefferqualität und Rohdaten bleiben nachvollziehbar
- SSRF-Schutz gegen interne Netzwerkziele

**Nächstes größeres Paket:** Recherchequellen & zeitgesteuerter Scanner 1.0.
