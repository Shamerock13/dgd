# DGD – Geprüfte Preisquellen aus dem KI-Export

Stand: 30. Juli 2026

Dieses Dokument ist die verbindliche Spezifikation für Paket 16.7.4.

## Ziel

Zeilen aus dem Tabellenblatt `Preisquellen` werden nicht direkt als aktive Scannerangebote übernommen. DGD prüft Identität, Zuordnung und Produktvariante und speichert neue oder veränderte Quellen zunächst deaktiviert zur manuellen Freigabe.

## Unveränderliche Identität

- Jede Preisquelle besitzt eine dauerhafte `offer_source_id` als UUID.
- Eine bereits vorhandene `offer_source_id` darf niemals einer anderen `fragrance_id` zugeordnet werden.
- Eine vorhandene `offer_source_id` darf nicht durch eine neue ID ersetzt werden.
- Doppelte `offer_source_id` innerhalb derselben Arbeitsmappe werden abgewiesen.
- Bei neuen Zeilen darf die KI eine zuvor vom DGD-Export vorgegebene leere ID nicht selbst erfinden. Neue Quellen erhalten ihre ID erst kontrolliert durch DGD.

## Pflichtangaben

Für eine übernehmbare Preisquelle sind erforderlich:

- `fragrance_id`
- `merchant_name`
- direkte `product_url` mit `http` oder `https`
- `size_ml`
- `concentration`
- `product_kind`
- `currency`
- `market_country`

`product_kind` wird auf kontrollierte Werte begrenzt:

- `regular`
- `tester`
- `set`
- `sample`
- `refill`

Suchseiten, Kategorieseiten und offensichtlich nicht direkte Produktlinks werden als Prüfkonflikt markiert.

## Variantenregeln

DGD behandelt folgende Kombination als eigenständige Angebotsvariante:

- Duft
- Händler
- Produkt-URL
- Größe
- Konzentration
- Produkttyp
- optionale Produktvariante

Größen, Konzentrationen, Tester, Sets, Samples und Refills dürfen beim Preisvergleich nicht miteinander vermischt werden.

## Scanner-Sicherheit

- Importierte Quellen starten immer mit `scanner_active = false`.
- Status neuer Quellen: `PENDING_REVIEW`.
- Eine geänderte Produkt-URL setzt `scanner_active = false` und Status `LINK_CHANGED`.
- Ein Excel-Wert `scanner_active = true` wird niemals direkt übernommen.
- Erst eine spätere ausdrückliche Admin-Freigabe darf den Scanner aktivieren.
- Ein Import startet keinen Scannerlauf.

## Vorschau

Die Rückimport-Vorschau zeigt pro Preisquelle:

- Händler und Duft
- `offer_source_id`
- alte und neue Produkt-URL
- Größe, Konzentration, Produkttyp und Variante
- Preis, Versand und Gesamtpreis
- Verfügbarkeit
- EAN/GTIN und Händler-SKU
- Markt und Währung
- Vertrauensstatus und Variantenwarnung
- Ergebnis der technischen Prüfung

Neue Quellen und Änderungen werden nicht automatisch ausgewählt, wenn eine Variantenwarnung oder ein Linkkonflikt vorliegt.

## Kontrollierte Übernahme

Eine ausgewählte Zeile wird unmittelbar vor dem Speichern erneut geprüft. Veraltete Vorschauen werden mit HTTP 409 abgewiesen.

Bei einer neuen Quelle:

- Händler wird gefunden oder kontrolliert angelegt.
- DGD erzeugt `offer_source_id`.
- Angebot wird deaktiviert mit Status `PENDING_REVIEW` gespeichert.
- Preiswerte dürfen gespeichert werden, aktivieren aber keinen Scanner.

Bei einer vorhandenen Quelle:

- `offer_source_id` bleibt identisch.
- Zuordnung zum Duft bleibt unverändert.
- Metadaten dürfen feldweise aktualisiert werden.
- Linkänderungen deaktivieren den Scanner und verlangen eine spätere Freigabe.

## Protokollierung

Jeder erfolgreiche Lauf wird in `import_quality_runs` protokolliert mit:

- Export-ID
- Dateiname
- ausgewählten Quellen
- neu angelegten Quellen
- aktualisierten Quellen
- deaktivierten Scannern
- erkannten Konflikten
- Zeitpunkt und Ergebnis

Fehler führen zum Rollback der gesamten Transaktion.

## Nicht Bestandteil von 16.7.4

- automatische Scanner-Aktivierung
- automatischer erster Abruf der Produktseite
- automatische Veröffentlichung als günstigstes Angebot
- Zusammenführung unterschiedlicher Größen oder Varianten
- Preisalarm
