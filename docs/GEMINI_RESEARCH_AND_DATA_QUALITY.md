# DGD – Gemini-Recherche und Datenqualität

Stand: 27. Juli 2026

Diese Datei beschreibt den aktuellen Recherche- und Prüfworkflow für Gemini-gestützte Ergänzungen, Duftzwillinge, Markenrecherche und die nachträgliche Bereinigung bestehender Daten.

## Grundprinzip

Gemini schreibt keine recherchierten Daten direkt ungeprüft in veröffentlichte Datensätze. Neue Informationen landen zunächst in den vorhandenen Prüf- und Import-Warteschlangen. Ausnahmen sind ausdrücklich bestätigte Aktionen wie das Übernehmen eines Feldwerts oder eines Duftzwillings.

## Gezielte Recherche für einen Duft

Unter **Quellen & Prüfung → Fehlende Duftdaten** kann für jeden offenen Datenauftrag **Mit Gemini ergänzen** gestartet werden.

Der Lauf:

- recherchiert nur den ausgewählten Duft,
- fordert nur aktuell offene Felder an,
- nutzt das gemeinsame DGD-Datenformat,
- speichert gefundene Feldwerte in der Prüf-Warteschlange,
- speichert belegte Duftzwilling-Hinweise in der Twin-Prüfung,
- meldet Tokenverbrauch, Quellenzahl und ausgeschlossene bekannte Werte zurück.

Endpoint:

```text
POST /api/enrichment/tasks/{fragrance_id}/research
```

## Recherche-Verlauf und Tokenkontrolle

Jeder gezielte Gemini-Lauf wird in `gemini_research_runs` protokolliert. Gespeichert werden:

- Duft und angeforderte Felder,
- Zeitpunkt und Status,
- verwendetes Modell,
- Anzahl gefundener Quellen,
- neu angelegte Feldfunde und Twin-Hinweise,
- Prompt-, Ausgabe- und Gesamttokens,
- eine gekürzte Fehlermeldung bei fehlgeschlagenen Läufen.

Die Oberfläche zeigt den letzten Lauf direkt am offenen Duftauftrag. Erfolgreiche Läufe erhalten eine Schutzzeit von 15 Minuten. Innerhalb dieser Zeit ist ein erneuter Start nur über **Trotzdem erneut suchen** und eine zusätzliche Bestätigung möglich.

Endpoints:

```text
GET  /api/enrichment/research-history?limit=500
GET  /api/enrichment/tasks/{fragrance_id}/research-history?limit=10
POST /api/enrichment/tasks/{fragrance_id}/research?force=false
POST /api/enrichment/tasks/{fragrance_id}/research?force=true
```

Die Schutzzeit verhindert versehentliche Doppelstarts, blockiert aber keine bewusst erzwungene erneute Prüfung.

## Markenrecherche

Unter **Quellen & Prüfung → Weitere Düfte einer Marke suchen** kann eine einzelne Marke ausgewählt werden.

Vor der Anfrage werden Gemini alle bereits vorhandenen und bereits vorgeschlagenen Duftnamen dieser Marke mitgegeben. Neue Kandidaten landen in der bestehenden Recherche-/Import-Warteschlange und werden nicht automatisch veröffentlicht.

Endpoint:

```text
POST /api/enrichment/brands/{brand_id}/research-fragrances?limit=15
```

## Gemeinsamer Datenstandard

Die Ausgabe wird sowohl im Prompt als auch serverseitig begrenzt und normalisiert.

- Markenname: maximal 160 Zeichen
- Duftname: maximal 200 Zeichen
- Konzentration: maximal 80 Zeichen
- Parfümeur: maximal 160 Zeichen
- Duftbeschreibung: maximal 350 Zeichen
- Akkorde: maximal 8 Begriffe
- Kopf-, Herz- und Basisnoten: jeweils maximal 10 Begriffe
- Vergleichsbegründung: maximal 240 Zeichen
- Quellenbeleg: maximal 500 Zeichen
- URLs: maximal 2000 Zeichen

