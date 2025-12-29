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

### HACS (doporučeno)

1. Otevřete HACS v Home Assistant
2. Přejděte do sekce "Integrations"
3. Klikněte na tři tečky v pravém horním rohu
4. Vyberte "Custom repositories"
5. Přidejte URL: `https://github.com/glaverCZ/pocasimeteo`
6. Kategorie: `Integration`
7. Klikněte na "Add"
8. Najděte "PočasíMeteo" v seznamu a klikněte na "Download"
9. Restartujte Home Assistant

### Manuální instalace

1. Zkopírujte složku `custom_components/pocasimeteo` do vaší `config/custom_components/` složky v Home Assistant
2. Restartujte Home Assistant

## Konfigurace

### Prostřednictvím UI

1. Přejděte do **Nastavení** → **Zařízení a služby**
2. Klikněte na tlačítko **+ PŘIDAT INTEGRACI**
3. Vyhledejte **PočasíMeteo**
4. Zadejte název meteorologické stanice (např. praha-6-ruzyne)
5. Vyberte preferovaný model předpovědi (výchozí: MASTER)
6. Dokončete konfiguraci

## Lovelace Custom Card

Integrace obsahuje pokročilou Lovelace custom card s podporou více modelů a srovnáním přesnosti.

### Instalace card

Card se **načítá automaticky** po instalaci integrace. Není potřeba manuálně přidávat žádné Lovelace resources.

> **Důležité:** Po instalaci nebo aktualizaci integrace vždy proveďte **hard refresh** (`Ctrl+F5` nebo `Cmd+Shift+R`) pro načtení aktuální verze card.

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
