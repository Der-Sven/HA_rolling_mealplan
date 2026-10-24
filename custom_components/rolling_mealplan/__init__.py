"""Integration setup for Rolling Mealplan."""

from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PANEL_URL
from .storage import MealPlanStore
from .websocket import async_register_websocket_commands

PLATFORMS = ["sensor"]
PANEL_FILE = Path(__file__).parent / "www" / "rolling-mealplan-panel.js"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register static frontend files and WebSocket support."""
    # These integration-wide routes are registered once, outside entry reloads.
    async_register_websocket_commands(hass)
    await hass.http.async_register_static_paths(
        [StaticPathConfig(PANEL_URL, str(PANEL_FILE), cache_headers=False)]
    )
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the meal plan entry and its sidebar panel."""
    store = MealPlanStore(hass, entry.data["anchor_date"])
    await store.async_load()
    hass.data[DOMAIN]["store"] = store
    hass.data[DOMAIN]["todo_entity"] = entry.data["todo_entity"]
    # Tie the sidebar panel to the config entry so unloading removes it cleanly.
    await panel_custom.async_register_panel(
        hass=hass,
        frontend_url_path=DOMAIN,
        webcomponent_name="rolling-mealplan-panel",
        module_url=PANEL_URL,
        sidebar_title="Speiseplan",
        sidebar_icon="mdi:food",
        embed_iframe=False,
        require_admin=False,
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the meal plan entry."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    frontend.async_remove_panel(hass, DOMAIN)
    hass.data[DOMAIN].clear()
    return True
