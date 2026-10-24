"""WebSocket commands for the Rolling Mealplan panel."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .storage import MealPlanStore


def _get_store(hass: HomeAssistant) -> MealPlanStore:
    """Return the loaded plan store."""
    store = hass.data.get(DOMAIN, {}).get("store")
    if store is None:
        raise HomeAssistantError("Der Speiseplan ist noch nicht eingerichtet.")
    return store


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/get"})
@websocket_api.async_response
async def ws_get(hass, connection, msg):
    """Send the plan to the frontend."""
    connection.send_result(msg["id"], _get_store(hass).get_data())


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_meal",
    vol.Optional("meal_id"): vol.Any(str, None),
    vol.Required("name"): str,
    vol.Required("ingredients"): [str],
})
@websocket_api.async_response
async def ws_save_meal(hass, connection, msg):
    """Create or update a meal."""
    try:
        meal_id = await _get_store(hass).async_save_meal(
            msg.get("meal_id"), msg["name"], msg["ingredients"]
        )
        connection.send_result(msg["id"], {"meal_id": meal_id})
    except (ValueError, HomeAssistantError) as err:
        connection.send_error(msg["id"], "invalid_plan", str(err))


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/delete_meal",
    vol.Required("meal_id"): str,
})
@websocket_api.async_response
async def ws_delete_meal(hass, connection, msg):
    """Remove a meal."""
    await _get_store(hass).async_delete_meal(msg["meal_id"])
    connection.send_result(msg["id"], {})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/set_day",
    vol.Required("day_index"): vol.All(int, vol.Range(min=0, max=363)),
    vol.Required("meal_id"): vol.Any(str, None),
})
@websocket_api.async_response
async def ws_set_day(hass, connection, msg):
    """Assign a meal to a repeating plan slot."""
    try:
        await _get_store(hass).async_set_day(msg["day_index"], msg["meal_id"])
        connection.send_result(msg["id"], {})
    except (ValueError, HomeAssistantError) as err:
        connection.send_error(msg["id"], "invalid_plan", str(err))


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/set_current_week",
    vol.Required("week_number"): vol.All(int, vol.Range(min=1, max=52)),
})
@websocket_api.async_response
async def ws_set_current_week(hass, connection, msg):
    """Set which plan week is active for the current calendar week."""
    try:
        await _get_store(hass).async_set_current_week(msg["week_number"])
        connection.send_result(msg["id"], {})
    except (ValueError, HomeAssistantError) as err:
        connection.send_error(msg["id"], "invalid_plan", str(err))


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/import",
    vol.Required("data"): dict,
})
@websocket_api.async_response
async def ws_import(hass, connection, msg):
    """Replace plan data after validating a JSON import."""
    try:
        await _get_store(hass).async_import(msg["data"])
        connection.send_result(msg["id"], {})
    except (ValueError, HomeAssistantError) as err:
        connection.send_error(msg["id"], "invalid_import", str(err))


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/add_ingredients",
    vol.Required("day_index"): vol.All(int, vol.Range(min=0, max=363)),
})
@websocket_api.async_response
async def ws_add_ingredients(hass, connection, msg):
    """Add only missing ingredients to the selected to-do list."""
    store = _get_store(hass)
    data = hass.data[DOMAIN]
    entity_id = data["todo_entity"]
    meal_id = store.data["schedule"][msg["day_index"]]
    meal = next((item for item in store.data["meals"] if item["id"] == meal_id), None)
    if meal is None:
        connection.send_error(msg["id"], "no_meal", "Für diesen Tag ist kein Gericht eingetragen.")
        return

    ingredients = meal["ingredients"]
    if not ingredients:
        connection.send_result(msg["id"], {"added": 0, "skipped": 0})
        return

    # Read open items once, then update the set after each insertion to catch
    # duplicates both in the existing list and within this dish.
    response = await hass.services.async_call(
        "todo",
        "get_items",
        {"entity_id": entity_id, "status": ["needs_action"]},
        blocking=True,
        return_response=True,
    )
    items = _extract_items(response, entity_id)
    existing = {_normalize(item.get("summary", "")) for item in items if isinstance(item, dict)}
    added = 0
    skipped = 0
    for ingredient in ingredients:
        key = _normalize(ingredient)
        if not key or key in existing:
            skipped += 1
            continue
        await hass.services.async_call(
            "todo",
            "add_item",
            {"entity_id": entity_id, "item": ingredient},
            blocking=True,
        )
        existing.add(key)
        added += 1

    connection.send_result(msg["id"], {"added": added, "skipped": skipped})


def _extract_items(response: Any, entity_id: str) -> list[dict[str, Any]]:
    """Normalize the response shapes returned by to-do providers."""
    # HA returns results keyed by entity ID; tolerate a direct list too.
    if isinstance(response, dict):
        scoped = response.get(entity_id, response)
        if isinstance(scoped, dict) and isinstance(scoped.get("items"), list):
            return scoped["items"]
        if isinstance(scoped, list):
            return scoped
    return []


def _normalize(value: str) -> str:
    """Normalize ingredient names for duplicate checks."""
    # Ignore case and repeated whitespace without changing display text.
    return " ".join(value.casefold().split())


def async_register_websocket_commands(hass: HomeAssistant) -> None:
    """Register this integration's frontend commands."""
    # Register once at component setup; handlers resolve the active store
    # for each request.
    for command in (ws_get, ws_save_meal, ws_delete_meal, ws_set_day, ws_set_current_week, ws_import, ws_add_ingredients):
        websocket_api.async_register_command(hass, command)
