# Troubleshoot - Řešení Problémů

## ❌ Lovelace Karta Nefunguje

### Symptom: "Custom element not found: pocasimeteo-card"

**Příčiny (v pořadí pravděpodobnosti):**

1. **Prostředek není přidaný v configuration.yaml**
   ```yaml
   # Zkontrolujte /config/configuration.yaml
   lovelace:
     resources:
       - url: /local/community/pocasimeteo-card/pocasimeteo-card.js
         type: module
   ```

2. **Soubor nemá správné oprávnění**
   ```bash
   ssh root@10.0.0.91
   ls -la /config/www/community/pocasimeteo-card/pocasimeteo-card.js
   # Mělo by být -rw-r--r-- a file by měl existovat
   ```

3. **Home Assistant nebyl restartován**
   - Nastavení → Systém → Restartovat Home Assistant
   - Čekejte 2-3 minuty

4. **Browser cache není vymazaný**
   - Ctrl+Shift+R (hard refresh)
   - Nebo: F12 → Application → Clear Storage → Clear All

### Debug

Otevřete **F12 → Console** a hledejte:

```javascript
// ✅ Mělo by být vidět:
🎨 Loading PocasimeteoCard...
🎨 PocasimeteoCard constructor called
🎨 PocasimeteoCard registered successfully
🎨 Card registered in Lovelace

// ❌ Pokud vidíte error:
Failed to load resource: ...pocasimeteo-card.js (404 Not Found)
// = Cesta je špatná
```

---

## ❌ Data se Neaktualizují

### Symptom: Teplota se nemění, data jsou stará

**Příčiny:**

1. **Refresh URL se nevolá**
   ```bash
   # Zkontrolujte logy
   ssh root@10.0.0.91
   grep "Refresh URL" /config/home-assistant.log | tail -10
   ```

   Mělo by být:
   ```
   → Calling refresh URL: https://ext.pocasimeteo.cz/...
   ✓ Refresh URL called successfully (HTTP 200)
   ```

2. **API je nedostupný**
   ```bash
   # Test z Home Assistant
   ssh root@10.0.0.91
   curl -v https://ext.pocasimeteo.cz/praha-6-ruzyne/predpoved/
   ```

   Mělo by vrátit HTTP 200

3. **Integrace se neinicializuje**
   ```bash
   ssh root@10.0.0.91
   grep "pocasimeteo" /config/home-assistant.log | head -20
   ```

   Mělo by být:
   ```
   ▶ Setting up PočasíMeteo integration
   → Creating coordinator
   ✓ PočasíMeteo setup completed successfully
   ```

### Řešení

```bash
# 1. Restartujte Home Assistant
ssh root@10.0.0.91
ha core restart

# 2. Počkejte 2-3 minuty

# 3. Zkontrolujte logy
tail -30 /config/home-assistant.log | grep pocasimeteo

# 4. Zkontrolujte Vývojář → Stavy
# Měla by existovat: weather.pocasimeteo_praha_6_ruzyne
# A měla by mít atributy: temperature, humidity, pressure, ...
```

---

## ❌ Entita Neexistuje

### Symptom: Vývojář → Stavy - žádná weather.pocasimeteo_*

**Příčiny:**

1. **Integrace není nainstalovaná**
   ```bash
   ssh root@10.0.0.91
   ls /config/custom_components/pocasimeteo/
   # Měly by být: __init__.py coordinator.py weather.py ...
   ```

2. **Python syntax error**
   ```bash
   ssh root@10.0.0.91
   python3 -m py_compile /config/custom_components/pocasimeteo/*.py
   # Pokud je chyba, uvede ji zde
   ```

3. **Integrace není v Home Assistant**
   - Nastavení → Zařízení a služby → Integrace
   - Měla by být "PočasíMeteo"
   - Pokud není: Vytvořit integraci → Vyhledat PočasíMeteo

### Řešení

```bash
# 1. Zkopírujte soubory
ssh root@10.0.0.91
mkdir -p /config/custom_components/pocasimeteo
cd pocasimeteo_ha_fixed
cp custom_components/pocasimeteo/* /config/custom_components/pocasimeteo/

# 2. Ověřte syntaxi
python3 -m py_compile /config/custom_components/pocasimeteo/*.py

# 3. Restartujte
ha core restart

# 4. Přidejte integraci
# Nastavení → Zařízení a služby → Vytvořit integraci
# Vyhledejte: PočasíMeteo
```

---

## ❌ Karta Vidí Entitu, Ale Bez Dat

### Symptom: Karta se zobrazuje, ale teplota je "--"

**Příčiny:**

1. **Entita nemá atributy**
   ```bash
   # Zkontrolujte atributy v Vývojář → Stavy
   # Měly by být: temperature, humidity, pressure, wind_speed, ...
   ```

