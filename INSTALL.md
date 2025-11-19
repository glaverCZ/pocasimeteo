# Instalace PočasíMeteo - Kompletní Průvodce

## 🚀 3 Kroky - Rychlá Instalace

### Krok 1: Kopírujte Soubory na Home Assistant

```bash
# Připojte se na Home Assistant přes SSH
ssh root@10.0.0.91

# Vytvořte adresáře
mkdir -p /config/custom_components/pocasimeteo
mkdir -p /config/www/community/pocasimeteo-card
mkdir -p /config/www/local/icons

# Zkopírujte soubory
# (Soubory si stáhněte ze: C:\Users\lkrasa\_DEV\ha\pocasimeteo_ha_fixed\)

# Pak nakopírujte:
# - Všechny .py soubory do /config/custom_components/pocasimeteo/
# - pocasimeteo-card.js do /config/www/community/pocasimeteo-card/
# - Všechny PNG ikony do /config/www/local/icons/
```

### Krok 2: Nakonfigurujte Lovelace

Otevřete `/config/configuration.yaml` a přidejte na konec:

```yaml
lovelace:
  resources:
    - url: /local/community/pocasimeteo-card/pocasimeteo-card.js
      type: module
```

Uložte a restartujte Home Assistant.

### Krok 3: Restartujte a Přidejte Integraci

1. **Restartujte Home Assistant:**
   - Nastavení → Systém → Restartovat Home Assistant
   - Čekejte 2-3 minuty

2. **Přidejte integraci:**
   - Nastavení → Zařízení a služby → Vytvořit integraci
   - Vyhledejte: "PočasíMeteo"
   - Vyberte stanici (Praha 6 - Ruzyně)
   - Vyberte model (MASTER, ALADIN, atd.)

3. **Přidejte Lovelace kartu:**
   - Lovelace editor (nahoře vpravo: ⋮ → Editovat Lovelace)
   - Přidejte novou kartu
   - Typ: `custom:pocasimeteo-card`
   - Entity: `weather.pocasimeteo_praha_6_ruzyne` (nebo vaše entity)

---

## 📦 Podrobná Instalace (Windows + SSH)

### Možnost 1: Přes Git (Doporučeno)

```powershell
# V PowerShell na Windows
$HA_IP = "10.0.0.91"
$HA_USER = "root"

# Připojte se na Home Assistant
ssh $HA_USER@$HA_IP

# Na Home Assistant spusťte:
cd /config/custom_components
git clone https://github.com/glaverCZ/pocasimeteo_ha pocasimeteo

# Zkopírujte custom card a ikony
cp pocasimeteo/www/pocasimeteo-card.js /config/www/community/pocasimeteo-card/
cp pocasimeteo/www/icons/*.png /config/www/local/icons/

# Restartujte
ha core restart
```

### Možnost 2: Manuálně přes SCP

```powershell
# V PowerShell na vašem PC

$HA_IP = "10.0.0.91"
$HA_USER = "root"
$LOCAL_PATH = "C:\Users\lkrasa\_DEV\ha\pocasimeteo_ha_fixed"

# 1. Vytvořte adresáře
ssh $HA_USER@$HA_IP "mkdir -p /config/custom_components/pocasimeteo && mkdir -p /config/www/community/pocasimeteo-card && mkdir -p /config/www/local/icons"

# 2. Kopírujte Python soubory
scp "$LOCAL_PATH\custom_components\pocasimeteo\__init__.py" "${HA_USER}@${HA_IP}:/config/custom_components/pocasimeteo/"
scp "$LOCAL_PATH\custom_components\pocasimeteo\coordinator.py" "${HA_USER}@${HA_IP}:/config/custom_components/pocasimeteo/"
scp "$LOCAL_PATH\custom_components\pocasimeteo\weather.py" "${HA_USER}@${HA_IP}:/config/custom_components/pocasimeteo/"
scp "$LOCAL_PATH\custom_components\pocasimeteo\const.py" "${HA_USER}@${HA_IP}:/config/custom_components/pocasimeteo/"
scp "$LOCAL_PATH\custom_components\pocasimeteo\config_flow.py" "${HA_USER}@${HA_IP}:/config/custom_components/pocasimeteo/"
scp "$LOCAL_PATH\custom_components\pocasimeteo\manifest.json" "${HA_USER}@${HA_IP}:/config/custom_components/pocasimeteo/"

# 3. Kopírujte custom card
scp "$LOCAL_PATH\www\pocasimeteo-card.js" "${HA_USER}@${HA_IP}:/config/www/community/pocasimeteo-card/"

# 4. Kopírujte ikony
scp "$LOCAL_PATH\www\icons\*.png" "${HA_USER}@${HA_IP}:/config/www/local/icons/"

# 5. Ověřte
ssh $HA_USER@$HA_IP "ls /config/custom_components/pocasimeteo/ && echo '---' && ls /config/www/local/icons/ | wc -l"
```

