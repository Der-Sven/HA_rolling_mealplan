Der Versuch, den InitializeDefaultDrives-Vorgang f�r den Anbieter "FileSystem" auszuf�hren, ist fehlgeschlagen.
"""Persistent data model for the rolling 12-week meal plan."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any
from uuid import uuid4

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN, STORAGE_KEY, STORAGE_VERSION

DAYS_IN_CYCLE = 84


class MealPlanStore:
    """Manage meals and the 84-day repeating schedule."""

    def __init__(self, hass: HomeAssistant, anchor_date: str) -> None:
        self.hass = hass
        self.anchor_date = anchor_date
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.data: dict[str, Any] = {
            "version": 1,
            "meals": [],
            "schedule": [None] * DAYS_IN_CYCLE,
        }
        self._listeners: set[Callable[[], None]] = set()

    async def async_load(self) -> None:
        """Load saved plan or create an empty one."""
        saved = await self._store.async_load()
        if isinstance(saved, dict):
            meals = saved.get("meals", [])
            schedule = saved.get("schedule", [])
            if isinstance(meals, list) and isinstance(schedule, list) and len(schedule) == DAYS_IN_CYCLE:
                self.data = {
                    "version": 1,
                    "meals": [m for m in meals if isinstance(m, dict) and m.get("id") and m.get("name")],
                    "schedule": schedule,
                }

    def add_listener(self, callback: Callable[[], None]) -> Callable[[], None]:
        """Subscribe an entity to plan changes."""
        self._listeners.add(callback)
        return lambda: self._listeners.discard(callback)

    def meal_for_date(self, day: date) -> tuple[dict[str, Any] | None, int]:
        """Return scheduled meal and cycle slot for a date."""
        offset = (day - date.fromisoformat(self.anchor_date)).days % DAYS_IN_CYCLE
        meal_id = self.data["schedule"][offset]
        return next((meal for meal in self.data["meals"] if meal["id"] == meal_id), None), offset

    def get_data(self) -> dict[str, Any]:
        """Return a JSON-safe copy for the frontend."""
        return {
            "version": 1,
            "anchor_date": self.anchor_date,
            "meals": self.data["meals"],
            "schedule": self.data["schedule"],
        }

    async def async_save_meal(self, meal_id: str | None, name: str, ingredients: list[str]) -> str:
        """Create or update a meal."""
        name = name.strip()
        if not name:
            raise ValueError("Der Name des Gerichts darf nicht leer sein.")
        meal_id = meal_id or uuid4().hex
        clean_ingredients = _clean_ingredients(ingredients)
        existing = next((meal for meal in self.data["meals"] if meal["id"] == meal_id), None)
        if existing:
            existing.update({"name": name, "ingredients": clean_ingredients})
        else:
            self.data["meals"].append({"id": meal_id, "name": name, "ingredients": clean_ingredients})
        await self._async_save()
        return meal_id

    async def async_delete_meal(self, meal_id: str) -> None:
        """Delete a meal and clear its scheduled occurrences."""
        self.data["meals"] = [meal for meal in self.data["meals"] if meal["id"] != meal_id]
        self.data["schedule"] = [None if item == meal_id else item for item in self.data["schedule"]]
        await self._async_save()

    async def async_set_day(self, day_index: int, meal_id: str | None) -> None:
        """Assign a meal to a cycle day."""
        if not 0 <= day_index < DAYS_IN_CYCLE:
            raise ValueError("Der Plan-Tag muss zwischen 0 und 83 liegen.")
        if meal_id and not any(meal["id"] == meal_id for meal in self.data["meals"]):
            raise ValueError("Das ausgewählte Gericht wurde nicht gefunden.")
        self.data["schedule"][day_index] = meal_id
        await self._async_save()

    async def async_import(self, payload: dict[str, Any]) -> None:
        """Replace the whole plan from versioned JSON data."""
        meals = payload.get("meals")
        schedule = payload.get("schedule")
        if not isinstance(meals, list) or not isinstance(schedule, list) or len(schedule) != DAYS_IN_CYCLE:
            raise ValueError("Der JSON-Import braucht Gerichte und genau 84 Plan-Tage.")
        clean_meals: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for raw in meals:
            if not isinstance(raw, dict):
                raise ValueError("Ein Gericht im Import ist ungültig.")
            name = str(raw.get("name", "")).strip()
            meal_id = str(raw.get("id") or uuid4().hex)
            if not name or meal_id in seen_ids:
                raise ValueError("Gerichtsnamen müssen gefüllt und IDs eindeutig sein.")
            seen_ids.add(meal_id)
            clean_meals.append({
                "id": meal_id,
                "name": name,
                "ingredients": _clean_ingredients(raw.get("ingredients", [])),
            })
        if any(item is not None and item not in seen_ids for item in schedule):
            raise ValueError("Der Import verweist auf ein unbekanntes Gericht.")
        self.data = {"version": 1, "meals": clean_meals, "schedule": schedule}
        await self._async_save()

    async def _async_save(self) -> None:
        await self._store.async_save(self.data)
        for listener in tuple(self._listeners):
            listener()


def _clean_ingredients(values: Any) -> list[str]:
    """Trim and de-duplicate ingredient names."""
    if not isinstance(values, list):
        values = []
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = str(value).strip()
        key = " ".join(item.casefold().split())
        if item and key not in seen:
            seen.add(key)
            result.append(item)
    return result
