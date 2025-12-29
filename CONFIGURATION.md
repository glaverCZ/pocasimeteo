# PočasíMeteo - Konfigurační Příručka

## Přehled

PočasíMeteo je pokročilá Custom Lovelace karta pro Home Assistant, která zobrazuje detailní meteorologické informace z PočasíMeteo API. Karta podporuje přepínání mezi různými predikčními modely a nabízí bohatou konfiguraci.

## Instalace

1. Zkopíruj složku `custom_components/pocasimeteo` do `<config>/custom_components/`
2. Zkopíruj soubor `www/pocasimeteo-card.js` do `<config>/www/`
3. Zkopíruj složku s ikonami `www/icons/` do `<config>/www/`
4. Restartuj Home Assistant

## Základní Konfigurace

### Minimální Konfigurace

```yaml
type: custom:pocasimeteo-card
entity: weather.pocasimeteo_praha_6_ruzyne
```

### Kompletní Konfigurace

```yaml
type: custom:pocasimeteo-card

# POVINNÉ
entity: weather.pocasimeteo_praha_6_ruzyne

# VOLITELNÉ - Detekce nejpřesnějšího modelu
best_match_temperature_entity: sensor.outdoor_temperature

# VOLITELNÉ - Rozšířené hodnocení modelů (více parametrů)
reference_humidity_entity: sensor.outdoor_humidity
reference_rainfall_entity: sensor.outdoor_rainfall
reference_wind_entity: sensor.outdoor_wind_speed
reference_wind_gust_entity: sensor.outdoor_wind_gust
reference_pressure_entity: sensor.outdoor_pressure

# VOLITELNÉ - Váhy pro hodnocení modelů
model_accuracy_weights:
  temperature: 30
  humidity: 20
  precipitation: 20
  wind: 20
  pressure: 10

# VOLITELNÉ - Hysteresis pro ruční výběr modelu (minuty)
model_selection_hysteresis: 30

# VOLITELNÉ - Layout a zobrazení
full_width: false
show_current_weather: true
show_hourly_forecast: true
show_daily_forecast: true

# VOLITELNÉ - Vlastní seznam modelů
models:
  - name: MASTER
    label: Master
  - name: ALADIN
    label: ALADIN
  - name: ICON
    label: ICON
```

## Layout na Desktopu

### Jak Dosáhnout Různých Šířek Karty

V Home Assistant se šířka karty řídí přes **nastavení dashboardu a grid systém**. Máš několik možností:

#### Možnost 1: Změna Šířky Karty v Editoru Dashboardu

1. Otevři svůj dashboard v **režimu editace** (ikona tužky)
2. Klikni na kartu PočasíMeteo
3. V levém panelu se zobrazí nastavení karty
4. Najdi **"Column size"** nebo **"Grid size"**
5. Nastav na:
   - **1 column** = 1/4 šířky (25%)
   - **2 columns** = 1/2 šířky (50%)
   - **3 columns** = 3/4 šířky (75%)
   - **4 columns** = celá šířka (100%)

#### Možnost 2: YAML Konfigurace s `layout_options`

Přidej do karty:

```yaml
type: custom:pocasimeteo-card
entity: weather.pocasimeteo_praha_6_ruzyne

# Layout - celá šířka
layout_options:
  grid_columns: 4  # 1-4 (1=25%, 2=50%, 3=75%, 4=100%)
  grid_rows: auto
```

**Příklady:**

```yaml
# Celá šířka (100%)
layout_options:
  grid_columns: 4

# Půlka šířky (50%)
layout_options:
  grid_columns: 2

# Třetina šířky (33%)
layout_options:
  grid_columns: 1
  grid_rows: auto
```

#### Možnost 3: Kombinace s Jiným Obsahem

Pokud chceš mít kartu vedle sebe s jiným obsahem:

