# Changelog

Všechny významné změny v tomto projektu budou zdokumentovány v tomto souboru.

Formát je založen na [Keep a Changelog](https://keepachangelog.com/cs/1.0.0/),
a tento projekt dodržuje [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Nevydáno]

### Plánované
- Senzory pro jednotlivé meteorologické parametry
- Možnost konfigurace intervalu aktualizace

## [1.1.0] - 2025-12-29

### Změněno
- Výběr meteorologické stanice nyní umožňuje zadat libovolný text místo výběru z přednastavených stanic
- Uživatel může použít jakoukoliv stanici dostupnou na PočasíMeteo.cz
- Název stanice se automaticky normalizuje (lowercase, mezery → pomlčky)

### Odstraněno
- Přednastavený seznam 4 stanic (Praha-Ruzyně, Brno, Ostrava, Plzeň)
- Zmínky o ČHMÚ z dokumentace

## [1.0.0] - 2025-12-29

### Přidáno
- Iniciální verze integrace PočasíMeteo
- Podpora meteorologických dat z PočasíMeteo.cz
- Podpora 8 meteorologických modelů (MASTER, ALADIN, ICON, GFS, ECMWF, WRF, COSMO, ARPEGE)
- Hodinová předpověď (48 hodin)
- Denní předpověď (7 dní)
- Config flow pro snadnou konfiguraci přes UI
- Česká a anglická lokalizace
- Automatická aktualizace každou hodinu
- Doplňující atributy (oblačnost, pravděpodobnost srážek, sníh, poryvy větru)

[Nevydáno]: https://github.com/glaverCZ/pocasimeteo/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/glaverCZ/pocasimeteo/releases/tag/v1.1.0
[1.0.0]: https://github.com/glaverCZ/pocasimeteo/releases/tag/v1.0.0
