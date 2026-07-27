# DGD – Katalogsuche, Filter und Pagination

Stand: 27. Juli 2026

## Ziel

Die öffentliche Duftsuche soll bei wachsendem Datenbestand nicht mehr alle Düfte vollständig in den Browser laden. Dafür stellt das Backend eine paginierte und gewichtete Katalogsuche bereit.

## Endpunkt

```text
GET /api/catalog/fragrances
```

Unterstützte Parameter:

- `q`: gewichtete Volltextsuche
- `brand_id`: Marke
- `gender`: Zielgruppe
- `concentration`: Konzentration
- `note`: strukturierte Duftnote
- `year_from`, `year_to`: Erscheinungsjahr
- `min_price`, `max_price`: Preisbereich
- `min_longevity`: Mindesthaltbarkeit
- `sort`: Sortierung
- `page`, `page_size`: Pagination

## Treffergewichtung

Die Suche priorisiert in dieser Reihenfolge:

1. exakter Duftname
2. Duftname beginnt mit Suchbegriff
3. exakter Markenname
4. Markenname beginnt mit Suchbegriff
5. Teiltreffer in Duft- oder Markenname
6. strukturierte Duftnoten
7. Akkorde
8. Parfümeur
9. Beschreibung

## Antwort

Die Antwort enthält:

- `items`: aktuelle Ergebnisseite
- `pagination`: Seite, Seitengröße, Gesamtzahl, Seitenzahl sowie Vor-/Zurück-Status
- `facets`: verfügbare Konzentrationen sowie kleinste und größte Jahreszahl

## Katalog 2.0 im Frontend

Der neue Katalog ist während der Dev-Abnahme unter folgender Seite erreichbar:

```text
/catalog.html
```

Die bestehende Hauptansicht erhält vorübergehend die Schaltfläche **Katalog 2.0 testen**. Der neue Katalog:

- verwendet ausschließlich den paginierten Katalogendpunkt,
- lädt standardmäßig 24 Düfte pro Seite,
- bietet Suche und Filter für Marke, Zielgruppe, Konzentration, Duftnote, Jahr, Preis und Haltbarkeit,
- speichert Suchbegriff, Filter, Sortierung und Seite in der URL,
- verzögert Texteingaben um 300 ms, damit nicht jeder Tastendruck eine Anfrage auslöst,
- ignoriert verspätete Antworten älterer Suchanfragen,
- besitzt verlinkbare Duftdetails über den URL-Parameter `fragrance`,
- verwendet die Browser-Historie beim Öffnen und Schließen von Ergebnissen,
- zeigt Lade-, Leer- und Fehlerzustände getrennt an.

Die alte Ansicht und das Admin-Center bleiben während dieses Zwischenschritts unverändert. Nach erfolgreicher Dev-Abnahme wird entschieden, ob der Katalog die bisherige öffentliche Ansicht direkt ersetzt oder schrittweise in `main.jsx` integriert wird.

## Sicherheits- und Lastgrenzen

- Suchtext maximal 120 Zeichen
- Seitengröße mindestens 6 und maximal 100
- Standardseitengröße 24
- keine Datenänderung durch Suchaufrufe
- vorhandene `FragranceOut`-Struktur bleibt für einzelne Treffer maßgeblich

## Noch offen in Paket 14

- neuen Katalog in der Dev-Umgebung praktisch abnehmen
- dauerhaft verlinkbare Marken- und Parfümeuransichten
- Admin-Suche getrennt stabilisieren
- Entscheidung und Umsetzung der Ablösung der bisherigen öffentlichen Duftliste

## Spätere Verbesserungen

- Tippfehler-Toleranz über PostgreSQL `pg_trgm`
- Vorschläge und Autovervollständigung
- Filterfacetten mit Trefferzahlen
- mehrere Duftnoten mit UND-/ODER-Verknüpfung
- kanonische, lesbare Slugs zusätzlich zu UUID-Links
