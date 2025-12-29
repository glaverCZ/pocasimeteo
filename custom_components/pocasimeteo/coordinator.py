"""Data update coordinator for PočasíMeteo."""
import asyncio
import logging
from datetime import datetime, timedelta

import aiohttp
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_URL_TEMPLATE, CONF_STATION, DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class PocasimeteoDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching PočasíMeteo data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.station = entry.data[CONF_STATION]
        self.api_url = API_URL_TEMPLATE.format(station=self.station)
        # URL pro refresh dat (musí se zavolat před stažením JSON)
        self.refresh_url = f"https://ext.pocasimeteo.cz/{self.station}/predpoved/"
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            async with async_timeout.timeout(30):
                async with aiohttp.ClientSession() as session:
                    # KROK 1: Nejdřív zavolej refresh URL pro aktualizaci dat
                    _LOGGER.debug("Refreshing data from %s", self.refresh_url)
                    async with session.get(self.refresh_url) as refresh_response:
                        if refresh_response.status != 200:
                            _LOGGER.warning("Refresh request returned status %s", refresh_response.status)
                        # Počkáme chvíli než se data aktualizují
                        await asyncio.sleep(2)
                    
                    # KROK 2: Pak teprve stáhni JSON s aktualizovanými daty
                    _LOGGER.debug("Fetching JSON data from %s", self.api_url)
                    async with session.get(self.api_url) as response:
                        if response.status != 200:
                            raise UpdateFailed(f"Error fetching data: {response.status}")
                        
                        data = await response.json()
                        
                        # Zpracování dat
                        processed_data = {
                            "available_models": data.get("_available_models", []),
                            "models": {}
                        }
                        
                        # Zpracuj data pro všechny modely
                        for model_data in data.get("data", []):
                            model_name = model_data.get("nazevModelu")
                            if model_name:
                                processed_data["models"][model_name] = {
                                    "data": model_data.get("data", []),
                                    "data_dne": model_data.get("data_dne", []),
                                    "last_update": model_data.get("PosledniAktualizace", "")
                                }
                        
                        return processed_data
                        
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}")
