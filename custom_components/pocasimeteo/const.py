"""Constants for the PočasíMeteo integration."""
from datetime import timedelta

DOMAIN = "pocasimeteo"
CONF_STATION = "station"
CONF_MODEL = "model"

# Příklady dostupných stanic (uživatel může zadat libovolnou stanici)
# Formát: název stanice odpovídající URL na pocasimeteo.cz
# Např.: praha-6-ruzyne, brno, ostrava, plzen, liberec, olomouc, atd.

# Dostupné modely předpovědi
WEATHER_MODELS = {
    "MASTER": "Master (Ensemble)",
    "ALADIN": "ALADIN",
    "ICON": "ICON",
    "GFS": "GFS",
    "ECMWF": "ECMWF",
    "WRF": "WRF",
    "COSMO": "COSMO",
    "ARPEGE": "ARPEGE",
}

# URL šablona pro API
API_URL_TEMPLATE = "https://ext.pocasimeteo.cz/{station}/predpoved/data/weather_data.json"

# Aktualizační interval - každou celou hodinu
UPDATE_INTERVAL = timedelta(hours=1)

# Mapování kódů počasí na HA podmínky
CONDITION_MAP = {
    "01": "sunny",
    "02": "partlycloudy",
    "03": "cloudy",
    "04": "cloudy",
    "09": "rainy",
    "10": "rainy",
    "11": "lightning-rainy",
    "13": "snowy",
    "46": "rainy",
    "50": "fog",
}
