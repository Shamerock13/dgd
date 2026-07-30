# DGD – Aktueller Projektstand

Stand: 30. Juli 2026

Diese Datei beschreibt den tatsächlich auf `main` vorhandenen Stand sowie den aktuell offenen Feature-Branch.

## Abgeschlossen und auf `main`

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

## Paket 16.7.3 – feldweise Freigabe und kontrollierte Übernahme

Branch: `feature/ai-research-import-apply` · Draft-PR #94

Umgesetzt:

- neue Werte sind in der Vorschau vorausgewählt
- Konflikte bleiben zunächst abgewählt
- Konflikte benötigen eine zusätzliche ausdrückliche Bestätigung
- jede Auswahl wird direkt vor dem Speichern erneut gegen die aktuelle Datenbank geprüft
- veraltete Vorschauen werden abgewiesen
- Stammdaten, Performance, Duft-DNA und Bildquellen können feldweise übernommen werden
- zusätzliche Duftnoten können selektiv angelegt und zugeordnet werden
- leere Zellen erzeugen keine Löschungen
- persönliche Felder bleiben gesperrt
- Preisquellen und Scanner bleiben in diesem Paket deaktiviert
- erfolgreiche Importläufe werden in `import_quality_runs` protokolliert
- Übernahme erfolgt innerhalb einer Transaktion mit Rollback bei Fehlern

## KI-Export und Rückimport

Der Admin-Bereich `KI-Export` unterstützt:

- Export aller Düfte oder nur von Datensätzen mit Lücken
- optionalen Markenfilter
- stabile `export_id` und `fragrance_id`
- neun Tabellenblätter: `Düfte`, `Noten`, `Performance`, `Duft-DNA`, `Bilder_Quellen`, `Preisquellen`, `Quellen`, `Anleitung`, `Metadaten`
- Ausschluss persönlicher Performance- und DNA-Werte
- Prüfung externer Ergänzungen mit Alt/Neu-Vergleich
- Erkennung von neuen Werten, Konflikten, ungültigen IDs und veränderten Exportkennungen

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

GitHub-CI prüft Backend-Compile und Frontend-Build. Praktische Abnahmen erfolgen ausschließlich in der Dev-Umgebung auf Unraid.

## Nächster Schritt

Paket 16.7.3 praktisch testen, dokumentierte Abnahme durchführen und anschließend PR #94 mergen.

Der Chat ist nicht das Projektgedächtnis. Maßgeblich sind Repository und Dokumentation.
