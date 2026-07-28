# DGD – Preisbeobachtung & Händlervergleich 1.0

Stand: 28. Juli 2026

## Ziel

Für jeden Duft sollen aktuelle Händlerangebote getrennt von den redaktionellen Duftdaten gespeichert werden. Aus den Angeboten werden der günstigste verfügbare Gesamtpreis, der Preis pro 100 ml und ein nachvollziehbarer Preisverlauf berechnet.

## Datenmodell

- `price_retailers`: Händler mit Basis-URL und Aktivstatus
- `fragrance_offers`: aktueller Zustand eines konkreten Händlerangebots
- `price_observations`: unveränderliche Einzelmessungen für den Preisverlauf

Ein Angebot ist durch Händler und Produkt-URL eindeutig. Jede neue Prüfung aktualisiert den aktuellen Angebotszustand und schreibt zusätzlich eine Beobachtung.

## Endpunkte

```text
GET  /api/prices/retailers
POST /api/prices/retailers
POST /api/prices/offers/check
GET  /api/prices/fragrances/{fragrance_id}?days=90
```

Der Duft-Endpunkt liefert:

- aktuell verfügbare und nicht verfügbare Angebote
- günstigstes verfügbares Angebot inklusive Versand
- Preis pro 100 ml, sofern eine Größe bekannt ist
- historischen niedrigsten Gesamtpreis
- Preisverlauf für 1 bis 1095 Tage

## Produktarten

Unterstützt werden zunächst:

- `bottle`
- `tester`
- `set`
- `sample`
- `refill`

Damit werden Flakons, Tester, Geschenksets, Proben und Nachfüllungen nicht versehentlich direkt miteinander verglichen. Die erste API sortiert dennoch primär nach Gesamtpreis; getrennte Oberflächenfilter folgen im nächsten Baustein.

## Sicherheits- und Qualitätsregeln

- Händler- und Produkt-URLs müssen vollständige HTTP- oder HTTPS-Adressen sein.
- Angebote werden immer einem vorhandenen Duft und einem aktiven Händler zugeordnet.
- Dieselbe Händler-URL darf nicht mehreren Düften zugeordnet werden.
- Preise und Versandkosten werden getrennt gespeichert; verglichen wird der Gesamtpreis.
- Ausverkaufte Angebote bleiben für Verlauf und Nachvollziehbarkeit erhalten, zählen aber nicht als günstigstes aktuelles Angebot.
- Die neue Preislogik greift nicht auf externe Seiten zu. Händleradapter und tägliche Scannerläufe folgen getrennt.

## Nächster Baustein

Admin-Oberfläche für Händler und manuelle Testangebote, danach Händleradapter und tägliche Preisprüfung über den getrennten Scanner-Worker.