2. **Špatné pojmenování atributů**
   - Zkontrolujte, zda jsou názvy atributů správné

3. **Koordinátor se neinicializuje**
   ```bash
   tail -50 /config/home-assistant.log | grep -A 5 "Creating coordinator"
   ```

### Debug v Kartě

Otevřete F12 → Console a vyhledejte:

```javascript
// ✅ Mělo by být:
🎨 Entity: weather.pocasimeteo_praha_6_ruzyne State: FOUND
🎨 Entity attributes: ["temperature", "humidity", "pressure", "wind_speed", ...]
🎨 updateContent() completed successfully

// ❌ Pokud je chyba:
🎨 Entity: weather.pocasimeteo_praha_6_ruzyne State: NOT FOUND
// = Entita neexistuje v Home Assistant
```

---

## ❌ PNG Ikony se Neloadují

### Symptom: Místo ikony je emoji

**Příčiny:**

1. **Ikony nejsou na správném místě**
   ```bash
   ssh root@10.0.0.91
   ls /config/www/local/icons/
   # Měly by být: a01d.png, a02d.png, a10.png, ...
   ```

2. **Chybí konkrétní ikona**
   ```javascript
   // V Console uvidíte:
   🎨 Icon not found: a10 - using emoji
   // = Soubor a10.png neexistuje
   ```

### Řešení

```bash
# 1. Zkopírujte ikony
ssh root@10.0.0.91
mkdir -p /config/www/local/icons
cp pocasimeteo_ha_fixed/www/icons/*.png /config/www/local/icons/

# 2. Ověřte
ls /config/www/local/icons/ | wc -l
# Mělo by být: cca 125

# 3. Hard refresh
# V Home Assistant: Ctrl+Shift+R
```

---

## ❌ YAML Syntax Error

### Symptom: Chyba v configuration.yaml

**Řešení:**

```yaml
# ❌ ŠPATNĚ:
lovelace:
resources:
  - url: /local/community/pocasimeteo-card/pocasimeteo-card.js
  type: module

# ✅ SPRÁVNĚ:
lovelace:
  resources:
    - url: /local/community/pocasimeteo-card/pocasimeteo-card.js
      type: module
```

Pozor na odsazení! YAML je citlivý na mezery.

---

## 📋 Checklist - Co Zkontrolovat

```
☐ Integrace je v /config/custom_components/pocasimeteo/
  ☐ __init__.py ✓
  ☐ coordinator.py ✓
  ☐ weather.py ✓
  ☐ const.py ✓
  ☐ config_flow.py ✓
  ☐ manifest.json ✓

☐ Custom card je v /config/www/community/pocasimeteo-card/
  ☐ pocasimeteo-card.js ✓

☐ Ikony jsou v /config/www/local/icons/
  ☐ a01d.png, a02d.png, ... ✓

☐ Lovelace prostředek je v configuration.yaml
  ☐ lovelace: ✓
  ☐   resources: ✓
  ☐     - url: /local/community/pocasimeteo-card/pocasimeteo-card.js ✓
  ☐       type: module ✓

☐ Home Assistant byl restartován
  ☐ Plný restart (ne jen frontend) ✓
  ☐ Čekání 2-3 minuty ✓

☐ Integrace je v Home Assistant
  ☐ Nastavení → Zařízení a služby → Integrace → PočasíMeteo ✓

☐ Entity existují
  ☐ Vývojář → Stavy → weather.pocasimeteo_* ✓

☐ Browser cache je vymazaný
  ☐ Ctrl+Shift+R ✓
  ☐ F12 → Application → Clear Storage ✓
```

---

## 🆘 Co Udělat Pokud Nic Nefunguje

1. **Sbírejte informace:**
   ```bash
   # Na Home Assistant
   ssh root@10.0.0.91

   # Logy
   tail -100 /config/home-assistant.log | grep pocasimeteo > /tmp/ha_logs.txt

   # Kontrola souborů
   ls -la /config/custom_components/pocasimeteo/ > /tmp/files.txt
   ls -la /config/www/community/pocasimeteo-card/ >> /tmp/files.txt
   ls /config/www/local/icons/ | wc -l >> /tmp/files.txt

   # Zobrazit soubory
   cat /tmp/ha_logs.txt
   cat /tmp/files.txt
   ```

2. **Otevřete Browser Console:**
   - F12 → Console
   - Zkopírujte všechny `🎨` zprávy

3. **Otevřete GitHub Issue:**
   - https://github.com/glaverCZ/pocasimeteo_ha/issues
   - Přiložte logy a screenshot z Console
   - Popište, co přesně vidíte/vidíte ne

---

**Snad to pomůže!** ☀️
