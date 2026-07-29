# DGD – Aktueller Projektstand

Stand: 29. Juli 2026

Diese Datei ist die kompakte, maßgebliche Übersicht über den tatsächlich auf `main` vorhandenen Funktionsstand. Änderungen in offenen Feature-Branches werden ausdrücklich als in Arbeit gekennzeichnet. Detailentscheidungen stehen zusätzlich in den jeweiligen Fachdateien unter `docs/`.

## Umgesetzte Pakete

1. Detailansicht & Duftzwillinge 2.0
2. Bildverwaltung & Bildquellen 1.0
3. Markenprofile 1.0
4. Quellen & Verifizierung 1.0
5. Parfümeurprofile 1.0
6. Datenqualität & redaktionelle Arbeitsliste 1.0
7. Lokaler Bildupload & Medienablage 1.0
8. Automatische Recherche & Import-Warteschlange 1.0
9. Recherchequellen & zeitgesteuerter Scanner 1.0
10. Quellenadapter & Mehrseiten-Scanner 1.0
11. Gemini-Recherche & Datenqualität 1.0
12. Gemini-Rechercheverlauf & Tokenkontrolle 1.0
13. Scanner-Betrieb & automatische Fälligkeit 1.0
14. Suche, Filter & Navigation 2.0
16.1 Strukturiertes Performance-Datenmodell
16.2 Performance-Karte im Duftprofil
16.3 Zeitlicher Duftverlauf
16.4.1 Duft-DNA-Datenmodell und API
16.4.2 Duft-DNA-Karte im Duftprofil

## Performance-Pakete 16.1 bis 16.3 abgeschlossen

Das strukturierte Performance-Modell, die öffentliche Performance-Karte und der zeitliche Duftverlauf für Opening, Herzphase und Drydown sind auf `main` vorhanden. Fehlende Werte bleiben sichtbar offen; zusätzliche Messpunkte werden nicht erfunden.

Migration `0012`, API-Ausgabe und Backendtests wurden in Dev bestätigt.

## Paket 16.4.1 abgeschlossen

Das Duft-DNA-Datenmodell wurde über PR #78 nach `main` übernommen. Enthalten sind 16 optionale Dimensionen von `0` bis `10`, getrennte aggregierte und persönliche Profile, Herkunft, Prüfstatus, Quellenanzahl, Vertrauen, Quellenabweichung und Recherchedatum. Migration `0013` sowie die Lese- und Speicherendpunkte wurden in Dev bestätigt. Testergebnis: `17 passed, 1 warning in 0.53s`.

## Paket 16.4.2 abgeschlossen

Die öffentliche Duft-DNA-Karte wurde über PR #79 nach `main` übernommen und in Dev visuell bestätigt. Sie zeigt vorhandene Dimensionen sortiert nach Stärke, eine prägende Signatur, Herkunft, Prüfstatus, Datenqualität und persönliche Werte in einem getrennten Bereich. Fehlende Dimensionen bleiben leer.

## Paket 16.4.3 in Arbeit

**Pflege und Recherche der Duft-DNA** liegt im Branch `feature/fragrance-dna-admin` und im Draft-PR #81.

Bereits umgesetzt:

- Admin-Editor für alle 16 DNA-Dimensionen
- Laden vorhandener aggregierter und persönlicher Werte
- getrennte Speicheraktionen für aggregierte und persönliche DNA
- Herkunft, Prüfstatus, Quellenanzahl, Vertrauen, Abweichung und Recherchedatum
- einzelne Werte können ausdrücklich geleert werden
- responsive Gestaltung
- Einbindung in die bestehende Duftbearbeitung des Admin-Centers

Noch offen:

- Frontend-Build in Dev
- partielles Profil speichern und erneut laden
- persönliche DNA getrennt speichern und erneut laden
- Prüfung, dass geleerte Werte nicht als `0` zurückkehren
- visuelle Abnahme und Merge
- kontrollierte Recherchevorschläge und Freigabeworkflow als nachgelagerter Baustein

## Paket 15 in Arbeit

**Datenvalidierung & Importqualität 2.0** besitzt Qualitätsvorschau, geschützten Commit, manuelle `REVIEW`-Entscheidungen und gespeicherte Importberichte. Offen bleibt die Absicherung des Master-Imports mit denselben Regeln.

## Paket 18 gestartet

**Preisbeobachtung & Händlervergleich 1.0** besitzt Händlerstammdaten, aktuelle Angebote, unveränderliche Preisbeobachtungen und einen Duft-Endpunkt für günstigsten Gesamtpreis, Preis pro 100 ml, historischen Bestpreis und Verlauf. Händleradapter und tägliche automatische Preisprüfungen folgen getrennt.

## Recherche- und Sicherheitsregeln

- nur öffentliche HTTP- und HTTPS-Ziele
- interne, private, reservierte und lokale Netzwerkziele bleiben blockiert
- keine automatische Veröffentlichung
- Dublettenprüfung vor Freigabe
- ähnliche Importkandidaten niemals automatisch zusammenführen
- Preise und Versand getrennt speichern und als Gesamtpreis vergleichen
- Duft-DNA nur aus strukturierten Werten darstellen
- fehlende DNA-Dimensionen niemals als `0` interpretieren
- ungeprüfte Recherche- oder KI-Vorschläge niemals automatisch veröffentlichen

## Datenbankstand

Das explizite DGD-Migrationsschema steht bei `0013`.

## Qualitätssicherung

Die GitHub-CI prüft:

```bash
python -m compileall -q backend/app
npm install
npm run build
```

Neue Pakete gelten erst nach erfolgreichem Test in der separaten Dev-Umgebung als praktisch abgenommen.

## Nächster Schritt

**Paket 16.4.3 im Dev-Frontend bauen und die manuelle DNA-Pflege mit partiellem, persönlichem und geleertem Profil prüfen.**

## Dokumentationsregel

Nach jedem größeren Paket werden mindestens `CURRENT_STATUS`, `PROJECT_CONTEXT`, `ROADMAP`, die Fachdatei und bei Workflowänderungen `DEV_WORKFLOW` geprüft.

Der Chat ist nicht das Projektgedächtnis. Maßgeblich sind Repository und Dokumentation.
