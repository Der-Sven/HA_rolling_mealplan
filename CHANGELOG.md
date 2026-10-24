# Changelog

## [0.4.4b0] - 2026-10-24

### Changed

- Im Kalender wird der Wochentag fett und das Datum darunter klein angezeigt, ohne das Datum doppelt auszugeben.


## [0.4.3b0] - 2026-10-24

### Changed

- Kalender und Gerichteliste sind zur übersichtlicheren Ansicht in getrennte Tabs aufgeteilt.
- Die Planwochennummer steht jetzt direkt neben dem Datumsbereich und wird aus dem rollierenden Plan berechnet.


## [0.4.2b0] - 2026-10-24

### Added

- In der Wochenansicht lässt sich auswählen, welche Planwoche für die aktuelle Kalenderwoche gelten soll. Der Start-Montag wird verschoben; Gerichte und Wochenreihenfolge bleiben bestehen.


## [0.4.1b0] - 2026-10-24

### Added

- JSON-Import übernimmt ein enthaltenes gültiges Start-Montag-Datum. So kann der importierte Speiseplan direkt am passenden Punkt im rollierenden Wochenzyklus starten.

### Fixed

- Options-Flow ist mit Home Assistant 2025.12 und neuer kompatibel.


## [0.4.0b0] - 2026-10-24

### Added

- Planlänge von 1 bis 52 Wochen in den Integrationseinstellungen konfigurierbar.
- Verlängern hängt leere Wochen an; Verkürzen entfernt nur die letzten Wochen. Die Gerichteliste bleibt unverändert.
- Die Wochenansicht zeigt die Nummer der Planwoche (1 bis zur eingestellten Planlänge), unabhängig von der Kalenderwoche.
- JSON- und CSV-Import berücksichtigen die konfigurierte Wochenzahl.

### Notes

- Weiterhin eine Vorabversion und noch kein stabiler Release.


Änderungen an diesem Projekt werden hier dokumentiert. Das Projekt befindet sich noch in der Entwicklung; Versionsnummern mit dem Suffix b kennzeichnen Vorabversionen.

## [0.3.0b0] - 2026-10-24

Erste funktionsfähige Vorabversion zur Erprobung in Home Assistant.

### Added

- Rollierender Speiseplan mit 12 Wochen ab einem konfigurierbaren Montag.
- Eigene Home Assistant-Seitenansicht mit Navigation durch die Wochen.
- Pflege der Gerichte und einfachen Zutatenlisten in Home Assistant.
- JSON-Import und -Export sowie CSV-Import des Plans.
- Sensoren für das Essen heute und morgen.
- Interaktion pro Plan-Tag, um fehlende Zutaten zu einer ausgewählten To-do-Liste hinzuzufügen.

### Notes

- Noch kein stabiler Release; Funktionen und Datenformat können sich ändern.
- Die erste Installation erfolgt als HACS-Vorabversion oder manuell.