# Suchstrategie 2.0

Der kombinierte Recherchelauf verwendet mehrere Suchvarianten pro Duft statt nur einer stark eingeschränkten Anfrage.

## Reihenfolge

1. exakte Marken- und Duftsuche
2. lockere Suche ohne vollständige Anführungszeichen
3. gezielte Referenzsuche auf Parfumo, Basenotes und Wikiparfum
4. gezielte Suche auf der offiziellen Markendomain, sofern vorhanden

Der Lauf sammelt Treffer dedupliziert und beendet die Variantenfolge, sobald ausreichend Ergebnisse vorliegen.

## Diagnose

Die API meldet zusätzlich:

- ausgeführte Suchanfragen
- Suchtreffer insgesamt
- leere Suchantworten
- vermutete Bot-, Consent- oder Blockierungsseiten
- verwendete Suchvarianten
- nicht verwertbare Treffer

Ein Lauf mit ausschließlich leeren oder blockierten Suchantworten lässt sich damit von einem echten Nullergebnis unterscheiden.
