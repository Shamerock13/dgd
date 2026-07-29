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

Fehlende Dimensionen bleiben leer. Ein fehlender Wert ist nicht `0`.

## Herkunft und Qualität

Aggregierte Profile speichern Herkunft, Prüfstatus, Quellenanzahl, Vertrauensgrad, Quellenabweichung und Recherchedatum. Persönliche Bewertungen liegen in einem getrennten Profil.

Erlaubte Herkunft:
- `MANUAL`
- `RESEARCH`
- `RULE_BASED`

Erlaubte Statuswerte:
- `OPEN`
- `REVIEW_REQUIRED`
- `VERIFIED`

## Datenprinzipien

- keine automatische Übernahme aus `sweetness`, `freshness`, Akkorden oder Duftnoten
- persönliche und aggregierte DNA niemals vermischen
- ungeprüfte Recherche- oder KI-Werte niemals automatisch veröffentlichen

## Umsetzungsstand

### 16.4.1 abgeschlossen

Migration `0013`, Validierung, API und Backendtests. Dev-Ergebnis: `17 passed, 1 warning in 0.53s`.

### 16.4.2 abgeschlossen

Responsive öffentliche Balkenkarte mit Sortierung nach Stärke, prägender Signatur, Qualitätsmetadaten, persönlichem Bereich und Leerzuständen.

### 16.4.3 in PR #81 praktisch abgenommen

Der Admin-Editor unterstützt:

- alle 16 Dimensionen
- partielle aggregierte Profile
- getrennte persönliche Profile
- Herkunft, Status und Qualitätsmetadaten
- bewusstes Leeren einzelner Werte
- Speichern und erneutes Laden beider Profile

Die DNA-Routen werden vor dem SPA-Fallback registriert, damit API-Aufrufe nicht auf `static/index.html` fallen.

## Nächster Baustein

16.4.4 ergänzt kontrollierte Recherchevorschläge, sichtbare Quellen und einen manuellen Prüf- und Freigabeworkflow.

Produktion wird nicht verändert. Abnahme erfolgt ausschließlich in der separaten Dev-Umgebung.
