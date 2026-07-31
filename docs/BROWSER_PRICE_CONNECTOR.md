# DGD Browser-Preis-Connector

Paket 16.7.6 ergänzt eine manuell gestartete Chrome-/Edge-Erweiterung für Händler, die sowohl normale Serverabrufe als auch serverseitiges Chromium blockieren.

## Ablauf

1. Die Preisquelle ist in DGD bereits freigegeben.
2. Ein fehlgeschlagener Serverabruf markiert sie als `BROWSER_REQUIRED` und deaktiviert den Server-Scanner.
3. Im Admin unter **Preisquellen prüfen** wird die Erweiterung als ZIP heruntergeladen.
4. Die Erweiterung wird in Chrome oder Edge als entpackte Erweiterung geladen.
5. In den Erweiterungsoptionen wird die lokale DGD-Backend-Adresse eingetragen, zum Beispiel `http://192.168.1.20:18080`.
6. Die hinterlegte Produktseite wird im normalen Browser geöffnet.
7. Erst nach einem bewussten Klick auf **Preis an DGD senden** werden Produktdaten an die lokale DGD-Instanz übertragen.

## Übertragene Produktdaten

- aktuelle URL und kanonische Produkt-URL
- Seitentitel
- strukturierte JSON-LD-Produktdaten
- preis- und produktbezogene Meta-Angaben
- begrenzter sichtbarer Seitentext zur Preis- und Verfügbarkeitserkennung
- Erweiterungsversion

Die Übertragung erfolgt ausschließlich an die vom Nutzer konfigurierte DGD-Adresse.

## Backend-Prüfungen

- Connector-Protokollheader muss vorhanden sein.
- Browser-Origin darf nur `chrome-extension://` oder `moz-extension://` sein, sofern ein Origin gesendet wird.
- Quelle muss `APPROVED` und als `BROWSER_REQUIRED` markiert sein.
- Händlerdomain, aktuelle URL, kanonische URL und gespeicherte Produkt-URL müssen zusammenpassen.
- Trackingparameter werden bei der Zuordnung ignoriert; produktrelevante Queryparameter bleiben erhalten.
- EUR-Preis muss zwischen 0,50 und 10.000 Euro liegen.
- Server-Scanner bleibt deaktiviert.
- Jede erfolgreiche Übernahme erzeugt eine `PriceObservation` und ein Audit-Ereignis `BROWSER_IMPORT_SUCCESS`.

## Sicherheitsgrenzen

- keine automatische Navigation durch Händlerseiten
- keine CAPTCHA- oder Bot-Schutz-Umgehung
- keine Login-Automatisierung
- keine Erfassung ohne bewussten Klick
- keine automatische Erstellung oder Freigabe neuer Preisquellen
- keine Übermittlung an fremde Server

## API

```text
GET  /api/prices/browser-connector/health
GET  /api/prices/browser-connector/extension.zip
POST /api/prices/browser-connector/import
```

Protokollkennung:

```text
X-DGD-Connector: browser-extension-v1
```
