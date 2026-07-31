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
- ✅ 18.1 Preisverlauf und Variantenvergleich im Duftprofil

## In Arbeit

### 18.2 🚧 Preisalarme und Schwellenwerte

- gewünschte vollständige Variante eindeutig auswählen
- Zielpreis inklusive Versand oder prozentualen Abstand zum historischen Tief festlegen
- Alarm aktivieren, deaktivieren, ändern und löschen
- Status, aktuelle Auswertung, letzte Auslösung und Auslösungszähler speichern
- erneute Auslösung erst nach zwischenzeitlichem Rücksetzen
- jede neue Preisbeobachtung automatisch auswerten
- ausverkaufte, ungeprüfte oder inaktive Quellen ignorieren
- Bedienung direkt im Preisbereich des Duftprofils
- externe E-Mail- und Push-Kanäle bleiben späteren Paketen vorbehalten

Issue #103, Draft-PR #104.

### 15 🚧 Datenvalidierung & Importqualität 2.0

Offen bleibt insbesondere die Absicherung des Master-Imports mit denselben Qualitätsregeln wie beim KI-Rückimport.

## Danach

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

- E-Mail-, Push- oder andere externe Kanäle für ausgelöste Preisalarme
- optionales Radar-Diagramm zusätzlich zur Balkendarstellung
- feinere Performance-Zeitpunkte
- `pg_trgm`, Autovervollständigung und Suchvorschläge
- Filterfacetten und Mehrfachauswahl
- lesbare Slugs

Nach jedem größeren Paket werden `CURRENT_STATUS`, `PROJECT_CONTEXT`, `ROADMAP`, die Fachdatei und bei Workflowänderungen `DEV_WORKFLOW` geprüft und aktualisiert.
