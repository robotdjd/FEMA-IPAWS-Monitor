"""The FEMA IPAWS Monitor integration."""
import logging
import os

DOMAIN = "ipaws_monitor"
PLATFORMS = ["sensor"]
_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    """Set up the IPAWS component configuration hooks."""
    return True

async def async_setup_entry(hass, entry):
    """Set up FEMA IPAWS Monitor from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data.get("fips_codes", [])

    # Forward the setup to the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register Frontend Card assets using the native async call directly
    local_www = hass.config.path("custom_components", DOMAIN, "www")
    if os.path.isdir(local_www):
        # Using the direct web route registrar to prevent object matching errors
        await hass.http.async_register_static_paths([
            type('StaticPath', (object,), {
                "url_path": "/ipaws_monitor_local",
                "path": local_www,
                "cache_headers": False
            })
        ])
        
        if "frontend_extra_module_url" not in hass.data:
            hass.data["frontend_extra_module_url"] = set()
        hass.data["frontend_extra_module_url"].add("/ipaws_monitor_local/ipaws-card.js")

    return True

async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok