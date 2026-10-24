# HA Rolling Mealplan

> **Work in progress — Vorabversion 0.4.3b0.** Noch kein stabiler Release; Funktionen und Datenformat können sich ändern.



Eine Home Assistant Custom Integration für einen wiederkehrenden Familien-Speiseplan. Der Plan startet an einem konfigurierbaren Montag und wiederholt sich nach einer einstellbaren Anzahl von Wochen (1 bis 52).

## Versionierung

Die Integrationsversion steht im Manifest der Integration. Der aktuelle Stand ist **0.4.3b0** (Vorabversion). HACS zeigt bei einem Repository ohne veröffentlichtes GitHub-Release nur den kurzen Commit-SHA. Für eine Versionsnummer in HACS wird ein GitHub-Release mit passendem Versions-Tag benötigt. Dieses Projekt verwendet dafür Vorabversionen; eine stabile Version ist noch nicht veröffentlicht.
## Funktionen

- Eigene Speiseplan-Seite in der Home Assistant Seitenleiste mit Wochen-Navigation und Planwochennummer; Kalender und Gerichteliste sind in getrennten Tabs
- Einstellbare Planlänge (1 bis 52 Wochen) in den Integrationseinstellungen; Verlängern fügt leere Wochen an, Verkürzen entfernt nur die letzten Wochen; Gerichte bleiben erhalten
- Aktuelle Planwoche direkt in der App festlegen, etwa nach einer Urlaubspause; der Start-Montag wird passend verschoben, die Gerichte bleiben in ihrer Reihenfolge
- Gerichte mit einfacher Zutatenliste in Home Assistant verwalten
- JSON importieren/exportieren und Plan aus CSV importieren
- Sensoren für heute und morgen für Dashboards; Attribute enthalten Datum und Zutaten
- Pro Tag Zutaten per Knopf in eine bei der Einrichtung gewählte To-do-Liste übernehmen
- Bereits offene, gleichnamige Zutaten werden übersprungen

## HACS

Eine Veröffentlichung im HACS Store ist für eine spätere stabile Version vorgesehen. Bis dahin wird die Integration manuell installiert.

## Manuelle Installation

1. Den Ordner custom_components/rolling_mealplan aus diesem Repository in <config>/custom_components/rolling_mealplan kopieren.
2. Home Assistant neu starten.
3. Die Integration unter Einstellungen → Geräte & Dienste → Integration hinzufügen hinzufügen.

Bei der Einrichtung werden der Montag der ersten Planwoche und die To-do-Listen-Entität gewählt. Die Planlänge beträgt zunächst 12 Wochen. Sie lässt sich danach unter **Einstellungen → Geräte & Dienste → Rolling Mealplan → Konfigurieren** ändern. Die angezeigte Wochennummer zählt innerhalb des rollierenden Plans (Woche 1 bis zur eingestellten letzten Woche), unabhängig von Kalenderwochen. Beim Verlängern werden leere Wochen angefügt; beim Verkürzen fallen nur die letzten Wochen weg. Die separat verwaltete Gerichteliste bleibt dabei unverändert.

## Speiseplan pflegen

Die Seitenleiste enthält anschließend **Speiseplan**. Zuerst Gerichte anlegen und deren Zutaten als kommagetrennte Liste eintragen, zum Beispiel: frische Tomaten, Passata, Basilikum, Croutons. Danach die Gerichte den einzelnen Wochentagen zuordnen. Durch die Wochen kann beliebig vor- und zurückgeblättert werden; Zuordnungen wiederholen sich nach der eingestellten Wochenzahl. Ein Gericht, das gelöscht wird, wird auch aus allen Plan-Tagen entfernt.

Der Einkaufslisten-Knopf fügt die Zutaten nur nach Interaktion hinzu. Home Assistant prüft zuvor die offenen Einträge der gewählten To-do-Liste auf gleiche Namen (ohne Beachtung von Groß-/Kleinschreibung und Mehrfach-Leerzeichen).

## JSON-Format

JSON-Export und -Import enthalten alle Gerichte, das Start-Montag-Datum und genau so viele Zyklustage, wie in den Integrationseinstellungen konfiguriert sind. Ein Eintrag im schedule ist eine Gericht-ID oder null. Beim Import wird das Start-Montag-Datum übernommen, wenn es im JSON enthalten und ein Montag ist. Alternativ akzeptiert der JSON-Import weeks als Liste mit je sieben Gericht-IDs pro Planwoche.

## CSV-Format

CSV importiert einen Plan mit der aktuell eingestellten Wochenzahl. Die Kopfzeile ist week,weekday,meal,ingredients. Woche ist 1 bis zur eingestellten Wochenzahl, Wochentag 1 bis 7 (Montag bis Sonntag). Zutaten werden innerhalb des Zutatenfelds mit Semikolon getrennt. Ein leerer meal-Wert lässt den Tag frei. Beim Import wird der bisherige Plan ersetzt.

## Hinweise

Diese erste Version speichert den Speiseplan lokal im Home Assistant Konfigurationsverzeichnis. Eine gemeinsame Bearbeitung mehrerer Home Assistant Installationen ist nicht vorgesehen.

## Lizenz

MIT