```yaml
# Dashboard s více kartami vedle sebe
views:
  - title: Počasí
    cards:
      # PočasíMeteo na levé straně (50% šířky)
      - type: custom:pocasimeteo-card
        entity: weather.pocasimeteo_praha_6_ruzyne
        layout_options:
          grid_columns: 2

      # Jiná karta na pravé straně (50% šířky)
      - type: entities
        title: Ostatní Info
        entities:
          - entity: sensor.temperature
          - entity: sensor.humidity
        layout_options:
          grid_columns: 2
```

#### Možnost 4: Responsive Layout (Doporučeno)

Pro lepší zobrazení na různých zařízeních:

```yaml
type: custom:pocasimeteo-card
entity: weather.pocasimeteo_praha_6_ruzyne

# Bude se automaticky přizpůsobit velikosti obrazovky
# Pokud chceš, můžeš nastavit i full_width
full_width: true
layout_options:
  grid_columns: 4  # Na desktopu celá šířka
```

### Příklady Layoutů

#### Desktop Full Width

```yaml
- type: custom:pocasimeteo-card
  entity: weather.pocasimeteo_praha_6_ruzyne
  best_match_temperature_entity: sensor.outdoor_temperature
  layout_options:
    grid_columns: 4
```

**Výsledek:** Karta přes celou šířku na desktopu

#### Desktop Vedle Sebe (50/50)

```yaml
cards:
  - type: custom:pocasimeteo-card
    entity: weather.pocasimeteo_praha_6_ruzyne
    layout_options:
      grid_columns: 2

  - type: custom:pocasimeteo-card
    entity: weather.pocasimeteo_brno
    layout_options:
      grid_columns: 2
```

**Výsledek:** Dvě karty vedle sebe, každá 50% šířky

#### Desktop Malá Verze (25%)

```yaml
- type: custom:pocasimeteo-card
  entity: weather.pocasimeteo_praha_6_ruzyne
  layout_options:
    grid_columns: 1
```

**Výsledek:** Karta na 1/4 šířky obrazovky

### Poznámky k Layoutu

- **`full_width: true`** v kartě = rozšíření celé karty, ale samotná šířka se řídí grid systémem
- **`layout_options: grid_columns`** = nastavení pozice v Home Assistant gridovém systému
- Na **mobilech** se automaticky přizpůsobí na plnou šířku
- **Responsive design** = karta se automaticky přizpůsobí dostupné šířce

## Konfiguračních Parametrů

### Povinné

#### `entity`
- **Typ:** `string`
- **Popis:** Entity ID weather komponentu z PočasíMeteo integrace
- **Příklad:** `weather.pocasimeteo_praha_6_ruzyne`

### Volitelné - Detekce Modelů

#### `best_match_temperature_entity`
- **Typ:** `string`
- **Popis:** Entity ID senzoru s aktuální teplotou. Karta automaticky vybere predikční model, jehož teplota se nejlépe shoduje s touto referenční teplotou. Model bude zvýrazněn v tabulátorech.
- **Příklad:** `sensor.outdoor_temperature`
- **Default:** Neurčeno (detekce vypnutá)
- **Poznámka:** Užitečné pro nalezení nejpřesnějšího modelu pro vaši lokaci

### Volitelné - Rozšířené Hodnocení Modelů

Karta podporuje pokročilé hodnocení přesnosti modelů na základě více parametrů (teplota, vlhkost, srážky, vítr, tlak). Toto hodnocení se zobrazuje jako:
- **Číselné skóre** (0-100%) na kartě modelu
- **Barevné označení:** zelené (80+%), žluté (60-79%), červené (<60%)
- **Tooltip** s detailním rozpadem chyb jednotlivých parametrů

#### `reference_humidity_entity`
- **Typ:** `string`
- **Popis:** Entity ID senzoru s aktuální vlhkostí vzduchu. Používá se pro hodnocení přesnosti modelů.
- **Příklad:** `sensor.outdoor_humidity`
- **Default:** Neurčeno (vlhkost se při hodnocení nepoužívá)
- **Poznámka:** Volitelné - bez nastavení se vlhkost v bodování modelu neuplaťuje

