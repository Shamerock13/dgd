# DGD 2.0 – Roadmap

Stand: 31. Juli 2026

## Abgeschlossen

- ✅ Pakete 1 bis 14
- ✅ 16.1 Strukturiertes Performance-Datenmodell
- ✅ 16.2 Performance-Karte im Duftprofil
- ✅ 16.3 Zeitlicher Duftverlauf
- ✅ 16.4.1 Duft-DNA-Datenmodell und API
- ✅ 16.4.2 Duft-DNA-Karte im Duftprofil
- ✅ 16.4.3 Manuelle Pflege der Duft-DNA
- ✅ 16.4.4 Kontrollierte Duft-DNA-Recherchevorschläge
- ✅ 16.5.1 Admin-Übersicht
- ✅ 16.5.2 Gruppierte Admin-Navigation
- ✅ 16.5.3 Strukturierte Duftbearbeitung
- ✅ 16.6.1 KI-Recherche für strukturierte Performance-Daten
- ✅ 16.7.1 Vollständiger KI-Recherche-Export
- ✅ 16.7.2 Geprüfte Rückimport-Vorschau
- ✅ 16.7.3 Feldweise Freigabe und kontrollierte Übernahme
- ✅ 16.7.4 Preisquellen geprüft übernehmen
- ✅ 16.7.5 Preisquellen im Admin prüfen und freigeben
- ✅ 16.7.6 Lokaler Browser-Connector für blockierte Händler

## In Arbeit

### 18.1 🚧 Preisverlauf und Variantenvergleich im Duftprofil

- nur freigegebene Quellen aktiver Händler öffentlich anzeigen
- Angebote nach Produktart, Größe und Konzentration gruppieren
- Tester, Sets, Proben, Nachfüllungen und Flakons getrennt vergleichen
- günstigsten Preis und historisches Tief je Variante berechnen
- Zeitraumfilter 30, 90 und 365 Tage
- responsive Verlaufsgrafik und sortierte Händlerliste

Issue #101, Draft-PR #102.

### 15 🚧 Datenvalidierung & Importqualität 2.0

Offen bleibt insbesondere die Absicherung des Master-Imports mit denselben Qualitätsregeln wie beim KI-Rückimport.

## Danach

### 18.2 ⬜ Preisalarme und Schwellenwerte

- gewünschte Variante eindeutig auswählen
- Zielpreis oder prozentualen Abstand zum historischen Tief festlegen
- Benachrichtigungsstatus und letzte Auslösung speichern
- keine Alarme für ausverkaufte oder ungeprüfte Quellen

### 18.3 ⬜ Komfort für Browser-Quellen

- mehrere bewusst gestartete Browserprüfungen nacheinander abarbeiten
- klarer Status für zuletzt manuell geprüfte Quellen
- keine automatische CAPTCHA- oder Schutzseiten-Umgehung

### Weitere größere Bereiche

- separates Datenmodell für beschreibende Duftmerkmale wie Jahreszeit, Anlass, Dichte, Temperaturwirkung und Signatur
- 17 Vergleich & Bewertung 2.0
- weitere Händleradapter und Produktsuche
- 19 spätere Benutzerfunktionen

## Für später

- optionales Radar-Diagramm zusätzlich zur Balkendarstellung
- feinere Performance-Zeitpunkte
- `pg_trgm`, Autovervollständigung und Suchvorschläge
- Filterfacetten und Mehrfachauswahl
- lesbare Slugs

Nach jedem größeren Paket werden `CURRENT_STATUS`, `PROJECT_CONTEXT`, `ROADMAP`, die Fachdatei und bei Workflowänderungen `DEV_WORKFLOW` geprüft und aktualisiert.
