"""Data update coordinator for PočasíMeteo."""
import asyncio
import logging
import random
from datetime import datetime, timedelta

import aiohttp
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

# Pokus importovat astral - pokud není dostupný, použij jednoduchý fallback
try:
    from astral import Observer
    from astral.sun import sun
    ASTRAL_AVAILABLE = True
except ImportError:
    ASTRAL_AVAILABLE = False

from .const import (
    API_URL_TEMPLATE,
    CONF_STATION,
    DATA_MAX_AGE_MINUTES,
    DATA_STALE_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    UPDATE_INTERVAL,
    PRAGUE_COORDINATES,
    PRAGUE_TIMEZONE,
)

_LOGGER = logging.getLogger(__name__)


class PocasimeteoDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching PočasíMeteo data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.hass = hass  # Ulož hass pro později
        self.station = entry.data[CONF_STATION]
        self.api_url = API_URL_TEMPLATE.format(station=self.station)
        # URL pro refresh dat (musí se zavolat před stažením JSON)
        self.refresh_url = f"https://ext.pocasimeteo.cz/{self.station}/predpoved/"

        # Hodinový interval aktualizace
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )

        # Pro sledování zastaralých dat
        self._last_successful_update = None
        self._data_is_stale = False

        # Pro sledování refresh URL - volá se max jednou za hodinu
        self._last_refresh_time = None

        # Nastav scheduler na 1-2 minuty po každé celé hodině
        self._setup_hourly_schedule(hass)

    def _setup_hourly_schedule(self, hass: HomeAssistant) -> None:
        """Setup scheduler to run update at 1-2 minutes past every hour."""
        from homeassistant.helpers.event import async_track_point_in_time

        async def schedule_next_update() -> None:
            """Schedule the next update at 1-2 minutes past the hour."""
            now = datetime.now(PRAGUE_TIMEZONE)

            # Vypočítej čas příštího updatu (1-2 minut po celé hodině)
            # Vyber náhodně mezi minutou 1 a 2 pro distribuci zátěže
            minute_offset = random.randint(1, 2)

            # Pokud jsme už během tohoto minútového okna, jdi na příští hodinu
            if now.minute >= minute_offset:
                # Příští hodina
                next_update_time = now.replace(minute=minute_offset, second=0, microsecond=0)
                next_update_time = next_update_time.replace(hour=(now.hour + 1) % 24)
                if now.hour + 1 >= 24:
                    next_update_time = next_update_time.replace(day=now.day + 1, hour=0)
            else:
                # Tato hodina
                next_update_time = now.replace(minute=minute_offset, second=0, microsecond=0)

            _LOGGER.debug(f"Scheduling next update at {next_update_time.strftime('%H:%M')}")

            # Zaregistruj callback na příští čas
            async_track_point_in_time(
                hass,
                self.async_request_refresh,
                next_update_time
            )

            # Zaregistruj se znovu pro příště
            async_track_point_in_time(
                hass,
                lambda _: asyncio.create_task(schedule_next_update()),
                next_update_time + timedelta(minutes=1)
            )

        # Nastartuj scheduler
        hass.async_create_task(schedule_next_update())

    def _get_sunrise_sunset(self) -> dict:
        """Calculate sunrise and sunset times for Prague."""
        try:
            if ASTRAL_AVAILABLE:
                # Používej astral library pokud je dostupný
                observer = Observer(
                    latitude=PRAGUE_COORDINATES["latitude"],
                    longitude=PRAGUE_COORDINATES["longitude"],
                    elevation=0
                )
                sun_data = sun(observer, date=datetime.now(PRAGUE_TIMEZONE).date(), tzinfo=PRAGUE_TIMEZONE)
                sunrise_str = sun_data["sunrise"].strftime("%H:%M")
                sunset_str = sun_data["sunset"].strftime("%H:%M")
            else:
                # Fallback na jednoduchý algoritmus bez závislostí
                import math
                today = datetime.now()
                day_of_year = today.timetuple().tm_yday

                latitude = PRAGUE_COORDINATES["latitude"]
                latitude_rad = math.radians(latitude)

                # Aproximace sluneční deklinace
                solar_declination = 0.4093 * math.sin((2 * math.pi * (day_of_year - 81)) / 365)

                # Časový úhel pro sunrise/sunset
                cos_hour_angle = -math.tan(latitude_rad) * math.tan(solar_declination)
                cos_hour_angle = max(-1, min(1, cos_hour_angle))
                hour_angle = math.acos(cos_hour_angle)

                # Sluneční čas
                sunrise_solar_time = 12 - (hour_angle * 180 / math.pi) / 15
                sunset_solar_time = 12 + (hour_angle * 180 / math.pi) / 15

                # Místní čas (Praha UTC+2 v létě, UTC+1 v zimě)
                # Zjednoduš na UTC+2 pro leto a UTC+1 pro zimu
                is_summer = 3 <= today.month <= 10  # Zjednodušená detekce léta
                timezone_offset = 2 if is_summer else 1

                sunrise_hour = sunrise_solar_time + timezone_offset
                sunset_hour = sunset_solar_time + timezone_offset

                # Normalizuj na 24h formát
                sunrise_hour = sunrise_hour % 24
                sunset_hour = sunset_hour % 24

                sunrise_str = f"{int(sunrise_hour):02d}:{int((sunrise_hour % 1) * 60):02d}"
                sunset_str = f"{int(sunset_hour):02d}:{int((sunset_hour % 1) * 60):02d}"

            _LOGGER.debug(f"Sunrise: {sunrise_str}, Sunset: {sunset_str}")

            return {
                "sunrise": sunrise_str,
                "sunset": sunset_str,
                "sunrise_datetime": None,
                "sunset_datetime": None,
            }
        except Exception as err:
            _LOGGER.error(f"Error calculating sunrise/sunset: {err}")
            # Fallback na typické hodnoty pro Prahu
            return {
                "sunrise": "06:30",
                "sunset": "19:30",
                "sunrise_datetime": None,
                "sunset_datetime": None,
            }

    async def _async_refresh_data(self, session):
        """Refresh data on the server side."""
        # Kontrola, zda se refresh už provádel
        now = datetime.now()

        # Pokud byla poslední refresh před více než 55 minutami, nebo ještě vůbec nebyla
        if self._last_refresh_time is None:
            time_since_refresh = float('inf')
            should_refresh = True
            _LOGGER.info("First refresh since startup - calling refresh URL")
        else:
            time_since_refresh = (now - self._last_refresh_time).total_seconds() / 60
            should_refresh = time_since_refresh > 55
            if should_refresh:
                _LOGGER.info(f"Refresh interval passed ({time_since_refresh:.0f}m) - calling refresh URL")
            else:
                _LOGGER.debug(f"Skipping refresh URL (last refresh was {time_since_refresh:.0f}m ago)")

        # Provádí refresh jen pokud je to poprvé, nebo pokud je to déle než 55 minut
        if should_refresh:
            try:
                _LOGGER.info("Calling refresh URL: %s", self.refresh_url)
                response = await session.get(self.refresh_url, timeout=15, allow_redirects=True)

                if response.status == 200:
                    _LOGGER.info("✓ Refresh URL called successfully (HTTP %s)", response.status)
                    self._last_refresh_time = now
                    # Počkáme, aby se data na serveru aktualizovala
                    await asyncio.sleep(3)
                else:
                    _LOGGER.warning("✗ Refresh URL returned HTTP %s", response.status)

            except asyncio.TimeoutError:
                _LOGGER.error("✗ Timeout calling refresh URL after 15 seconds")
            except Exception as err:
                _LOGGER.error("✗ Error calling refresh URL: %s", err, exc_info=True)
                # I když refresh selže, pokračujeme ve fetchování existujících dat

    def _parse_timestamp(self, timestamp_str: str) -> datetime | None:
        """Parse timestamp from API format 'DD.MM.YYYY HH:MM'."""
        if not timestamp_str or not isinstance(timestamp_str, str):
            _LOGGER.debug(f"Skipping invalid timestamp: {timestamp_str}")
            return None

        timestamp_str = timestamp_str.strip()
        if not timestamp_str:
            return None

        try:
            return datetime.strptime(timestamp_str, "%d.%m.%Y %H:%M")
        except (ValueError, TypeError) as err:
            _LOGGER.debug(f"Failed to parse timestamp '{timestamp_str}': {err}")
            return None

    def _get_data_age_minutes(self, timestamp_str: str) -> int | None:
        """Get data age in minutes."""
        parsed_time = self._parse_timestamp(timestamp_str)
        if not parsed_time:
            return None

        age = datetime.now() - parsed_time
        return int(age.total_seconds() / 60)

    def _extract_model_data(self, response_data: dict, model_name: str) -> dict | None:
        """Extract model data from various API response formats."""
        if not isinstance(response_data, dict):
            _LOGGER.debug(f"Response data for {model_name} is not a dict")
            return None

        # Preferuj root-level data pokud jsou k dispozici
        data_array = response_data.get("data", [])
        data_dne = response_data.get("data_dne", [])
        last_update = response_data.get("PosledniAktualizace", "")

        _LOGGER.debug(f"Extract {model_name}: data_array={len(data_array)} items, data_dne={len(data_dne)} items, last_update={last_update}")

        # Kontrola: Pokud data[0] je objekt s "data" polem, je to vnořená struktura (ALADIN, atd)
        if isinstance(data_array, list) and len(data_array) > 0:
            first_item = data_array[0]
            if isinstance(first_item, dict):
                # Pokud data[0] má vlastní "data" pole, vyextrahuj je
                if "data" in first_item and isinstance(first_item.get("data"), list):
                    # Toto je vnořená struktura - vyextrahuj data z prvního objektu
                    data_array = first_item.get("data", [])
                    # Pokud nemáme data_dne na root, vezmi ze struktury
                    if not data_dne and "data_dne" in first_item:
                        data_dne = first_item.get("data_dne", [])
                # Pokud pouze chybí data_dne na root, zkus v data[0]
                elif not data_dne and "data_dne" in first_item and isinstance(first_item["data_dne"], list):
                    data_dne = first_item["data_dne"]

        # Format 1: Přímý formát - data jsou přímo v response
        if isinstance(data_array, list):
            return {
                "data": data_array,
                "data_dne": data_dne,
                "last_update": last_update
            }

        # Format 2: Model je zagníždený v klíči s názvem modelu (např. "MASTER": {...})
        if model_name in response_data and isinstance(response_data[model_name], dict):
            model_obj = response_data[model_name]
            model_data_array = model_obj.get("data", [])
            model_data_dne = model_obj.get("data_dne", [])
            model_last_update = model_obj.get("PosledniAktualizace", "")

            # Kontrola: Pokud data[0] je objekt s "data" polem, vyextrahuj vnitřní data
            if isinstance(model_data_array, list) and len(model_data_array) > 0:
                first_item = model_data_array[0]
                if isinstance(first_item, dict):
                    if "data" in first_item and isinstance(first_item.get("data"), list):
                        model_data_array = first_item.get("data", [])
                        if not model_data_dne and "data_dne" in first_item:
                            model_data_dne = first_item.get("data_dne", [])
                    elif not model_data_dne and "data_dne" in first_item and isinstance(first_item["data_dne"], list):
                        model_data_dne = first_item["data_dne"]

            if isinstance(model_data_array, list):
                return {
                    "data": model_data_array,
                    "data_dne": model_data_dne,
                    "last_update": model_last_update
                }

        # Format 3: Data v poli objektů s názvem modelu
        if isinstance(response_data.get("data"), list):
            for item in response_data["data"]:
                if isinstance(item, dict) and item.get("nazevModelu") == model_name:
                    item_data = item.get("data", [])
                    item_data_dne = item.get("data_dne", [])

                    # Kontrola: Pokud data[0] je objekt s "data" polem, vyextrahuj vnitřní data
                    if isinstance(item_data, list) and len(item_data) > 0:
                        first_subitem = item_data[0]
                        if isinstance(first_subitem, dict):
                            if "data" in first_subitem and isinstance(first_subitem.get("data"), list):
                                item_data = first_subitem.get("data", [])
                                if not item_data_dne and "data_dne" in first_subitem:
                                    item_data_dne = first_subitem.get("data_dne", [])
                            elif not item_data_dne and "data_dne" in first_subitem and isinstance(first_subitem["data_dne"], list):
                                item_data_dne = first_subitem["data_dne"]

                    return {
                        "data": item_data,
                        "data_dne": item_data_dne,
                        "last_update": item.get("PosledniAktualizace", "")
                    }

        return None

    def _check_data_staleness(self, processed_data: dict) -> dict:
        """Check if data is stale and add staleness info."""
        # Vezmi timestamp z prvního modelu (všechny by měly mít stejný)
        first_model_data = next(iter(processed_data["models"].values()), {})
        last_update = first_model_data.get("last_update", "")

        data_age_minutes = self._get_data_age_minutes(last_update)
        is_stale = False

        if data_age_minutes is not None and data_age_minutes > DATA_MAX_AGE_MINUTES:
            is_stale = True
            _LOGGER.warning(
                f"Data is stale: {data_age_minutes} minutes old (max allowed: {DATA_MAX_AGE_MINUTES})"
            )

        # Přidej info o zastaralosti do všech modelů
        for model_data in processed_data["models"].values():
            model_data["data_age_minutes"] = data_age_minutes
            model_data["data_stale"] = is_stale

        # Ulož stav
        self._data_is_stale = is_stale
        self._last_successful_update = datetime.now()

        return processed_data

    async def _async_update_data(self):
        """Fetch data from API."""
        _LOGGER.info("▶ Starting PočasíMeteo data update for station: %s", self.station)
        try:
            async with async_timeout.timeout(60):  # Delší timeout pro více requestů
                async with aiohttp.ClientSession() as session:
                    _LOGGER.debug("ClientSession created successfully")

                    # KROK 0: Spočítej sunrise/sunset
                    sun_times = self._get_sunrise_sunset()

                    # KROK 1: Refresh URL - volá se max jednou za hodinu
                    _LOGGER.info("→ KROK 1: Calling refresh data method")
                    await self._async_refresh_data(session)
                    _LOGGER.info("→ KROK 1: Refresh data method completed")

                    # KROK 2: Stáhni data pro všechny modely
                    _LOGGER.info("→ KROK 2: Fetching data for all models")

                    # Import WEATHER_MODELS from const
                    from .const import WEATHER_MODELS

                    available_model_names = list(WEATHER_MODELS.keys())

                    processed_data = {
                        "available_models": available_model_names,
                        "models": {},
                        "sun_times": sun_times  # Přidej sunrise/sunset do kořenových dat
                    }

                    # Všechny dostupné modely s odpovídajícími soubory (z WEATHER_MODELS)
                    models_to_fetch = {
                        name: info["file"] for name, info in WEATHER_MODELS.items()
                    }

                    # Fetchuj data pro všechny modely
                    for model_name, filename in models_to_fetch.items():
                        # Sestav URL pro daný model (ve stejné složce)
                        model_url = f"https://ext.pocasimeteo.cz/{self.station}/predpoved/data/{filename}"

                        try:
                            async with session.get(model_url, timeout=10) as response:
                                if response.status == 200:
                                    data = await response.json()

                                    # Zkus extrahovat data v různých formátech
                                    extracted_data = self._extract_model_data(data, model_name)
                                    if extracted_data:
                                        processed_data["models"][model_name] = extracted_data
                                        _LOGGER.debug(f"Successfully fetched data for {model_name}")
                                    else:
                                        _LOGGER.warning(f"Failed to extract data for {model_name} from {model_url}")
                                else:
                                    _LOGGER.debug(f"Model {model_name} not available (status {response.status})")
                        except asyncio.TimeoutError:
                            _LOGGER.debug(f"Timeout fetching {model_name} from {model_url}")
                        except Exception as err:
                            _LOGGER.debug(f"Error fetching {model_name}: {err}")

                    # Pokud nemáme alespoň MASTER, je to chyba
                    if "MASTER" not in processed_data["models"]:
                        raise UpdateFailed("Failed to fetch MASTER model data")

                    # Pokud nemáme data pro ostatní modely, použij MASTER data jako fallback
                    # aby entity mohly existovat
                    master_data_copy = processed_data["models"].get("MASTER", {})
                    for model in available_model_names:
                        if model not in processed_data["models"] and master_data_copy:
                            _LOGGER.debug(f"Using MASTER data as fallback for {model}")
                            processed_data["models"][model] = master_data_copy.copy()

                    _LOGGER.info(f"Successfully fetched data for {len(processed_data['models'])} models")

                    # Kontrola zastaralosti dat
                    _LOGGER.info("→ KROK 3: Checking data staleness")
                    processed_data = self._check_data_staleness(processed_data)

                    _LOGGER.info("✓ Successfully fetched data for %d models", len(processed_data["models"]))

                    # Zaznamenej accuracy dat - pokud je k dispozici reference_temperature_entity
                    await self._track_model_accuracy(processed_data)

                    return processed_data

        except aiohttp.ClientError as err:
            _LOGGER.error("✗ API communication error: %s", err, exc_info=True)
            raise UpdateFailed(f"Error communicating with API: {err}")
        except Exception as err:
            _LOGGER.error("✗ Unexpected error: %s", err, exc_info=True)
            raise UpdateFailed(f"Unexpected error: {err}")

    async def _track_model_accuracy(self, processed_data: dict) -> None:
        """Track accuracy of each model against reference temperature entity.

        Fires an event for each model comparing forecast temperature vs actual.
        Home Assistant will record this in history for later analysis.
        """
        try:
            # Ziskej reference_temperature_entity z config entry options
            reference_entity = None
            for entry in self.hass.config_entries.async_entries(DOMAIN):
                if entry.data.get(CONF_STATION) == self.station:
                    # Hledej v options (nastavení integrací)
                    reference_entity = entry.options.get("reference_temperature_entity")
                    break

            if not reference_entity:
                _LOGGER.debug("No reference_temperature_entity configured for accuracy tracking")
                return

            # Ziskej aktuální teplotu z reference entity
            ref_entity_state = self.hass.states.get(reference_entity)
            if not ref_entity_state or not ref_entity_state.state:
                _LOGGER.debug(f"Reference entity {reference_entity} has no state")
                return

            try:
                actual_temp = float(ref_entity_state.state)
            except (ValueError, TypeError):
                _LOGGER.debug(f"Reference entity {reference_entity} state is not a number: {ref_entity_state.state}")
                return

            # Pro každý model vypočítej chybu (absolutní diference)
            for model_name, model_data in processed_data["models"].items():
                forecast_data = model_data.get("data", [])
                if not forecast_data:
                    continue

                # Vezmi teplotu z prvního forecastu (nejbližší budoucnost)
                first_forecast = forecast_data[0] if isinstance(forecast_data, list) else forecast_data

                if isinstance(first_forecast, dict):
                    try:
                        forecast_temp = float(first_forecast.get("teplota", 0))
                    except (ValueError, TypeError):
                        continue

                    # Vypočítej absolutní chybu
                    error = abs(forecast_temp - actual_temp)

                    # Vyslij event pro zaznamenání v HA history
                    self.hass.bus.async_fire(
                        "pocasimeteo_accuracy_update",
                        {
                            "model": model_name,
                            "station": self.station,
                            "reference_entity": reference_entity,
                            "actual_temperature": actual_temp,
                            "forecast_temperature": forecast_temp,
                            "absolute_error": error,
                            "timestamp": datetime.now(PRAGUE_TIMEZONE).isoformat()
                        }
                    )

                    _LOGGER.debug(
                        f"Model {model_name}: actual={actual_temp}°C, forecast={forecast_temp}°C, error={error:.1f}°C"
                    )

        except Exception as err:
            _LOGGER.debug(f"Error tracking model accuracy: {err}", exc_info=True)
