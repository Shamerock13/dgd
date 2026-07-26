# Daten- und Duftzwilling-Recherche 1.0

## Ziel

Der Admin-Bereich besitzt einen gemeinsamen Knopf **Daten & Duftzwillinge suchen**. Der Lauf kombiniert die Prüfung vorhandener Datensätze mit einer begrenzten Webrecherche nach ausdrücklich genannten Dupes, Clones, Alternativen und „inspired by“-Düften.

## Ablauf

1. Alle vorhandenen Düfte werden auf fehlende Angaben geprüft.
2. Für unvollständige Düfte werden Anreicherungsaufträge aktualisiert.
3. Bis zu einer begrenzten Zahl von Düften ohne bekannte Twin-Verknüpfung werden als Suchbasis verwendet.
4. Öffentliche Suchergebnisse werden nur dann gespeichert, wenn Titel oder Textausschnitt eindeutige Hinweisbegriffe enthalten.
5. Jeder Hinweis erhält Quelle, URL, Textausschnitt, erkannte Aussage und Trefferqualität.
6. Die Ergebnisse landen in einer eigenen Prüfwarteschlange.

## Qualitätsregeln

- Kein Suchtreffer wird automatisch als Duftzwilling veröffentlicht.
- Die Fundstelle bleibt dauerhaft am Vorschlag erhalten.
- Suchergebnistitel dienen nur als vorläufige Bezeichnung der Alternative.
- Bereits bekannte Alternativen werden nach Möglichkeit mit einem vorhandenen DGD-Duft verknüpft.
- Mehrere Quellen dürfen später zu einem gemeinsamen Paar zusammengefasst werden.
- Algorithmische Notenähnlichkeit ersetzt keine explizite Quellenangabe.
- Mögliche Dubletten und Duftzwillinge bleiben fachlich getrennte Kategorien.

## Sicherheit und Betrieb

- Öffentliche Recherche ist pro Knopfdruck auf maximal 30 Ausgangsdüfte begrenzt; die Oberfläche verwendet zunächst 10.
- Interne, private und lokale Netzwerkziele bleiben gesperrt.
- Fehler eines einzelnen Suchlaufs brechen die übrige Datenlückenprüfung nicht ab.
- Es gibt keine automatische Zusammenführung oder Löschung vorhandener Datensätze.

## Endpunkte

- `POST /api/enrichment/run?twin_limit=10`
- `POST /api/enrichment/scan-gaps`
- `GET /api/enrichment/tasks`
- `GET /api/enrichment/twin-suggestions`
- `POST /api/enrichment/twin-suggestions/{id}/reject`
- `GET /api/enrichment/dupe-evidence`

## Nächster Ausbau

- Gruppierung mehrerer Belege zum selben Duftzwilling-Paar
- manuelle Zuordnung unbekannter Alternativen zu vorhandenen oder neuen Düften
- Freigabe eines belegten Vorschlags als echter `twin_match`
- Quellengewichtung nach Hersteller, Fachquelle, Händler und Community
- quellenabhängige Adapter, unter anderem für gepflegte Duftdatenbanken
