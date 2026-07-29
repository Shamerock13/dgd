# Kontrollierte Duft-DNA-Vorschläge

## Ziel

Recherche-, Regel- und KI-Ergebnisse werden nicht direkt veröffentlicht. Sie werden als prüfbare Vorschläge gespeichert und erst nach einer bewussten Entscheidung in die aggregierte Duft-DNA übernommen.

## Datenmodell

Ein Vorschlag enthält:

- Duft-ID
- partielle DNA-Werte
- Herkunft `RESEARCH`, `AI_ASSISTED`, `RULE_BASED` oder `MANUAL`
- Quellenbezeichnung und optionale URL
- Begründung
- Vertrauen von `0` bis `1`
- Status `OPEN`, `APPROVED` oder `REJECTED`
- Erstellungs- und Prüfzeitpunkt
- optionale Prüfnotiz

## Freigaberegeln

- `OPEN` verändert keine veröffentlichten Werte.
- Eine Freigabe übernimmt nur ausdrücklich bestätigte Dimensionen.
- Bereits vorhandene, nicht bestätigte DNA-Dimensionen bleiben erhalten.
- Eine Ablehnung verändert die veröffentlichte DNA nicht.
- Persönliche DNA bleibt immer unberührt.
- Freigegebene Vorschläge setzen die aggregierte Herkunft auf `RESEARCH` und den Prüfstatus auf `REVIEW_REQUIRED`.

## API

```text
POST /api/fragrance-dna/proposals
GET  /api/fragrance-dna/proposals
POST /api/fragrance-dna/proposals/{proposal_id}/review
```

## Admin-Arbeitsliste

Das Admin-Center besitzt den Bereich **DNA-Vorschläge**. Er zeigt offene Vorschläge mit Duft, Quelle, Begründung, Vertrauen und vorgeschlagenen Dimensionen.

Vor der Freigabe kann jede Dimension einzeln abgewählt werden. Nur markierte Werte werden in die aggregierte Duft-DNA übernommen. Ablehnung und Freigabe können mit einer Prüfnotiz dokumentiert werden.

## Sicherheit

Es gibt keine automatische Veröffentlichung. KI- oder Rechercheergebnisse bleiben bis zur bewussten Freigabe vollständig getrennt von den sichtbaren Duft-DNA-Werten.

Produktion bleibt unangetastet. Abnahme erfolgt ausschließlich in der Dev-Umgebung.
