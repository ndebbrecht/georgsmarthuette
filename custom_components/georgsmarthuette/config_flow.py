from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries

from .const import DOMAIN, DEFAULT_NAME

class GeorgsmarthuetteConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            await self.async_set_unique_id("gmh_public_data")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=DEFAULT_NAME, data=user_input)

        schema = vol.Schema({
            vol.Optional("awigo_city", default="Georgsmarienhütte"): str,
            vol.Required("awigo_street"): str,
            vol.Required("awigo_house_number"): str,
            vol.Optional("awigo_house_number_suffix", default=""): str,
            vol.Optional("latitude", default=52.2020): float,
            vol.Optional("longitude", default=8.0440): float,
            vol.Optional("camera_url", default=""): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
