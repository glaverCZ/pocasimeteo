# 🚀 PočasíMeteo - Instalace do Home Assistant

Jednoduchá instalace PočasíMeteo přímo do Home Assistanta jedním příkazem.

## ⚡ Nejrychlejší Instalace (2 minuty)

### V SSH terminálu Home Assistanta:

```bash
# Stáhni a spusť instalátor
curl -fsSL https://raw.githubusercontent.com/glaverCZ/pocasimeteo_ha/main/ha-install.py | python3 - stodulky
```

Nebo ručně:

```bash
cd /config
wget https://raw.githubusercontent.com/glaverCZ/pocasimeteo_ha/main/ha-install.py
python3 ha-install.py stodulky
```

## 🎯 Jak Funguje

Skript `ha-install.py`:
1. ✅ Stáhne integraci z GitHubu
2. ✅ Stáhne custom Lovelace kartu
3. ✅ Stáhne všechny PNG ikony
4. ✅ Aktualizuje `configuration.yaml`
5. ✅ Restartuje Home Assistant

## 📋 Příklady Použití

### Interaktivní režim (bez argumentů)

```bash
python3 ha-install.py
# Ptá se na stanici a model
```

### S výchozími parametry

```bash
python3 ha-install.py stodulky
# Stanice: stodulky
# Model: MASTER (default)
```

### S vlastním modelem

```bash
python3 ha-install.py stodulky ALADIN
# Stanice: stodulky
# Model: ALADIN
```

### Ostatní stanice

```bash
python3 ha-install.py praha-6-ruzyne
python3 ha-install.py brno
python3 ha-install.py ostrava
python3 ha-install.py plzen
```

## ✨ Dostupné Modely

- `MASTER` - Ensemble (default, nejlepší dlouhodobě)
- `ALADIN` - Nejlepší 0-6 hodin
- `ICON` - Dobrý 6-24 hodin
- `ECMWF` - Dlouhodobá předpověď
- `GFS` - Globální model
- `WRF` - Detailní lokální
- `COSMO` - Vysoká rozlišovací schopnost
- `ARPEGE` - Francouzský model
- `YRno` - Norský model

## 🔧 Kde Spustit

### Možnost 1: SSH Web Terminal (Nejjednodušší)

1. V Home Assistantu: **Nastavení** → **Add-ons, Backups & Supervisory** → **Add-on Store**
2. Hledej: **SSH & Web Terminal**
3. Instaluj a nastav heslo
4. Otevři **Web Terminal** v add-onu
5. Spusť: `python3 ha-install.py stodulky`

### Možnost 2: SSH z PC

```bash
ssh root@10.0.0.91
# Zadej heslo
python3 ha-install.py stodulky
```

Nebo přes PowerShell (Windows):

```powershell
ssh root@10.0.0.91
python3 ha-install.py stodulky
```

## 📝 Co Se Nainstaluje

Po spuštění skriptu:

```
/config/
├── custom_components/pocasimeteo/
│   ├── __init__.py
│   ├── coordinator.py
│   ├── weather.py
│   ├── const.py
│   ├── config_flow.py
│   └── manifest.json
│
├── www/
│   ├── pocasimeteo-card.js          (Custom Lovelace karta)
│   └── icons/                        (125 PNG ikon)
│
└── configuration.yaml                (Aktualizován)
```

## ✅ Po Instalaci

### 1. Restart Home Assistant

```bash
# Automaticky po instalaci, ale lze ručně:
ha core restart
```

Čekej 2-3 minuty.

### 2. Přidej Integraci

**Nastavení** → **Zařízení a služby** → **Vytvořit integraci**

Hledej: **PočasíMeteo**

Nastav:
- Stanice: `stodulky` (nebo tvoje stanice)
- Model: `MASTER` (nebo vybraný model)

### 3. Přidej Lovelace Kartu

**Lovelace editor** → **Přidat kartu** → **Manual**

```yaml
type: custom:pocasimeteo-card
entity: weather.pocasimeteo_stodulky
```

## 🆘 Chyby

### "Home Assistant config not found"

```
❌ Chyba: Nelze nalézt Home Assistant config na /config
```

- Ujisti se, že běžíš skript v Home Assistantovi
- Ne na PC s Home Assistantem!

### "Nelze stáhnout z GitHubu"

```
❌ Chyba: Nelze stáhnout integraci z GitHubu
```

- Zkontroluj připojení k internetu
- Zkontroluj, že GitHub je dostupný

### "Entity se neobjeví"

1. Restartuj Home Assistant (F5 browser + `ha core restart`)
2. Počkej 3 minuty
3. Zkontroluj v **Vývojář** → **Stavy** → hledej `pocasimeteo`

## 📞 Pomoc

- GitHub: https://github.com/glaverCZ/pocasimeteo_ha
- Issues: https://github.com/glaverCZ/pocasimeteo_ha/issues

## 🎁 Co Dál?

Pokud chceš:

- **Více stanic**: Spusť skript znovu s jinou stanicí
- **Více modelů**: V Home Assistantovi přidej více integrací
- **Automatické výběry**: Nastav `best_match_temperature_entity`

## 💡 Technické Detaily

Skript si stáhne:

```
https://raw.githubusercontent.com/glaverCZ/pocasimeteo_ha/main/custom_components/pocasimeteo/*
https://raw.githubusercontent.com/glaverCZ/pocasimeteo_ha/main/www/pocasimeteo-card.js
https://raw.githubusercontent.com/glaverCZ/pocasimeteo_ha/main/www/icons/*.png
```

A nainstaluje přímo do `/config/`.

## ✨ Hotovo!

Měl by jsi mít PočasíMeteo v provozu. Vychutnej si! 🌤️

---

**Verze**: 1.0
**Poslední aktualizace**: 2024-11-23
**Autor**: GlavER CZ
