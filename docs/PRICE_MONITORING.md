# DGD – Preisbeobachtung & Händlervergleich 1.0

Stand: 31. Juli 2026

## Ziel

Für jeden Duft werden aktuelle Händlerangebote getrennt von den redaktionellen Duftdaten gespeichert. Aus den Angeboten entstehen ein nachvollziehbarer Preisverlauf, variantengenaue Bestpreise und später Preisalarme.

## Datenmodell

- `price_retailers`: Händler mit Basis-URL und Aktivstatus
- `fragrance_offers`: aktueller Zustand einer konkreten Händler-Produktseite
- `price_observations`: unveränderliche Einzelmessungen für den Preisverlauf
- `price_source_review_events`: Freigaben, Ablehnungen, Scannerentscheidungen, Tests und Browserimporte

Ein Angebot besitzt eine stabile `offer_source_id`. Händler und Produkt-URL bleiben eindeutig zugeordnet. Jede erfolgreiche Prüfung aktualisiert den aktuellen Angebotszustand und schreibt zusätzlich eine Preisbeobachtung.

## Prüf- und Freigabeworkflow

Neue oder geänderte Preisquellen starten mit:

```text
review_status = PENDING_REVIEW
scanner_active = false
```

Im Admin-Bereich **Preisquellen prüfen** werden Produktseite, Händler, Größe, Konzentration, Variante und Produkttyp kontrolliert. Die Quelle kann anschließend freigegeben oder abgelehnt werden. Die Scanner-Aktivierung bleibt eine separate bewusste Aktion.

Automatische Scannerläufe berücksichtigen nur:

- freigegebene Preisquellen
- ausdrücklich aktivierte Quellen
- aktive Händler
- unterstützte Händleradapter

## Server-Scanner und Browser-Connector

Der getrennte Container `DGD-Dev-Scanner` prüft fällige Quellen standardmäßig im 24-Stunden-Rhythmus. Der leichte HTTP-Abruf fällt bei Bedarf auf serverseitiges Chromium zurück.

Blockiert ein Händler auch Chromium, wird die Quelle auf `BROWSER_REQUIRED` gesetzt und der Server-Scanner deaktiviert. Die Chrome-/Edge-Erweiterung liest erst nach einem bewussten Klick die aktuell geöffnete Produktseite und überträgt strukturierte Produktdaten an die lokale DGD-API. CAPTCHA-, Login-, Proxy- oder Bot-Schutz-Umgehungen finden nicht statt.

## Wichtige Endpunkte

```text
GET  /api/prices/retailers
POST /api/prices/retailers
POST /api/prices/offers/check
GET  /api/prices/fragrances/{fragrance_id}?days=90
GET  /api/prices/review/offers
POST /api/prices/review/offers/{offer_id}/decision
POST /api/prices/review/offers/{offer_id}/scanner
POST /api/prices/review/offers/{offer_id}/test
GET  /api/prices/browser-connector/health
POST /api/prices/browser-connector/import
GET  /api/prices/browser-connector/extension.zip
GET  /api/prices/scanner/status
POST /api/prices/scanner/run-due
```

## Variantenvergleich

Paket 18.1 gruppiert öffentliche Angebote anhand von:

- Produktart
- Größe in ml
- normalisierter Konzentration

Flakons, Tester, Sets, Proben und Nachfüllungen werden nicht direkt miteinander verglichen. Auch unterschiedliche Größen und Konzentrationen bleiben getrennt. Unvollständige Variantendaten bilden eine eigene deutlich gekennzeichnete Gruppe.

Der Duft-Endpunkt liefert je Variantengruppe:

- aktuelle und nicht verfügbare Angebote
- günstigstes lieferbares Angebot inklusive Versand
- Preis pro 100 ml
- historisches Allzeittief
- Abstand des aktuellen Bestpreises zum Tief
- Preisbeobachtungen für den gewählten Zeitraum
- täglich günstigsten beobachteten Gesamtpreis für die Verlaufsgrafik
- letzte Prüfung und Datenvollständigkeit

## Sicherheits- und Qualitätsregeln

- öffentliche Preise stammen ausschließlich aus freigegebenen Quellen aktiver Händler
- Händler- und Produkt-URLs müssen vollständige HTTP- oder HTTPS-Adressen sein
- die Produkt-Domain muss zur gespeicherten Händler-Domain gehören
- nur ausdrücklich freigegebene Quellen werden automatisch abgerufen
- dieselbe Händler-URL darf nicht mehreren Düften zugeordnet werden
- Preise und Versandkosten werden getrennt gespeichert; verglichen wird der Gesamtpreis
- ausverkaufte Angebote bleiben für Verlauf und Nachvollziehbarkeit erhalten, zählen aber nicht als aktuelles Bestangebot
- jede erfolgreiche automatische oder manuelle Prüfung erzeugt eine unveränderliche Preisbeobachtung
- unterschiedliche Varianten dürfen niemals als gleichwertige Angebote vermischt werden

## Nächste Bausteine

- Preisalarme mit variantengenauem Zielpreis oder Abstand zum historischen Tief
- Komfortfunktionen für mehrere bewusst gestartete Browserprüfungen
- zusätzliche Händleradapter und kontrollierte Produktsuche
