# DGD – Aktueller Projektstand

Stand: 31. Juli 2026

Diese Datei beschreibt den tatsächlich auf `main` vorhandenen Stand sowie das aktuell in Dev bearbeitete Paket.

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
- 16.7.5 Preisquellen im Admin prüfen, freigeben und für Scanner verwalten
- 16.7.6 Lokaler Chrome-/Edge-Browser-Connector für serverseitig blockierte Händler

## Preisquellen und Scanner

Importierte Preisquellen erhalten eine stabile `offer_source_id` und starten mit `PENDING_REVIEW`. Im Admin können sie geprüft, freigegeben oder abgelehnt werden. Die Scanner-Aktivierung ist eine zusätzliche bewusste Aktion und setzt eine freigegebene Quelle, einen aktiven Händler und einen unterstützten Adapter voraus.

Automatische sowie manuelle Sammelläufe berücksichtigen ausschließlich Quellen mit `review_status = APPROVED`, `scanner_active = true` und aktivem Händler. Entscheidungen, Tests und Scanneränderungen werden in `price_source_review_events` protokolliert.

Direkte HTTP-Aufrufe verwenden bei Bedarf einen serverseitigen Chromium-Fallback. Blockiert ein Händler auch diesen Weg, wird die Quelle auf `BROWSER_REQUIRED` gesetzt und vom Server-Scanner ausgeschlossen. Preis und Verfügbarkeit können anschließend bewusst über die lokale Chrome-/Edge-Erweiterung übernommen werden. Jeder Browserimport erzeugt eine Preisbeobachtung und ein Audit-Ereignis.

## Aktuell in Dev

### Paket 18.1 – Preisverlauf und Variantenvergleich im Duftprofil

- öffentliche Preise berücksichtigen nur freigegebene Quellen aktiver Händler
- Angebote werden nach Produktart, Größe und Konzentration gruppiert
- Flakons, Tester, Sets, Proben und Nachfüllungen werden nicht direkt miteinander verglichen
- günstigster Preis und historisches Tief gelten jeweils nur für dieselbe Variante
- Zeitraumumschaltung 30, 90 und 365 Tage
- responsive Verlaufsgrafik und Händlerliste im öffentlichen Duftprofil

Issue #101, Draft-PR #102, Branch `feature/price-variant-history`.

## Daten- und Sicherheitsprinzipien

- Produktion bleibt unberührt
- leere Zellen bedeuten keine Löschung
- persönliche Werte bleiben strikt von aggregierten Daten getrennt
- ungeprüfte KI-Werte werden nie automatisch veröffentlicht
- Konflikte müssen bewusst bestätigt werden
- Preisquellen aktivieren niemals automatisch einen Scanner
- öffentliche Preisangebote stammen nur aus freigegebenen Quellen aktiver Händler
- unterschiedliche Produktvarianten werden nicht als direkte Alternativen vermischt
- CAPTCHA-, Proxy- oder Bot-Schutz-Umgehungen sind ausgeschlossen

## Datenbankstand

Explizites DGD-Migrationsschema bis `0017`.

## Qualitätssicherung

Paket 16.7.6 wurde praktisch in Dev abgenommen. GitHub Actions `DGD CI` Lauf 286 war erfolgreich. Paket 18.1 wird vor dem Merge erneut praktisch in Dev geprüft.

## Nächster Schritt

Dev-Abnahme der gruppierten Variantenpreise und des Preisverlaufs. Danach folgen je nach Priorität Preisalarme beziehungsweise die weitere Datenvalidierung des Master-Imports.

Der Chat ist nicht das Projektgedächtnis. Maßgeblich sind Repository und Dokumentation.
