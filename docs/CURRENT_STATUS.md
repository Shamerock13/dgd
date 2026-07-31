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

## Preisquellen, Scanner und Verlauf

Importierte Preisquellen erhalten eine stabile `offer_source_id` und starten mit `PENDING_REVIEW`. Im Admin können sie geprüft, freigegeben oder abgelehnt werden. Die Scanner-Aktivierung ist eine zusätzliche bewusste Aktion und setzt eine freigegebene Quelle, einen aktiven Händler und einen unterstützten Adapter voraus.

Automatische sowie manuelle Sammelläufe berücksichtigen ausschließlich Quellen mit `review_status = APPROVED`, `scanner_active = true` und aktivem Händler. Entscheidungen, Tests und Scanneränderungen werden in `price_source_review_events` protokolliert.

Direkte HTTP-Aufrufe verwenden bei Bedarf einen serverseitigen Chromium-Fallback. Blockiert ein Händler auch diesen Weg, wird die Quelle auf `BROWSER_REQUIRED` gesetzt und vom Server-Scanner ausgeschlossen. Preis und Verfügbarkeit können anschließend bewusst über die lokale Chrome-/Edge-Erweiterung übernommen werden. Jeder Browserimport erzeugt eine Preisbeobachtung und ein Audit-Ereignis.

Der öffentliche Preisvergleich gruppiert Angebote nach Produktart, Größe und Konzentration. Flakons, Tester, Sets, Proben und Nachfüllungen sowie abweichende Größen werden nicht als direkte Alternativen vermischt. Bestpreis, Allzeittief und Verlauf gelten immer nur für dieselbe Variante.

## Aktuell in Dev

### Paket 18.2 – Preisalarme und Schwellenwerte

- lokaler Alarm je vollständiger Preisvariante
- Zielpreis inklusive Versand oder maximaler Abstand zum historischen Tief
- Status `WAITING`, `TRIGGERED`, `NO_ELIGIBLE_OFFER`, `VARIANT_MISSING` oder `INACTIVE`
- erneute Auslösung erst nach zwischenzeitlichem Rücksetzen
- automatische Neubewertung bei jeder neuen Preisbeobachtung
- manuelle Prüfung, Server-Scanner und Browser-Connector nutzen denselben Auswertungsweg
- Bearbeitung direkt im Preisbereich des Duftprofils
- keine E-Mail- oder Push-Benachrichtigung in diesem Paket

Issue #103, Draft-PR #104, Branch `feature/price-alerts`.

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
- CAPTCHA-, Proxy- oder Bot-Schutz-Umgehungen sind ausgeschlossen

## Datenbankstand

Explizites DGD-Migrationsschema bis `0018`.

## Qualitätssicherung

Paket 18.1 wurde praktisch in Dev abgenommen und über PR #102 gemerged. Paket 18.2 wird vor dem Merge erneut praktisch in Dev geprüft. GitHub Actions prüfen Backend-Compile und Frontend-Build.

## Nächster Schritt

Dev-Abnahme für Anlegen, Auslösen, Deaktivieren und Löschen eines variantengenauen Preisalarms. Danach folgt entweder 18.3 Komfort für Browser-Quellen oder die weitere Datenvalidierung des Master-Imports.

Der Chat ist nicht das Projektgedächtnis. Maßgeblich sind Repository und Dokumentation.