#### `reference_rainfall_entity`
- **Typ:** `string`
- **Popis:** Entity ID senzoru se srážkami (dešť). Používá se pro hodnocení přesnosti modelů.
- **Příklad:** `sensor.outdoor_rainfall`
- **Default:** Neurčeno (srážky se při hodnocení nepoužívají)
- **Poznámka:** Volitelné - bez nastavení se srážky v bodování modelu neuplatňují

#### `reference_wind_entity`
- **Typ:** `string`
- **Popis:** Entity ID senzoru s aktuální rychlostí větru. Používá se pro hodnocení přesnosti modelů.
- **Příklad:** `sensor.outdoor_wind_speed`
- **Default:** Neurčeno (rychlost větru se při hodnocení nepoužívá)
- **Poznámka:** Volitelné - bez nastavení se vítr v bodování modelu neuplatňuje

#### `reference_wind_gust_entity`
- **Typ:** `string`
- **Popis:** Entity ID senzoru s nárazem větru. Používá se pro hodnocení přesnosti modelů.
- **Příklad:** `sensor.outdoor_wind_gust`
- **Default:** Neurčeno (nárazy větru se při hodnocení nepoužívají)
- **Poznámka:** Volitelné - bez nastavení se nárazy v bodování modelu neuplatňují

#### `reference_pressure_entity`
- **Typ:** `string`
- **Popis:** Entity ID senzoru s atmosférickým tlakem. Používá se pro hodnocení přesnosti modelů.
- **Příklad:** `sensor.outdoor_pressure`
- **Default:** Neurčeno (tlak se při hodnocení nepoužívá)
- **Poznámka:** Volitelné - bez nastavení se tlak v bodování modelu neuplatňuje

#### `model_accuracy_weights`
- **Typ:** `object`
- **Popis:** Konfigurovatelné váhy pro jednotlivé parametry při výpočtu skóre modelu. Vyšší váha = větší vliv na finální skóre.
- **Struktura:**
  ```yaml
  model_accuracy_weights:
    temperature: 30      # Váha teploty (procenta)
    humidity: 20         # Váha vlhkosti (procenta)
    precipitation: 20    # Váha srážek (procenta)
    wind: 20            # Váha větru (procenta)
    pressure: 10        # Váha tlaku (procenta)
  ```
- **Default:**
  ```yaml
  temperature: 30
  humidity: 20
  precipitation: 20
  wind: 20
  pressure: 10
  ```
- **Příklad - zvýšení důležitosti teploty:**
  ```yaml
  model_accuracy_weights:
    temperature: 50      # Teplota je důležitější
    humidity: 15
    precipitation: 15
    wind: 15
    pressure: 5
  ```
- **Poznámka:** Součet vah se automaticky normalizuje na 100%, takže můžeš použít libovolné hodnoty

#### `model_selection_hysteresis`
- **Typ:** `number`
- **Popis:** Počet minut, jak dlouho karta respektuje ruční výběr modelu před návratem k automatické detekci. Vhodné pro zabránění přeskakování modelů.
- **Jednotka:** minuty
- **Default:** `30` (30 minut)
- **Příklad - 15 minut hysterezis:**
  ```yaml
  model_selection_hysteresis: 15
  ```
- **Příklad - bez hysterezis (vždy auto-select):**
  ```yaml
  model_selection_hysteresis: 0
  ```
- **Poznámka:** Když uživatel ručně klikne na model, karta se automaticky nepřepne na jiný model po dobu nastaveného času.

### Volitelné - Layout

#### `full_width`
- **Typ:** `boolean`
- **Popis:** Pokud je `true`, karta se rozšíří přes celou dostupnou šířku
- **Hodnoty:** `true` / `false`
- **Default:** `false`
- **Příklady:**
  ```yaml
  full_width: true    # Karta zabírá celou šířku
  full_width: false   # Standardní šířka karty
  ```

