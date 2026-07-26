# Hotfix: Auswahl in Quellen & Prüfung

## Problem
Beim Wechsel der Zuordnung oder bei der Auswahl eines Objekts konnte die Adminansicht abbrechen, wenn ein Duft, eine Marke oder ein Duftzwilling nicht die erwartete vollständig verschachtelte Frontend-Struktur hatte.

## Korrektur
- Eingangslisten werden defensiv als Arrays behandelt.
- Zielbezeichnungen verwenden sichere Fallbacks für Marke, Original und Alternative.
- Einträge ohne ID werden nicht als auswählbare Ziele angeboten.
- Nicht-speichernde Schaltflächen erhalten `type="button"`.
- Fehlerhafte oder ältere Datensätze können die gesamte Auswahl nicht mehr blockieren.

## Test
- Backend-Compile über CI
- Frontend-Build über CI
- Zuordnung Duft, Marke, Duftzwilling und Allgemein wechseln
- Objekt auswählen
- Quellenfilter wechseln
