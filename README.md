# PočasíMeteo Weather Integration - FIXED VERSION

Opravená a vylepšená verze integrace Home Assistant pro **PočasíMeteo** s plnou podporou:
- ✅ Lovelace custom karty s debug loggingem
- ✅ Automatické fetchování dat (refresh URL)
- ✅ Detekce zastaralých dat
- ✅ 8 meteorologických modelů

## 🔧 OPRAVY V TÉTO VERZI

### 1. **Lovelace Karta - Debug Edition**
- ✅ Přidán detailní logging pro debug (`🎨` v konzoli)
- ✅ Lepší error handling s zobrazením chyb na kartě
- ✅ Kontrola existence entit a atributů
- ✅ Fallback na emoji pokud PNG ikony neexistují

### 2. **Data Fetching - Refresh URL**
- ✅ Refresh URL se volá před fetchováním JSON (samovolně)
- ✅ Throttling max 1x za hodinu
- ✅ Logging pro tracking volání
- ✅ Čekání na server (3 sekundy po refresh)

### 3. **Configuration & Setup**
- ✅ Aktualizované instrukce pro Home Assistant
- ✅ Správná konfigurace Lovelace prostředku
- ✅ Debug příkazy pro ověření

## 📦 Obsah

```
pocasimeteo_ha_fixed/
├── README.md                              (tato dokumentace)
├── INSTALL.md                             (instalační instrukce)
├── TROUBLESHOOT.md                        (řešení problémů)
├── custom_components/pocasimeteo/
│   ├── __init__.py                        (inicializace)
│   ├── coordinator.py                     (data fetching s refresh)
│   ├── weather.py                         (weather entity)
│   ├── const.py                           (konstanty)
│   ├── config_flow.py                     (UI konfigurace)
│   ├── manifest.json                      (metadata)
│   └── translations/                      (jazykové soubory)
├── www/
│   ├── pocasimeteo-card.js               (custom karta s debug)
│   └── icons/                             (125+ PNG ikon)
└── .gitignore
```

## 🚀 Rychlá instalace

### Na Home Assistant (SSH)

```bash
# 1. Stáhněte soubory
cd /config/custom_components
git clone https://github.com/glaverCZ/pocasimeteo_ha pocasimeteo

# 2. Zkopírujte custom card a ikony
cp pocasimeteo/www/pocasimeteo-card.js /config/www/community/pocasimeteo-card/
cp pocasimeteo/www/icons/*.png /config/www/local/icons/

# 3. Restartujte Home Assistant
ha core restart
```

### V Home Assistant UI

1. **Nastavení → Zařízení a služby → Vytvořit integraci**
   - Vyhledejte: "PočasíMeteo"
   - Vyberte stanici
   - Vyberte model

2. **Přidejte Lovelace prostředek**
   - Otevřete `/config/configuration.yaml`
   - Přidejte:
   ```yaml
   lovelace:
     resources:
       - url: /local/community/pocasimeteo-card/pocasimeteo-card.js
         type: module
   ```

3. **Restartujte Home Assistant**

4. **Přidejte kartu do Lovelace**
   - Editor → Nová karta
   - Typ: `custom:pocasimeteo-card`
   - Entity: `weather.pocasimeteo_*`

## ⚙️ Konfigurace Karty

### Základní Konfigurace

```yaml
type: custom:pocasimeteo-card
entity: weather.pocasimeteo_praha_6_ruzyne
```

### Parametry

| Parametr | Typ | Default | Popis |
|----------|-----|---------|-------|
| `entity` | string | - | **Povinná** - entita počasí (weather.*) |
| `scale` | number | 1.0 | Zvětšení/zmenšení všech prvků |
| `show_current_weather` | boolean | true | Zobrazit aktuální počasí |
| `show_hourly_forecast` | boolean | true | Zobrazit hodinovou předpověď |
| `show_daily_forecast` | boolean | true | Zobrazit denní předpověď |
| `full_width` | boolean | false | Karta na plnou šířku |

### Příklady

**Zvětšení na 1.2x (20% větší):**
```yaml
type: custom:pocasimeteo-card
entity: weather.pocasimeteo_praha_6_ruzyne
scale: 1.2
```

**Zmenšení na 0.8x (20% menší):**
```yaml
type: custom:pocasimeteo-card
entity: weather.pocasimeteo_praha_6_ruzyne
scale: 0.8
```

**Všechny možnosti najednou:**
```yaml
type: custom:pocasimeteo-card
entity: weather.pocasimeteo_praha_6_ruzyne
scale: 1.1
show_current_weather: true
show_hourly_forecast: true
show_daily_forecast: true
full_width: false
```

