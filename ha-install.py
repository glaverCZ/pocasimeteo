#!/usr/bin/env python3
"""
PočasíMeteo - Automatická instalace v Home Assistantovi
Stáhne vše přímo z GitHubu a nainstaluje.

Spustit: python3 ha-install.py [stanice] [model]

Příklady:
  python3 ha-install.py                          # Interaktivní
  python3 ha-install.py stodulky                 # Default model
  python3 ha-install.py stodulky ALADIN          # Custom model
"""

import os
import sys
import shutil
import json
import zipfile
import tempfile
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError

# Barvy
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

# GitHub Repository
GITHUB_REPO = "https://raw.githubusercontent.com/glaverCZ/pocasimeteo_ha/main"

# Cesty v Home Assistantovi
HA_CONFIG = Path("/config")
CUSTOM_COMPONENTS = HA_CONFIG / "custom_components" / "pocasimeteo"
WWW_ICONS = HA_CONFIG / "www" / "icons"
WWW_CARD = HA_CONFIG / "www" / "pocasimeteo-card.js"

def print_status(message, status_type="info"):
    """Vytiskni status zprávu"""
    symbols = {
        "info": f"{BLUE}ℹ️{RESET}",
        "success": f"{GREEN}✅{RESET}",
        "error": f"{RED}❌{RESET}",
        "warning": f"{YELLOW}⚠️{RESET}",
    }
    print(f"{symbols.get(status_type, '')} {message}")

def check_ha_environment():
    """Zkontroluj, že jsme v Home Assistantovi"""
    if not HA_CONFIG.exists():
        print_status("Chyba: Nelze nalézt Home Assistant config na /config", "error")
        return False

    print_status("Home Assistant nalezen na /config", "success")
    return True

def download_file(url, destination):
    """Stáhni soubor z GitHubu"""
    try:
        print_status(f"Stahuji: {url.split('/')[-1]}...", "info")
        response = urlopen(url, timeout=10)
        destination.parent.mkdir(parents=True, exist_ok=True)

        with open(destination, 'wb') as f:
            f.write(response.read())

        return True
    except Exception as e:
        print_status(f"Chyba při stahování: {e}", "error")
        return False

def download_integration():
    """Stáhni integraci z GitHubu"""
    print_status("Stahuji integraci z GitHubu...", "info")

    files = [
        "__init__.py",
        "coordinator.py",
        "weather.py",
        "const.py",
        "config_flow.py",
        "manifest.json"
    ]

    CUSTOM_COMPONENTS.mkdir(parents=True, exist_ok=True)

    for file in files:
        url = f"{GITHUB_REPO}/custom_components/pocasimeteo/{file}"
        destination = CUSTOM_COMPONENTS / file

        if not download_file(url, destination):
            return False

        print_status(f"  ↳ {file}", "success")

    return True

def download_card():
    """Stáhni custom card z GitHubu"""
    print_status("Stahuji custom card z GitHubu...", "info")

    url = f"{GITHUB_REPO}/www/pocasimeteo-card.js"
    destination = WWW_CARD

    if download_file(url, destination):
        print_status(f"  ↳ pocasimeteo-card.js", "success")
        return True

    return False

