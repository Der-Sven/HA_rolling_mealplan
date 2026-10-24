# HA Rolling Mealplan

Eine Home Assistant Custom Integration für einen wiederkehrenden Speiseplan mit 12 Wochen.

> **Entwicklungsstand:** Projektgerüst. Die Integrationsfunktionen und die Wochenansicht werden schrittweise ergänzt.

## Geplante Funktionen

- Der Plan umfasst 12 Wochen (84 Tage), startet an einem Montag und wiederholt sich danach fortlaufend.
- Gerichte werden über die Home Assistant Oberfläche gepflegt. Import und Export unterstützen JSON und CSV.
- Pro Gericht wird eine einfache Zutatenliste gespeichert; vollständige Rezepte sind nicht vorgesehen.
- Eine Wochenansicht bietet Navigation durch vergangene und kommende Wochen.
- Sensoren stellen das Gericht für heute und morgen als Home Assistant Entitäten bereit.
- Ein Knopf pro Tag fügt die Zutaten dieses Gerichts auf Wunsch der konfigurierten To-do-Liste hinzu. Bereits vorhandene offene Einträge werden übersprungen.
- Die Oberfläche startet auf Deutsch. Weitere Sprachen können später über Home Assistant Übersetzungen ergänzt werden.

## Installation (manuell)

Nach Fertigstellung lässt sich die Integration manuell über HACS als benutzerdefiniertes Repository installieren. Bis dahin ist eine manuelle Installation möglich:

1. Repository herunterladen oder klonen.
2. Den Ordner custom_components/rolling_mealplan in das gleichnamige Verzeichnis unter <config>/custom_components/ kopieren.
3. Home Assistant neu starten.
4. Unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** nach **Rolling Mealplan** suchen.
5. Im Einrichtungsdialog den Montag der ersten Planwoche und die To-do-Liste auswählen.

Der aktuelle Projektstand enthält noch nicht alle beschriebenen Funktionen und ist noch nicht für den produktiven Einsatz vorgesehen.

## HACS

Das Repository wird für die manuelle HACS-Installation vorbereitet. Eine spätere Einreichung in die HACS-Standardliste ist ein eigener Schritt und setzt die zu diesem Zeitpunkt geltenden HACS-Anforderungen sowie eine Prüfung voraus.

## Austauschformat

JSON ist das vollständige Sicherungs- und Austauschformat. Es enthält die Gerichte mit Zutaten und die Zuordnung aller 84 Tage zu Gerichten. Beispiel für einen Gerichtseintrag:

    {
      "id": "tomatensuppe",
      "name": "Tomatensuppe",
      "ingredients": ["frische Tomaten", "Passata", "Basilikum", "Croutons"]
    }

CSV eignet sich für den tabellarischen Import und Export des Wochenplans. JSON bleibt erforderlich, wenn Zutatenlisten vollständig übertragen werden sollen.

## Entwicklung

Der Integrationscode liegt in custom_components/rolling_mealplan. Fehlerberichte und Beiträge sind willkommen, sobald das Repository veröffentlicht ist.

## Lizenz

Noch festzulegen.
