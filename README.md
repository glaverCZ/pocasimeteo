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

### Krok 1: Instalace integrace

#### HACS (doporučeno)

1. Otevřete HACS v Home Assistant
2. Přejděte do sekce **"Integrations"**
3. Klikněte na **+ EXPLORE & DOWNLOAD REPOSITORIES**
4. Vyhledejte **"PočasíMeteo"**
5. Klikněte na **Download**
6. **Restartujte Home Assistant**

#### Manuální instalace

1. Zkopírujte složku `custom_components/pocasimeteo` do vaší `config/custom_components/` složky v Home Assistant
2. **Restartujte Home Assistant**

### Krok 2: Konfigurace integrace

1. Přejděte do **Nastavení** → **Zařízení a služby** → **+ PŘIDAT INTEGRACI**
2. Vyhledejte **"PočasíMeteo"**
3. Zadejte název stanice (např. praha-6-ruzyne)
4. Vyberte preferovaný model předpovědi (výchozí: MASTER)
5. Dokončete konfiguraci

### Krok 3: Instalace Lovelace Card (volitelné, ale doporučeno)

Pro zobrazení počasí s pokročilými funkcemi nainstalujte [PočasíMeteo Card](https://github.com/glaverCZ/pocasimeteo-card):

1. Otevřete HACS v Home Assistant
2. Přejděte do sekce **"Frontend"**
3. Klikněte na **+ EXPLORE & DOWNLOAD REPOSITORIES**
4. Vyhledejte **"PočasíMeteo Card"**
5. Klikněte na **Download**
6. **Restartujte Home Assistant**
7. **Smažte browser cache** (Ctrl+F5 nebo Cmd+Shift+R)

## Konfigurace

### Prostřednictvím UI

1. Přejděte do **Nastavení** → **Zařízení a služby**
2. Klikněte na tlačítko **+ PŘIDAT INTEGRACI**
3. Vyhledejte **PočasíMeteo**
4. Zadejte název meteorologické stanice (např. praha-6-ruzyne)
5. Vyberte preferovaný model předpovědi (výchozí: MASTER)
6. Dokončete konfiguraci

## Lovelace Custom Card

Pro pokročilé zobrazení počasí s podporou více modelů a srovnáním přesnosti nainstalujte **[PočasíMeteo Card](https://github.com/glaverCZ/pocasimeteo-card)** (samostatný repozitář).

Card nabízí:
- Podporu všech 7 meteorologických modelů
- Automatický výběr nejpřesnějšího modelu
- Srovnání předpovědi s aktuálními hodnotami
- Vlastní pořadí dlaždic
- 125+ PNG ikon počasí

Pro instalaci a dokumentaci viz **https://github.com/glaverCZ/pocasimeteo-card**

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
