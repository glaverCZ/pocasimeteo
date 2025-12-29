"""Config flow for PočasíMeteo integration."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_MODEL, CONF_STATION, DOMAIN, WEATHER_MODELS

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
            # Normalize station name to lowercase and replace spaces with dashes
            station = user_input[CONF_STATION].lower().strip().replace(" ", "-")
            user_input[CONF_STATION] = station

            await self.async_set_unique_id(station)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"PočasíMeteo ({station})",
                data=user_input,
            )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_STATION): str,
                vol.Required(CONF_MODEL, default="MASTER"): vol.In(WEATHER_MODELS),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
