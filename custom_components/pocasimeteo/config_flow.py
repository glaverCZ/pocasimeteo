"""Config flow for PočasíMeteo integration."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_MODEL, CONF_STATION, DOMAIN, WEATHER_MODELS, DEFAULT_STATION, DEFAULT_STATION_NAME

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
            station = user_input[CONF_STATION].strip().lower()

            # Validace - stanice musí obsahovat nějaký text
            if not station:
                errors[CONF_STATION] = "invalid_station"
            else:
                await self.async_set_unique_id(station)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=station,
                    data={
                        CONF_STATION: station,
                        CONF_MODEL: user_input.get(CONF_MODEL, "MASTER"),
                    },
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_STATION, default=DEFAULT_STATION): vol.All(
                    vol.Coerce(str), vol.Length(min=1, max=100)
                ),
                vol.Required(CONF_MODEL, default="MASTER"): vol.In(WEATHER_MODELS),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "station_example": "praha-6-ruzyne, brno, ostrava, plzen, apod."
            },
        )
