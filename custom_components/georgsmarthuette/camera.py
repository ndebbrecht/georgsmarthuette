from __future__ import annotations

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .sources import GMH_CAMERAS

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    session = async_get_clientsession(hass)
    cameras = [GeorgsmarthuetteStillImageCamera(key, url, session) for key, url in GMH_CAMERAS.items()]
    custom_camera_url = entry.data.get("camera_url")
    if custom_camera_url:
        cameras.append(GeorgsmarthuetteStillImageCamera("custom", custom_camera_url, session))
    async_add_entities(cameras)

class GeorgsmarthuetteStillImageCamera(Camera):
    def __init__(self, key: str, image_url: str, session) -> None:
        super().__init__()
        self._attr_name = f"GMH Kamera {key.replace('_', ' ')}"
        self._attr_unique_id = f"georgsmarthuette_camera_{key}"
        self._image_url = image_url
        self._session = session

    async def async_camera_image(self, width: int | None = None, height: int | None = None) -> bytes | None:
        async with self._session.get(self._image_url, headers={"User-Agent": "Georgsmarthuette/0.1"}) as response:
            if response.status >= 400:
                return None
            return await response.read()
