from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, DEFAULT_NAME
from .sources import AwigoClient

class GeorgsmarthuetteConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            camera_url = (user_input.get("camera_url") or "").strip()
            if camera_url and not (camera_url.startswith("http://") or camera_url.startswith("https://")):
                errors["camera_url"] = "invalid_url"

            if not errors:
                try:
                    session = async_get_clientsession(self.hass)
                    awigo = AwigoClient(session)
                    await awigo.resolve_address(
                        user_input.get("awigo_street", ""),
                        user_input.get("awigo_house_number", ""),
                        user_input.get("awigo_house_number_suffix", ""),
                        user_input.get("awigo_city", "Georgsmarienhütte"),
                    )
                except ValueError:
                    errors["awigo_street"] = "address_not_found"
                except Exception:  # noqa: BLE001 - network failure during config-flow validation
                    errors["base"] = "cannot_connect"

            if not errors:
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
