# DGD – Datenvalidierung & Importqualität 2.0

Stand: 27. Juli 2026

## Ziel

Importe sollen nicht nur technisch lesbar sein, sondern vor dem Schreiben nachvollziehbar zwischen neuen Datensätzen, sicheren Dubletten, Prüfhinweisen und blockierenden Fehlern unterscheiden.

## Neuer Prüfendpunkt

```text
POST /api/import/quality/preview
```

Multipart-Felder:

- `file`: CSV oder XLSX
- `import_type`: `fragrances` oder `twins`

Der bestehende Import bleibt zunächst unverändert. Der neue Endpunkt ist ein reiner Prüfpfad und schreibt keine Daten.

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

## Rückgabe

Die Vorschau enthält:

- Anzahl pro Entscheidung
- `safe_to_commit`
- normalisierte Identitäten
- konkrete Fehler pro Zeile
- Kandidaten mit Trefferart und Ähnlichkeitswert
- Grund für die jeweilige Entscheidung

## Nächster Schritt

Die neue Qualitätsvorschau wird im Admin-Center sichtbar gemacht. Erst nach praktischer Dev-Abnahme wird entschieden, wie sie den bisherigen Import-Commit absichert.
