# Quellenprofile & Prüfoberfläche 1.0

## Ziel

DGD soll Webtreffer nicht gleich behandeln. Die Herkunft entscheidet mit darüber, ob ein Fund nur ein Hinweis oder ein belastbarer Beleg ist.

## Quellenreihenfolge

1. **Offizielle Hersteller- oder Markenseite**
   - höchste Priorität
   - bevorzugte Quelle für Produktname, Erscheinungsjahr, Konzentration, Parfümeur und offizielle Duftnoten
   - immer die konkrete Produktseite statt einer allgemeinen Startseite speichern

2. **Parfumo**
   - gute Recherche- und Gegenprüfungsquelle
   - direkte Fundseite speichern
   - nur begrenzte Abrufe
   - Community-Aussagen, Bewertungen und Ähnlichkeitseinschätzungen bleiben subjektive Hinweise

3. **Basenotes**
   - ergänzende Community- und Archivquelle
   - möglichst gegen offizielle Quellen oder weitere unabhängige Belege prüfen

4. **Wikiparfum**
   - zusätzliche Referenz für Duftnoten und Zuordnungen
   - nicht allein für automatische Übernahmen verwenden

5. **Händlerseiten und allgemeine Webtreffer**
   - niedrigere Priorität
   - nützlich für Verfügbarkeit, Produktbilder und Hinweise
   - Marketingtexte und fremde Beschreibungen werden nicht ungeprüft übernommen

## Gesperrte automatische Quelle

Fragrantica wird als `BLOCKED_AUTOMATION` hinterlegt. Die aktuellen Nutzungsbedingungen untersagen Scraping und nicht autorisierte automatisierte Zugriffe. Treffer dieser Domain werden vom DGD-Recherchelauf übersprungen.

## Technische Umsetzung

Neue Tabelle:

- `research_source_profiles`

Felder:

- Domain
- Anzeigename
- Kategorie
- Priorität
- automatische Nutzung erlaubt
- gesperrt
- interne Notiz

Neue Endpunkte:

- `GET /api/enrichment/source-profiles`
- `POST /api/enrichment/source-profiles/install-defaults`

Der Twin-Recherchelauf:

- erkennt offizielle Marken-Domains über `brands.website_url`
- gewichtet bekannte Quellenprofile
- überspringt gesperrte Domains
- speichert Quellenkategorie und Quellenpriorität am Vorschlag

## Prüfoberfläche

Im Recherche-Admin werden nun angezeigt:

- installierte Quellenprofile
- offene Datenlücken pro Duft
- gefundene Duftzwillinge inklusive Quellenkategorie und Priorität
- zugeordnete DGD-Alternative, falls erkannt
- Übernehmen eines vollständig zugeordneten Twin-Vorschlags
- Ablehnen eines Hinweises

## Sicherheitsregel

Ein Duftzwilling kann nur übernommen werden, wenn beide Düfte bereits als eindeutige DGD-Datensätze vorhanden sind. Unbekannte Alternativen müssen zuerst importiert oder zugeordnet werden. Bestehende Twin-Paare werden nicht doppelt angelegt.

## Validierung

```bash
python -m compileall -q backend/app
cd frontend
npm install
npm run build
```

## Nächstes Paket

**Gefundene Felddaten & selektive Übernahme 1.0**

Dabei erhält jeder Datenlücken-Auftrag konkrete Fundwerte mit Altwert, neuem Wert, Quelle und Einzel-Freigabe. Automatisch dürfen weiterhin ausschließlich leere, eindeutig belegte Faktenfelder ergänzt werden.
