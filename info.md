# PočasíMeteo Card

Pokročilá Lovelace custom card pro zobrazení meteorologických předpovědí z PočasíMeteo.cz s podporou více modelů.

## Funkce

- **7 meteorologických modelů:** MASTER, ALADIN, ICONDE, ICONEU, YRno, GFS, WRF
- **Automatický výběr nejpřesnějšího modelu** podle referenčních senzorů
- **Srovnání s reálnými hodnotami** (teplota, vlhkost, vítr)
- **Pokročilé vizualizace** s 125+ PNG ikonami počasí
- **Přizpůsobitelné pořadí dlaždic**

## Požadavky

Tato card vyžaduje **PočasíMeteo integraci** (backend):
1. HACS → Integrations → Vyhledejte "PočasíMeteo"
2. Download a restartujte Home Assistant

## Použití

```yaml
type: custom:pocasimeteo-card
entity: weather.pocasimeteo_praha_6_ruzyne
```

### Pokročilá konfigurace

```yaml
type: custom:pocasimeteo-card
entity: weather.pocasimeteo_praha_6_ruzyne
# Automatický výběr nejpřesnějšího modelu
best_match_temperature_entity: sensor.venku_teplota
# Zobrazení rozdílu oproti reference
temperature_entity: sensor.venku_teplota
humidity_entity: sensor.venku_vlhkost
wind_speed_entity: sensor.venku_vitr
```

## Dokumentace

Kompletní dokumentace: [GitHub](https://github.com/glaverCZ/pocasimeteo)
