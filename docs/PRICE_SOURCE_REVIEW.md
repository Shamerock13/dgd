# Preisquellen-Prüfung

Paket 16.7.5 ergänzt die manuelle Prüfung importierter Preisquellen, eine getrennte Scanner-Freigabe und einen sicheren Einzeltest.

## Status

- `PENDING_REVIEW`: importiert, aber noch nicht freigegeben
- `APPROVED`: Produktseite und Variante wurden manuell geprüft
- `REJECTED`: Quelle wurde bewusst abgelehnt

## Sicherheitsregeln

- Eine Freigabe aktiviert niemals automatisch den Scanner.
- Neue Händler bleiben inaktiv, sofern sie nicht bewusst aktiviert werden.
- Ablehnen deaktiviert einen eventuell gesetzten Scannerstatus.
- Eine Quelle benötigt eine stabile `offer_source_id`.
- Produkt-URL und Händler-Domain müssen zusammenpassen.
- Scanner können nur für freigegebene Quellen, aktive Händler und unterstützte Händleradapter aktiviert werden.
- Automatische und manuelle Sammelläufe berücksichtigen ausschließlich `APPROVED` + `scanner_active = true`.
- Ein Einzeltest benötigt ebenfalls eine freigegebene Quelle, einen aktiven Händler und einen unterstützten Adapter.
- Freigaben, Ablehnungen, Scanneränderungen sowie erfolgreiche und fehlgeschlagene Einzeltests werden in `price_source_review_events` protokolliert.
- Die letzten zwölf Ereignisse werden direkt in der Admin-Karte angezeigt.
- Produktion bleibt während Entwicklung und Dev-Abnahme unberührt.

## Admin-Ablauf

1. Importierte Quelle unter `Preisquellen prüfen` öffnen.
2. Produktseite, Variante, Größe, Konzentration und Händler kontrollieren.
3. Quelle freigeben oder ablehnen.
4. Scanner bei Bedarf separat aktivieren.
5. Mit `Quelle jetzt testen` einen einzelnen Händlerabruf ausführen.
6. Ergebnis und Prüfverlauf in derselben Karte kontrollieren.

## API

```text
GET  /api/prices/review/offers
POST /api/prices/review/offers/{offer_id}/decision
POST /api/prices/review/offers/{offer_id}/scanner
POST /api/prices/review/offers/{offer_id}/test
```

Der Einzeltest speichert bei Erfolg eine normale Preisbeobachtung. Fehler werden protokolliert, verändern den Freigabe- oder Scannerstatus aber nicht automatisch.