**Dostupné stupně zvětšení:**
- `0.7` - malá (30% menší)
- `0.85` - menší (15% menší)
- `1.0` - normální (výchozí)
- `1.15` - větší (15% větší)
- `1.3` - velká (30% větší)
- `1.5` - velmi velká (50% větší)

## 🔍 DEBUG - Řešení problémů

### Lovelace Karta Nefunguje?

1. Otevřete **F12 → Console** v Home Assistant
2. Hledejte zprávy s `🎨`:
   - `🎨 Loading PocasimeteoCard...` ✅ = soubor se načítá
   - `🎨 PocasimeteoCard registered` ✅ = karta je registrována
   - Pokud nejsou → soubor se nenačítá (špatná cesta)

3. Zkontrolujte Network tab:
   - Měl by být request na `/local/community/pocasimeteo-card/pocasimeteo-card.js`
   - Status by měl být **200** (OK)

### Data se Neaktualizují?

1. Zkontrolujte Home Assistant logy:
   ```bash
   # SSH do Home Assistant
   tail -50 /config/home-assistant.log | grep pocasimeteo
   ```

2. Hledejte zprávy:
   - `▶ Setting up PočasíMeteo` = integrace se inicializuje
   - `→ Calling refresh URL` = refresh se volá
   - `✓ Refresh URL called successfully` = refresh OK
   - `✓ Successfully fetched data` = data stažena OK

3. Pokud refresh URL není volán:
   - Zkontrolujte, zda máte připojení k internetu
   - Ověřte, že `https://ext.pocasimeteo.cz/praha-6-ruzyne/predpoved/` je dostupná

### Entity Neexistují?

1. V Home Assistant: **Vývojář → Stavy**
2. Vyhledejte: `weather.pocasimeteo`
3. Pokud nejsou:
   - Zkontrolujte logy pro chyby
   - Restartujte Home Assistant
   - Zkontrolujte, že integrace je v Nastavení → Zařízení a služby → Integrace

## 🎨 Debug Logger Reference

V Browser Console budete vidět zprávy:

```
🎨 Loading PocasimeteoCard...                    = soubor se načítá
🎨 PocasimeteoCard constructor called           = třída se vytváří
🎨 setConfig called with: {...}                 = konfigurace se nastavuje
🎨 hass setter called                           = Home Assistant data se přijímají
🎨 First render, creating HTML                  = HTML se vytváří
🎨 render() completed                           = HTML je hotovo
🎨 updateContent() called                       = obsah se aktualizuje
🎨 Entity: weather.pocasimeteo... State: FOUND  = entita existuje
🎨 Loading icon: a10                            = ikona se načítá
🎨 Card registered in Lovelace                  = karta je registrována
❌ Chyba zprávy - počátek v konzoli             = něco je špatně
```

## 📊 Jak Funguje Refresh

1. **Coordinator.py** se spustí každou hodinu (UPDATE_INTERVAL)
2. **Krok 1:** Zavolá `_async_refresh_data()`
   - Zkontroluje, zda od poslední refresh uplynulo 55+ minut
   - Pokud ano → zavolá: `https://ext.pocasimeteo.cz/{station}/predpoved/`
   - Počká 3 sekundy (server si data aktualizuje)
3. **Krok 2:** Stáhne JSON data pro všechny modely
   - `MASTER_data.json`, `ALADIN_data.json`, atd.
4. **Krok 3:** Zkontroluje stáří dat
   - Pokud data jsou starší 90 minut → zobrazí varovný banner

## 🤝 Support

Máte problém?

1. Nejdřív si přečtěte [TROUBLESHOOT.md](TROUBLESHOOT.md)
2. Zkontrolujte [INSTALL.md](INSTALL.md) pro detaily
3. Otevřete [Issue na GitHubu](https://github.com/glaverCZ/pocasimeteo_ha/issues)

Přiložte:
- ✅ Screenshot Browser Console s chybami
- ✅ Home Assistant logy (grep pocasimeteo)
- ✅ Co přesně vidíte (nebo nevidíte)

## 📝 Verze

- **1.0.0** - Fixed & Debugged Edition
- Lovelace karta s debug loggingem
- Správný data refresh (fetch + JSON)
- Detekce zastaralých dat

---

**Vytvořeno s láskou k počasí** ☀️🌧️⛅

GitHub: https://github.com/glaverCZ/pocasimeteo_ha
