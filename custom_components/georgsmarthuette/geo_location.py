from __future__ import annotations

from typing import Any

try:
    from homeassistant.components.geo_location import GeolocationEvent
except ImportError:  # Home Assistant renamed the base entity in newer releases.
    from homeassistant.components.geo_location import GeolocationEvent as GeolocationEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GeorgsmarthuetteCoordinator


def _slug(value: str) -> str:
    return (
        value.lower()
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
        .replace(" ", "_")
        .replace("/", "_")
        .replace("+", "_")
        .replace('"', "")
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: GeorgsmarthuetteCoordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {}
    entities: list[GeorgsmarthuetteGeoLocation] = []

    for item in (data.get("parking") or {}).get("locations", []):
        if item.get("latitude") is not None and item.get("longitude") is not None:
            entities.append(GeorgsmarthuetteGeoLocation(coordinator, "parking", item.get("id") or _slug(item.get("name", "parking")), item))

    for item in (data.get("charging") or {}).get("locations", []):
        if item.get("latitude") is not None and item.get("longitude") is not None:
            entities.append(GeorgsmarthuetteGeoLocation(coordinator, "charging", _slug(item.get("address", "charging")), item))

    async_add_entities(entities)


class GeorgsmarthuetteGeoLocation(CoordinatorEntity[GeorgsmarthuetteCoordinator], GeolocationEvent):
    def __init__(self, coordinator: GeorgsmarthuetteCoordinator, source_type: str, source_id: str, initial: dict[str, Any]) -> None:
        super().__init__(coordinator)
        self._source_type = source_type
        self._source_id = source_id
        self._attr_unique_id = f"georgsmarthuette_{source_type}_{source_id}"
        self._attr_name = self._name(initial)

    def _items(self) -> list[dict[str, Any]]:
        data = self.coordinator.data or {}
        if self._source_type == "parking":
            return (data.get("parking") or {}).get("locations", [])
        return (data.get("charging") or {}).get("locations", [])

    def _item(self) -> dict[str, Any]:
        for item in self._items():
            candidate = item.get("id") if self._source_type == "parking" else _slug(item.get("address", "charging"))
            if str(candidate) == str(self._source_id):
                return item
        return {}

    def _name(self, item: dict[str, Any]) -> str:
        if self._source_type == "parking":
            return f"GMH {item.get('name', 'Parkplatz')}"
        return f"GMH Ladeort {item.get('address', self._source_id)}"

    @property
    def source(self) -> str:
        return f"Georgsmarthütte {self._source_type}"

    @property
    def latitude(self) -> float | None:
        return self._item().get("latitude")

    @property
    def longitude(self) -> float | None:
        return self._item().get("longitude")

    @property
    def distance(self) -> float | None:
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        item = dict(self._item())
        item["source_type"] = self._source_type
        item["live_status_available"] = False
        return item
