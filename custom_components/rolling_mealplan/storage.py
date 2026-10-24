"""Persistent data model for the rolling 12-week meal plan."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, timedelta
from typing import Any
from uuid import uuid4

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DEFAULT_WEEKS, DOMAIN, STORAGE_KEY, STORAGE_VERSION

MAX_WEEKS = 52


class MealPlanStore:
    """Manage meals and a configurable repeating weekly schedule."""

    def __init__(self, hass: HomeAssistant, anchor_date: str, weeks: int = DEFAULT_WEEKS) -> None:
        self.hass = hass
        self.anchor_date = anchor_date
        self.weeks = max(1, min(MAX_WEEKS, int(weeks)))
        self.days_in_cycle = self.weeks * 7
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.data: dict[str, Any] = {
            "version": 1,
            "anchor_date": self.anchor_date,
            "meals": [],
            "schedule": [None] * self.days_in_cycle,
        }
        self._listeners: set[Callable[[], None]] = set()

    async def async_load(self) -> None:
        """Load saved plan or create an empty one."""
        saved = await self._store.async_load()
        if isinstance(saved, dict):
            meals = saved.get("meals", [])
            schedule = saved.get("schedule", [])
            if isinstance(meals, list) and isinstance(schedule, list):
                # Restore an imported plan anchor, falling back to the configured anchor
                # for data saved by older versions of the integration.
                saved_anchor = saved.get("anchor_date")
                if isinstance(saved_anchor, str):
                    try:
                        parsed_anchor = date.fromisoformat(saved_anchor)
                    except ValueError:
                        parsed_anchor = None
                    if parsed_anchor is not None and parsed_anchor.weekday() == 0:
                        self.anchor_date = saved_anchor
                # Preserve assignments that fit; extend empty or truncate only the last days.
                resized_schedule = schedule[:self.days_in_cycle] + [None] * max(0, self.days_in_cycle - len(schedule))
                self.data = {
                    "version": 1,
                    "anchor_date": self.anchor_date,
                    "meals": [m for m in meals if isinstance(m, dict) and m.get("id") and m.get("name")],
                    "schedule": resized_schedule,
                }
                if len(schedule) != self.days_in_cycle:
                    await self._store.async_save(self.data)

    def add_listener(self, callback: Callable[[], None]) -> Callable[[], None]:
        """Subscribe an entity to plan changes."""
        self._listeners.add(callback)
        return lambda: self._listeners.discard(callback)

    def meal_for_date(self, day: date) -> tuple[dict[str, Any] | None, int]:
        """Return scheduled meal and cycle slot for a date."""
        # The anchor is day 0. Modulo maps dates before it and dates after
        # the last plan week back into the same cycle.
        offset = (day - date.fromisoformat(self.anchor_date)).days % self.days_in_cycle
        meal_id = self.data["schedule"][offset]
        return next((meal for meal in self.data["meals"] if meal["id"] == meal_id), None), offset

    def get_data(self) -> dict[str, Any]:
        """Return a JSON-safe copy for the frontend."""
        return {
            "version": 1,
            "anchor_date": self.anchor_date,
            "weeks": self.weeks,
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
        if not 0 <= day_index < self.days_in_cycle:
            raise ValueError(f"Der Plan-Tag muss zwischen 0 und {self.days_in_cycle - 1} liegen.")
        if meal_id and not any(meal["id"] == meal_id for meal in self.data["meals"]):
            raise ValueError("Das ausgewählte Gericht wurde nicht gefunden.")
        self.data["schedule"][day_index] = meal_id
        await self._async_save()

    async def async_set_current_week(self, week_number: int) -> None:
        """Make a plan week apply to the current calendar week."""
        if not 1 <= week_number <= self.weeks:
            raise ValueError(f"Die Planwoche muss zwischen 1 und {self.weeks} liegen.")

        # Use Home Assistant's local date so the selected current week follows
        # the installation's timezone rather than the server's UTC date.
        today = dt_util.now().date()
        current_monday = today - timedelta(days=today.weekday())
        new_anchor = current_monday - timedelta(days=(week_number - 1) * 7)
        self.anchor_date = new_anchor.isoformat()
        self.data["anchor_date"] = self.anchor_date
        await self._async_save()

    async def async_import(self, payload: dict[str, Any]) -> None:
        """Replace the whole plan from versioned JSON data."""
        meals = payload.get("meals")
        schedule = payload.get("schedule")
        if not isinstance(meals, list) or not isinstance(schedule, list) or len(schedule) != self.days_in_cycle:
            raise ValueError(f"Der JSON-Import braucht Gerichte und genau {self.days_in_cycle} Plan-Tage.")
        # Validate into a separate copy first. A malformed import must not
        # partially replace the saved plan.
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
        # A JSON export may carry the cycle's start Monday. Validate it before
        # replacing the current plan so malformed imports cannot alter state.
        imported_anchor = payload.get("anchor_date", self.anchor_date)
        if not isinstance(imported_anchor, str):
            raise ValueError("Das Startdatum im JSON-Import ist ungültig.")
        try:
            parsed_anchor = date.fromisoformat(imported_anchor)
        except ValueError as err:
            raise ValueError("Das Startdatum im JSON-Import ist ungültig.") from err
        if parsed_anchor.weekday() != 0:
            raise ValueError("Das Startdatum im JSON-Import muss ein Montag sein.")

        self.anchor_date = imported_anchor
        self.data = {"version": 1, "anchor_date": self.anchor_date, "meals": clean_meals, "schedule": schedule}
        await self._async_save()

    async def _async_save(self) -> None:
        await self._store.async_save(self.data)
        # Iterate over a snapshot in case a listener unsubscribes while called.
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
        # Compare normalized text but keep the first spelling and order
        # for display.
        key = " ".join(item.casefold().split())
        if item and key not in seen:
            seen.add(key)
            result.append(item)
    return result
