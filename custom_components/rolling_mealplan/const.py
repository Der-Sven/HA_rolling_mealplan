"""Constants for Rolling Mealplan."""

DOMAIN = "rolling_mealplan"
STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}_data"
DEFAULT_WEEKS = 12
MIN_WEEKS = 1
MAX_WEEKS = 52
PLATFORM = "sensor"
PANEL_URL = f"/{DOMAIN}/rolling-mealplan-panel.js"
