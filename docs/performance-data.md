# Performance-Daten in DGD

## Ziel

DGD speichert Duft-Performance nicht nur als freien Text, sondern als vergleichbare strukturierte Werte. Rechercheergebnisse und persönliche Erfahrungen bleiben getrennt.

## Datenmodell

### Recherchierte beziehungsweise aggregierte Werte

| Feld | Bedeutung |
| --- | --- |
| `longevity_min_hours` | untere Grenze der Haltbarkeit in Stunden |
| `longevity_max_hours` | obere Grenze der Haltbarkeit in Stunden |
| `longevity_score` | normalisierte Haltbarkeit von 0 bis 10 |
| `projection` | allgemeine Projektion von 0 bis 10; Legacy-Feld bleibt kompatibel |
| `projection_first_hour` | Projektion während der ersten Stunde |
| `projection_after_three_hours` | Projektion nach ungefähr drei Stunden |
| `sillage` | Stärke der Duftspur von 0 bis 10 |
| `drydown_strength` | wahrgenommene Stärke im Drydown von 0 bis 10 |
| `performance_score` | zusammengefasste Gesamtperformance von 0 bis 10 |

### Qualität und Herkunft

| Feld | Bedeutung |
| --- | --- |
| `performance_source_count` | Anzahl berücksichtigter Quellen |
| `performance_confidence` | Vertrauensgrad von 0 bis 1 |
| `performance_disagreement` | Streuung beziehungsweise Widerspruch der Quellen von 0 bis 1 |
| `performance_status` | `OPEN`, `REVIEW_REQUIRED` oder `VERIFIED` |
| `performance_researched_at` | Zeitpunkt der letzten Recherche |
| `performance_version` | untersuchte Version oder Reformulierung |
| `performance_production_period` | zugehöriger Produktionszeitraum |

### Persönliche Werte

| Feld | Bedeutung |
| --- | --- |
| `personal_longevity_hours` | persönlich erlebte Haltbarkeit in Stunden |
| `personal_projection` | persönliche Projektion von 0 bis 10 |
| `personal_sillage` | persönliche Sillage von 0 bis 10 |
| `personal_performance_score` | persönliche Gesamtbewertung von 0 bis 10 |

Persönliche Werte dürfen nicht mit aggregierten Community- oder Recherchewerten vermischt werden.

## Darstellung im Duftprofil

Die Performance-Karte im öffentlichen Katalog zeigt:

- Haltbarkeit als Stundenbereich und Score
- Gesamtperformance, Projektion, Sillage und Drydown
- Vertrauensgrad, Quellenanzahl, Quellenabweichung und Prüfstatus
- Version, Produktionszeitraum und Recherchedatum
- persönliche Bewertung in einem optisch getrennten Bereich
- ein aus dem Gesamtwert abgeleitetes, rein beschreibendes Stärke-Badge

## Zeitlicher Duftverlauf

Paket 16.3 visualisiert ausschließlich bereits vorhandene strukturierte Werte:

1. `projection_first_hour` als Opening von 0 bis 1 Stunde
2. `projection_after_three_hours` als Herzphase nach ungefähr drei Stunden
3. `drydown_strength` als Stärke der späteren Basisphase

Jede Phase zeigt Score, verbale Einordnung und einen Balken. Eine kurze Zusammenfassung beschreibt nur das Verhältnis dieser drei vorhandenen Werte. Sie erzeugt keine zusätzlichen Messpunkte und ist keine KI-Recherche.

Fehlt ein Phasenwert, bleibt die betreffende Phase sichtbar und wird mit `Noch offen` gekennzeichnet. Sind alle drei Werte leer, erklärt die Karte ausdrücklich, dass noch kein zeitlicher Verlauf vorliegt.

## Einordnungen

Für die sichtbaren Stärke-Bezeichnungen gelten feste Bereiche:

- 8,0 bis 10,0: sehr stark
- 6,0 bis unter 8,0: stark
- 4,0 bis unter 6,0: mittel beziehungsweise durchschnittlich
- 2,0 bis unter 4,0: hautnah
- unter 2,0: sehr dezent

Diese Texte sind Darstellungsregeln und keine zusätzlichen gespeicherten Forschungsdaten.

## Validierung

- Scores liegen zwischen 0 und 10.
- Vertrauensgrad und Quellenabweichung liegen zwischen 0 und 1.
- Quellenanzahl ist nicht negativ.
- `longevity_min_hours` darf nicht größer als `longevity_max_hours` sein.
- Produktionsjahre und Zeiträume müssen plausibel sein.

## Migration

Migration `0012` ergänzt alle Performance-Felder idempotent. Bestehende Datensätze werden nicht überschrieben. Neue Performance-Werte starten leer, der Prüfstatus standardmäßig mit `OPEN`.

## Weiterer Ausbau

Ein feinerer Verlauf mit zusätzlichen Zeitpunkten benötigt später ein eigenes Datenmodell und eigene Quellenwerte. Solche Zwischenwerte werden bis dahin weder erfunden noch aus den drei vorhandenen Phasen hochgerechnet.
