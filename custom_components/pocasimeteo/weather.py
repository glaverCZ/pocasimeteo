"""Weather entity for PočasíMeteo."""
import logging
from datetime import datetime

from homeassistant.components.weather import (
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_PRECIPITATION,
    ATTR_FORECAST_TEMP,
    ATTR_FORECAST_TIME,
    ATTR_FORECAST_WIND_BEARING,
    ATTR_FORECAST_WIND_SPEED,
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPressure, UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONDITION_MAP, CONF_MODEL, DOMAIN, WEATHER_MODELS, ICON_CODE_MAP, PRAGUE_TIMEZONE
from .coordinator import PocasimeteoDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def _get_czech_holiday(date: datetime) -> str | None:
    """Get Czech holiday name for given date, or None if no holiday."""
    # Fixed Czech holidays (month, day)
    fixed_holidays = {
        (1, 1): "Nový rok",
        (5, 1): "Svátek práce",
        (5, 8): "Den vítězství",
        (7, 5): "Den slovanských věrozvěstů",
        (7, 6): "Upálení Jana Husa",
        (9, 28): "Den české státnosti",
        (10, 28): "Vznik samostatného československého státu",
        (11, 17): "Den boje za svobodu a demokracii",
        (12, 24): "Štedrej den",
        (12, 25): "Boží hod",
        (12, 26): "Den svatého Štěpána",
    }

    # Easter-dependent holidays - calculate Easter date
    # Using simplified algorithm for Czech holidays
    # For 2024-2026, use hardcoded values to avoid complex calculations
    easter_holidays_2024 = {
        (3, 29): "Velký pátek",
        (3, 31): "Velikonoční neděle",
        (4, 1): "Velikonoční pondělí",
    }
    easter_holidays_2025 = {
        (4, 18): "Velký pátek",
        (4, 20): "Velikonoční neděle",
        (4, 21): "Velikonoční pondělí",
    }
    easter_holidays_2026 = {
        (4, 3): "Velký pátek",
        (4, 5): "Velikonoční neděle",
        (4, 6): "Velikonoční pondělí",
    }

    month_day = (date.month, date.day)

    # Check fixed holidays
    if month_day in fixed_holidays:
        return fixed_holidays[month_day]

    # Check Easter-dependent holidays by year
    if date.year == 2024 and month_day in easter_holidays_2024:
        return easter_holidays_2024[month_day]
    elif date.year == 2025 and month_day in easter_holidays_2025:
        return easter_holidays_2025[month_day]
    elif date.year == 2026 and month_day in easter_holidays_2026:
        return easter_holidays_2026[month_day]

    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PočasíMeteo weather entity."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    # VŽDY vytvoř MASTER jako primární entitu (bez suffixu)
    # Toto je důležité pro Lovelace custom card, která očekává MASTER bez suffixu
    entities.append(
        PocasimeteoWeather(
            coordinator,
            entry,
            "MASTER",
            is_primary=True
        )
    )

    # Pak vytvoř entity pro všechny ostatní modely (s suffixem)
    for model in WEATHER_MODELS.keys():
        if model != "MASTER":
            entities.append(
                PocasimeteoWeather(
                    coordinator,
                    entry,
                    model,
                    is_primary=False
                )
            )

    async_add_entities(entities)


class PocasimeteoWeather(CoordinatorEntity, WeatherEntity):
    """Representation of a PočasíMeteo weather entity."""

    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_HOURLY | WeatherEntityFeature.FORECAST_DAILY
    )

    def __init__(
        self,
        coordinator: PocasimeteoDataUpdateCoordinator,
        entry: ConfigEntry,
        model: str,
        is_primary: bool = False,
    ) -> None:
        """Initialize the weather entity."""
        super().__init__(coordinator)

        self._model = model
        self._station = entry.data["station"]
        self._is_primary = is_primary

        # Nastavení unique_id a entity_id
        station_clean = self._station.replace("-", "_")

        # Get model label from WEATHER_MODELS
        model_label = WEATHER_MODELS.get(model, {}).get("label", model)

        if is_primary:
            # Primární entita bez suffixu
            self._attr_unique_id = f"pocasimeteo_{station_clean}"
            self._attr_name = f"PočasíMeteo {self._station}"
        else:
            # Ostatní entity se suffixem modelu (používej label místo názvu)
            model_lower = model.lower()
            self._attr_unique_id = f"pocasimeteo_{station_clean}_{model_lower}"
            self._attr_name = f"PočasíMeteo {self._station} {model_label}"

    def _is_after_sunset(self) -> bool:
        """Check if current time is after sunset."""
        if not self.coordinator.data:
            return False

        sun_times = self.coordinator.data.get("sun_times", {})
        sunset_str = sun_times.get("sunset", "")

        if not sunset_str:
            return False

        try:
            # Parsuj čas západu slunce
            sunset_time = datetime.strptime(sunset_str, "%H:%M").time()
            # Porovnej s aktuálním časem
            current_time = datetime.now(PRAGUE_TIMEZONE).time()
            return current_time >= sunset_time
        except (ValueError, TypeError):
            return False

    def _get_icon_with_night_adjustment(self, icon_code: str) -> str:
        """Get icon code, replacing sunny icons with moon icon if after sunset."""
        # Mapy ikon které se mají nahradit měsíčkem po западu
        sunny_to_moon_map = {
            "a01d": "a01n",  # Slunečno → Měsíc/jasno v noci
            "a02d": "a02n",  # Polojasno → Polojasno v noci
        }

        # Pokud jsme po západu slunce a je to denní ikona slunce, nahraď ji noční
        if self._is_after_sunset() and icon_code in sunny_to_moon_map:
            return sunny_to_moon_map[icon_code]

        return icon_code

    @property
    def native_temperature(self) -> float | None:
        """Return the current temperature."""
        current = self._get_current_data()
        if current:
            return current.get("Te")
        return None

    @property
    def humidity(self) -> int | None:
        """Return the humidity."""
        current = self._get_current_data()
        if current:
            return current.get("Vl")
        return None

    @property
    def native_pressure(self) -> float | None:
        """Return the pressure."""
        current = self._get_current_data()
        if current:
            return current.get("Tl")
        return None

    @property
    def native_wind_speed(self) -> float | None:
        """Return the wind speed."""
        current = self._get_current_data()
        if current:
            return current.get("V")
        return None

    @property
    def wind_bearing(self) -> float | None:
        """Return the wind bearing."""
        current = self._get_current_data()
        if current:
            return current.get("VSS")
        return None

    @property
    def condition(self) -> str | None:
        """Return the weather condition."""
        current = self._get_current_data()
        if current and current.get("Ik"):
            icon_code = current["Ik"].split(".")[0][:2]
            return CONDITION_MAP.get(icon_code, "unknown")
        return None

    def _get_current_data(self) -> dict | None:
        """Get current weather data for this model."""
        if not self.coordinator.data:
            return None

        model_data = self.coordinator.data.get("models", {}).get(self._model, {})
        hourly_data = model_data.get("data", [])

        if not hourly_data:
            return None

        # Pokus najít nejbližší aktuální čas
        from datetime import datetime as dt_module
        now = dt_module.now()

        closest_item = None
        closest_diff = float('inf')

        for item in hourly_data[:24]:  # Hledej v prvních 24 hodinách
            try:
                item_time = dt_module.strptime(item.get("Dat", ""), "%m/%d/%y %H:%M:%S")
                diff = abs((item_time - now).total_seconds())
                if diff < closest_diff:
                    closest_diff = diff
                    closest_item = item
                # Pokud jsme našli budoucí čas a máme kandidáta, skončíme
                if item_time > now and closest_item:
                    break
            except (ValueError, KeyError):
                continue

        return closest_item if closest_item else hourly_data[0]

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        """Return the hourly forecast."""
        if not self.coordinator.data:
            _LOGGER.warning(f"[{self._model}] No coordinator data available")
            return None

        model_data = self.coordinator.data.get("models", {}).get(self._model, {})
        if not model_data:
            _LOGGER.warning(f"[{self._model}] No model data in coordinator for this model")
            return None

        hourly_data = model_data.get("data", [])
        _LOGGER.debug(f"[{self._model}] async_forecast_hourly: found {len(hourly_data)} hourly items")

        forecasts = []
        for item in hourly_data[:48]:  # 48 hodin dopředu
            try:
                dt = datetime.strptime(item["Dat"], "%m/%d/%y %H:%M:%S")
                icon_code = item.get("Ik", "").split(".")[0][:2]

                forecast = {
                    ATTR_FORECAST_TIME: dt.isoformat(),
                    ATTR_FORECAST_TEMP: item.get("Te"),
                    ATTR_FORECAST_PRECIPITATION: item.get("S", 0),
                    ATTR_FORECAST_WIND_SPEED: item.get("V"),
                    ATTR_FORECAST_WIND_BEARING: item.get("VSS"),
                    ATTR_FORECAST_CONDITION: CONDITION_MAP.get(icon_code, "unknown"),
                }
                forecasts.append(forecast)
            except (KeyError, ValueError) as err:
                _LOGGER.warning(f"[{self._model}] Error parsing forecast data: %s", err)
                continue

        _LOGGER.debug(f"[{self._model}] async_forecast_hourly: returning {len(forecasts)} forecasts")
        return forecasts

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast."""
        if not self.coordinator.data:
            _LOGGER.warning(f"[{self._model}] No coordinator data available")
            return None

        model_data = self.coordinator.data.get("models", {}).get(self._model, {})
        if not model_data:
            _LOGGER.warning(f"[{self._model}] No model data in coordinator for this model")
            return None

        daily_data = model_data.get("data_dne", [])
        _LOGGER.debug(f"[{self._model}] async_forecast_daily: found {len(daily_data)} daily items")

        forecasts = []
        for item in daily_data[:7]:  # 7 dní dopředu
            try:
                dt = datetime.strptime(item["Dat_dne"], "%m/%d/%y %H:%M:%S")
                icon_code = item.get("IkD", "").split(".")[0][:2]

                forecast = {
                    ATTR_FORECAST_TIME: dt.isoformat(),
                    ATTR_FORECAST_TEMP: item.get("Tmax"),  # Maximální teplota
                    "templow": item.get("Tmin"),  # Minimální teplota
                    ATTR_FORECAST_PRECIPITATION: item.get("S_den", 0),
                    ATTR_FORECAST_CONDITION: CONDITION_MAP.get(icon_code, "unknown"),
                }
                forecasts.append(forecast)
            except (KeyError, ValueError) as err:
                _LOGGER.warning(f"[{self._model}] Error parsing daily forecast: %s", err)
                continue

        _LOGGER.debug(f"[{self._model}] async_forecast_daily: returning {len(forecasts)} forecasts")
        return forecasts

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        current = self._get_current_data()
        if not current:
            return {}

        model_data = self.coordinator.data.get("models", {}).get(self._model, {})
        data_stale = model_data.get("data_stale", False)
        data_age_minutes = model_data.get("data_age_minutes")

        # Vrať raw ikonu z API - frontend si řeší mapování
        # API vrací správný d/n suffix již v Ik (např. "01d.png", "01n.png", "46.png")
        ik_value = current.get("Ik", "")

        # Get current date/time info
        now = datetime.now()
        czech_day_names = ["Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle"]
        day_name = czech_day_names[now.weekday()]
        date_str = f"{day_name} {now.day}. {now.strftime('%B')}"  # e.g., "Středa 19. listopadu"
        time_str = now.strftime("%H:%M")
        holiday_name = _get_czech_holiday(now)

        # Získej sunrise/sunset
        sun_times = self.coordinator.data.get("sun_times", {})
        sunrise_time = sun_times.get("sunrise", "")
        sunset_time = sun_times.get("sunset", "")

        # Get available models from coordinator data
        available_models = self.coordinator.data.get("available_models", [])

        # Get model label
        model_label = WEATHER_MODELS.get(self._model, {}).get("label", self._model)

        attributes = {
            "model": model_label,
            "available_models": available_models,
            "cloudiness": current.get("O"),
            "precipitation_probability": current.get("SP"),
            "snow": current.get("SK", 0),
            "wind_gust": current.get("VN"),
            "wind_direction": current.get("VS"),
            "wind_direction_czech": current.get("VS", "--"),  # VS je již v češtině (S, J, V, Z, SV, atd.)
            "data_stale": data_stale,
            "icon_code": ik_value,  # Raw ikona z API - frontend si řeší mapování
            "current_date": date_str,
            "current_time": time_str,
            "sunrise": sunrise_time,
            "sunset": sunset_time,
        }

        if holiday_name:
            attributes["current_holiday"] = holiday_name

        if data_age_minutes is not None:
            attributes["data_age_minutes"] = data_age_minutes

        # Přidej hodinovou předpověď
        hourly_data = model_data.get("data", [])
        if hourly_data:
            forecast_hourly = []
            # Debug: Log první 3 ikony pro tento model
            icon_samples_logged = 0

            for item in hourly_data[:48]:  # 48 hodin dopředu
                try:
                    dt = datetime.strptime(item["Dat"], "%m/%d/%y %H:%M:%S")
                    api_icon_code = item.get("Ik", "").split(".")[0][:2] if item.get("Ik") else ""
                    raw_icon = item.get("Ik", "")

                    # Debug: Log sample icons
                    if icon_samples_logged < 3 and raw_icon:
                        _LOGGER.info(f"[{self._model}] Icon sample {icon_samples_logged + 1}: Ik='{raw_icon}' → icon_code='{api_icon_code}'")
                        icon_samples_logged += 1

                    forecast = {
                        "datetime": dt.isoformat(),
                        "temperature": item.get("Te"),
                        "precipitation": item.get("S", 0),
                        "wind_speed": item.get("V"),
                        "wind_gust": item.get("VN"),
                        "wind_bearing": item.get("VSS"),
                        "condition": CONDITION_MAP.get(api_icon_code, "unknown"),
                        "icon_code": raw_icon,  # Raw ikona z API - frontend si řeší mapování
                    }
                    forecast_hourly.append(forecast)
                except (KeyError, ValueError):
                    continue

            if forecast_hourly:
                attributes["forecast_hourly"] = forecast_hourly

        # Přidej denní předpověď
        daily_data = model_data.get("data_dne", [])
        if daily_data:
            forecast_daily = []
            for item in daily_data[:7]:  # 7 dní dopředu
                try:
                    dt = datetime.strptime(item["Dat_dne"], "%m/%d/%y %H:%M:%S")
                    api_icon_code = item.get("IkD", "").split(".")[0][:2] if item.get("IkD") else ""

                    # Mapuj na PNG filename - fallback na "a04" pokud není znám
                    icon_filename = ICON_CODE_MAP.get(api_icon_code, "a04")

                    # Mapuj IkD přesně tak jak je (s .png, s d/n suffixy)
                    ikd_value = item.get("IkD", "")
                    forecast = {
                        "datetime": dt.isoformat(),
                        "temperature": item.get("Tmax"),  # Maximální teplota
                        "templow": item.get("Tmin"),  # Minimální teplota
                        "precipitation": item.get("S_den", 0),
                        "wind_speed_max": item.get("Vmax"),  # Max vítr za den
                        "wind_gust_max": item.get("VNmax"),  # Max poryvy za den
                        "condition": CONDITION_MAP.get(api_icon_code, "unknown"),
                        "icon_code": ikd_value,  # Raw ikona z API (např. "46.png", "04.png", "01d.png")
                    }
                    forecast_daily.append(forecast)
                except (KeyError, ValueError):
                    continue

            if forecast_daily:
                attributes["forecast_daily"] = forecast_daily

        return attributes
