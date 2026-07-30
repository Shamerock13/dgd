# DGD – Aktueller Projektstand

Stand: 30. Juli 2026

Diese Datei beschreibt den tatsächlich auf `main` vorhandenen Stand sowie unmittelbar vor dem Merge bestätigte Änderungen.

## Abgeschlossen

- Pakete 1 bis 14
- 16.1 Strukturiertes Performance-Datenmodell
- 16.2 Performance-Karte im Duftprofil
- 16.3 Zeitlicher Duftverlauf
- 16.4 Duft-DNA-Datenmodell, Anzeige, manuelle Pflege und kontrollierte Vorschläge
- 16.5.1 Admin-Übersicht
- 16.5.2 Gruppierte Admin-Navigation
- 16.5.3 Strukturierte Duftbearbeitung
- 16.6.1 KI-Recherche für strukturierte Performance-Daten
- 16.7.1 Vollständiger KI-Recherche-Export als XLSX
- 16.7.2 Geprüfte Rückimport-Vorschau ohne Datenbankänderung
- 16.7.3 Feldweise Freigabe und kontrollierte Übernahme

## Paket 16.7.3

In Dev praktisch bestätigt und über PR #94 für `main` freigegeben:

- neue Werte sind in der Vorschau vorausgewählt
- Konflikte bleiben zunächst abgewählt und benötigen eine ausdrückliche Bestätigung
- jede Auswahl wird direkt vor dem Speichern erneut gegen die aktuelle Datenbank geprüft
- veraltete Vorschauen werden abgewiesen
- Stammdaten, Performance, numerische Duft-DNA und Bildquellen können feldweise übernommen werden
- zusätzliche Duftnoten können selektiv angelegt und zugeordnet werden
- leere Zellen erzeugen keine Löschungen
- persönliche Felder bleiben gesperrt
- Preisquellen und Scanner bleiben deaktiviert
- erfolgreiche Importläufe werden in `import_quality_runs` protokolliert
- Fehler führen zum vollständigen Rollback
- ungültige beschreibende DNA-Strukturen werden beim Import abgewiesen
- lokale Duftbilder werden unter `/media/fragrances` gespeichert und im Dev-Frontend ausgeliefert
- der normale Dufteditor sendet nur seine erlaubten Formularfelder und bleibt mit KI-Daten kompatibel

## KI-Export und Rückimport

Der Admin-Bereich `KI-Export` unterstützt Export, geprüfte Vorschau und kontrollierte Übernahme. Technische Kennungen bleiben stabil; persönliche Performance- und DNA-Werte sind ausgeschlossen. Preisquellen bleiben bis Paket 16.7.4 reine Vorschau.

## Daten- und Sicherheitsprinzipien

- Produktion bleibt unberührt
- leere Zellen bedeuten keine Löschung
- fehlende Werte bleiben unbekannt und werden nicht als `0` interpretiert
- persönliche Werte bleiben strikt von aggregierten Daten getrennt
- ungeprüfte KI-Werte werden nie automatisch veröffentlicht
- Konflikte müssen bewusst bestätigt werden
- Preisquellen aktivieren niemals automatisch einen Scanner

## Datenbankstand

Explizites DGD-Migrationsschema bis `0015`.

## Qualitätssicherung

Dev-Abnahme erfolgreich. GitHub Actions `DGD CI` Lauf 201 für den finalen Branch-Stand erfolgreich.

## Nächster Schritt

Paket 16.7.4: Preisquellen geprüft übernehmen und Scanner-Aktivierung weiterhin getrennt absichern.

Der Chat ist nicht das Projektgedächtnis. Maßgeblich sind Repository und Dokumentation.