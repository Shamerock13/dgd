# DGD – Datenvalidierung & Importqualität 2.0

Stand: 27. Juli 2026

## Ziel

Importe sollen vor dem Schreiben nachvollziehbar zwischen neuen Datensätzen, sicheren Dubletten, Prüfhinweisen und blockierenden Fehlern unterscheiden.

## Endpunkte

```text
POST /api/import/quality/preview
POST /api/import/quality/commit
```

Multipart-Felder:

- `file`: CSV oder XLSX
- `import_type`: `fragrances` oder `twins`
- beim Commit zusätzlich `duplicate_mode`: `skip` oder `update`

Die Vorschau schreibt keine Daten. Der abgesicherte Commit liest und bewertet die Datei unmittelbar vor dem Schreiben erneut.

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

Im Bereich **Datenimport** steht die Schaltfläche **Qualität & Dubletten prüfen** bereit. Sie verwendet dieselbe gewählte Datei und Importart wie der bestehende Import.

Angezeigt werden:

- Anzahl für `CREATE`, `DUPLICATE`, `REVIEW` und `BLOCK`
- Gesamtstatus `safe_to_commit`
- Entscheidung und Begründung pro Zeile
- konkrete Fehler
- gefundene Kandidaten samt Ähnlichkeitswert und Trefferart

Backend-Prüfpfad und Admin-Anzeige wurden praktisch in Dev bestätigt.

## Commit-Schutz

Der Admin-Import verwendet den abgesicherten Endpunkt `/api/import/quality/commit`.

- Ohne aktuelle Qualitätsprüfung wird sie automatisch ausgeführt.
- Nach Änderung von Datei oder Importart verfällt die vorherige Freigabe.
- `REVIEW` oder `BLOCK` stoppen den gesamten Import mit HTTP 409.
- Nur konfliktfreie Dateien gelangen zum bestehenden `commit_import`.
- Direkt vor dem Schreiben wird serverseitig erneut geprüft; eine alte Browseranzeige kann den Schutz nicht umgehen.
- Sichere Dubletten bleiben erlaubt und folgen weiterhin dem gewählten Modus `skip` oder `update`.

Der ältere Endpunkt `/api/import/commit` bleibt vorerst aus Kompatibilitätsgründen bestehen. Das Admin-Center verwendet ihn nicht mehr.

## Nächster Schritt

Praktische Dev-Abnahme des geschützten Commit-Ablaufs. Danach wird festgelegt, wie bewusst bestätigte `REVIEW`-Entscheidungen dauerhaft und nachvollziehbar gespeichert werden.
