#FEMA IPAWS Monitor integration
import logging
import os
from homeassistant.components.frontend import async_register_built_in_panel

DOMAIN = "ipaws_monitor"
_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    #Set up the ipaws_monitor component
    
    # Static directory path mapping
    local_www = hass.config.path("custom_components", DOMAIN, "www")
    
    if os.path.isdir(local_www):
        # 1. Host the www folder at /ipaws_monitor_local/
        hass.http.register_static_path(
            "/ipaws_monitor_local", local_www, cache_headers=False
        )
        
        # 2. Inject the card script into the frontend ecosystem dynamically
        hass.components.frontend.async_register_built_in_panel(
            None,
            None,
            None,
            update_frontend_url="/ipaws_monitor_local/ipaws-card.js"
        )
        # Note: In modern HA versions, alternative frontend registration is handled via:
        # hass.data["frontend_extra_module_url"].add("/ipaws_monitor_local/ipaws-card.js")
        if "frontend_extra_module_url" not in hass.data:
            hass.data["frontend_extra_module_url"] = set()
        hass.data["frontend_extra_module_url"].add("/ipaws_monitor_local/ipaws-card.js")

    return True