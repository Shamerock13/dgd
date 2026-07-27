# DGD – Aktueller Projektstand

Stand: 27. Juli 2026

Diese Datei ist die kompakte, maßgebliche Übersicht über den tatsächlich auf `main` vorhandenen Funktionsstand. Detailentscheidungen stehen zusätzlich in den jeweiligen Fachdateien unter `docs/`.

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

## Paket 15 in Arbeit

**Datenvalidierung & Importqualität 2.0** besitzt folgende Prüf- und Sicherheitsendpunkte:

```text
POST /api/import/quality/preview
POST /api/import/quality/commit
```

Die Qualitätslogik:

- normalisiert Marken- und Duftidentitäten konservativ,
- erkennt exakte und sicher normalisierte Dubletten,
- meldet ähnliche Schreibweisen ausschließlich als manuellen Prüfhinweis,
- blockiert unvollständige oder widersprüchliche Zeilen,
- liefert pro Zeile Entscheidung, Begründung, Fehler und Kandidaten,
- führt niemals allein aufgrund eines ähnlichen Namens Datensätze zusammen.

Backend-Prüfpfad und Admin-Anzeige wurden praktisch in Dev bestätigt. Im Admin-Bereich **Datenimport** zeigt **Qualität & Dubletten prüfen** die Entscheidungen `CREATE`, `DUPLICATE`, `REVIEW` und `BLOCK` samt Kandidaten und Fehlern.

Der nächste Baustein schützt den Schreibvorgang: Das Admin-Center verwendet `/api/import/quality/commit`, prüft die Datei unmittelbar vor dem Schreiben erneut und stoppt den gesamten Import bei `REVIEW` oder `BLOCK`. Sichere Dubletten folgen weiterhin dem Modus `skip` oder `update`. Die praktische Dev-Abnahme dieses Commit-Schutzes steht noch aus.

## Paket 14 abgeschlossen

Der öffentliche Katalog ist serverseitig paginiert und unterstützt gewichtete Suche, Filter, Sortierung sowie dauerhaft verlinkbare Zustände für Suchergebnisse, Duftdetails, Markenprofile und Parfümeurprofile. Die Admin-Listen für Düfte und Marken besitzen Suche und Pagination. Alle Bestandteile wurden praktisch in Dev bestätigt.

## Scanner-Betrieb

Die Dev-Umgebung besitzt den getrennten Container `DGD-Dev-Scanner`. Der Worker verarbeitet ausschließlich aktive und fällige Recherchequellen, verhindert parallele Doppelläufe und veröffentlicht keine Treffer automatisch.

## Recherche- und Sicherheitsregeln

- nur öffentliche HTTP- und HTTPS-Ziele
- interne, private, reservierte und lokale Netzwerkziele bleiben blockiert
- keine automatische Veröffentlichung
- Dublettenprüfung vor Freigabe
- Gemini-Twins nur mit konkreter Grounding-Quelle
- bekannte Feldwerte und Twin-Kandidaten werden ausgeschlossen
- Duftnoten und Akkorde werden zentral normalisiert

## Datenbankstand

Das explizite DGD-Migrationsschema bleibt bei `0011`. Für die bisherigen Bausteine von Paket 15 ist keine Datenbankänderung erforderlich.

## Qualitätssicherung

Die GitHub-CI prüft:

```bash
python -m compileall -q backend/app
npm install
npm run build
```

Neue Pakete gelten erst nach erfolgreichem Test in der separaten Dev-Umgebung als praktisch abgenommen.

## Nächster Schritt

**Den abgesicherten Import-Commit in Dev mit einer konfliktfreien und einer gesperrten Datei testen.**

## Dokumentationsregel

Nach jedem größeren Paket werden mindestens `CURRENT_STATUS`, `PROJECT_CONTEXT`, `ROADMAP`, die Fachdatei und bei Workflowänderungen `DEV_WORKFLOW` geprüft.

Der Chat ist nicht das Projektgedächtnis. Maßgeblich sind Repository und Dokumentation.
