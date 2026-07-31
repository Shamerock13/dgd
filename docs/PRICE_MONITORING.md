# DGD – Preisbeobachtung & Händlervergleich 1.0

Stand: 31. Juli 2026

## Ziel

Für jeden Duft werden aktuelle Händlerangebote getrennt von den redaktionellen Duftdaten gespeichert. Aus den Angeboten entstehen ein nachvollziehbarer Preisverlauf, variantengenaue Bestpreise und lokale Preisalarme.

## Datenmodell

- `price_retailers`: Händler mit Basis-URL und Aktivstatus
- `fragrance_offers`: aktueller Zustand einer konkreten Händler-Produktseite
- `price_observations`: unveränderliche Einzelmessungen für den Preisverlauf
- `price_source_review_events`: Freigaben, Ablehnungen, Scannerentscheidungen, Tests und Browserimporte
- `price_alerts`: variantengenaue lokale Schwellenwerte und Auslösestatus

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
GET    /api/prices/retailers
POST   /api/prices/retailers
POST   /api/prices/offers/check
GET    /api/prices/fragrances/{fragrance_id}?days=90
GET    /api/prices/fragrances/{fragrance_id}/alerts
PUT    /api/prices/fragrances/{fragrance_id}/alerts/{variant_key}
DELETE /api/prices/fragrances/{fragrance_id}/alerts/{variant_key}
GET    /api/prices/review/offers
POST   /api/prices/review/offers/{offer_id}/decision
POST   /api/prices/review/offers/{offer_id}/scanner
POST   /api/prices/review/offers/{offer_id}/test
GET    /api/prices/browser-connector/health
GET    /api/prices/browser-connector/queue
POST   /api/prices/browser-connector/import
GET    /api/prices/browser-connector/extension.zip
GET    /api/prices/scanner/status
POST   /api/prices/scanner/run-due
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

## Preisalarme

Paket 18.2 speichert einen Alarm eindeutig je Duft und `variant_key`. Ein Alarm darf nur für eine vollständig bestimmte Variante mit Größe und Konzentration angelegt werden.

Mögliche Regeln:

- Zielpreis inklusive Versand in EUR
- maximaler prozentualer Abstand zum historischen Tief
- beide Regeln gleichzeitig; eine erfüllte Regel reicht zur Auslösung

Statuswerte:

```text
INACTIVE
WAITING
TRIGGERED
NO_ELIGIBLE_OFFER
VARIANT_MISSING
```

Der Auslösungszähler steigt nur beim Wechsel von einem anderen Zustand nach `TRIGGERED`. Solange der Preis unter der Schwelle bleibt, erzeugen weitere Prüfungen keine neue Auslösung. Erst wenn der Alarm zwischenzeitlich wieder auf `WAITING`, `NO_ELIGIBLE_OFFER` oder `VARIANT_MISSING` wechselt, kann eine spätere Zielerreichung erneut auslösen.

Jede neue `price_observations`-Zeile stößt innerhalb derselben Datenbanktransaktion eine Neubewertung an. Das gilt damit für manuell gespeicherte Preisprüfungen, automatische Scannerläufe, bewusst übertragene Browser-Connector-Preise und zukünftige Importwege, die ebenfalls eine Preisbeobachtung schreiben.

## Browser-Prüfrunde

Paket 18.3 ergänzt eine zustandslose Prüfliste für Quellen, die nur über den normalen Browser geprüft werden können. In die Queue gelangen ausschließlich Angebote mit:

```text
review_status = APPROVED
trust_status = BROWSER_REQUIRED
scanner_active = false
retailer.active = true
```

Die letzte manuelle Prüfung stammt aus dem jüngsten Audit-Ereignis `BROWSER_IMPORT_SUCCESS`. Daraus entstehen die Statuswerte:

```text
NEVER_CHECKED
DUE
CURRENT
```

Die Fälligkeit richtet sich nach `scan_interval`. Unterstützt werden Stunden-, Tages-, Wochen- und Monatsangaben sowie kompakte Werte wie `24h` oder `7d`. Unbekannte oder leere Angaben verwenden einen sicheren Standard von 24 Stunden.

Sortierung:

1. noch nie manuell geprüfte Quellen
2. danach die am längsten nicht manuell geprüften Quellen

Der Admin zeigt die Anzahl fälliger, nie geprüfter und aktueller Browser-Quellen. Die Prüfrunde startet erst nach einem bewussten Klick und öffnet die erste fällige Händlerseite. Nach jeder erfolgreichen Übernahme fragt die Erweiterung die Queue erneut ab. Eine weitere Produktseite wird nur über den Knopf **Nächste fällige Quelle öffnen** geladen. Ist nichts mehr fällig, zeigt die Erweiterung **Prüfrunde abgeschlossen**.

Die Queue speichert keine Sitzung. Browser- oder Containerneustarts hinterlassen daher keine halbfertige Runde; der aktuelle Zustand ergibt sich jederzeit neu aus den erfolgreichen Browserimporten.

## Sicherheits- und Qualitätsregeln

- öffentliche Preise stammen ausschließlich aus freigegebenen Quellen aktiver Händler
- Händler- und Produkt-URLs müssen vollständige HTTP- oder HTTPS-Adressen sein
- die Produkt-Domain muss zur gespeicherten Händler-Domain gehören
- nur ausdrücklich freigegebene Quellen werden automatisch abgerufen
- dieselbe Händler-URL darf nicht mehreren Düften zugeordnet werden
- Preise und Versandkosten werden getrennt gespeichert; verglichen wird der Gesamtpreis
- ausverkaufte Angebote bleiben für Verlauf und Nachvollziehbarkeit erhalten, zählen aber nicht als aktuelles Bestangebot
- Preisalarme werten ausschließlich lieferbare Angebote freigegebener Quellen aktiver Händler aus
- Browser-Prüfrunden enthalten keine ungeprüften Quellen, inaktiven Händler oder Server-Scanner-Quellen
- jede Händlerseite wird ausschließlich nach einem bewussten Klick geöffnet und übertragen
- jede erfolgreiche automatische oder manuelle Prüfung erzeugt eine unveränderliche Preisbeobachtung
- unterschiedliche Varianten dürfen niemals als gleichwertige Angebote vermischt werden
- CAPTCHA-, Proxy- und Bot-Schutz-Umgehungen bleiben ausgeschlossen

## Nächste Bausteine

- externe Benachrichtigungskanäle für ausgelöste Preisalarme
- zusätzliche Händleradapter und kontrollierte Produktsuche
- weitere Datenvalidierung des Master-Imports
