# ☀️ PočasíMeteo pro Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/glaverCZ/pocasimeteo.svg)](https://github.com/glaverCZ/pocasimeteo/releases)
[![License](https://img.shields.io/github/license/glaverCZ/pocasimeteo.svg)](LICENSE)

Integrace pro zobrazení předpovědi počasí z [PočasíMeteo.cz](https://www.pocasimeteo.cz/) v Home Assistant.

---

## ✨ Co tato integrace umí

### 📊 7 meteorologických modelů
- **MASTER** - Souhrnný model (ensemble)
- **ALADIN** - Nejlepší pro krátkodobou předpověď (0-24h)
- **ICONDE** - Model ICON-DE
- **ICONEU** - Model ICON-EU (dříve COSMO)
- **YRno** - Norský model
- **GFS** - Americký globální model
- **WRF** - Model WRF

### 🌤️ Předpověď
- ⏰ **Hodinová předpověď** - až 48 hodin dopředu
- 📅 **Denní předpověď** - až 7 dní dopředu

### 📍 Libovolná stanice
Podporuje všechny meteorologické stanice dostupné na PočasíMeteo.cz:
- Praha, Brno, Ostrava, Plzeň, Liberec...
- Více než 100 lokalit po celé ČR

### 🔄 Automatická aktualizace
Data se aktualizují automaticky každou hodinu.

---

## 📦 Instalace

### Metoda 1: HACS (doporučeno)

1. Otevřete **HACS** v Home Assistant
2. Klikněte na **Integrations**
3. Klikněte na **⊕ Explore & Download Repositories**
4. Vyhledejte **"PočasíMeteo"**
5. Klikněte na **Download**
6. **Restartujte Home Assistant**

### Metoda 2: Manuální instalace

1. Stáhněte nejnovější verzi z [Releases](https://github.com/glaverCZ/pocasimeteo/releases)
2. Rozbalte a zkopírujte složku `custom_components/pocasimeteo` do `config/custom_components/`
3. **Restartujte Home Assistant**

---

## ⚙️ Konfigurace

Po instalaci:

1. Přejděte do **⚙️ Nastavení** → **Zařízení a služby**
2. Klikněte na **➕ Přidat integraci**
3. Vyhledejte **"PočasíMeteo"**
4. Zadejte **název stanice** (např. `praha-6-ruzyne`)
5. Vyberte **preferovaný model** (doporučujeme MASTER)
6. Dokončete nastavení

### 🗺️ Jak najít název stanice?

1. Jděte na [PočasíMeteo.cz](https://www.pocasimeteo.cz/)
2. Najděte svoji lokalitu
3. URL adresa obsahuje název - např. `https://www.pocasimeteo.cz/predpoved/cr/praha-6-ruzyne`
4. Použijte část za posledním lomítkem: `praha-6-ruzyne`

### 🔧 Pokročilá nastavení (volitelné)

Po přidání integrace můžete konfigurovat **referenční senzory** pro sledování přesnosti modelů:

1. Přejděte do **⚙️ Nastavení** → **Zařízení a služby**
2. Najděte **PočasíMeteo** integraci
3. Klikněte na **KONFIGUROVAT**

**Dostupné referenční entity:**

| Parametr | Popis | Příklad entity |
|----------|-------|----------------|
| **Reference Temperature Entity** | Venkovní teplotní senzor pro sledování přesnosti modelů | `sensor.venku_teplota` |
| **Reference Humidity Entity** | Venkovní vlhkostní senzor | `sensor.venku_vlhkost` |
| **Reference Wind Entity** | Senzor rychlosti větru | `sensor.venku_vitr` |
| **Reference Wind Gust Entity** | Senzor poryvů větru | `sensor.venku_vitr_poryvy` |
| **Reference Rainfall Entity** | Senzor srážek | `sensor.venku_srazky` |
| **Reference Pressure Entity** | Senzor atmosférického tlaku | `sensor.venku_tlak` |
| **Reference Wind Direction Entity** | Senzor směru větru | `sensor.venku_vitr_smer` |

**K čemu slouží referenční senzory?**
- Integrace porovnává předpověď s vašimi skutečnými hodnotami
- Automaticky sleduje, který model je nejpřesnější pro vaši lokalitu
- Data se ukládají do atributů entity pro použití v card nebo automatizacích
- Card může automaticky vybírat nejpřesnější model

---

## 🎨 Pokročilá vizualizace (volitelné)

Pro krásné zobrazení s grafy a pokročilými funkcemi nainstalujte **[PočasíMeteo Card](https://github.com/glaverCZ/pocasimeteo-card)**:

### Co umí card?

- 📊 **Interaktivní grafy** předpovědi
- 🔄 **Přepínání mezi modely** jedním kliknutím
- 🎯 **Automatický výběr nejpřesnějšího modelu**
- 🌈 **125+ barevných PNG ikon počasí**
- 📐 **Vlastní rozložení** dlaždic

### Instalace card

1. Otevřete **HACS** → **Frontend**
2. Klikněte na **⊕ Explore & Download Repositories**
3. Vyhledejte **"PočasíMeteo Card"**
4. Klikněte na **Download**
5. **Restartujte Home Assistant**
6. **Smažte cache prohlížeče** (Ctrl+F5)

Kompletní dokumentace: **https://github.com/glaverCZ/pocasimeteo-card**

---

## 📱 Entity

Po nastavení integrace se vytvoří **7 weather entit** (jedna pro každý model):

```
weather.pocasimeteo_<stanice>          ← MASTER (primární)
weather.pocasimeteo_<stanice>_aladin   ← ALADIN
weather.pocasimeteo_<stanice>_icon     ← ICONDE
weather.pocasimeteo_<stanice>_cosmo    ← ICONEU
weather.pocasimeteo_<stanice>_yrno     ← YRno
weather.pocasimeteo_<stanice>_gfs      ← GFS
weather.pocasimeteo_<stanice>_wrf      ← WRF
```

Všechny entity můžete používat v dashboardech, automatizacích a skriptech.

---

## 🤖 Příklad automatizace

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
          message: >
            🌧️ Dnes bude pravděpodobně pršet!
            Pravděpodobnost: {{ state_attr('weather.pocasimeteo_praha_6_ruzyne', 'precipitation_probability') }}%
```

---

## ℹ️ Důležité informace

### Omezení
- Data jsou dostupná pouze pro stanice na PočasíMeteo.cz
- Aktualizace každou hodinu (omezení API)
- Některé modely nemusí být vždy dostupné

### Atributy entit
Každá weather entita obsahuje:
- 🌡️ Teplota, vlhkost, tlak
- 💨 Rychlost a směr větru, poryvy
- ☁️ Oblačnost, srážky, sníh
- 🕐 Čas poslední aktualizace

---

## 🆘 Podpora

### Našli jste chybu nebo máte nápad?
- [📝 Vytvořte issue](https://github.com/glaverCZ/pocasimeteo/issues)
- [💻 Přispějte kódem](https://github.com/glaverCZ/pocasimeteo/pulls)

### Odkazy
- **Frontend card:** [glaverCZ/pocasimeteo-card](https://github.com/glaverCZ/pocasimeteo-card)
- **PočasíMeteo.cz:** [www.pocasimeteo.cz](https://www.pocasimeteo.cz/)

---

## 📄 Licence

MIT License - viz [LICENSE](LICENSE) soubor.

## ⚠️ Upozornění

Tato integrace není oficiálně podporována provozovateli PočasíMeteo.cz. Jedná se o neoficiální komunitní projekt.

---

<div align="center">

**Vytvořeno pro českou Home Assistant komunitu** ❤️

</div>
