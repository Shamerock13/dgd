# DGD 2.0 – Roadmap

Stand: 29. Juli 2026

## Abgeschlossen

- ✅ Pakete 1 bis 14
- ✅ 16.1 Strukturiertes Performance-Datenmodell
- ✅ 16.2 Performance-Karte im Duftprofil
- ✅ 16.3 Zeitlicher Duftverlauf
- ✅ 16.4.1 Duft-DNA-Datenmodell und API
- ✅ 16.4.2 Duft-DNA-Karte im Duftprofil

## Kurz vor Abschluss

### 16.4.3 🚧 Manuelle Pflege der Duft-DNA

In PR #81 umgesetzt und in Dev bestätigt:

- Admin-Editor für alle 16 Dimensionen
- aggregierte und persönliche DNA getrennt
- Herkunft, Prüfstatus und Qualitätsmetadaten
- partielle Profile
- bewusstes Leeren einzelner Werte
- erneutes Laden gespeicherter Daten
- Router-Reihenfolge vor dem SPA-Fallback korrigiert

Offen: Squash-Merge nach `main`.

## In Arbeit

### 15 🚧 Datenvalidierung & Importqualität 2.0

Offen bleibt insbesondere die Absicherung des Master-Imports mit denselben Qualitätsregeln.

### 18 🚧 Preisbeobachtung & Händlervergleich 1.0

Vorhanden sind Händlerstammdaten, aktuelle Angebote, Preisbeobachtungen und Preisvergleich. Es folgen Händleradapter, tägliche Scannerläufe, Preisbox, Verlauf und Preisalarm.

## Als Nächstes

### 16.4.4 ⬜ Kontrollierte Duft-DNA-Recherche

- Recherchevorschläge getrennt von veröffentlichten Werten speichern
- Quellen und Begründung sichtbar machen
- Prüf- und Freigabeworkflow
- keine automatische Veröffentlichung ungeprüfter KI-Werte

Danach:
- 16 Admin-Bereich 2.0
- 17 Vergleich & Bewertung 2.0
- 19 spätere Benutzerfunktionen

## Für später

- optionales Radar-Diagramm zusätzlich zur Balkendarstellung
- feinere Performance-Zeitpunkte
- `pg_trgm`, Autovervollständigung und Suchvorschläge
- Filterfacetten und Mehrfachauswahl
- lesbare Slugs

Nach jedem größeren Paket werden `CURRENT_STATUS`, `PROJECT_CONTEXT`, `ROADMAP`, die Fachdatei und bei Workflowänderungen `DEV_WORKFLOW` geprüft und aktualisiert.
