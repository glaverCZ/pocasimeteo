# PočasíMeteo

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/glaverCZ/pocasimeteo.svg)](https://github.com/glaverCZ/pocasimeteo/releases)
[![License](https://img.shields.io/github/license/glaverCZ/pocasimeteo.svg)](LICENSE)

Home Assistant integrace pro meteorologická data z [PočasíMeteo.cz](https://www.pocasimeteo.cz/).

## Funkce

- **Libovolná meteorologická stanice:**
  - Zadejte název stanice dostupné na PočasíMeteo.cz
  - Např.: praha-6-ruzyne, brno, ostrava, plzen, liberec, olomouc, atd.

- **7 meteorologických modelů:**
  - MASTER (Ensemble)
  - ALADIN
  - ICONDE (ICON)
  - ICONEU (COSMO)
  - YRno
  - GFS
  - WRF

- **Předpověď:**
  - Hodinová předpověď (48 hodin)
  - Denní předpověď (7 dní)

- **Aktuální podmínky:**
  - Teplota
  - Vlhkost
  - Tlak
  - Rychlost a směr větru
  - Stav počasí

- **Doplňující atributy:**
  - Oblačnost
  - Pravděpodobnost srážek
  - Sníh
  - Poryvy větru
  - Směr větru (text)

- **Automatická aktualizace:** Každou hodinu

## Instalace

### Krok 1: Instalace integrace přes HACS (doporučeno)

1. Otevřete HACS v Home Assistant
2. Přejděte do sekce **"Integrations"**
3. Klikněte na **+ EXPLORE & DOWNLOAD REPOSITORIES**
4. Vyhledejte **"PočasíMeteo"**
5. Klikněte na **Download**
6. **Restartujte Home Assistant**

### Krok 2: Instalace Lovelace card (NUTNÉ pro zobrazení počasí)

**DŮLEŽITÉ:** HACS automaticky nenainstaluje Lovelace card pro integrace. Musíte ji přidat manuálně.

#### Metoda 1: Stažení přes GitHub (doporučeno)

1. Stáhněte soubor [pocasimeteo-card.js](https://raw.githubusercontent.com/glaverCZ/pocasimeteo/main/custom_components/pocasimeteo/www/pocasimeteo-card.js)
2. Vytvořte složku `/config/www/community/pocasimeteo-card/` (pokud neexistuje)
3. Zkopírujte `pocasimeteo-card.js` do této složky
4. Přidejte resource v Home Assistant:
   - Otevřete **Nastavení** → **Dashboardy** → **Resources** (vpravo nahoře tři tečky)
   - Klikněte na **+ PŘIDAT RESOURCE**
   - URL: `/hacsfiles/pocasimeteo-card/pocasimeteo-card.js`
   - Typ zdroje: **JavaScript Module**
   - Klikněte na **CREATE**
5. **Smažte browser cache** (Ctrl+F5 nebo Cmd+Shift+R)

#### Metoda 2: Z lokální instalace HACS

Pokud jste nainstalovali integraci přes HACS, card už je ve složce, stačí ji jen zaregistrovat:

1. Card je již stažena v `/config/custom_components/pocasimeteo/www/pocasimeteo-card.js`
2. Zkopírujte ji do `/config/www/community/pocasimeteo-card/pocasimeteo-card.js`
3. Přidejte resource stejně jako v Metodě 1 (body 4-5)

### Manuální instalace (bez HACS)

1. Zkopírujte složku `custom_components/pocasimeteo` do vaší `config/custom_components/` složky v Home Assistant
2. Zkopírujte `custom_components/pocasimeteo/www/pocasimeteo-card.js` do `/config/www/community/pocasimeteo-card/pocasimeteo-card.js`
3. Přidejte resource podle instrukcí výše (Metoda 1, body 4-5)
4. Restartujte Home Assistant

## Konfigurace

### Prostřednictvím UI

1. Přejděte do **Nastavení** → **Zařízení a služby**
2. Klikněte na tlačítko **+ PŘIDAT INTEGRACI**
3. Vyhledejte **PočasíMeteo**
4. Zadejte název meteorologické stanice (např. praha-6-ruzyne)
5. Vyberte preferovaný model předpovědi (výchozí: MASTER)
6. Dokončete konfiguraci

## Lovelace Custom Card

Integrace obsahuje pokročilou Lovelace custom card s podporou více modelů a srovnáním přesnosti. Po instalaci card (viz instrukce výše) ji můžete použít v dashboard.

### Použití card

```yaml
type: custom:pocasimeteo-card
entity: weather.pocasimeteo_praha_6_ruzyne
models:
  - name: MASTER
    label: MASTER
  - name: ALADIN
    label: ALADIN
  - name: ICON
    label: ICONDE
  - name: COSMO
    label: ICONEU
  - name: YRno
    label: YRno
  - name: GFS
    label: GFS
  - name: WRF
    label: WRF
```

### Pokročilá konfigurace

```yaml
type: custom:pocasimeteo-card
entity: weather.pocasimeteo_praha_6_ruzyne
# Automatický výběr nejpřesnějšího modelu podle reference entity
best_match_temperature_entity: sensor.venku_teplota
# Zobrazení rozdílu oproti reference
temperature_entity: sensor.venku_teplota
humidity_entity: sensor.venku_vlhkost
wind_speed_entity: sensor.venku_vitr
# Vlastní pořadí dlaždic
tile_order:
  - temperature
  - humidity
  - precipitation
  - icon
  - wind
  - wind_gust
  - wind_direction
  - pressure
```

### Příklad automatizace

```yaml
automation:
  - alias: "Upozornění na déšť"
    trigger:
      - platform: numeric_state
        entity_id: weather.pocasimeteo_praha_6_ruzyne
        attribute: precipitation_probability
        above: 70
    action:
      - service: notify.mobile_app
        data:
          message: "Dnes bude pravděpodobně pršet ({{ state_attr('weather.pocasimeteo_praha_6_ruzyne', 'precipitation_probability') }}%)"
```

## Entity

Integrace vytvoří pro každou nakonfigurovanou stanici **7 weather entit** (jednu pro každý model):

- **Primární entita** (MASTER): `weather.pocasimeteo_<stanice>`
- **ALADIN**: `weather.pocasimeteo_<stanice>_aladin`
- **ICONDE**: `weather.pocasimeteo_<stanice>_icon`
- **ICONEU**: `weather.pocasimeteo_<stanice>_cosmo`
- **YRno**: `weather.pocasimeteo_<stanice>_yrno`
- **GFS**: `weather.pocasimeteo_<stanice>_gfs`
- **WRF**: `weather.pocasimeteo_<stanice>_wrf`

Všechny entity jsou dostupné pro použití v dashboard a automatizacích.

## Známé omezení

- Data jsou dostupná pouze pro stanice dostupné na PočasíMeteo.cz
- Aktualizace probíhá každou hodinu (limitováno API)
- Některé modely nemusí být vždy dostupné (závisí na API)
- Název stanice musí odpovídat URL formátu na PočasíMeteo.cz (např. praha-6-ruzyne)

## Podpora

Máte-li problém nebo nápad na vylepšení:
- [Vytvořte issue](https://github.com/glaverCZ/pocasimeteo/issues)
- [Přispějte kódem](https://github.com/glaverCZ/pocasimeteo/pulls)

## Licence

Tento projekt je licencován pod MIT licencí - viz [LICENSE](LICENSE) soubor pro detaily.

## Upozornění

Tato integrace není oficiálně podporována ani schvalována provozovateli PočasíMeteo.cz.

---

**Vytvořeno pro Home Assistant komunitu**
