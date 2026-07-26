# Such-Fallback und Diagnose

Der kombinierte Lauf verwendet jetzt mehrere Parservarianten für die öffentlichen DuckDuckGo-HTML- und Lite-Ausgaben.

Wenn die normale HTML-Ausgabe keine verwertbaren Treffer enthält, wird automatisch die Lite-Ausgabe versucht. Der Lauf meldet zusätzlich:

- gelesene Suchtreffer
- Suchen ohne Treffer
- Treffer ohne verwertbare Feldaussage
- verwendete Fallback-Abrufe
- technische Fehler

Die Feldfund-Zahl im Frontend verwendet den Backend-Wert `findings_created`. Dadurch werden tatsächlich angelegte Ergänzungen korrekt angezeigt.

Die bestehenden Schutzregeln bleiben erhalten: keine automatische Übernahme, keine Vollseitenabrufe gesperrter Quellen und keine Überschreibung bestehender Werte.
