"""Constants for the PočasíMeteo integration."""
from datetime import datetime, timedelta

DOMAIN = "pocasimeteo"
CONF_STATION = "station"
CONF_MODEL = "model"

# Dostupné stanice (můžeš rozšířit)
STATIONS = {
    "praha-6-ruzyne": "Praha 6 - Ruzyně",
    "brno": "Brno",
    "ostrava": "Ostrava",
    "plzen": "Plzeň",
}

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

# Maximální věk dat v minutách (starší data jsou považována za zastaralá)
DATA_MAX_AGE_MINUTES = 90

# Interval pro zkrácený update pokud jsou data zastaralá (v minutách)
DATA_STALE_UPDATE_INTERVAL_MINUTES = 5

# Mapování API ikon na skutečné PNG soubory (s prefixem "a")
ICON_CODE_MAP = {
    "01": "a01d",  # Slunečno den
    "02": "a02d",  # Polojasno den
    "03": "a03d",  # Zataženo den
    "04": "a04",   # Zataženo
    "05": "a05d",  # Déšť den
    "06": "a06d",  # Sníh den
    "07": "a07d",  # Bouřka den
    "08": "a08d",  # Mrak den
    "09": "a09",   # Déšť
    "10": "a10",   # Déšť
    "11": "a11",   # Bouřka
    "13": "a13",   # Sníh
    "46": "a10",   # Déšť (přímé mapování API)
    "50": "a50",   # Mlha
}

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


def get_best_model_for_forecast(hours_ahead: int = 0) -> str:
    """
    Určí nejlepší model pro předpověď podle času dopředu.
    
    Args:
        hours_ahead: Kolik hodin dopředu předpovídáme
        
    Returns:
        Název nejlepšího modelu
    """
    if hours_ahead <= 6:
        # Krátkodobá předpověď (0-6h): ALADIN je nejlepší pro ČR
        return "ALADIN"
    elif hours_ahead <= 24:
        # Středněkrátkodobá (6-24h): ICON nebo ALADIN
        return "ICON"
    elif hours_ahead <= 72:
        # Střednědobá (1-3 dny): ECMWF je nejpřesnější
        return "ECMWF"
    else:
        # Dlouhodobá (3+ dny): MASTER (ensemble) je nejspolehlivější
        return "MASTER"
