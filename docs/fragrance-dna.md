# Duft-DNA in DGD

## Ziel

Die Duft-DNA beschreibt den wahrgenommenen Charakter eines Duftes als strukturierte, vergleichbare Werte. Sie ergänzt Noten, Akkorde und Performance, ersetzt diese aber nicht.

## Dimensionen

Jede Dimension ist optional und wird von `0` bis `10` bewertet:

- `fresh` – frisch
- `citrus` – zitrisch
- `green` – grün
- `aquatic` – aquatisch
- `floral` – floral
- `fruity` – fruchtig
- `sweet` – süß
- `gourmand` – gourmandig
- `spicy` – würzig
- `woody` – holzig
- `smoky` – rauchig
- `earthy` – erdig
- `resinous` – harzig
- `leathery` – ledrig
- `powdery` – pudrig
- `animalic` – animalisch

Fehlende Dimensionen bleiben leer. Ein fehlender Wert ist nicht gleichbedeutend mit `0`.

## Herkunft und Qualität

Ein aggregiertes Profil erhält zusätzlich:

- `dna_source_count` – Anzahl berücksichtigter Quellen
- `dna_confidence` – Vertrauensgrad von `0` bis `1`
- `dna_disagreement` – Quellenabweichung von `0` bis `1`
- `dna_status` – `OPEN`, `REVIEW_REQUIRED` oder `VERIFIED`
- `dna_origin` – `MANUAL`, `RESEARCH` oder `RULE_BASED`
- `dna_researched_at` – Zeitpunkt der letzten Recherche

Persönliche Bewertungen werden in einem getrennten Profil gespeichert und niemals mit aggregierten Werten vermischt.

## Keine automatische Legacy-Übernahme

Die vorhandenen Felder `sweetness` und `freshness` werden nicht automatisch in die Duft-DNA übernommen. Ebenso werden aus `accords`, `top_notes`, `heart_notes` oder `base_notes` keine Werte ohne ausdrücklich dokumentierte und geprüfte Regel abgeleitet.

## Darstellung

Die erste UI-Version zeigt Balken für vorhandene Dimensionen, sortiert nach Stärke. Herkunft, Prüfstatus, Vertrauensgrad und Quellenanzahl bleiben sichtbar. Bei vollständig leeren Profilen erscheint ein klarer Leerzustand.

Ein Radar-Diagramm ist eine spätere optionale Ergänzung und ersetzt nicht die barriereärmere Balkendarstellung.

## Umsetzung

Paket 16.4 wird geteilt:

1. **16.4.1 Datenmodell und API** – Migration, Validierung, Tests und Dokumentation
2. **16.4.2 Duft-DNA-Karte** – responsive Darstellung im öffentlichen Duftprofil

Produktion wird nicht verändert. Abnahme und Migration erfolgen ausschließlich in der separaten Dev-Umgebung.