def download_icons():
    """Stáhni ikony z GitHubu"""
    print_status("Stahuji ikony z GitHubu (~130 souborů)...", "info")

    # Seznam všech ikon
    icons = [
        "a01d", "a01n", "a02d", "a02n", "a03d", "a03n", "a04",
        "a05d", "a05n", "a06d", "a06n", "a07d", "a07n", "a08d", "a08n",
        "a09", "a10", "a11", "a12", "a13", "a14", "a15",
        "a20d", "a20n", "a21d", "a21n", "a22", "a23",
        "a24d", "a24n", "a25d", "a25n", "a26d", "a26n",
        "a27d", "a27n", "a28d", "a28n", "a29d", "a29n",
        "a30", "a31", "a32", "a33", "a34",
        "a40d", "a40n", "a41d", "a41n", "a42d", "a42n",
        "a43d", "a43n", "a44d", "a44n", "a45d", "a45n",
        "a46", "a47", "a48", "a49", "a50",
        "a60d", "a60n", "a61d", "a61n", "a62d", "a62n",
        "a63d", "a63n", "a64d", "a64n", "a65d", "a65n",
        "a66d", "a66n", "a67d", "a67n", "a68d", "a68n",
        "a70d", "a70n", "a71d", "a71n", "a72d", "a72n",
        "a73d", "a73n", "a74d", "a74n", "a75d", "a75n",
        "a76d", "a76n", "a77d", "a77n", "a78d", "a78n",
        "clear_day", "clear_night", "cloudy", "fog",
        "mlha", "mlha-dest", "mlha-snih",
        "oblacno_bourka_d", "oblacno_bourka_n",
        "otaznik", "otaznik-OLD",
        "partly_cloudy_day", "partly_cloudy_night",
        "polojasno-destova-prehanka", "polojasno-snezeni",
        "rain", "skoro_zatazeno",
        "skoro_zatazeno_bourka_d", "skoro_zatazeno_bourka_n",
        "skoro_zatazeno_dest_1", "skoro_zatazeno_dest_2",
        "skoro_zatazeno_dest_se_snehem",
        "skoro_zatazeno_snezeni_1", "skoro_zatazeno_snezeni_2",
        "sleet", "snow", "zatazeno_bourka"
    ]

    WWW_ICONS.mkdir(parents=True, exist_ok=True)

    count = 0
    for icon in icons:
        url = f"{GITHUB_REPO}/www/icons/{icon}.png"
        destination = WWW_ICONS / f"{icon}.png"

        if download_file(url, destination):
            count += 1
        else:
            # Ignoruj chyby u jednotlivých ikon, stahni co se dá
            continue

    if count > 0:
        print_status(f"  ↳ Stahovány ikony ({count} souborů)", "success")
        return True

    return False

def extract_integration(zip_path):
    """Extrahuj integraci z ZIP balíčku"""
    print_status("Extrahuju integraci...", "info")

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Najdi custom_components/pocasimeteo v ZIP
            pocasimeteo_files = [f for f in zf.namelist() if 'custom_components/pocasimeteo' in f]

            if not pocasimeteo_files:
                print_status("Chyba: Integrace nenalezena v ZIP", "error")
                return False

            # Vytvoř adresář
            CUSTOM_COMPONENTS.parent.mkdir(parents=True, exist_ok=True)
            CUSTOM_COMPONENTS.mkdir(exist_ok=True)

            # Extrahuj Python soubory
            for file in pocasimeteo_files:
                if file.endswith(('.py', 'manifest.json')):
                    zf.extract(file, path=HA_CONFIG.parent)
                    file_name = Path(file).name
                    print_status(f"  ↳ {file_name}", "success")

            return True

    except Exception as e:
        print_status(f"Chyba při extrakci: {e}", "error")
        return False

def extract_card(zip_path):
    """Extrahuj custom card z ZIP balíčku"""
    print_status("Extrahuju custom card...", "info")

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Najdi pocasimeteo-card.js v ZIP
            card_files = [f for f in zf.namelist() if 'pocasimeteo-card.js' in f]

            if not card_files:
                print_status("Varování: Custom card nenalezen", "warning")
                return False

            WWW_CARD.parent.mkdir(parents=True, exist_ok=True)

            for file in card_files:
                zf.extract(file, path=HA_CONFIG.parent)
                print_status(f"  ↳ pocasimeteo-card.js", "success")
                return True

            return False

    except Exception as e:
        print_status(f"Chyba při extrakci card: {e}", "error")
        return False

def extract_icons(zip_path):
    """Extrahuj ikony z ZIP balíčku"""
    print_status("Extrahuju ikony (~130 souborů)...", "info")

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Najdi PNG ikony v ZIP
            icon_files = [f for f in zf.namelist() if f.endswith('.png')]

            if not icon_files:
                print_status("Varování: Ikony nenalezeny", "warning")
                return False

            WWW_ICONS.mkdir(parents=True, exist_ok=True)

            # Extrahuj všechny PNG soubory
            for file in icon_files:
                zf.extract(file, path=HA_CONFIG.parent)

            print_status(f"  ↳ Nahrány všechny ikony ({len(icon_files)} souborů)", "success")
            return True

    except Exception as e:
        print_status(f"Chyba při extrakci ikon: {e}", "error")
        return False

