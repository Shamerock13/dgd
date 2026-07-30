# DGD – Aktueller Projektstand

Stand: 30. Juli 2026

Diese Datei beschreibt den tatsächlich auf `main` vorhandenen Stand sowie unmittelbar vor dem Merge bestätigte Änderungen.

## Abgeschlossen

- Pakete 1 bis 14
- 16.1 Strukturiertes Performance-Datenmodell
- 16.2 Performance-Karte im Duftprofil
- 16.3 Zeitlicher Duftverlauf
- 16.4 Duft-DNA-Datenmodell, Anzeige, manuelle Pflege und kontrollierte Vorschläge
- 16.5.1 Admin-Übersicht
- 16.5.2 Gruppierte Admin-Navigation
- 16.5.3 Strukturierte Duftbearbeitung
- 16.6.1 KI-Recherche für strukturierte Performance-Daten
- 16.7.1 Vollständiger KI-Recherche-Export als XLSX
- 16.7.2 Geprüfte Rückimport-Vorschau ohne Datenbankänderung
- 16.7.3 Feldweise Freigabe und kontrollierte Übernahme
- 16.7.4 Preisquellen geprüft übernehmen

## Paket 16.7.4

In Dev praktisch bestätigt und über PR #96 für `main` freigegeben:

- Preisquellen werden gegen bestehende Angebote und stabile `offer_source_id` abgeglichen
- neue Quellen erhalten ihre Kennung ausschließlich durch DGD
- unbekannte, doppelte oder zu einem anderen Duft gehörende Kennungen werden abgewiesen
- direkte Produkt-URLs, Händler, Größe, Konzentration, Variante, Produkttyp, Währung und Markt werden geprüft
- deutsche Produkttypen wie „reguläre Ware“, „Probe“, „Geschenkset“ und „Nachfüllung“ werden auf interne Codes normalisiert
- neue Händler werden zunächst deaktiviert angelegt
- neue und geänderte Preisquellen starten mit `PENDING_REVIEW`
- `scanner_active` bleibt bei jeder Übernahme garantiert `false`
- Konflikte benötigen weiterhin eine ausdrückliche Bestätigung
- erfolgreiche Übernahmen werden einschließlich erzeugter `offer_source_id` protokolliert
- Fehler führen zum vollständigen Rollback

## KI-Export und Rückimport

Der Admin-Bereich `KI-Export` unterstützt Export, geprüfte Vorschau und kontrollierte Übernahme von Stammdaten, Performance, Duft-DNA, Bildquellen, Duftnoten und Preisquellen. Technische Kennungen bleiben stabil; persönliche Performance- und DNA-Werte sind ausgeschlossen.

## Daten- und Sicherheitsprinzipien

- Produktion bleibt unberührt
- leere Zellen bedeuten keine Löschung
- fehlende Werte bleiben unbekannt und werden nicht als `0` interpretiert
- persönliche Werte bleiben strikt von aggregierten Daten getrennt
- ungeprüfte KI-Werte werden nie automatisch veröffentlicht
- Konflikte müssen bewusst bestätigt werden
- Preisquellen aktivieren niemals automatisch einen Scanner
- neue Händler und Quellen bleiben bis zur manuellen Prüfung deaktiviert

## Datenbankstand

Explizites DGD-Migrationsschema bis `0016`.

## Qualitätssicherung

Dev-Abnahme erfolgreich. GitHub Actions `DGD CI` Lauf 218 für den final getesteten Branch-Stand erfolgreich.

## Nächster Schritt

Als nächstes folgt die manuelle Prüf- und Freigabeoberfläche für Preisquellen beziehungsweise die weitere Admin-Protokollansicht. Automatisierte Scannerläufe bleiben davon getrennt.

Der Chat ist nicht das Projektgedächtnis. Maßgeblich sind Repository und Dokumentation.
