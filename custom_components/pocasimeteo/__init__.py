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
    # Install Lovelace card to www/community/pocasimeteo-card/
    # HACS doesn't copy www/ folder from integrations, so we download it from GitHub
    # This runs on every HA restart to ensure card is always available
    try:
        import aiohttp
        import shutil

        _LOGGER.warning("=" * 80)
        _LOGGER.warning("POCASIMETEO CARD INSTALLATION START")
        _LOGGER.warning("=" * 80)

        # Determine paths
        config_dir = hass.config.path()
        _LOGGER.warning("→ Config directory: %s", config_dir)

        dest_dir = Path(hass.config.path("www/community/pocasimeteo-card"))
        _LOGGER.warning("→ Target directory: %s", dest_dir)

        dest_path = dest_dir / "pocasimeteo-card.js"
        _LOGGER.warning("→ Target file: %s", dest_path)

        # Create directory
        _LOGGER.warning("→ Creating directory...")
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            _LOGGER.warning("✓ Directory created/verified: %s", dest_dir)
        except Exception as mkdir_err:
            _LOGGER.error("✗ Failed to create directory: %s", mkdir_err, exc_info=True)
            raise

        # Try to find card locally first (for manual installations)
        local_card = Path(__file__).parent / "www" / "pocasimeteo-card.js"
        _LOGGER.warning("→ Checking for local card: %s", local_card)
        _LOGGER.warning("→ Local card exists: %s", local_card.exists())

        if local_card.exists():
            _LOGGER.warning("→ Found card locally, copying...")
            try:
                shutil.copy2(local_card, dest_path)
                _LOGGER.warning("✓ Card copied from local installation")
                _LOGGER.warning("  Source: %s", local_card)
                _LOGGER.warning("  Dest: %s", dest_path)
                _LOGGER.warning("  Size: %d bytes", dest_path.stat().st_size)
            except Exception as copy_err:
                _LOGGER.error("✗ Failed to copy local card: %s", copy_err, exc_info=True)
                raise
        elif not dest_path.exists():
            # Download card from GitHub
            card_url = "https://raw.githubusercontent.com/glaverCZ/pocasimeteo/main/custom_components/pocasimeteo/www/pocasimeteo-card.js"
            _LOGGER.warning("→ Card not found locally, downloading from GitHub...")
            _LOGGER.warning("  URL: %s", card_url)

            try:
                async with aiohttp.ClientSession() as session:
                    _LOGGER.warning("→ Sending HTTP request...")
                    async with session.get(card_url) as response:
                        _LOGGER.warning("  HTTP Status: %d", response.status)
                        if response.status == 200:
                            content = await response.read()
                            _LOGGER.warning("  Downloaded: %d bytes", len(content))
                            dest_path.write_bytes(content)
                            _LOGGER.warning("✓ Card downloaded and saved to: %s", dest_path)
                            _LOGGER.warning("  File size: %d bytes", dest_path.stat().st_size)
                        else:
                            _LOGGER.error("✗ Failed to download card: HTTP %d", response.status)
                            _LOGGER.error("  Response: %s", await response.text())
            except Exception as download_err:
                _LOGGER.error("✗ Failed during download: %s", download_err, exc_info=True)
                raise
        else:
            _LOGGER.warning("✓ Card already exists at %s", dest_path)
            _LOGGER.warning("  Size: %d bytes", dest_path.stat().st_size)

        # Verify file exists before registering
        if not dest_path.exists():
            _LOGGER.error("✗ CRITICAL: Card file does NOT exist after installation!")
            _LOGGER.error("  Expected at: %s", dest_path)
        else:
            _LOGGER.warning("✓ Card file verified: %s (%d bytes)", dest_path, dest_path.stat().st_size)

        # Register card with frontend
        _LOGGER.warning("→ Registering card with frontend...")
        hass.components.frontend.add_extra_js_url(
            hass, "/hacsfiles/pocasimeteo-card/pocasimeteo-card.js"
        )
        _LOGGER.warning("✓ Card registered at /hacsfiles/pocasimeteo-card/pocasimeteo-card.js")

        _LOGGER.warning("=" * 80)
        _LOGGER.warning("POCASIMETEO CARD INSTALLATION COMPLETE")
        _LOGGER.warning("=" * 80)

    except Exception as err:
        _LOGGER.error("=" * 80)
        _LOGGER.error("POCASIMETEO CARD INSTALLATION FAILED!")
        _LOGGER.error("=" * 80)
        _LOGGER.error("✗ Error: %s", err, exc_info=True)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PočasíMeteo from a config entry."""
    _LOGGER.info("▶ Setting up PočasíMeteo integration")

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
