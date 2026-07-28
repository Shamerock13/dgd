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
GET  /api/prices/scanner/status
POST /api/prices/scanner/run-due?interval_hours=24&limit=100
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

## Automatischer Preis-Scanner

Der getrennte Container `DGD-Dev-Scanner` prüft vorhandene Händlerangebote automatisch erneut. Standardmäßig gilt:

```text
PRICE_SCANNER_ENABLED=true
PRICE_SCAN_INTERVAL_HOURS=24
```

Ein Angebot wird fällig, sobald seine letzte Prüfung mindestens 24 Stunden zurückliegt. Pro Worker-Zyklus werden höchstens 100 fällige Angebote verarbeitet. Fehler eines einzelnen Händlers oder Angebots werden protokolliert und stoppen weder weitere Angebote noch den Worker.

Die erste Adapterstufe liest strukturierte Produktdaten im Format JSON-LD aus. Freigegeben sind derzeit Produktseiten der sechs Standardhändler. Das bedeutet noch keine automatische Produktsuche: Eine konkrete Produkt-URL wird zunächst im Admin-Bereich einem Duft zugeordnet und anschließend täglich selbstständig aktualisiert.

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
- Automatische Prüfungen akzeptieren ausschließlich öffentliche Netzwerkziele.
- Die Produkt-Domain muss zur gespeicherten Händler-Domain gehören.
- Nur ausdrücklich freigegebene Händler-Domains werden automatisch abgerufen.
- Angebote werden immer einem vorhandenen Duft und einem aktiven Händler zugeordnet.
- Dieselbe Händler-URL darf nicht mehreren Düften zugeordnet werden.
- Preise und Versandkosten werden getrennt gespeichert; verglichen wird der Gesamtpreis.
- Ausverkaufte Angebote bleiben für Verlauf und Nachvollziehbarkeit erhalten, zählen aber nicht als günstigstes aktuelles Angebot.
- Jeder erfolgreiche automatische Abruf erzeugt eine unveränderliche Preisbeobachtung.

## Nächster Baustein

Automatische Produktsuche nach Marke und Duftname, danach Anzeige des günstigsten Angebots und des Preisverlaufs in der Duftdetailansicht.
