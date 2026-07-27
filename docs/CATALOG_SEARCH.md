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

## Sicherheits- und Lastgrenzen

- Suchtext maximal 120 Zeichen
- Seitengröße mindestens 6 und maximal 100
- Standardseitengröße 24
- keine Datenänderung durch Suchaufrufe
- vorhandene `FragranceOut`-Struktur bleibt für einzelne Treffer maßgeblich

## Noch offen in Paket 14

- Frontend an den paginierten Endpunkt anbinden
- Filterzustand in der URL speichern
- dauerhaft verlinkbare Duft-, Marken- und Parfümeuransichten
- zuverlässige Browser-Zurück-Navigation
- Admin-Suche getrennt stabilisieren
