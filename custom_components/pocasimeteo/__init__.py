"""The PočasíMeteo integration."""
import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import PocasimeteoDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.WEATHER]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the PočasíMeteo component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PočasíMeteo from a config entry."""
    _LOGGER.info("▶ Setting up PočasíMeteo integration")

    # Copy card to www/community/pocasimeteo-card/ for automatic loading
    # This runs once per config entry setup
    try:
        import shutil

        source_path = Path(__file__).parent / "www" / "pocasimeteo-card.js"
        dest_dir = Path(hass.config.path("www/community/pocasimeteo-card"))
        dest_path = dest_dir / "pocasimeteo-card.js"

        _LOGGER.info("→ Checking card source: %s", source_path)

        # Create directory if it doesn't exist
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Copy file if source exists
        if source_path.exists():
            shutil.copy2(source_path, dest_path)
            _LOGGER.info("✓ PočasíMeteo: Card copied to %s", dest_path)
        else:
            _LOGGER.error("✗ PočasíMeteo: Card source NOT FOUND at %s", source_path)

        # Add JS URL to frontend - this loads the card automatically
        hass.components.frontend.add_extra_js_url(
            hass, "/hacsfiles/pocasimeteo-card/pocasimeteo-card.js"
        )
        _LOGGER.info("✓ PočasíMeteo: Frontend JS registered")

    except Exception as err:
        _LOGGER.error("✗ Failed to setup PočasíMeteo frontend: %s", err, exc_info=True)

    try:
        _LOGGER.info("→ Creating coordinator")
        coordinator = PocasimeteoDataUpdateCoordinator(hass, entry)

        _LOGGER.info("→ Running first refresh")
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.info("✓ First refresh completed")

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = coordinator

        _LOGGER.info("→ Setting up platforms: %s", PLATFORMS)
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        _LOGGER.info("✓ PočasíMeteo setup completed successfully")

        # Listen to options updates
        entry.async_on_unload(entry.add_update_listener(async_update_entry))

        return True
    except Exception as err:
        _LOGGER.error("✗ Error setting up PočasíMeteo: %s", err, exc_info=True)
        raise


async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok
