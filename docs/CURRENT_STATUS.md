# DGD – Aktueller Projektstand

Stand: 29. Juli 2026

Diese Datei beschreibt den tatsächlich auf `main` vorhandenen Stand sowie noch offene Feature-Branches.

## Abgeschlossen

- Pakete 1 bis 14
- 16.1 Strukturiertes Performance-Datenmodell
- 16.2 Performance-Karte im Duftprofil
- 16.3 Zeitlicher Duftverlauf
- 16.4.1 Duft-DNA-Datenmodell und API
- 16.4.2 Duft-DNA-Karte im Duftprofil

## Paket 16.4.3 – manuelle Duft-DNA-Pflege

Branch: `feature/fragrance-dna-admin` · PR #81

Umgesetzt und in Dev bestätigt:

- Admin-Editor für alle 16 DNA-Dimensionen
- Laden vorhandener aggregierter und persönlicher Werte
- getrennte Speicheraktionen für aggregierte und persönliche DNA
- Herkunft, Prüfstatus, Quellenanzahl, Vertrauen, Abweichung und Recherchedatum
- partielle Profile bleiben partiell
- einzelne Werte können bewusst geleert werden und kommen nicht als `0` zurück
- erneutes Laden gespeicherter aggregierter und persönlicher Werte erfolgreich
- responsive Einbindung in die bestehende Duftbearbeitung
- DNA-Routen werden vor dem SPA-Fallback registriert

Die Dev-Abnahme durch den Nutzer war erfolgreich. Offen ist nur noch der Merge von PR #81. Kontrollierte Recherchevorschläge und ein Freigabeworkflow folgen als eigener Baustein.

## Weitere Arbeitsstränge

- Paket 15: Master-Import noch mit denselben Qualitätsregeln absichern
- Paket 18: Händleradapter, tägliche Preisprüfung, Preisbox und Verlauf folgen

## Daten- und Sicherheitsprinzipien

- Produktion bleibt unberührt
- fehlende DNA-Dimensionen sind unbekannt, nicht `0`
- persönliche DNA bleibt von aggregierten Werten getrennt
- ungeprüfte Recherche- oder KI-Vorschläge werden nie automatisch veröffentlicht
- ähnliche Importkandidaten werden niemals automatisch zusammengeführt

## Datenbankstand

Explizites DGD-Migrationsschema: `0013`.

## Qualitätssicherung

GitHub-CI prüft Backend-Compile und Frontend-Build. Backendtests für 16.4.1: `17 passed, 1 warning in 0.53s`.

## Nächster Schritt

PR #81 zusammenführen. Danach Paket 16.4.4 für kontrollierte DNA-Recherchevorschläge und Freigabe starten.

Der Chat ist nicht das Projektgedächtnis. Maßgeblich sind Repository und Dokumentation.