#### `show_current_weather`
- **Typ:** `boolean`
- **Popis:** Zobrazit/skrýt sekci s aktuálním počasím (čas, teplota, tlak, vlhkost, vítr, nárazy)
- **Hodnoty:** `true` / `false`
- **Default:** `true`
- **Příklady:**
  ```yaml
  show_current_weather: true    # Zobrazit aktuální počasí
  show_current_weather: false   # Skrýt aktuální počasí
  ```

#### `show_hourly_forecast`
- **Typ:** `boolean`
- **Popis:** Zobrazit/skrýt sekci s hodinovou předpovědí (24 hodin)
- **Hodnoty:** `true` / `false`
- **Default:** `true`
- **Příklady:**
  ```yaml
  show_hourly_forecast: true    # Zobrazit hodinovou předpověď
  show_hourly_forecast: false   # Skrýt hodinovou předpověď
  ```

#### `show_daily_forecast`
- **Typ:** `boolean`
- **Popis:** Zobrazit/skrýt sekci s denní předpovědí (7 dní)
- **Hodnoty:** `true` / `false`
- **Default:** `true`
- **Příklady:**
  ```yaml
  show_daily_forecast: true    # Zobrazit denní předpověď
  show_daily_forecast: false   # Skrýt denní předpověď
  ```

### Volitelné - Modely

#### `models`
- **Typ:** `array`
- **Popis:** Vlastní seznam predikčních modelů k zobrazení v tabulátorech
- **Default:** Všech 9 dostupných modelů
- **Struktura:**
  ```yaml
  models:
    - name: MASTER        # Identifikátor modelu
      label: Master       # Zobrazované jméno
    - name: ALADIN
      label: ALADIN
  ```

**Dostupné modely:**
- `MASTER` - Master (Ensemble) - nejlepší dlouhodobá předpověď
- `ALADIN` - ALADIN - nejlepší krátkodobá předpověď (0-6h)
- `ICON` - ICON - střednědodbá (6-24h)
- `GFS` - GFS - dlouhodobá
- `ECMWF` - ECMWF - dlouhodobá (nejpřesnější v EU)
- `WRF` - WRF - detailní lokální
- `COSMO` - COSMO - vysoká rozlišovací schopnost
- `ARPEGE` - ARPEGE - francouzský model
- `YRno` - YRno - norský model

**Příklad - pouze vybrané modely:**
```yaml
models:
  - name: MASTER
    label: Master (Ensemble)
  - name: ALADIN
    label: ALADIN (0-6h)
  - name: ICON
    label: ICON (6-24h)
  - name: ECMWF
    label: ECMWF (Long-term)
```

## Příklady Konfigurace

### Příklad 1: Standardní Setup

```yaml
- type: custom:pocasimeteo-card
  entity: weather.pocasimeteo_praha_6_ruzyne
  best_match_temperature_entity: sensor.outdoor_temperature
```

Zobrazuje:
- Aktuální počasí s referenční teplotou
- Hodinovou předpověď
- Denní předpověď
- Přepínání mezi modely s automatickou detekci nejpřesnějšího

### Příklad 2: Full Width s Výběrem Sekcí

```yaml
- type: custom:pocasimeteo-card
  entity: weather.pocasimeteo_praha_6_ruzyne
  full_width: true
  show_current_weather: true
  show_hourly_forecast: true
  show_daily_forecast: false
```

Zobrazuje:
- Karta přes celou šířku
- Aktuální počasí
- Hodinová předpověď
- Skrytá denní předpověď

### Příklad 3: Minimální Verze

```yaml
- type: custom:pocasimeteo-card
  entity: weather.pocasimeteo_praha_6_ruzyne
  show_hourly_forecast: false
  show_daily_forecast: false
```

Zobrazuje:
- Pouze aktuální počasí

### Příklad 4: Vlastní Modely

