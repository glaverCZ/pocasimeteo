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

    # Install Lovelace card to www/community/pocasimeteo-card/
    # HACS doesn't copy www/ folder from integrations, so we download it from GitHub
    try:
        import aiohttp
        import shutil

        dest_dir = Path(hass.config.path("www/community/pocasimeteo-card"))
        dest_path = dest_dir / "pocasimeteo-card.js"

        # Create directory if it doesn't exist
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Try to find card locally first (for manual installations)
        local_card = Path(__file__).parent / "www" / "pocasimeteo-card.js"

        if local_card.exists():
            _LOGGER.info("→ Found card locally, copying...")
            shutil.copy2(local_card, dest_path)
            _LOGGER.info("✓ Card copied from local installation")
        elif not dest_path.exists():
            # Download card from GitHub
            _LOGGER.info("→ Card not found locally, downloading from GitHub...")
            card_url = "https://raw.githubusercontent.com/glaverCZ/pocasimeteo/main/custom_components/pocasimeteo/www/pocasimeteo-card.js"

            async with aiohttp.ClientSession() as session:
                async with session.get(card_url) as response:
                    if response.status == 200:
                        content = await response.read()
                        dest_path.write_bytes(content)
                        _LOGGER.info("✓ Card downloaded from GitHub (%d bytes)", len(content))
                    else:
                        _LOGGER.error("✗ Failed to download card: HTTP %d", response.status)
        else:
            _LOGGER.info("✓ Card already exists at %s", dest_path)

        # Register card with frontend
        hass.components.frontend.add_extra_js_url(
            hass, "/hacsfiles/pocasimeteo-card/pocasimeteo-card.js"
        )
        _LOGGER.info("✓ PočasíMeteo: Card registered at /hacsfiles/pocasimeteo-card/pocasimeteo-card.js")

    except Exception as err:
        _LOGGER.error("✗ Failed to setup card: %s", err, exc_info=True)

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
