# Kontrollierte Duft-DNA-Recherchevorschläge

## Ziel

Recherche- und KI-Ergebnisse werden niemals direkt als veröffentlichte Duft-DNA gespeichert. Sie landen zuerst als getrennte Vorschläge in einer Prüfwarteschlange.

## Status

- `OPEN` – wartet auf Prüfung
- `APPROVED` – bewusst freigegeben
- `REJECTED` – abgelehnt, bleibt nachvollziehbar

## Daten

Ein Vorschlag enthält:

- Duft-ID
- partielle DNA-Werte
- Herkunft
- Quellenbezeichnung und optionale URL
- Begründung
- Vertrauensgrad
- Erstellungszeitpunkt
- Prüfentscheidung, Prüfzeitpunkt und Prüfnotiz

## Freigabeprinzip

Eine Freigabe übernimmt nur ausdrücklich bestätigte Dimensionen. Nicht bestätigte oder fehlende Dimensionen verändern die vorhandene aggregierte Duft-DNA nicht.

Eine Ablehnung verändert die aggregierte Duft-DNA überhaupt nicht.

## Sicherheit

- keine automatische Veröffentlichung
- persönliche DNA bleibt unberührt
- offene Vorschläge bleiben getrennt von sichtbaren Profilwerten
- KI ist nur Hilfsmittel zur Vorschlagserstellung, nicht Freigabeinstanz
- Produktion bleibt bis zur abgeschlossenen Dev-Abnahme unverändert
