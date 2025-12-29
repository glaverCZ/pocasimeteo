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

from .const import CONDITION_MAP, CONF_MODEL, DOMAIN, WEATHER_MODELS
from .coordinator import PocasimeteoDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PočasíMeteo weather entity."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Vytvoř weather entity pro všechny dostupné modely
    entities = []
    for model in coordinator.data.get("available_models", []):
        if model in WEATHER_MODELS:
            entities.append(
                PocasimeteoWeather(
                    coordinator,
                    entry,
                    model,
                    is_primary=(model == entry.data[CONF_MODEL])
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
        
        # Nastavení unique_id a názvu
        if is_primary:
            self._attr_unique_id = f"{entry.entry_id}"
            self._attr_name = f"PočasíMeteo {coordinator.station}"
        else:
            self._attr_unique_id = f"{entry.entry_id}_{model}"
            self._attr_name = f"PočasíMeteo {coordinator.station} ({WEATHER_MODELS[model]})"

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
        
        if hourly_data:
            return hourly_data[0]  # První položka je aktuální
        return None

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
                    ATTR_FORECAST_TEMP: item.get("Tprum"),  # Průměrná teplota
                    "templow": item.get("Tmin"),
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
            
        return {
            "model": WEATHER_MODELS.get(self._model, self._model),
            "cloudiness": current.get("O"),
            "precipitation_probability": current.get("SP"),
            "snow": current.get("SK", 0),
            "wind_gust": current.get("VN"),
            "wind_direction": current.get("VS"),
        }
