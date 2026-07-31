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
- 18.1 Preisverlauf und Variantenvergleich im öffentlichen Duftprofil
- 18.2 Variantengenaue lokale Preisalarme und Schwellenwerte

## Preisquellen, Scanner, Verlauf und Alarme

Importierte Preisquellen erhalten eine stabile `offer_source_id` und starten mit `PENDING_REVIEW`. Im Admin können sie geprüft, freigegeben oder abgelehnt werden. Die Scanner-Aktivierung ist eine zusätzliche bewusste Aktion und setzt eine freigegebene Quelle, einen aktiven Händler und einen unterstützten Adapter voraus.

Automatische sowie manuelle Sammelläufe berücksichtigen ausschließlich Quellen mit `review_status = APPROVED`, `scanner_active = true` und aktivem Händler. Entscheidungen, Tests und Scanneränderungen werden in `price_source_review_events` protokolliert.

Direkte HTTP-Aufrufe verwenden bei Bedarf einen serverseitigen Chromium-Fallback. Blockiert ein Händler auch diesen Weg, wird die Quelle auf `BROWSER_REQUIRED` gesetzt und vom Server-Scanner ausgeschlossen. Preis und Verfügbarkeit können anschließend bewusst über die lokale Chrome-/Edge-Erweiterung übernommen werden. Jeder Browserimport erzeugt eine Preisbeobachtung und ein Audit-Ereignis.

Der öffentliche Preisvergleich gruppiert Angebote nach Produktart, Größe und Konzentration. Flakons, Tester, Sets, Proben und Nachfüllungen sowie abweichende Größen werden nicht als direkte Alternativen vermischt. Bestpreis, Allzeittief und Verlauf gelten immer nur für dieselbe Variante.

Variantengenaue Preisalarme unterstützen einen Zielpreis inklusive Versand oder einen maximalen Abstand zum historischen Tief. Jede neue Preisbeobachtung bewertet betroffene Alarme innerhalb derselben Transaktion neu. Eine erneute Auslösung erfolgt erst nach einem zwischenzeitlichen Rücksetzen.

## Aktuell in Dev

### Paket 18.3 – Prüfrunde für Browser-Preisquellen

- Queue ausschließlich für freigegebene `BROWSER_REQUIRED`-Quellen aktiver Händler
- Status `NEVER_CHECKED`, `DUE` oder `CURRENT`
- Fälligkeit nach `scan_interval`, unbekannte Werte sicher mit 24 Stunden behandeln
- nie geprüfte Quellen zuerst, danach älteste manuelle Prüfung
- Admin zeigt fällige, noch nie geprüfte und aktuelle Quellen
- bewusster Start der Prüfrunde im Admin
- Erweiterung bietet nach erfolgreichem Import die nächste fällige Quelle an
- jede weitere Produktseite öffnet sich ausschließlich nach einem Klick
- bestehender Einzelimport bleibt unverändert
- keine automatische Navigation, kein Hintergrund-Crawling und keine Schutzseiten-Umgehung

Issue #105, Draft-PR #106, Branch `feature/browser-price-review-queue`.

## Daten- und Sicherheitsprinzipien

- Produktion bleibt unberührt
- leere Zellen bedeuten keine Löschung
- persönliche Werte bleiben strikt von aggregierten Daten getrennt
- ungeprüfte KI-Werte werden nie automatisch veröffentlicht
- Konflikte müssen bewusst bestätigt werden
- Preisquellen aktivieren niemals automatisch einen Scanner
- öffentliche Preisangebote stammen nur aus freigegebenen Quellen aktiver Händler
- unterschiedliche Produktvarianten werden nicht als direkte Alternativen vermischt
- Preisalarme werten nur lieferbare, freigegebene Angebote aktiver Händler aus
- Browser-Prüfrunden öffnen und übertragen jede Seite nur nach einer bewussten Nutzeraktion
- CAPTCHA-, Proxy- oder Bot-Schutz-Umgehungen sind ausgeschlossen

## Datenbankstand

Explizites DGD-Migrationsschema bis `0018`. Paket 18.3 benötigt keine neue Migration.

## Qualitätssicherung

Paket 18.2 wurde praktisch in Dev abgenommen, mit CI-Lauf 309 geprüft und über PR #104 gemerged. Paket 18.3 wird vor dem Merge erneut praktisch in Dev geprüft. GitHub Actions validieren Backend-Compile, Erweiterungsskripte und Frontend-Build.

## Nächster Schritt

Dev-Abnahme der Browser-Prüfrunde: Start im Admin, erfolgreiche Übernahme, bewusster Wechsel zur nächsten Quelle und sauberer Abschlusszustand.

Der Chat ist nicht das Projektgedächtnis. Maßgeblich sind Repository und Dokumentation.