```yaml
- type: custom:pocasimeteo-card
  entity: weather.pocasimeteo_praha_6_ruzyne
  best_match_temperature_entity: sensor.outdoor_temperature
  models:
    - name: MASTER
      label: Master (Ensemble)
    - name: ALADIN
      label: ALADIN (Best 0-6h)
    - name: ECMWF
      label: ECMWF (Best Long-term)
```

Zobrazuje:
- Pouze 3 vybrané modely v tabulátorech
- Automatická detekce nejpřesnějšího modelu

### Příklad 5: Pokročilé Hodnocení Modelů (Rozšířené)

```yaml
- type: custom:pocasimeteo-card
  entity: weather.pocasimeteo_praha_6_ruzyne
  best_match_temperature_entity: sensor.outdoor_temperature

  # Rozšířené reference entity pro pokročilé bodování
  reference_humidity_entity: sensor.outdoor_humidity
  reference_rainfall_entity: sensor.outdoor_rainfall
  reference_wind_entity: sensor.outdoor_wind_speed
  reference_wind_gust_entity: sensor.outdoor_wind_gust
  reference_pressure_entity: sensor.outdoor_pressure

  # Vlastní váhy - zvýšit důležitost teploty a snížit ostatní
  model_accuracy_weights:
    temperature: 50
    humidity: 15
    precipitation: 15
    wind: 15
    pressure: 5

  # Hysteresis - udržuj ruční výběr modelu po dobu 20 minut
  model_selection_hysteresis: 20
```

Zobrazuje:
- Skóre modelů (0-100%) na kartách s barvou (zelená/žlutá/červená)
- Automatický výběr nejlepšího modelu na základě více parametrů
- Detail chyb jednotlivých parametrů v tooltipu
- Hysteresis zabránit skákání mezi modely

### Příklad 6: Minimální Extendované Hodnocení

```yaml
- type: custom:pocasimeteo-card
  entity: weather.pocasimeteo_praha_6_ruzyne

  # Pouze teplota a vlhkost - jednodušší hodnocení
  best_match_temperature_entity: sensor.outdoor_temperature
  reference_humidity_entity: sensor.outdoor_humidity
```

Zobrazuje:
- Skóre modelů s váhou 60% teplota, 40% vlhkost
- Ostatní parametry se neuplatňují

## Zobrazovaná Data

### Aktuální Počasí

Karta zobrazuje:
- **Čas a Datum:** Systémový čas aktualizovaný každou celou hodinu
- **Aktuální Teplota:** Z vybraného predikčního modelu
- **Referenční Teplota:** Z `best_match_temperature_entity` (pokud nastavena)
- **Vlhkost:** V procentech
- **Tlak:** V hPa (hektopascalech)
- **Vítr:** V m/s (metrech za sekundu) - konvertováno z km/h
- **Nárazy Větru:** V m/s
- **Ikona:** Custom PNG ikona odpovídající počasí
- **Selhání dat:** Zobrazuje upozornění, pokud data jsou starší než 90 minut

### Hodinová Předpověď

- **Prvních 24 hodin**
- Čas, teplota, ikona, vítr, srážky
- Automatická detekce noci (18:00-06:00) - přepínání na noční ikony
- Horizontální posuvník na desktopu

### Denní Předpověď

- **Příštích 7 dní**
- Den týdne, ikona, maximální/minimální teplota, vítr, srážky
- Vždy denní ikony (bez nočního režimu)
- Horizontální posuvník na desktopu

## Tabulátory Modelů

Karta zobrazuje tabulátory pro všechny dostupné modely:

- **Aktivní model:** Zvýrazněn modrou barvou
- **Nejpřesnější model:** Mírně zvýrazněn (je-li `best_match_temperature_entity` nastavena)
- **Skóre modelu:** Zobrazuje číselné skóre (0-100%) založené na přesnosti modelu
  - **Zelená barva (80+%):** Velmi přesný model
  - **Žlutá barva (60-79%):** Moderně přesný model
  - **Červená barva (<60%):** Méně přesný model
