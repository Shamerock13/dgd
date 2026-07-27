# DGD – Datenvalidierung & Importqualität 2.0

Stand: 27. Juli 2026

## Ziel

Importe sollen nicht nur technisch lesbar sein, sondern vor dem Schreiben nachvollziehbar zwischen neuen Datensätzen, sicheren Dubletten, Prüfhinweisen und blockierenden Fehlern unterscheiden.

## Prüfendpunkt

```text
POST /api/import/quality/preview
```

Multipart-Felder:

- `file`: CSV oder XLSX
- `import_type`: `fragrances` oder `twins`

Der Endpunkt ist ein reiner Prüfpfad und schreibt keine Daten. Die praktische Backend-Abnahme in Dev war erfolgreich.

## Identitätsnormalisierung

Für Marken- und Duftnamen werden konservativ ignoriert:

- Groß- und Kleinschreibung
- Akzente und Umlaute in ihrer Grundform
- Satzzeichen und Bindestriche
- Warenzeichen
- mehrfache Leerzeichen

Abkürzungen und fehlende Wörter werden bewusst nicht automatisch gleichgesetzt.

## Entscheidungen

- `CREATE`: kein vorhandener oder ähnlicher Datensatz
- `DUPLICATE`: exakte oder sicher normalisierte vorhandene Identität
- `REVIEW`: ähnliche Schreibweise; ausschließlich manueller Prüfhinweis
- `BLOCK`: ungültige, unvollständige oder widersprüchliche Zeile

Ähnliche Treffer werden niemals automatisch zusammengeführt.

## Admin-Integration

Im Bereich **Datenimport** steht zusätzlich die Schaltfläche **Qualität & Dubletten prüfen** bereit. Sie verwendet dieselbe gewählte Datei und Importart wie der bestehende Import, zeigt aber eine getrennte, nur lesende Qualitätsauswertung.

Angezeigt werden:

- Anzahl für `CREATE`, `DUPLICATE`, `REVIEW` und `BLOCK`
- Gesamtstatus `safe_to_commit`
- Entscheidung und Begründung pro Zeile
- konkrete Fehler
- gefundene Kandidaten samt Ähnlichkeitswert und Trefferart

Die bestehende Importvorschau und der Commit-Pfad bleiben unverändert. Die neue Ansicht entscheidet noch nicht automatisch, welche Zeilen geschrieben oder zusammengeführt werden.

## Nächster Schritt

Nach praktischer Dev-Abnahme der Admin-Anzeige wird festgelegt, wie bestätigte `REVIEW`-Entscheidungen gespeichert werden und wie der Import-Commit bei ungelösten Konflikten abgesichert wird.
