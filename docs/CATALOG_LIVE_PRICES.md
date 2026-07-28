# Live Händlerpreise im öffentlichen Katalog

Die öffentliche Duftdetailseite lädt zusätzlich zur Duft-API die Preisübersicht über
`GET /api/prices/fragrances/{fragrance_id}`.

Wenn verfügbare Händlerangebote vorhanden sind, ersetzt der günstigste Gesamtpreis den statischen Duftpreis in der Detailansicht. Angezeigt werden Händler, Größe, Versand, Preis pro 100 ml und ein externer Produktlink. Alle verfügbaren Angebote erscheinen zusätzlich als Liste.

Fehlen Händlerangebote, bleibt der bisherige manuell gepflegte Duftpreis beziehungsweise „Nicht hinterlegt“ sichtbar. Andere Fachdaten werden nicht automatisch erfunden oder überschrieben.
