# PočasíMeteo

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/glaverCZ/pocasimeteo.svg)](https://github.com/glaverCZ/pocasimeteo/releases)
[![License](https://img.shields.io/github/license/glaverCZ/pocasimeteo.svg)](LICENSE)

Home Assistant integrace pro meteorologická data z [PočasíMeteo.cz](https://www.pocasimeteo.cz/).

## Funkce

- **4 meteorologické stanice:**
  - Praha 6 - Ruzyně
  - Brno
  - Ostrava
  - Plzeň

- **8 meteorologických modelů:**
  - MASTER (Ensemble)
  - ALADIN
  - ICON
  - GFS
  - ECMWF
  - WRF
  - COSMO
  - ARPEGE

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
4. Vyberte meteorologickou stanici
5. Vyberte preferovaný model předpovědi (výchozí: MASTER)
6. Dokončete konfiguraci

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

Integrace vytvoří pro každou nakonfigurovanou stanici:
- **Hlavní weather entitu** s preferovaným modelem
- **Dodatečné weather entity** pro všechny dostupné modely (pokud je API vrací)

Názvy entit:
- Hlavní: `weather.pocasimeteo_<stanice>`
- Další modely: `weather.pocasimeteo_<stanice>_<model>`

## Známé omezení

- Data jsou dostupná pouze pro vybrané stanice v České republice
- Aktualizace probíhá každou hodinu (limitováno API)
- Některé modely nemusí být vždy dostupné (závisí na API)

## Podpora

Máte-li problém nebo nápad na vylepšení:
- [Vytvořte issue](https://github.com/glaverCZ/pocasimeteo/issues)
- [Přispějte kódem](https://github.com/glaverCZ/pocasimeteo/pulls)

## Licence

Tento projekt je licencován pod MIT licencí - viz [LICENSE](LICENSE) soubor pro detaily.

## Upozornění

Tato integrace není oficiálně podporována ani schvalována provozovateli PočasíMeteo.cz ani Českým hydrometeorologickým ústavem (ČHMÚ).

---

**Vytvořeno pro Home Assistant komunitu**
