"""Config flow for Rolling Mealplan."""

from __future__ import annotations

from datetime import date, timedelta

import voluptuous as vol
from homeassistant.util import dt as dt_util
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DEFAULT_WEEKS, DOMAIN, MAX_WEEKS, MIN_WEEKS


class RollingMealplanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure the rolling plan."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Set the first Monday and the shopping list entity."""
        errors = {}
        if user_input is not None:
            # This Monday anchors the rolling plan, independent of calendar months.
            anchor = date.fromisoformat(user_input["anchor_date"])
            if anchor.weekday() != 0:
                errors["anchor_date"] = "not_monday"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Familien-Speiseplan",
                    data={
                        "anchor_date": user_input["anchor_date"],
                        "todo_entity": user_input["todo_entity"],
                    },
                )

        today = dt_util.now().date()
        suggested_monday = today - timedelta(days=today.weekday())
        schema = vol.Schema({
            vol.Required("anchor_date", default=suggested_monday.isoformat()): selector.DateSelector(),
            vol.Required("todo_entity"): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="todo", multiple=False)
            ),
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Allow the plan length to be changed after initial setup."""
        return RollingMealplanOptionsFlow()


class RollingMealplanOptionsFlow(config_entries.OptionsFlow):
    """Configure the number of rolling plan weeks."""

    async def async_step_init(self, user_input=None):
        """Show and save the desired plan length."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        current_weeks = self.config_entry.options.get("weeks", DEFAULT_WEEKS)
        schema = vol.Schema({
            vol.Required("weeks", default=current_weeks): selector.NumberSelector(
                selector.NumberSelectorConfig(min=MIN_WEEKS, max=MAX_WEEKS, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
        })
        return self.async_show_form(step_id="init", data_schema=schema)
