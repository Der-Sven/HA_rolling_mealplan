Der Versuch, den InitializeDefaultDrives-Vorgang f�r den Anbieter "FileSystem" auszuf�hren, ist fehlgeschlagen.
"""Today and tomorrow meal sensors."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .storage import MealPlanStore


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up the meal sensors."""
    store: MealPlanStore = hass.data[DOMAIN]["store"]
    async_add_entities(
        [
            MealSensor(hass, entry, store, is_tomorrow=False),
            MealSensor(hass, entry, store, is_tomorrow=True),
        ]
    )


class MealSensor(SensorEntity):
    """Sensor that exposes a meal for a given day."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_icon = "mdi:food"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        store: MealPlanStore,
        *,
        is_tomorrow: bool,
    ) -> None:
        self.hass = hass
        self._store = store
        self._is_tomorrow = is_tomorrow
        suffix = "tomorrow" if is_tomorrow else "today"
        self._attr_unique_id = f"{entry.entry_id}_{suffix}"
        self._attr_name = "Morgen" if is_tomorrow else "Heute"
        self._remove_listener = None
        self._remove_midnight = None
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Familien-Speiseplan",
            "manufacturer": "HA Rolling Mealplan",
            "model": "12-Wochen-Plan",
        }

    @property
    def native_value(self) -> str | None:
        """Return the scheduled meal name."""
        day = dt_util.now().date() + (timedelta(days=1) if self._is_tomorrow else timedelta())
        meal, _ = self._store.meal_for_date(day)
        return meal["name"] if meal else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose date and ingredients for dashboard use."""
        day = dt_util.now().date() + (timedelta(days=1) if self._is_tomorrow else timedelta())
        meal, _ = self._store.meal_for_date(day)
        return {
            "date": day.isoformat(),
            "ingredients": meal["ingredients"] if meal else [],
        }

    async def async_added_to_hass(self) -> None:
        """Subscribe to changes and refresh after midnight."""
        await super().async_added_to_hass()
        self._remove_listener = self._store.add_listener(self._handle_update)

        @callback
        def midnight_update(_now) -> None:
            self.async_write_ha_state()

        self._remove_midnight = async_track_time_change(
            self.hass, midnight_update, hour=0, minute=0, second=0
        )

    async def async_will_remove_from_hass(self) -> None:
        """Remove listeners."""
        if self._remove_listener:
            self._remove_listener()
        if self._remove_midnight:
            self._remove_midnight()

    @callback
    def _handle_update(self) -> None:
        """Update entity after plan edits."""
        self.async_write_ha_state()


