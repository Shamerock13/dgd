# Preisquellen-Prüfung

Paket 16.7.5 ergänzt die manuelle Prüfung importierter Preisquellen.

## Status

- `PENDING_REVIEW`: importiert, aber noch nicht freigegeben
- `APPROVED`: Produktseite und Variante wurden manuell geprüft
- `REJECTED`: Quelle wurde bewusst abgelehnt

## Sicherheitsregeln

- Eine Freigabe aktiviert niemals automatisch den Scanner.
- Neue Händler bleiben inaktiv, sofern sie nicht bei der Freigabe bewusst aktiviert werden.
- Ablehnen deaktiviert einen eventuell gesetzten Scannerstatus.
- Eine Quelle benötigt eine stabile `offer_source_id`.
- Produkt-URL und Händler-Domain müssen zusammenpassen.
- Jede Entscheidung wird in `price_source_review_events` protokolliert.
- Produktion bleibt während Entwicklung und Dev-Abnahme unberührt.

## API

```text
GET  /api/prices/review/offers
POST /api/prices/review/offers/{offer_id}/decision
```

Die spätere Scanner-Aktivierung bleibt eine eigene, getrennte Admin-Aktion.