Unbekannte Werte bleiben leer oder `null`; sie sollen nicht erfunden werden.

## Schutz vor Wiederholungen

### Duftzwillinge

Vor jeder Gemini-Anfrage werden bekannte Twin-Kandidaten gesammelt:

- vorhandene Twin-Verknüpfungen,
- offene Vorschläge,
- übernommene Vorschläge,
- abgelehnte Vorschläge,
- als Dublette markierte Vorschläge.

Diese Namen werden im Prompt ausdrücklich ausgeschlossen. Zusätzlich verhindert ein Fingerprint identische neue Vorschläge.

### Ergänzungswerte

Für jedes offene Feld werden bereits bekannte Werte berücksichtigt:

- `PENDING`
- `APPROVED`
- `REJECTED`
- `CONFLICT`

Diese Werte werden Gemini als Ausschlussliste mitgegeben. Identische Antworten werden außerdem serverseitig abgefangen, bevor sie erneut in der Prüfliste erscheinen.

## Grounding-Pflicht für Duftzwillinge

Ein Gemini-Twin darf nur gespeichert werden, wenn die Antwort mindestens eine brauchbare HTTP-/HTTPS-Grounding-Quelle enthält.

Nicht ausreichend sind:

- fehlende Grounding-Daten,
- eine generische Google-Suchadresse,
- ungültige oder nicht öffentliche URLs.

Unbelegte Twin-Kandidaten werden nicht in die Prüfliste übernommen. Sie werden lediglich als `twins_blocked_ungrounded` gezählt.

Normale Feldvorschläge können weiterhin in die Prüfung gelangen, auch wenn keine Twin-Quelle vorhanden ist.

## Datenbereinigung für Duftnoten und Akkorde

Unter **Quellen & Prüfung → Duftnoten und Akkorde bereinigen** steht ein zweistufiger Workflow zur Verfügung.

1. **Prüflauf starten**
   - verändert keine Daten,
   - zeigt geprüfte und betroffene Datensätze,
   - liefert Beispieländerungen mit Vorher-/Nachher-Werten.
2. **Bereinigung anwenden**
   - erfordert eine Bestätigung,
   - schreibt die bereinigten Werte,
   - führt notwendige Zusammenführungen doppelter Duftnoten aus.

Endpoint:

```text
POST /api/enrichment/cleanup-existing-values?dry_run=true
POST /api/enrichment/cleanup-existing-values?dry_run=false
```

Bereinigt werden unter anderem:

- runde, eckige und geschweifte Klammern,
- einfache und doppelte Anführungszeichen,
- JSON-artige Listen,
- Präfixe wie `Kopfnoten:`, `Herznoten:`, `Basisnoten:` und `Akkorde:`,
- Trennzeichen wie Komma, Semikolon, senkrechter Strich und Zeilenumbruch,
- doppelte Begriffe,
- führendes `und` beziehungsweise `and`.

Dieselbe Normalisierung gilt für neue Gemini-Ergebnisse und für die historische Bereinigung.

## Fehlerbehandlung

Gemini-Aufrufe wiederholen vorübergehende Fehler bis zu dreimal. Als vorübergehend gelten insbesondere HTTP-Status:

```text
429, 502, 503, 504
```

Die Backend-Läufe verwenden begrenzte Zeitüberschreitungen und rollen Datenbankänderungen bei Fehlern zurück.

## Wichtige Backend-Dateien

```text
backend/app/gemini_research.py
backend/app/smart_gemini_runner.py
backend/app/targeted_research_routes.py
backend/app/brand_research_routes.py
backend/app/grounding_policy.py
backend/app/finding_dedupe.py
backend/app/data_standards.py
backend/app/combined_research_routes.py
backend/app/research_run_history.py
```

## Wichtige Frontend-Datei

```text
frontend/src/verification.jsx
```

## Betriebsregel

Alle Änderungen werden zuerst in der separaten Dev-Umgebung getestet. Produktionscontainer und produktive Datenbank werden für Entwicklung und Tests nicht direkt verändert.
