# DGD 2.0 – Roadmap

Stand: 30. Juli 2026

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

## In Arbeit

### 15 🚧 Datenvalidierung & Importqualität 2.0

Offen bleibt insbesondere die Absicherung des Master-Imports mit denselben Qualitätsregeln wie beim KI-Rückimport.

### 18 🚧 Preisbeobachtung & Händlervergleich 1.0

Vorhanden sind Händlerstammdaten, aktuelle Angebote, Preisbeobachtungen und Preisvergleich. Es folgen Händleradapter, tägliche Scannerläufe, Preisbox, Verlauf und Preisalarm.

## Als Nächstes

### 16.7.4 ⬜ Preisquellen geprüft übernehmen

- `offer_source_id` stabil und zeilenweise validieren
- neue direkte Produktlinks zunächst deaktiviert speichern
- Händler, Variante, Größe, Konzentration, Set/Tester und Produkttyp prüfen
- Gesamtpreis einschließlich Versand vergleichbar speichern
- geänderte Links nur nach bewusster Freigabe aktivieren
- alte Scannerzuordnung bei Linkänderung zunächst deaktivieren
- keine automatische Scanner-Aktivierung ungeprüfter Quellen
- Preisquellen in Vorschau, Freigabe und Auditprotokoll integrieren

Danach:

- separates Datenmodell für beschreibende Duftmerkmale wie Jahreszeit, Anlass, Dichte, Temperaturwirkung und Signatur
- 16.5.4 weitere Admin-Werkzeuge und Protokollansichten
- 17 Vergleich & Bewertung 2.0
- 18 Händleradapter und automatisierte Preisaktualisierung
- 19 spätere Benutzerfunktionen

## Für später

- optionales Radar-Diagramm zusätzlich zur Balkendarstellung
- feinere Performance-Zeitpunkte
- `pg_trgm`, Autovervollständigung und Suchvorschläge
- Filterfacetten und Mehrfachauswahl
- lesbare Slugs

Nach jedem größeren Paket werden `CURRENT_STATUS`, `PROJECT_CONTEXT`, `ROADMAP`, die Fachdatei und bei Workflowänderungen `DEV_WORKFLOW` geprüft und aktualisiert.