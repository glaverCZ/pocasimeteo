"""Constants for the PočasíMeteo integration."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

DOMAIN = "pocasimeteo"
CONF_STATION = "station"
CONF_MODEL = "model"

# Souřadnice a časové pásmo pro Prahu
PRAGUE_COORDINATES = {"latitude": 50.0755, "longitude": 14.4378}
PRAGUE_TIMEZONE = ZoneInfo("Europe/Prague")

# Příklady dostupných stanic (uživatel může zadat libovolnou stanici)
# Formát: název stanice odpovídající URL na pocasimeteo.cz
# Např.: praha-6-ruzyne, brno, ostrava, plzen, liberec, olomouc, atd.

# Dostupné modely předpovědi
# Format: "MODEL_NAME": {"label": "Display Label", "file": "API_filename.json"}
WEATHER_MODELS = {
    "MASTER": {"label": "MASTER", "file": "MASTER_data.json"},
    "ALADIN": {"label": "ALADIN", "file": "ALADIN_data.json"},
    "ICON": {"label": "ICONEU", "file": "ICON_data.json"},  # ICON_data.json = ICON-EU (evropský)
    "COSMO": {"label": "ICONDE", "file": "COSMO_data.json"},  # COSMO_data.json = ICON-DE (německý)
    "YRno": {"label": "YRno", "file": "YRno_data.json"},
    "GFS": {"label": "GFS", "file": "GFS_data.json"},
    "WRF": {"label": "WRF", "file": "WRF_data.json"},
}

# Backwards compatibility - pro selectory v config flow
WEATHER_MODELS_LABELS = {name: info["label"] for name, info in WEATHER_MODELS.items()}

# URL šablona pro API
API_URL_TEMPLATE = "https://ext.pocasimeteo.cz/{station}/predpoved/data/weather_data.json"

# Aktualizační interval - 1 minutu po každé celé hodině (s malou náhodností pro distribuci zátěže)
# Pozn: Tento interval se ignoruje v coordinatoru, kde se místo toho nastavuje konkrétní čas
UPDATE_INTERVAL = timedelta(hours=1)

# Maximální věk dat v minutách (starší data jsou považována za zastaralá)
DATA_MAX_AGE_MINUTES = 90

# Interval pro zkrácený update pokud jsou data zastaralá (v minutách)
DATA_STALE_UPDATE_INTERVAL_MINUTES = 5

# Mapování API ikon na skutečné PNG soubory (s prefixem "a")
# Defaultní logika: "01" → "a01.png", "46" → "a46.png", atd.
# Bez speciálního mapování - mapování probíhá čistě v frontend kódu
ICON_CODE_MAP = {}

# Mapování kódů počasí na HA podmínky
# Podporuje jak číselné kódy (01, 46, atd.) tak textové názvy ikon
CONDITION_MAP = {
    # Číselné kódy (standardní ČHMÚ)
    "01": "sunny",           # Jasno
    "02": "partlycloudy",    # Polojasno
    "03": "cloudy",          # Oblačno
    "04": "cloudy",          # Zataženo
    "05": "fog",             # Mlha
    "06": "rainy",           # Déšť
    "07": "snowy",           # Sníh
    "08": "snowy",           # Déšť se sněhem
    "09": "rainy",           # Přeháňky
    "10": "rainy",           # Déšť
    "11": "lightning-rainy", # Bouřky
    "12": "snowy",           # Sněžení
    "13": "snowy",           # Sníh
    "14": "snowy",           # Sněžení
    "15": "snowy",           # Sněhové přeháňky
    "20": "cloudy",          # Skoro zataženo
    "21": "cloudy",          # Skoro zataženo
    "22": "rainy",           # Déšť
    "23": "snowy",           # Sníh
    "24": "rainy",           # Přeháňky
    "25": "rainy",           # Přeháňky
    "26": "lightning-rainy", # Bouřky
    "27": "lightning-rainy", # Bouřky
    "28": "snowy",           # Sněžení
    "29": "snowy",           # Sněžení
    "30": "rainy",           # Déšť
    "31": "snowy",           # Sníh
    "32": "snowy",           # Sníh
    "33": "snowy",           # Sníh
    "34": "snowy",           # Sníh
    "40": "fog",             # Mlha
    "41": "fog",             # Mlha
    "42": "fog",             # Mlha
    "43": "fog",             # Mlha
    "44": "fog",             # Mlha
    "45": "fog",             # Mlha
    "46": "rainy",           # Déšť
    "47": "rainy",           # Déšť
    "48": "snowy",           # Sníh
    "49": "snowy",           # Sníh
    "50": "fog",             # Mlha
    "60": "rainy",           # Mírný déšť
    "61": "rainy",           # Déšť
    "62": "rainy",           # Silný déšť
    "63": "rainy",           # Déšť
    "64": "rainy",           # Déšť
    "65": "rainy",           # Silný déšť
    "66": "snowy",           # Déšť se sněhem
    "67": "snowy",           # Déšť se sněhem
    "68": "snowy",           # Déšť se sněhem
    "70": "snowy",           # Mírné sněžení
    "71": "snowy",           # Sněžení
    "72": "snowy",           # Silné sněžení
    "73": "snowy",           # Sněžení
    "74": "snowy",           # Sněžení
    "75": "snowy",           # Silné sněžení
    "76": "snowy",           # Sněhové zrna
    "77": "snowy",           # Sněhové vločky
    "78": "snowy",           # Sněhové krystalky

    # Textové názvy ikon (pro WRF a další modely)
    "clear_day": "sunny",
    "clear_night": "clear-night",
    "partly_cloudy_day": "partlycloudy",
    "partly_cloudy_night": "partlycloudy",
    "cloudy": "cloudy",
    "fog": "fog",
    "mlha": "fog",
    "mlha-dest": "rainy",
    "mlha-snih": "snowy",
    "rain": "rainy",
    "snow": "snowy",
    "sleet": "snowy",
    "polojasno-destova-prehanka": "rainy",
    "polojasno-snezeni": "snowy",
    "skoro_zatazeno": "cloudy",
    "skoro_zatazeno_dest_1": "rainy",
    "skoro_zatazeno_dest_2": "rainy",
    "skoro_zatazeno_dest_se_snehem": "snowy",
    "skoro_zatazeno_snezeni_1": "snowy",
    "skoro_zatazeno_snezeni_2": "snowy",  # ← TEN Z VAŠEHO PŘÍKLADU
    "skoro_zatazeno_bourka_d": "lightning-rainy",
    "skoro_zatazeno_bourka_n": "lightning-rainy",
    "oblacno_bourka_d": "lightning-rainy",
    "oblacno_bourka_n": "lightning-rainy",
    "zatazeno_bourka": "lightning-rainy",
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
