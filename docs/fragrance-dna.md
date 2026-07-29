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

Ein aggregiertes Profil erhält zusätzlich Quellenanzahl, Vertrauensgrad, Quellenabweichung, Prüfstatus, Herkunft und Recherchedatum. Persönliche Bewertungen werden in einem getrennten Profil gespeichert und niemals mit aggregierten Werten vermischt.

## Keine automatische Legacy-Übernahme

Die vorhandenen Felder `sweetness` und `freshness` werden nicht automatisch übernommen. Ebenso werden aus Akkorden oder Duftnoten keine DNA-Werte ohne ausdrücklich dokumentierte und geprüfte Regel abgeleitet.

## Paket 16.4.1 abgeschlossen

Auf `main` vorhanden:

- Migration `0013`
- 16 validierte Dimensionen von `0` bis `10`
- aggregierte und persönliche DNA getrennt
- Herkunft `MANUAL`, `RESEARCH` oder `RULE_BASED`
- Status `OPEN`, `REVIEW_REQUIRED` oder `VERIFIED`
- Endpunkte zum Lesen und Speichern
- Dev-Abnahme mit erfolgreicher Migration und `17 passed, 1 warning`

## Paket 16.4.2 in Arbeit

Branch: `feature/fragrance-dna-card`

Die öffentliche Duftdetailansicht erhält eine responsive Balkenkarte mit:

- vorhandenen Dimensionen, absteigend nach Stärke sortiert
- prägender Signatur aus den drei stärksten vorhandenen Dimensionen
- Herkunft und Prüfstatus
- Vertrauen, Quellenanzahl, Quellenabweichung und Datenstand
- klar getrenntem persönlichen DNA-Bereich
- sichtbarem Leerzustand ohne erfundene Werte

Die Karte liest ausschließlich `GET /api/fragrances/{fragrance_id}/dna`. Ein Radar-Diagramm bleibt eine spätere optionale Ergänzung und ersetzt nicht die barriereärmere Balkendarstellung.

## Abnahme

Vor dem Merge von 16.4.2:

- Frontend-Build
- Prüfung eines Duftes ohne DNA
- Prüfung eines Duftes mit partiellem DNA-Profil
- Prüfung persönlicher DNA
- Desktop- und Mobilansicht

Produktion wird nicht verändert. Abnahme erfolgt ausschließlich in der separaten Dev-Umgebung.
