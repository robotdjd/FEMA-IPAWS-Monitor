"""Config flow for FEMA IPAWS Monitor integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

DOMAIN = "ipaws_monitor"

_LOGGER = logging.getLogger(__name__)

class IpawsMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FEMA IPAWS Monitor."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Clean up the input string into a list of strings
            fips_list = [x.strip() for x in user_input["fips_codes"].split(",") if x.strip()]
            
            if not fips_list:
                errors["base"] = "invalid_fips"
            else:
                return self.async_create_entry(
                    title="FEMA IPAWS Monitor", 
                    data={"fips_codes": fips_list}
                )

        # Default configuration values for the UI prompt
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "fips_codes", 
                        default="039049, 039041"
                    ): str,
                }
            ),
            errors=errors,
        )