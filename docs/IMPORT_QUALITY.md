# DGD – Datenvalidierung & Importqualität 2.0

Stand: 27. Juli 2026

## Ziel

Importe sollen vor dem Schreiben nachvollziehbar zwischen neuen Datensätzen, sicheren Dubletten, Prüfhinweisen und blockierenden Fehlern unterscheiden.

## Endpunkte

```text
POST /api/import/quality/preview
POST /api/import/quality/commit
GET  /api/import/quality/runs
```

Multipart-Felder:

- `file`: CSV oder XLSX
- `import_type`: `fragrances` oder `twins`
- beim Commit zusätzlich `duplicate_mode`: `skip` oder `update`
- beim Commit zusätzlich `review_decisions`: JSON-Liste der bewussten Entscheidungen

Die Vorschau schreibt keine Daten. Der abgesicherte Commit liest und bewertet die Datei unmittelbar vor dem Schreiben erneut.

## Identitätsnormalisierung

Für Marken- und Duftnamen werden konservativ ignoriert:

- Groß- und Kleinschreibung
- Akzente und Umlaute in ihrer Grundform
- Satzzeichen und Bindestriche
- Warenzeichen
- mehrfache Leerzeichen

Abkürzungen und fehlende Wörter werden bewusst nicht automatisch gleichgesetzt.

## Entscheidungen der Qualitätsprüfung

- `CREATE`: kein vorhandener oder ähnlicher Datensatz
- `DUPLICATE`: exakte oder sicher normalisierte vorhandene Identität
- `REVIEW`: ähnliche Schreibweise; manuelle Entscheidung erforderlich
- `BLOCK`: ungültige, unvollständige oder widersprüchliche Zeile

Ähnliche Treffer werden niemals automatisch zusammengeführt. `BLOCK` kann nicht manuell freigegeben werden.

## Manuelle REVIEW-Auflösung

Für einen Duft mit `REVIEW` stehen drei Möglichkeiten bereit:

- `create`: den importierten Marken- und Duftnamen bewusst als neuen Datensatz anlegen
- `use_existing`: einen aktuell angebotenen vorhandenen Kandidaten verwenden
- `exclude`: die Zeile aus diesem Import ausschließen

Bei Duftzwillingen kann die Zeile ausgeschlossen oder durch die bewusste Auswahl von Original und Alternative aufgelöst werden.

Der Browser überträgt nur die Entscheidung und die gewählten Kandidaten-IDs. Der Server:

1. liest dieselbe Datei erneut,
2. berechnet die Qualitätsprüfung erneut,
3. akzeptiert Entscheidungen nur für weiterhin vorhandene `REVIEW`-Zeilen,
4. akzeptiert ausschließlich Kandidaten aus der aktuellen Prüfung,
5. verhindert, dass mehrere Zeilen durch Entscheidungen auf dieselbe Identität zusammenfallen,
6. schreibt erst nach vollständiger erfolgreicher Prüfung.

## Admin-Integration

Im Bereich **Datenimport** steht die Schaltfläche **Qualität & Dubletten prüfen** bereit. Sie verwendet dieselbe gewählte Datei und Importart wie der bestehende Import.

Angezeigt werden:

- Anzahl für `CREATE`, `DUPLICATE`, `REVIEW` und `BLOCK`
- Entscheidung und Begründung pro Zeile
- konkrete Fehler
- gefundene Kandidaten samt Ähnlichkeitswert und Trefferart
- Auswahlfelder für manuelle `REVIEW`-Entscheidungen
- die letzten gespeicherten Importberichte

Backend-Prüfpfad, Admin-Anzeige und geschützter Commit wurden praktisch in Dev bestätigt. Die praktische Abnahme der neuen manuellen Entscheidungen steht noch aus.

## Commit-Schutz

Der Admin-Import verwendet den abgesicherten Endpunkt `/api/import/quality/commit`.

- Ohne aktuelle Qualitätsprüfung wird sie automatisch ausgeführt.
- Nach Änderung von Datei oder Importart verfällt die vorherige Anzeige.
- `BLOCK` stoppt den gesamten Import mit HTTP 409.
- Offene oder ungültige `REVIEW`-Entscheidungen stoppen den gesamten Import.
- Direkt vor dem Schreiben wird serverseitig erneut geprüft.
- Sichere Dubletten folgen weiterhin dem gewählten Modus `skip` oder `update`.
- Ausgeschlossene Zeilen werden gezählt, aber nicht geschrieben.

Der ältere Endpunkt `/api/import/commit` bleibt vorerst aus Kompatibilitätsgründen bestehen. Das Admin-Center verwendet ihn nicht mehr.

## Importberichte

Die Tabelle `import_quality_runs` speichert pro Commit-Versuch:

- Dateiname und Importart
- Dublettenmodus
- Status `SUCCESS`, `BLOCKED` oder `FAILED`
- Qualitätszahlen
- manuelle Entscheidungen
- ausgeschlossene Zeilen
- Ergebniszahlen des Imports
- Fehlermeldung bei gestoppten oder fehlgeschlagenen Läufen

Die letzten Berichte sind über `GET /api/import/quality/runs` abrufbar und werden im Admin-Center angezeigt.

## Nächster Schritt

Praktische Dev-Abnahme mit mindestens einer `REVIEW`-Datei: neuen Datensatz akzeptieren, vorhandenen Kandidaten verwenden, Zeile ausschließen und Bericht nach dem Neuladen kontrollieren.