---

## ⚙️ Konfigurace Lovelace

### Metoda 1: Úprava configuration.yaml

```bash
# Připojte se na Home Assistant
ssh root@10.0.0.91

# Otevřete editor (pokud máte File Editor add-on)
# Nebo upravte pomocí nano:
nano /config/configuration.yaml

# Přidejte na konec:
lovelace:
  resources:
    - url: /local/community/pocasimeteo-card/pocasimeteo-card.js
      type: module

# Uložte: Ctrl+O → Enter → Ctrl+X
```

### Metoda 2: Lovelace UI (pokud je dostupný)

- Nastavení → Automatizace a scény → Lovelace
- Klikněte na três tečky (⋮)
- Vyberte "Resources" nebo "Lovelace resources"
- Přidejte nový prostředek:
  ```
  URL: /local/community/pocasimeteo-card/pocasimeteo-card.js
  Typ: JavaScript Module
  ```

---

## 🔍 Ověření Instalace

### 1. Soubory na Místě?

```bash
ssh root@10.0.0.91

# Integrace
ls /config/custom_components/pocasimeteo/
# Měly by být: __init__.py coordinator.py weather.py const.py config_flow.py manifest.json

# Custom card
ls -l /config/www/community/pocasimeteo-card/pocasimeteo-card.js
# Měl by existovat

# Ikony
ls /config/www/local/icons/ | head -5
# Měly by být: a01d.png a01n.png a02d.png ...
```

### 2. Configuration.yaml Je Správná?

```bash
ssh root@10.0.0.91
grep -A 3 "lovelace:" /config/configuration.yaml
```

Mělo by vyjít:
```yaml
lovelace:
  resources:
    - url: /local/community/pocasimeteo-card/pocasimeteo-card.js
      type: module
```

### 3. Python Soubory Jsou OK?

```bash
ssh root@10.0.0.91
python3 -m py_compile /config/custom_components/pocasimeteo/*.py
echo "✅ Syntaxe OK"
```

### 4. Home Assistant Logy

```bash
ssh root@10.0.0.91
tail -20 /config/home-assistant.log | grep pocasimeteo
```

Měly by obsahovat:
```
▶ Setting up PočasíMeteo integration
→ Creating coordinator
✓ PočasíMeteo setup completed successfully
```

---

## 🚦 Post-Instalace

### 1. Ověřte Entity

V Home Assistant:
- **Vývojář → Stavy**
- Vyhledejte: `weather.pocasimeteo`

Měly by existovat:
- `weather.pocasimeteo_praha_6_ruzyne` (primární)
- `weather.pocasimeteo_praha_6_ruzyne_aladin` (model)
- atd.

### 2. Ověřte Custom Card

V Home Assistant:
- Otevřete **F12 (Developer Tools)**
- Jděte na **Console**
- Měly by být zprávy s `🎨`:
  ```
  🎨 Loading PocasimeteoCard...
  🎨 PocasimeteoCard registered successfully
  🎨 Card registered in Lovelace
  ```

### 3. Přidejte Kartu do Lovelace

- Otevřete Lovelace editor (nahoře vpravo: ⋮ → Editovat Lovelace)
- Klikněte: **Přidat kartu**
- Vyberte: **Manual** (ručně)
- Vložte:
  ```yaml
  type: custom:pocasimeteo-card
  entity: weather.pocasimeteo_praha_6_ruzyne
  default_model: MASTER
  ```

---

## ❌ Problémy?

Pokud máte problémy, přečtěte si [TROUBLESHOOT.md](TROUBLESHOOT.md).

Nejčastější problémy:

1. **Karta není vidět**: Chybí prostředek v `configuration.yaml`
2. **Data se neaktualizují**: Refresh URL se nevolá (zkontrolujte logy)
3. **Entity neexistuje**: Integrace se nenačetla (Python syntax error?)

---

## 📞 Podpora

Máte otázku?

1. Přečtěte si [README.md](README.md) a [TROUBLESHOOT.md](TROUBLESHOOT.md)
2. Zkontrolujte Home Assistant logy
3. Otevřete GitHub Issue s detaily

GitHub: https://github.com/glaverCZ/pocasimeteo_ha/issues

---

**Zbývá ještě něco? Kontaktujte mě!** 🚀