def update_lovelace_config(station):
    """Aktualizuj configuration.yaml s Lovelace resources"""
    print_status("Aktualizuji configuration.yaml...", "info")

    config_file = HA_CONFIG / "configuration.yaml"

    if not config_file.exists():
        print_status("Varování: configuration.yaml nenalezen", "warning")
        return False

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Zkontroluj, jestli už je tam
        if 'pocasimeteo-card.js' in content:
            print_status("  ↳ Lovelace prostředek již existuje", "success")
            return True

        # Přidej na konec
        lovelace_config = """
lovelace:
  resources:
    - url: /local/pocasimeteo-card.js
      type: module
"""
        with open(config_file, 'a', encoding='utf-8') as f:
            f.write(lovelace_config)

        print_status("  ↳ configuration.yaml aktualizován", "success")
        return True

    except Exception as e:
        print_status(f"Chyba: {e}", "error")
        return False

def verify_installation():
    """Ověř, že vše bylo nainstalováno"""
    print_status("Ověřuji instalaci...", "info")

    checks = [
        ("Integrace", CUSTOM_COMPONENTS / "__init__.py"),
        ("Custom card", WWW_CARD),
        ("Ikony", WWW_ICONS),
    ]

    all_ok = True
    for name, path in checks:
        if path.exists():
            print_status(f"  ✅ {name}", "success")
        else:
            print_status(f"  ❌ {name} CHYBÍ", "error")
            all_ok = False

    return all_ok

def show_next_steps(station, model):
    """Zobraz další kroky"""
    print()
    print(f"{GREEN}╔════════════════════════════════════════════╗{RESET}")
    print(f"{GREEN}║     ✅ INSTALACE ÚSPĚŠNĚ DOKONČENA         ║{RESET}")
    print(f"{GREEN}╚════════════════════════════════════════════╝{RESET}")
    print()
    print(f"{BLUE}📋 CO DĚLAT DÁL:{RESET}")
    print()
    print("1. Restartuj Home Assistant:")
    print("   → Nastavení → Systém → Restartovat Home Assistant")
    print("   → Čekej 2-3 minuty")
    print()
    print("2. Přidej integraci:")
    print("   → Nastavení → Zařízení a služby → Vytvořit integraci")
    print("   → Hledej: PočasíMeteo")
    print(f"   → Stanice: {station}")
    print(f"   → Model: {model}")
    print()
    print("3. Přidej kartu na dashboard:")
    print("   → Lovelace editor → Přidat kartu")
    print("   → Typ: custom:pocasimeteo-card")
    print(f"   → Entity: weather.pocasimeteo_{station}")
    print()
    print(f"{GREEN}Hotovo! 🚀{RESET}")
    print()

def main():
    # Parsuj argumenty - stanice a model jsou volitelné
    station = None
    model = "MASTER"

    if len(sys.argv) > 1:
        station = sys.argv[1].lower().strip()
    if len(sys.argv) > 2:
        model = sys.argv[2].upper().strip()

    # Pokud není zadána stanice, ptej se
    if not station:
        print()
        print(f"{BLUE}╔════════════════════════════════════════════╗{RESET}")
        print(f"{BLUE}║   🌤️  PočasíMeteo - Interaktivní Instalace║{RESET}")
        print(f"{BLUE}╚════════════════════════════════════════════╝{RESET}")
        print()
        station = input("Zadej název stanice (např. stodulky): ").lower().strip()

        if not station:
            print_status("Stanice musí být zadána!", "error")
            sys.exit(1)

        model_input = input("Zadej model (default: MASTER): ").upper().strip()
        if model_input:
            model = model_input

    print()
    print(f"{BLUE}╔════════════════════════════════════════════╗{RESET}")
    print(f"{BLUE}║   🌤️  PočasíMeteo - Instalace v HA        ║{RESET}")
    print(f"{BLUE}║          Stanice: {station:<23} ║{RESET}")
    print(f"{BLUE}║          Model: {model:<27} ║{RESET}")
    print(f"{BLUE}╚════════════════════════════════════════════╝{RESET}")
    print()

    # Zkontroluj prostředí
    if not check_ha_environment():
        sys.exit(1)

    print()

    # Instalace - stahuj z GitHubu
    if not download_integration():
        print_status("Chyba: Nelze stáhnout integraci z GitHubu", "error")
        sys.exit(1)

    if not download_card():
        print_status("Varování: Nelze stáhnout custom card", "warning")

    if not download_icons():
        print_status("Varování: Nelze stáhnout všechny ikony", "warning")

    print()

    # Konfigurace
    update_lovelace_config(station)

    print()

    # Ověření
    if not verify_installation():
        print_status("Některé soubory se nebyly nainstalování!", "error")
        sys.exit(1)

    print()

    # Další kroky
    show_next_steps(station, model)

if __name__ == "__main__":
    main()
