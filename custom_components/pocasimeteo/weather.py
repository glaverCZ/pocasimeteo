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

from .const import CONDITION_MAP, CONF_MODEL, DOMAIN, WEATHER_MODELS, STATIONS, ICON_CODE_MAP
from .coordinator import PocasimeteoDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PočasíMeteo weather entity."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Vytvoř weather entity pro všechny modely
    # Primární entita bude ta podle výběru uživatele (nebo MASTER jako fallback)
    primary_model = entry.data.get(CONF_MODEL, "MASTER")
    
    entities = []
    
    # Nejdřív vytvoř primární entitu (bez suffixu v názvu)
    entities.append(
        PocasimeteoWeather(
            coordinator,
            entry,
            primary_model,
            is_primary=True
        )
    )
    
    # Pak vytvoř entity pro všechny ostatní modely
    for model in WEATHER_MODELS.keys():
        if model != primary_model:
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
        
        if is_primary:
            # Primární entita bez suffixu
            self._attr_unique_id = f"pocasimeteo_{station_clean}"
            self._attr_name = f"PočasíMeteo {STATIONS.get(self._station, self._station)}"
        else:
            # Ostatní entity se suffixem modelu
            model_lower = model.lower()
            self._attr_unique_id = f"pocasimeteo_{station_clean}_{model_lower}"
            self._attr_name = f"PočasíMeteo {STATIONS.get(self._station, self._station)} {model}"

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
            return None
            
        model_data = self.coordinator.data.get("models", {}).get(self._model, {})
        hourly_data = model_data.get("data", [])
        
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
                _LOGGER.warning("Error parsing forecast data: %s", err)
                continue
                
        return forecasts

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast."""
        if not self.coordinator.data:
            return None
            
        model_data = self.coordinator.data.get("models", {}).get(self._model, {})
        daily_data = model_data.get("data_dne", [])
        
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
                _LOGGER.warning("Error parsing daily forecast: %s", err)
                continue
                
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

        # Extrahuj ikonu kód z API a mapuj na PNG soubor
        api_icon_code = current.get("Ik", "").split(".")[0] if current.get("Ik") else ""
        # Mapuj API kód na PNG soubor (např. "46" → "a10.png")
        icon_filename = ICON_CODE_MAP.get(api_icon_code, f"a{api_icon_code}")

        attributes = {
            "model": WEATHER_MODELS.get(self._model, self._model),
            "cloudiness": current.get("O"),
            "precipitation_probability": current.get("SP"),
            "snow": current.get("SK", 0),
            "wind_gust": current.get("VN"),
            "wind_direction": current.get("VS"),
            "data_stale": data_stale,
            "icon_code": icon_filename,  # Vrať mapovaný PNG filename pro frontend
        }

        if data_age_minutes is not None:
            attributes["data_age_minutes"] = data_age_minutes

        return attributes
