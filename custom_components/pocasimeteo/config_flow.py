"""Config flow for PočasíMeteo integration."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import CONF_MODEL, CONF_STATION, DOMAIN, WEATHER_MODELS

_LOGGER = logging.getLogger(__name__)

# Config option keys
CONF_REFERENCE_TEMPERATURE_ENTITY = "reference_temperature_entity"
CONF_REFERENCE_WIND_ENTITY = "reference_wind_entity"
CONF_REFERENCE_WIND_GUST_ENTITY = "reference_wind_gust_entity"
CONF_REFERENCE_RAINFALL_ENTITY = "reference_rainfall_entity"
CONF_REFERENCE_HUMIDITY_ENTITY = "reference_humidity_entity"
CONF_REFERENCE_PRESSURE_ENTITY = "reference_pressure_entity"
CONF_REFERENCE_WIND_DIRECTION_ENTITY = "reference_wind_direction_entity"


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

            # Validace - stanice musí obsahovat nějaký text
            if not station:
                errors[CONF_STATION] = "invalid_station"
            else:
                await self.async_set_unique_id(station)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"PočasíMeteo ({station})",
                    data={
                        CONF_STATION: station,
                        CONF_MODEL: user_input.get(CONF_MODEL, "MASTER"),
                    },
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
            description_placeholders={
                "station_example": "praha-6-ruzyne, brno, ostrava, plzen, apod."
            },
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return PocasimeteoOptionsFlow(config_entry)


class PocasimeteoOptionsFlow(config_entries.OptionsFlow):
    """Handle options for PočasíMeteo integration."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_REFERENCE_TEMPERATURE_ENTITY,
                    default=self.config_entry.options.get(
                        CONF_REFERENCE_TEMPERATURE_ENTITY, ""
                    ),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                        device_class="temperature",
                    )
                ),
                vol.Optional(
                    CONF_REFERENCE_WIND_ENTITY,
                    default=self.config_entry.options.get(
                        CONF_REFERENCE_WIND_ENTITY, ""
                    ),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                    )
                ),
                vol.Optional(
                    CONF_REFERENCE_WIND_GUST_ENTITY,
                    default=self.config_entry.options.get(
                        CONF_REFERENCE_WIND_GUST_ENTITY, ""
                    ),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                    )
                ),
                vol.Optional(
                    CONF_REFERENCE_RAINFALL_ENTITY,
                    default=self.config_entry.options.get(
                        CONF_REFERENCE_RAINFALL_ENTITY, ""
                    ),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                    )
                ),
                vol.Optional(
                    CONF_REFERENCE_HUMIDITY_ENTITY,
                    default=self.config_entry.options.get(
                        CONF_REFERENCE_HUMIDITY_ENTITY, ""
                    ),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                        device_class="humidity",
                    )
                ),
                vol.Optional(
                    CONF_REFERENCE_PRESSURE_ENTITY,
                    default=self.config_entry.options.get(
                        CONF_REFERENCE_PRESSURE_ENTITY, ""
                    ),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                        device_class="pressure",
                    )
                ),
                vol.Optional(
                    CONF_REFERENCE_WIND_DIRECTION_ENTITY,
                    default=self.config_entry.options.get(
                        CONF_REFERENCE_WIND_DIRECTION_ENTITY, ""
                    ),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            description_placeholders={
                "reference_temp_description": "Entity containing actual temperature for model accuracy comparison"
            },
        )
