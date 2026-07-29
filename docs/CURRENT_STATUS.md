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
16.4.1 Duft-DNA-Datenmodell

## Performance-Pakete 16.1 bis 16.3 abgeschlossen

Das strukturierte Performance-Modell, die öffentliche Performance-Karte und der zeitliche Duftverlauf für Opening, Herzphase und Drydown sind auf `main` vorhanden. Fehlende Werte bleiben sichtbar offen; zusätzliche Messpunkte werden nicht erfunden.

Migration `0012`, API-Ausgabe und Backendtests wurden in Dev bestätigt.

## Paket 16.4.1 abgeschlossen

Das Duft-DNA-Datenmodell wurde über PR #78 nach `main` übernommen. Enthalten sind:

- 16 optionale Dimensionen von `0` bis `10`
- aggregierte und persönliche DNA strikt getrennt
- Herkunft, Prüfstatus, Quellenanzahl, Vertrauen, Quellenabweichung und Recherchedatum
- Migration `0013`
- Endpunkte zum Lesen und Speichern der DNA
- keine automatische Übernahme aus Legacy-Feldern, Akkorden oder Duftnoten

Die Dev-Abnahme bestätigte Backendstart, Migration `0013`, sichtbare Endpunkte und `17 passed, 1 warning in 0.53s`.

## Paket 16.4.2 in Arbeit

**Duft-DNA-Karte** liegt im Branch `feature/fragrance-dna-card`.

Die öffentliche Duftdetailansicht erhält:

- responsive Balken für vorhandene DNA-Dimensionen
- Sortierung nach Stärke
- eine Signatur aus den drei stärksten vorhandenen Dimensionen
- Herkunft, Prüfstatus und Datenqualität
- persönliche DNA in einem getrennten Bereich
- klare Leerzustände ohne erfundene Werte

Frontend-Build und visuelle Dev-Abnahme stehen noch aus.

## Paket 15 in Arbeit

**Datenvalidierung & Importqualität 2.0** besitzt Qualitätsvorschau, geschützten Commit, manuelle `REVIEW`-Entscheidungen und gespeicherte Importberichte. Offen bleibt die Absicherung des Master-Imports mit denselben Regeln.

## Paket 18 gestartet

**Preisbeobachtung & Händlervergleich 1.0** besitzt Händlerstammdaten, aktuelle Angebote, unveränderliche Preisbeobachtungen und einen Duft-Endpunkt für günstigsten Gesamtpreis, Preis pro 100 ml, historischen Bestpreis und Verlauf. Händleradapter und tägliche automatische Preisprüfungen folgen getrennt.

## Scanner-Betrieb

Die Dev-Umgebung besitzt den getrennten Container `DGD-Dev-Scanner`. Der Worker verarbeitet ausschließlich aktive und fällige Recherchequellen, verhindert parallele Doppelläufe und veröffentlicht keine Treffer automatisch.

## Recherche- und Sicherheitsregeln

- nur öffentliche HTTP- und HTTPS-Ziele
- interne, private, reservierte und lokale Netzwerkziele bleiben blockiert
- keine automatische Veröffentlichung
- Dublettenprüfung vor Freigabe
- ähnliche Importkandidaten niemals automatisch zusammenführen
- Preise und Versand getrennt speichern und als Gesamtpreis vergleichen
- ausverkaufte Angebote nicht als günstigsten Preis anzeigen
- Duftnoten und Akkorde zentral normalisieren
- Duft-DNA nur aus strukturierten Werten darstellen
- fehlende DNA-Dimensionen niemals als `0` interpretieren

## Datenbankstand

Das explizite DGD-Migrationsschema steht bei `0013`.

## Qualitätssicherung

Die GitHub-CI prüft:

```bash
python -m compileall -q backend/app
npm install
npm run build
```

Backendtests in Dev:

```bash
docker cp backend/tests DGD-Dev-Backend:/app/tests
docker exec -it DGD-Dev-Backend python -m pytest -q /app/tests
```

Neue Pakete gelten erst nach erfolgreichem Test in der separaten Dev-Umgebung als praktisch abgenommen.

## Nächster Schritt

**Paket 16.4.2 im Dev-Frontend bauen und die Duft-DNA-Karte mit leerem, partiellem und persönlichem Profil prüfen. Danach PR zusammenführen.**

## Dokumentationsregel

Nach jedem größeren Paket werden mindestens `CURRENT_STATUS`, `PROJECT_CONTEXT`, `ROADMAP`, die Fachdatei und bei Workflowänderungen `DEV_WORKFLOW` geprüft.

Der Chat ist nicht das Projektgedächtnis. Maßgeblich sind Repository und Dokumentation.
