"""Config flow for PočasíMeteo integration."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_MODEL, CONF_STATION, DOMAIN, STATIONS, WEATHER_MODELS

_LOGGER = logging.getLogger(__name__)


class PocasimeteoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PočasíMeteo."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_STATION])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=STATIONS[user_input[CONF_STATION]],
                data=user_input,
            )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_STATION): vol.In(STATIONS),
                vol.Required(CONF_MODEL, default="MASTER"): vol.In(WEATHER_MODELS),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
