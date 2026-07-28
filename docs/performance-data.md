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
- Verlaufspunkte für die erste Stunde und nach drei Stunden
- Vertrauensgrad, Quellenanzahl, Quellenabweichung und Prüfstatus
- Version, Produktionszeitraum und Recherchedatum
- persönliche Bewertung in einem optisch getrennten Bereich

Fehlende Werte werden als `Noch offen` oder `–` dargestellt. Das Frontend leitet keine neuen Werte aus den alten Feldern `longevity` und `projection` ab.

## Validierung

- Scores liegen zwischen 0 und 10.
- Vertrauensgrad und Quellenabweichung liegen zwischen 0 und 1.
- Quellenanzahl ist nicht negativ.
- `longevity_min_hours` darf nicht größer als `longevity_max_hours` sein.
- Produktionsjahre und Zeiträume müssen plausibel sein.

## Migration

Migration `0012` ergänzt alle Performance-Felder idempotent. Bestehende Datensätze werden nicht überschrieben. Neue Performance-Werte starten leer, der Prüfstatus standardmäßig mit `OPEN`.

## Geplanter Ausbau

Paket 16.3 soll einen feineren zeitlichen Duftverlauf abbilden, zum Beispiel Opening, Herzphase und Drydown. Bis dafür ein eigenes Datenmodell feststeht, werden keine zusätzlichen Verlaufspunkte erfunden oder aus vorhandenen Scores berechnet.
