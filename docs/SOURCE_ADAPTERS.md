# DGD – Quellenadapter & Mehrseiten-Scanner

## Stand

Paket **Quellenadapter & Mehrseiten-Scanner 1.0**.

## Ziel

Recherchequellen können entweder eine einzelne Produktseite oder eine Listen-, Kategorie- beziehungsweise Suchseite darstellen. Mehrseitenquellen sammeln zunächst passende Produktlinks und übergeben jede begrenzte Produktseite anschließend an den bestehenden DGD-Scanner. Treffer landen weiterhin ausschließlich in der Import-Warteschlange.

## Adapter

### SINGLE

- scannt genau die hinterlegte URL
- geeignet für einzelne Produkt- oder Duftseiten
- verwendet weiterhin JSON-LD und den vorhandenen Titel-Fallback

### LIST

- liest Links aus der hinterlegten Listen- oder Kategorieseite
- löst relative Links gegen die Quellenadresse auf
- entfernt URL-Fragmente und doppelte Links
- filtert optional mit einem regulären Ausdruck
- bleibt standardmäßig auf derselben Domain
- verarbeitet höchstens 100 Produktseiten pro Scan

## Quellenfelder

- `adapter_type`: `SINGLE` oder `LIST`
- `link_pattern`: optionaler regulärer Ausdruck für Produktlinks
- `max_pages`: Begrenzung zwischen 1 und 100
- `same_domain_only`: externe Domains verwerfen
- `interval_hours`: bestehendes Scanintervall
- `active`: Quelle in Sammelläufe aufnehmen

## Sicherheit

- interne, private, reservierte und lokale Netzwerkziele bleiben gesperrt
- gefundene Produktseiten werden erneut durch die öffentliche URL-Prüfung geschickt
- keine automatische Veröffentlichung oder Freigabe
- harte Begrenzung von 2 MB HTML pro Seite
- harte Begrenzung von 100 Produktseiten pro Quellenlauf
- Weiterleitungen werden nur über den bestehenden HTTP-Client verarbeitet

## Scan-Historie

Zusätzlich werden gespeichert:

- `pages_scanned`: tatsächlich erfolgreich geprüfte Produktseiten
- `links_discovered`: auf der Startseite gefundene und akzeptierte Links
- Anzahl gefundener Kandidaten
- Anzahl neu angelegter Kandidaten
- Anzahl möglicher Dubletten
- Fehlerstatus des gesamten Quellenlaufs

## Bedienung

Unter **Admin → Recherche** kann beim Anlegen einer Quelle der Quellentyp gewählt werden. Bei `LIST` erscheinen Link-Filter, Seitenlimit und Domain-Begrenzung. Ein sinnvoller Filter ist möglichst spezifisch, beispielsweise:

```text
/product/|/products/|/parfum/|/fragrance/
```

Ein leerer Filter akzeptiert alle HTTP-/HTTPS-Links derselben Domain bis zum Seitenlimit. Das ist nur für sehr gezielte Kategorieseiten empfehlenswert.

## Tests

- SINGLE-Quelle verarbeitet genau eine Seite
- LIST-Quelle findet relative und absolute Produktlinks
- doppelte Links werden nur einmal verarbeitet
- fremde Domains werden bei aktivierter Domain-Grenze verworfen
- ungültige reguläre Ausdrücke werden beim Speichern abgelehnt
- `max_pages` wird auf höchstens 100 begrenzt
- Treffer landen nur in `research_candidates`
- Backend-Compile und Frontend-Build müssen grün sein

## Nächste Ideen

- vorkonfigurierte Adapter für bekannte Quelltypen
- CSS-Selektoren zusätzlich zu regulären Ausdrücken
- Pagination über „Nächste Seite“-Links
- robots.txt- und Crawl-Delay-Unterstützung
- pausierbare Hintergrundläufe mit Fortschrittsanzeige
- automatische tägliche Ausführung durch einen eigenen Worker
