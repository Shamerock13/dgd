# Recherche zu Feldfunden

Der kombinierte Admin-Lauf **Daten & Duftzwillinge suchen** erzeugt jetzt neben Datenlücken und Twin-Hinweisen auch konkrete Feldvorschläge für die redaktionelle Prüfung.

## Ablauf

1. Offene `enrichment_tasks` bestimmen die zu recherchierenden Düfte und Felder.
2. Pro Duft wird eine eng gefasste Websuche mit Marke, Duftname und den fehlenden Feldern ausgeführt.
3. Gesperrte Domains werden verworfen.
4. Suchausschnitte werden auf klar erkennbare Werte geprüft.
5. Vollständige Seiten werden nur bei offiziellen Markendomains oder ausdrücklich automatisierbaren Quellenprofilen abgerufen.
6. Gefundene Werte werden in `enrichment_findings` geschrieben und erscheinen unter **Quellen & Prüfung**.

## Unterstützte Felder

- Erscheinungsjahr
- Konzentration
- Parfümeur
- Beschreibung aus strukturierten Seitendaten
- Bild-URL aus strukturierten Seitendaten
- Kopf-, Herz- und Basisnoten
- Akkorde

## Sicherheits- und Qualitätsregeln

- Kein Fund wird automatisch in den Duftdatensatz übernommen.
- Bestehende abweichende Werte werden nie überschrieben.
- Jeder Fund behält Quellenname, direkte URL, Textausschnitt und Vertrauenswert.
- Bereits entschiedene Funde bleiben entschieden; ein erneuter Lauf setzt sie nicht wieder auf offen.
- Fragrantica bleibt für automatische Abrufe gesperrt.
- Parfumo, Basenotes und Wikiparfum werden standardmäßig nur über öffentlich sichtbare Suchausschnitte ausgewertet, solange ihr Quellenprofil keinen automatischen Vollseitenabruf erlaubt.
- HTTP-Weiterleitungen werden bei Vollseitenabrufen nicht automatisch verfolgt.
- Pro Lauf gelten begrenzte Duft- und Trefferzahlen.

## API

- `POST /api/enrichment/discover-findings?limit=10`
- `POST /api/enrichment/run?twin_limit=10&finding_limit=10`

Die Antwort des kombinierten Laufs enthält `gaps`, `findings` und `twins`. Die bestehende Oberfläche bleibt kompatibel und kann die zusätzlichen Details später gesondert anzeigen.
