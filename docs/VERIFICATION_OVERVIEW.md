# Quellen & Prüfung – zentrale Übersicht

## Ziel

Der Bereich **Quellen & Prüfung** ist die zentrale redaktionelle Übersicht. Die Recherche-Seite bleibt für aktive Such- und Scanvorgänge zuständig.

## Sichtbar in Quellen & Prüfung

- bestehendes Quellenregister mit Vertrauens- und Nutzungsstatus
- empfohlene Quellenprofile inklusive Priorität und Automationssperre
- Schaltfläche zum idempotenten Installieren oder Aktualisieren der Standardprofile
- offene Datenlücken pro Duft
- konkret fehlende Felder wie Jahr, Konzentration, Parfümeur, Beschreibung, Bild, Quelle und Duftpyramide
- Schaltfläche zum erneuten Berechnen der Datenlücken

## Abgrenzung

- **Recherche:** Scans starten, Webtreffer sammeln, Kandidaten und Duftzwilling-Hinweise prüfen.
- **Quellen & Prüfung:** Quellenregeln, Quellenstatus und redaktionelle Vollständigkeit überblicken.

Die Informationen dürfen in beiden Bereichen erscheinen, wenn sie für den jeweiligen Arbeitsablauf nötig sind. Der redaktionelle Gesamtüberblick liegt jedoch unter **Quellen & Prüfung**.

## Validierung

- Backend unverändert; vorhandene Endpunkte werden wiederverwendet.
- Frontend-Build über die zentrale DGD-CI.
- Keine Produktionsumgebung wird verändert.