- **Tooltip:** Najeď myší na tabulator pro zobrazení detailního rozpadu chyb jednotlivých parametrů
- **Kliknutí na tabulator:** Přepne na vybraný model a aktivuje hysteresis (pokud nastaven)

### Výpočet Skóre Modelu

Skóre se počítá pomocí algoritmu Z-score normalizace:

1. **Sběr dat:** Pro každý model a jednotlivý parametr se vypočítá chyba (rozdíl od referenční hodnoty)
2. **Normalizace:** Chyby se normalizují pomocí Z-score (přepočítá různé jednotky na jednotnou stupnici)
3. **Vážení:** Každý parametr má svou váhu (default: teplota 30%, ostatní po 20%)
4. **Finální skóre:** Vážený průměr všech parametrů = skóre 0-100%

Příklad: Model s teplotou blíž k referenční a dobrým odhadem větru bude mít vyšší skóre než model s přesnou teplotou ale špatným odhadem větru.

## Jednotky

- **Teplota:** °C (stupně Celsia)
- **Tlak:** hPa (hektopaskaly)
- **Vítr:** m/s (metry za sekundu)
- **Srážky:** mm (milimetry)

## CSS Přizpůsobení (Advanced)

Karta používá Home Assistant CSS proměnné. Můžeš je přepsat přidáním vlastního stylu:

```yaml
- type: custom:pocasimeteo-card
  entity: weather.pocasimeteo_praha_6_ruzyne
  style: |
    ha-card {
      --primary-color: #2196f3;
      --primary-background-color: #ffffff;
      --primary-text-color: #212121;
    }
```

## Řešení Problémů

### Ikony se Nezobrazují

**Příčina:** PNG ikony nejsou v adresáři `/local/icons/`

**Řešení:**
1. Zkontroluj, že složka `www/icons/` existuje
2. Ujisti se, že všechny PNG soubory jsou tam (a01d.png, a01n.png, atd.)
3. Zkontroluj permisiony adresáře
4. Restartuj Home Assistant

### Karta se Nezobrazuje

**Příčina:** Lovelace nelze najít custom element

**Řešení:**
1. Zkontroluj, že `www/pocasimeteo-card.js` existuje
2. Přidej deklaraci do `ui-lovelace.yaml`:
   ```yaml
   resources:
     - url: /local/pocasimeteo-card.js
       type: module
   ```
3. Vymažte cache prohlížeče (Ctrl+F5)
4. Restartuj Home Assistant

### Teplota je Špatná

**Příčina:** Jiný predikční model je vybraný

**Řešení:**
1. Zkontroluj vybraný model v tabulátorech
2. Pokud je `best_match_temperature_entity` nastavena, karta by měla automaticky vybrat nejpřesnější model
3. Můžeš ručně kliknout na jiný model v tabulátoru

### Data Nejsou Aktuální

**Příčina:** Data jsou starší než 90 minut

**Řešení:**
1. Zkontroluj, že integraci běží správně
2. Zkontroluj API připojení
3. Upozornění se zobrazí jako oranžový banner

## Aktualizace Dat

- **Hodinová předpověď:** Aktualizuje se každou celou hodinu (14:01, 15:01, atd.)
- **Denní předpověď:** Aktualizuje se každou celou hodinu
- **Čas a Datum:** Aktualizuje se každou celou hodinu (synchronizace se serverem)
- **Model Switcher:** Přepínání je okamžité

## Poznámky

- Karta automaticky detekuje dostupné modely z Home Assistant
- Primární entita je bez suffixu (weather.pocasimeteo_praha_6_ruzyne)
- Ostatní modely mají suffix (weather.pocasimeteo_praha_6_ruzyne_aladin)
- Karta je responzivní a přizpůsobí se šířce dostupného místa
- Na mobilních zařízeních se zobrazují vertikální scrollbary pro předpovědi

## Autor

PočasíMeteo Weather Card - Custom integration pro Home Assistant s podporou více predikčních modelů z PočasíMeteo API.

## License

Open source - volně použitelné
