"""The PočasíMeteo integration."""
import logging
from pathlib import Path
import json

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import storage

from .const import DOMAIN
from .coordinator import PocasimeteoDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)
LOVELACE_RESOURCES_STORAGE_KEY = "lovelace_resources"
LOVELACE_RESOURCES_STORAGE_VERSION = 1

PLATFORMS = [Platform.WEATHER]


async def _async_add_lovelace_resource(hass: HomeAssistant) -> None:
    """Add card to Lovelace resources if not already present."""
    try:
        store = storage.Store(hass, LOVELACE_RESOURCES_STORAGE_VERSION, LOVELACE_RESOURCES_STORAGE_KEY)
        data = await store.async_load() or {"items": []}

        card_url = "/hacsfiles/pocasimeteo/pocasimeteo-card.js"

        # Check if resource already exists
        resources = data.get("items", [])
        existing = any(r.get("url") == card_url for r in resources)

        if not existing:
            # Add new resource
            new_resource = {
                "id": f"pocasimeteo_card_{len(resources)}",
                "type": "module",
                "url": card_url
            }
            resources.append(new_resource)
            data["items"] = resources
            await store.async_save(data)
            _LOGGER.info("✓ Added card to Lovelace resources storage")

            # Reload resources
            try:
                await hass.services.async_call(
                    "lovelace",
                    "reload_resources",
                    {},
                    blocking=False,
                )
            except Exception:
                pass
        else:
            _LOGGER.debug("Card already in Lovelace resources")

    except Exception as err:
        _LOGGER.warning("Could not add card to Lovelace resources: %s", err)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the PočasíMeteo component."""
    # Register static path for www folder (supports both HACS and manual installation)
    hass.http.async_register_static_paths([
        {
            "url_path": "/hacsfiles/pocasimeteo",
            "path": str(Path(__file__).parent / "www"),
        }
    ])

    # Also register under /local path for manual installations
    hass.http.async_register_static_paths([
        {
            "url_path": "/local/pocasimeteo",
            "path": str(Path(__file__).parent / "www"),
        }
    ])

    _LOGGER.info("✓ PočasíMeteo frontend resources registered")
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

        # Register Lovelace card resource automatically
        _LOGGER.info("→ Registering Lovelace card")
        try:
            # Add to frontend for immediate availability
            hass.components.frontend.add_extra_js_url(
                hass, "/hacsfiles/pocasimeteo/pocasimeteo-card.js"
            )

            # Add to Lovelace resources storage
            await _async_add_lovelace_resource(hass)

            _LOGGER.info("✓ Lovelace card registered")
        except Exception as card_err:
            _LOGGER.warning("Failed to register Lovelace card: %s", card_err)

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
