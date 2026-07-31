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
- ✅ 18.2 Preisalarme und Schwellenwerte

## In Arbeit

### 18.3 🚧 Prüfrunde für Browser-Preisquellen

- Queue nur für freigegebene `BROWSER_REQUIRED`-Quellen aktiver Händler
- Status nie geprüft, fällig oder aktuell
- Fälligkeit aus `scan_interval` mit sicherem 24-Stunden-Standard
- nie geprüfte Quellen zuerst, danach älteste manuelle Prüfung
- Admin zeigt Status und startet die Runde bewusst
- Erweiterung bietet nach erfolgreicher Übernahme die nächste fällige Quelle an
- jede weitere Seite wird ausschließlich nach einem Klick geöffnet
- keine automatische Navigation, kein Hintergrund-Crawling und keine Schutzseiten-Umgehung

Issue #105, Draft-PR #106.

### 15 🚧 Datenvalidierung & Importqualität 2.0

Offen bleibt insbesondere die Absicherung des Master-Imports mit denselben Qualitätsregeln wie beim KI-Rückimport.

## Danach

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
