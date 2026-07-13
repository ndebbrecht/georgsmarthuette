from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity, BinarySensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GeorgsmarthuetteCoordinator
from .sources import classify_rss_items

@dataclass(frozen=True, kw_only=True)
class GeorgsmarthuetteBinarySensorDescription(BinarySensorEntityDescription):
    is_on_fn: Callable[[dict[str, Any]], bool] = lambda data: False
    attrs_fn: Callable[[dict[str, Any]], dict[str, Any]] = lambda data: {}


def _weather_warning(data: dict[str, Any]) -> bool:
    current = (data.get("weather") or {}).get("current", {})
    code = current.get("weather_code")
    wind = current.get("wind_gusts_10m") or 0
    rain = current.get("rain") or 0
    return bool(code in {95, 96, 99, 65, 66, 67, 75, 77, 82, 85, 86} or wind >= 60 or rain >= 10)


def _duete_warning(data: dict[str, Any]) -> bool:
    level = None
    station = (data.get("duete") or {}).get("getPegelDatenspurenResult", {})
    for parameter in station.get("Parameter", []):
        for trace in parameter.get("Datenspuren", []):
            value = trace.get("AktuellerMesswert")
            if isinstance(value, (int, float)) and value not in (-888, -777, -999):
                level = value
            for warning_level in trace.get("Meldestufen", []):
                threshold = warning_level.get("Wert")
                if level is not None and threshold is not None and level >= threshold:
                    return True
    return False


def _air_warning(data: dict[str, Any]) -> bool:
    aqi = ((data.get("air_quality") or {}).get("current") or {}).get("european_aqi")
    return bool(isinstance(aqi, (int, float)) and aqi >= 50)


def _vos_disruption(data: dict[str, Any]) -> bool:
    return bool((data.get("vos_disruptions") or {}).get("relevant_count"))


def _vos_attrs(data: dict[str, Any]) -> dict[str, Any]:
    vos = data.get("vos_disruptions") or {}
    return {"source": vos.get("source"), "relevant_count": vos.get("relevant_count"), "items": (vos.get("relevant_items") or [])[:10]}


def _roadworks_problem(data: dict[str, Any]) -> bool:
    return bool((data.get("county_roadworks") or {}).get("relevant_count"))


def _roadworks_attrs(data: dict[str, Any]) -> dict[str, Any]:
    roadworks = data.get("county_roadworks") or {}
    return {"source": roadworks.get("source"), "relevant_count": roadworks.get("relevant_count"), "items": (roadworks.get("relevant_items") or [])[:10]}


def _city_traffic_news(data: dict[str, Any]) -> bool:
    return bool(classify_rss_items(data.get("rss_items") or [], "traffic")["count"])


def _city_traffic_news_attrs(data: dict[str, Any]) -> dict[str, Any]:
    summary = classify_rss_items(data.get("rss_items") or [], "traffic")
    return {
        "source": "https://www.georgsmarienhuette.de/portal/rss.xml",
        "relevant_count": summary["count"],
        "keywords": summary["keywords"],
        "items": summary["items"][:10],
        "note": "Offizielle Stadt-RSS-Meldungen mit Verkehrs-/Baustellen-Schlagworten; ergänzend zu VOS und Landkreis.",
    }


def _city_weather_news(data: dict[str, Any]) -> bool:
    return bool(classify_rss_items(data.get("rss_items") or [], "weather_flood")["count"])


def _city_weather_news_attrs(data: dict[str, Any]) -> dict[str, Any]:
    summary = classify_rss_items(data.get("rss_items") or [], "weather_flood")
    return {
        "source": "https://www.georgsmarienhuette.de/portal/rss.xml",
        "relevant_count": summary["count"],
        "keywords": summary["keywords"],
        "items": summary["items"][:10],
        "note": "Offizielle Stadt-RSS-Meldungen mit Wetter-, Hochwasser-, Hitze- oder Trockenheitsbezug.",
    }


def _nina_warning(data: dict[str, Any]) -> bool:
    return bool((data.get("nina_warnings") or {}).get("warning_count"))


def _nina_attrs(data: dict[str, Any]) -> dict[str, Any]:
    nina = data.get("nina_warnings") or {}
    return {
        "source": nina.get("source"),
        "coverage": nina.get("coverage"),
        "ars": nina.get("ars"),
        "warning_count": nina.get("warning_count"),
        "warnings": (nina.get("warnings") or [])[:10],
    }


BINARY_DESCRIPTIONS = [
    GeorgsmarthuetteBinarySensorDescription(key="weather_warning", name="GMH Wetterwarnung Proxy", device_class=BinarySensorDeviceClass.SAFETY, is_on_fn=_weather_warning, attrs_fn=lambda d: (d.get("weather") or {}).get("current", {})),
    GeorgsmarthuetteBinarySensorDescription(key="duete_warning", name="Düte Hochwasserwarnung Wersen", device_class=BinarySensorDeviceClass.SAFETY, is_on_fn=_duete_warning),
    GeorgsmarthuetteBinarySensorDescription(key="air_quality_warning", name="GMH Luftqualitätswarnung", device_class=BinarySensorDeviceClass.SAFETY, is_on_fn=_air_warning, attrs_fn=lambda d: (d.get("air_quality") or {}).get("current", {})),
    GeorgsmarthuetteBinarySensorDescription(key="vos_disruption", name="GMH VOS relevante Verkehrsstörung", device_class=BinarySensorDeviceClass.PROBLEM, is_on_fn=_vos_disruption, attrs_fn=_vos_attrs),
    GeorgsmarthuetteBinarySensorDescription(key="county_roadworks", name="GMH Landkreis relevante Baustelle", device_class=BinarySensorDeviceClass.PROBLEM, is_on_fn=_roadworks_problem, attrs_fn=_roadworks_attrs),
    GeorgsmarthuetteBinarySensorDescription(key="city_traffic_news", name="GMH Stadt Verkehrs-/Baumeldung", device_class=BinarySensorDeviceClass.PROBLEM, is_on_fn=_city_traffic_news, attrs_fn=_city_traffic_news_attrs),
    GeorgsmarthuetteBinarySensorDescription(key="city_weather_news", name="GMH Stadt Wetter-/Wassermeldung", device_class=BinarySensorDeviceClass.SAFETY, is_on_fn=_city_weather_news, attrs_fn=_city_weather_news_attrs),
    GeorgsmarthuetteBinarySensorDescription(key="nina_warning", name="GMH NINA amtliche Warnung", device_class=BinarySensorDeviceClass.SAFETY, is_on_fn=_nina_warning, attrs_fn=_nina_attrs),
    GeorgsmarthuetteBinarySensorDescription(key="source_errors", name="GMH Datenquellen Fehler", device_class=BinarySensorDeviceClass.PROBLEM, is_on_fn=lambda d: bool(d.get("errors")), attrs_fn=lambda d: {"errors": d.get("errors") or {}}),
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: GeorgsmarthuetteCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GeorgsmarthuetteBinarySensor(coordinator, description) for description in BINARY_DESCRIPTIONS])

class GeorgsmarthuetteBinarySensor(CoordinatorEntity[GeorgsmarthuetteCoordinator], BinarySensorEntity):
    entity_description: GeorgsmarthuetteBinarySensorDescription

    def __init__(self, coordinator: GeorgsmarthuetteCoordinator, description: GeorgsmarthuetteBinarySensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"georgsmarthuette_{description.key}"

    @property
    def is_on(self) -> bool:
        return self.entity_description.is_on_fn(self.coordinator.data or {})

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self.entity_description.attrs_fn(self.coordinator.data or {})
