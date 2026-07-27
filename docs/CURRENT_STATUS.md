# DGD – Aktueller Projektstand

Stand: 27. Juli 2026

Diese Datei ist die kompakte, maßgebliche Übersicht über den tatsächlich auf `main` vorhandenen Funktionsstand. Detailentscheidungen bleiben zusätzlich in den jeweiligen Fachdateien unter `docs/` dokumentiert.

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

## Aktueller Recherche-Stand

DGD kann einzelne öffentliche Produktseiten sowie verwaltete Recherchequellen prüfen. Quellen können als `SINGLE` oder `LIST` betrieben werden.

Der Adapter `SINGLE` liest genau die hinterlegte Seite. Der Adapter `LIST` liest eine Listen-, Kategorie-, Marken- oder Suchseite, sammelt passende Produktlinks und arbeitet sie nacheinander ab.

Zusätzlich steht Gemini mit Google Search als kontrollierter Rechercheanbieter zur Verfügung:

- gezielte Recherche eines einzelnen Dufts mit offenen Feldern,
- Markenrecherche nach weiteren, noch nicht vorhandenen Düften,
- gemeinsamer deutscher Datenstandard mit festen Feld- und Zeichenlimits,
- Ausschluss bereits vorhandener, offener, übernommener, abgelehnter oder konfliktbehafteter Feldwerte,
- Ausschluss bereits bekannter oder geprüfter Duftzwillinge,
- strikte Grounding-Pflicht für neue Gemini-Twin-Vorschläge,
- serverseitige Normalisierung von Duftnoten und Akkorden,
- sichtbarer Prüflauf vor der historischen Datenbereinigung.

Sicherheits- und Lastgrenzen:

- nur öffentliche HTTP- und HTTPS-Ziele
- interne, private, reservierte und lokale Netzwerkziele bleiben blockiert
- optional nur Links derselben Domain
- regulärer Ausdruck als Linkfilter
- maximal 1 bis 100 Produktseiten pro Lauf
- keine automatische Veröffentlichung
- jeder Fund landet zunächst in der Import- oder Prüf-Warteschlange
- Dublettenprüfung bleibt vor der Freigabe aktiv
- Duftzwillinge ohne konkrete Grounding-Quelle werden nicht gespeichert
- temporäre Gemini-Fehler `429`, `502`, `503` und `504` werden begrenzt wiederholt

Scanläufe speichern zusätzlich die Anzahl gefundener Links und tatsächlich geprüfter Produktseiten. Fehler einzelner Unterseiten brechen einen gesamten Listenlauf nicht sofort ab.

Technische Detaildokumentation:

- `docs/RESEARCH_AUTOMATION.md`
- `docs/SOURCE_ADAPTERS.md`
- `docs/GEMINI_RESEARCH_AND_DATA_QUALITY.md`

## Datenbankstand

Das explizite DGD-Migrationsschema bleibt bei `0011`. Die Tabellen der verwalteten Recherchequellen und Scanläufe werden idempotent über die registrierten SQLAlchemy-Modelle angelegt. Bestehende Recherchetabellen werden beim Start um die Adapterfelder ergänzt.

Die neueren Gemini-, Deduplizierungs-, Grounding- und Bereinigungsfunktionen verwenden die vorhandenen Recherche-, Prüf- und Twin-Tabellen. Die Twin-Vorschlagsstruktur unterstützt zusätzlich getrennte Angaben für Marke und Duftname sowie eine ausführlichere Vergleichsbegründung.

## Qualitätssicherung

Die zentrale GitHub-CI unter `.github/workflows/ci.yml` prüft bei Pull Requests und Änderungen auf `main`:

```bash
python -m compileall -q backend/app
npm install
npm run build
```

## Nächstes größeres Paket

**Scanner-Betrieb & automatische Fälligkeit 1.0**

Geplante Schwerpunkte:

- eigener Scanner-Dienst beziehungsweise Worker im Dev-Compose
- regelmäßiger Aufruf nur fälliger aktiver Quellen
- Sperre gegen parallele Doppelläufe
- Laufzeit-, Fehler- und Erfolgskennzahlen
- klarer Ein-/Ausschalter für automatische Scans
- keine automatische Freigabe von Warteschlangen-Treffern
- dokumentierte Betriebs-, Neustart- und Backup-Regeln

## Dokumentationsregel

Nach jedem größeren Paket werden mindestens geprüft:

- `docs/CURRENT_STATUS.md`
- `docs/PROJECT_CONTEXT.md`
- `docs/ROADMAP.md`
- die jeweilige technische Fachdatei
- `docs/DEV_WORKFLOW.md`, falls sich Arbeitsweise oder Tests ändern

Der Chat ist nicht das Projektgedächtnis. Maßgeblich sind Repository und Dokumentation.
