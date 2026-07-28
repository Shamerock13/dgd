# DGD – Preisbeobachtung & Händlervergleich 1.0

Stand: 28. Juli 2026

## Ziel

Für jeden Duft sollen aktuelle Händlerangebote getrennt von den redaktionellen Duftdaten gespeichert werden. Aus den Angeboten werden der günstigste verfügbare Gesamtpreis, der Preis pro 100 ml und ein nachvollziehbarer Preisverlauf berechnet.

## Datenmodell

- `price_retailers`: Händler mit Basis-URL und Aktivstatus
- `fragrance_offers`: aktueller Zustand eines konkreten Händlerangebots
- `price_observations`: unveränderliche Einzelmessungen für den Preisverlauf

Ein Angebot ist durch Händler und Produkt-URL eindeutig. Jede neue Prüfung aktualisiert den aktuellen Angebotszustand und schreibt zusätzlich eine Beobachtung.

## Standardhändler

Beim Backend-Start werden idempotent sechs aktive Händler angelegt, sofern sie noch nicht existieren:

- Douglas
- Flaconi
- Notino
- Parfumdreams
- easycosmetic
- Sephora

Bestehende Händler werden dabei weder überschrieben noch doppelt angelegt.

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

## Admin-Oberfläche

Im Admin-Center steht der Bereich **Preise & Händler** bereit. Dort können:

- die automatisch angelegten Händler geprüft werden,
- weitere Händler ergänzt werden,
- manuelle Testangebote einem Duft zugeordnet werden,
- Größe, Produktart, Preis, Versand und Lieferbarkeit gespeichert werden.

Jede manuelle Speicherung erzeugt ebenfalls eine unveränderliche Preisbeobachtung.

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
- Die neue Preislogik greift noch nicht automatisch auf externe Seiten zu. Händleradapter und tägliche Scannerläufe folgen getrennt.

## Nächster Baustein

Erste Händleradapter und tägliche Preisprüfung über den getrennten Scanner-Worker. Danach Anzeige des günstigsten Angebots und des Preisverlaufs in der Duftdetailansicht.
