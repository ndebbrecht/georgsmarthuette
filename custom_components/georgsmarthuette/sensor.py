from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfLength, UnitOfPressure, UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GeorgsmarthuetteCoordinator
from .sources import AWIGO_WASTE_TYPES, AwigoCollectionDate, GMH_LINK_SOURCES, TRAIN_STATIONS

@dataclass(frozen=True, kw_only=True)
class GeorgsmarthuetteSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any] = lambda data: None
    attrs_fn: Callable[[dict[str, Any]], dict[str, Any]] = lambda data: {}


def _current(data: dict[str, Any], key: str) -> Any:
    return (data.get("weather") or {}).get("current", {}).get(key)


def _air(data: dict[str, Any], key: str) -> Any:
    return (data.get("air_quality") or {}).get("current", {}).get(key)


def _hourly_first(data: dict[str, Any], key: str) -> Any:
    values = (data.get("weather") or {}).get("hourly", {}).get(key) or []
    return values[0] if values else None


def _next_collection(data: dict[str, Any], waste_type: str | None = None) -> AwigoCollectionDate | None:
    today = date.today()
    dates: list[AwigoCollectionDate] = [item for item in data.get("awigo_dates", []) if item.day >= today]
    if waste_type is not None:
        dates = [item for item in dates if item.waste_type == waste_type]
    return min(dates, key=lambda item: item.day, default=None)


def _collection_attrs(item: AwigoCollectionDate | None) -> dict[str, Any]:
    if item is None:
        return {}
    return {
        "date": item.day.isoformat(),
        "waste_type": item.waste_type,
        "days_until": (item.day - date.today()).days,
        "delayed": item.delayed,
        "mobile_location": item.mobile_location,
    }


def _awigo_address_attrs(data: dict[str, Any]) -> dict[str, Any]:
    address = data.get("awigo_address")
    attrs = {"ics_url": data.get("awigo_ics_url")}
    if address:
        attrs.update({"city": address.city_label, "street": address.street_label, "house_number": address.number_label, "city_id": address.city_id, "street_id": address.street_id, "location_id": address.location_id})
    if error := (data.get("errors") or {}).get("awigo"):
        attrs["error"] = error
    return attrs


def _pollen_value(data: dict[str, Any], name: str) -> Any:
    pollen = data.get("pollen") or {}
    values = pollen.get("Pollen") or pollen.get("pollen") or {}
    item = values.get(name) or values.get(name.lower()) or {}
    today = item.get("today") or item.get("Heute") or item.get("today_desc")
    return today


def _duete_water_level(data: dict[str, Any]) -> Any:
    station = (data.get("duete") or {}).get("getPegelDatenspurenResult", {})
    for parameter in station.get("Parameter", []):
        for trace in parameter.get("Datenspuren", []):
            value = trace.get("AktuellerMesswert")
            if isinstance(value, (int, float)) and value not in (-888, -777, -999):
                return value
    return None


def _duete_attrs(data: dict[str, Any]) -> dict[str, Any]:
    station = (data.get("duete") or {}).get("getPegelDatenspurenResult", {})
    attrs = {"station": station.get("Name", "Wersen"), "water": station.get("GewaesserName", "Düte"), "station_id": station.get("STA_ID", 116), "url": "https://www.pegelonline.nlwkn.niedersachsen.de/Pegel/Karte/Binnenpegel/ID/116"}
    levels = []
    for parameter in station.get("Parameter", []):
        for trace in parameter.get("Datenspuren", []):
            for level in trace.get("Meldestufen", []):
                levels.append(level)
    if levels:
        attrs["warning_levels"] = levels
    return attrs


def _train_departure(data: dict[str, Any], station_key: str, direction: str | None = None) -> dict[str, Any] | None:
    departures = (data.get("train_departures") or {}).get(station_key) or []
    if direction:
        departures = [item for item in departures if str(item.get("destination", "")).lower().startswith(direction.lower())]
    return departures[0] if departures else None


def _train_value(data: dict[str, Any], station_key: str, direction: str | None = None) -> Any:
    item = _train_departure(data, station_key, direction)
    return item.get("scheduledDeparture") if item else None


def _train_attrs(data: dict[str, Any], station_key: str, direction: str | None = None) -> dict[str, Any]:
    station = TRAIN_STATIONS[station_key]
    item = _train_departure(data, station_key, direction)
    attrs: dict[str, Any] = {**station, "source": f"https://dbf.finalrewind.org/{station['ds100']}.json", "direction_filter": direction}
    if item:
        attrs.update({
            "destination": item.get("destination"),
            "train": item.get("train"),
            "train_number": item.get("trainNumber"),
            "delay_departure": item.get("delayDeparture"),
            "delay_arrival": item.get("delayArrival"),
            "cancelled": bool(item.get("isCancelled")),
            "platform": item.get("platform"),
            "scheduled_platform": item.get("scheduledPlatform"),
            "via": item.get("via"),
            "missing_realtime": item.get("missingRealtime"),
        })
    return attrs


def _parking(data: dict[str, Any], key: str) -> Any:
    return (data.get("parking") or {}).get(key)


def _parking_attrs(data: dict[str, Any]) -> dict[str, Any]:
    parking = data.get("parking") or {}
    return {
        "location_count": parking.get("location_count"),
        "regular_count": parking.get("regular_count"),
        "hiking_count": parking.get("hiking_count"),
        "source": parking.get("source"),
        "live_status_available": parking.get("live_status_available", False),
        "note": "Städtische Parkplatz-POI-Stammdaten; einzelne Standorte werden als geo_location-Entities angelegt.",
    }


def _charging(data: dict[str, Any], key: str) -> Any:
    return (data.get("charging") or {}).get(key)


def _charging_attrs(data: dict[str, Any]) -> dict[str, Any]:
    charging = data.get("charging") or {}
    return {
        "station_count": charging.get("station_count"),
        "location_count": charging.get("location_count"),
        "charging_points": charging.get("charging_points"),
        "fast_charging_points": charging.get("fast_charging_points"),
        "normal_charging_points": charging.get("normal_charging_points"),
        "max_power_kw": charging.get("max_power_kw"),
        "source": charging.get("source"),
        "source_page": charging.get("source_page"),
        "live_status_available": charging.get("live_status_available", False),
        "note": "Bundesnetzagentur-Stammdaten; einzelne Ladeorte werden als geo_location-Entities angelegt.",
    }


def _vos_attrs(data: dict[str, Any]) -> dict[str, Any]:
    vos = data.get("vos_disruptions") or {}
    relevant = vos.get("relevant_items") or []
    return {
        "source": vos.get("source"),
        "total_count": vos.get("total_count"),
        "relevant_count": vos.get("relevant_count"),
        "items": relevant[:10],
        "note": "Öffentliche VOS-Störungs-/Baustellenseite, gefiltert nach GMH-Ortsbegriffen und relevanten Linien.",
    }


def _vos_latest(data: dict[str, Any]) -> Any:
    relevant = (data.get("vos_disruptions") or {}).get("relevant_items") or []
    return relevant[0].get("title") if relevant else None


def _latest_rss(data: dict[str, Any]) -> Any:
    items = data.get("rss_items") or []
    return items[0].title if items else None


def _latest_rss_attrs(data: dict[str, Any]) -> dict[str, Any]:
    items = data.get("rss_items") or []
    if not items:
        return {}
    item = items[0]
    return {"link": item.link, "description": item.description, "published": item.published, "image": item.image, "item_count": len(items)}

SENSOR_DESCRIPTIONS: list[GeorgsmarthuetteSensorDescription] = [
    GeorgsmarthuetteSensorDescription(key="awigo_next_collection", name="GMH AWIGO nächste Abfuhr", device_class=SensorDeviceClass.DATE, value_fn=lambda d: (_next_collection(d).day if _next_collection(d) else None), attrs_fn=lambda d: _collection_attrs(_next_collection(d)) | _awigo_address_attrs(d)),
    *[
        GeorgsmarthuetteSensorDescription(key=f"awigo_next_{waste.lower().replace('ü','ue').replace(' ','_')}", name=f"GMH AWIGO nächste Abfuhr {waste}", device_class=SensorDeviceClass.DATE, value_fn=lambda d, w=waste: (_next_collection(d, w).day if _next_collection(d, w) else None), attrs_fn=lambda d, w=waste: _collection_attrs(_next_collection(d, w)) | _awigo_address_attrs(d))
        for waste in AWIGO_WASTE_TYPES.values()
    ],
    GeorgsmarthuetteSensorDescription(key="temperature", name="GMH Temperatur", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: _current(d, "temperature_2m")),
    GeorgsmarthuetteSensorDescription(key="apparent_temperature", name="GMH gefühlte Temperatur", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: _current(d, "apparent_temperature")),
    GeorgsmarthuetteSensorDescription(key="humidity", name="GMH Luftfeuchte", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.HUMIDITY, state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: _current(d, "relative_humidity_2m")),
    GeorgsmarthuetteSensorDescription(key="pressure", name="GMH Luftdruck", native_unit_of_measurement=UnitOfPressure.HPA, device_class=SensorDeviceClass.PRESSURE, state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: _current(d, "pressure_msl")),
    GeorgsmarthuetteSensorDescription(key="wind_speed", name="GMH Windgeschwindigkeit", native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR, device_class=SensorDeviceClass.WIND_SPEED, state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: _current(d, "wind_speed_10m")),
    GeorgsmarthuetteSensorDescription(key="wind_gusts", name="GMH Windböen", native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR, device_class=SensorDeviceClass.WIND_SPEED, state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: _current(d, "wind_gusts_10m")),
    GeorgsmarthuetteSensorDescription(key="wind_direction", name="GMH Windrichtung", native_unit_of_measurement="°", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: _current(d, "wind_direction_10m")),
    GeorgsmarthuetteSensorDescription(key="precipitation", name="GMH Niederschlag", native_unit_of_measurement=UnitOfLength.MILLIMETERS, device_class=SensorDeviceClass.PRECIPITATION, state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: _current(d, "precipitation")),
    GeorgsmarthuetteSensorDescription(key="rain", name="GMH Regen", native_unit_of_measurement=UnitOfLength.MILLIMETERS, device_class=SensorDeviceClass.PRECIPITATION, state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: _current(d, "rain")),
    GeorgsmarthuetteSensorDescription(key="precipitation_probability", name="GMH Regenwahrscheinlichkeit nächste Stunde", native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: _hourly_first(d, "precipitation_probability")),
    GeorgsmarthuetteSensorDescription(key="uv_index", name="GMH UV-Index", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: _hourly_first(d, "uv_index")),
    GeorgsmarthuetteSensorDescription(key="cloud_cover", name="GMH Bewölkung", native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: _current(d, "cloud_cover")),
    GeorgsmarthuetteSensorDescription(key="european_aqi", name="GMH Luftqualität EU AQI", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: _air(d, "european_aqi")),
    GeorgsmarthuetteSensorDescription(key="pm10", name="GMH PM10", native_unit_of_measurement="µg/m³", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: _air(d, "pm10")),
    GeorgsmarthuetteSensorDescription(key="pm25", name="GMH PM2.5", native_unit_of_measurement="µg/m³", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: _air(d, "pm2_5")),
    GeorgsmarthuetteSensorDescription(key="no2", name="GMH Stickstoffdioxid", native_unit_of_measurement="µg/m³", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: _air(d, "nitrogen_dioxide")),
    GeorgsmarthuetteSensorDescription(key="ozone", name="GMH Ozon", native_unit_of_measurement="µg/m³", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: _air(d, "ozone")),
    *[GeorgsmarthuetteSensorDescription(key=f"pollen_{p.lower()}", name=f"GMH Pollen {p}", value_fn=lambda d, p=p: _pollen_value(d, p), attrs_fn=lambda d: {"source": "DWD"}) for p in ["Hasel", "Erle", "Birke", "Graeser", "Roggen", "Beifuss", "Ambrosia"]],
    GeorgsmarthuetteSensorDescription(key="duete_wersen_level", name="Düte Pegel Wersen", native_unit_of_measurement="cm", device_class=SensorDeviceClass.DISTANCE, state_class=SensorStateClass.MEASUREMENT, value_fn=_duete_water_level, attrs_fn=_duete_attrs),
    *[
        GeorgsmarthuetteSensorDescription(key=f"train_{station_key}_next", name=f"{station['name']} nächste Zugabfahrt", value_fn=lambda d, station_key=station_key: _train_value(d, station_key), attrs_fn=lambda d, station_key=station_key: _train_attrs(d, station_key))
        for station_key, station in TRAIN_STATIONS.items()
    ],
    *[
        GeorgsmarthuetteSensorDescription(key=f"train_{station_key}_next_osnabrueck", name=f"{station['name']} nächste Abfahrt Richtung Osnabrück", value_fn=lambda d, station_key=station_key: _train_value(d, station_key, "Osnabrück"), attrs_fn=lambda d, station_key=station_key: _train_attrs(d, station_key, "Osnabrück"))
        for station_key, station in TRAIN_STATIONS.items()
    ],
    *[
        GeorgsmarthuetteSensorDescription(key=f"train_{station_key}_next_bielefeld", name=f"{station['name']} nächste Abfahrt Richtung Bielefeld", value_fn=lambda d, station_key=station_key: _train_value(d, station_key, "Bielefeld"), attrs_fn=lambda d, station_key=station_key: _train_attrs(d, station_key, "Bielefeld"))
        for station_key, station in TRAIN_STATIONS.items()
    ],
    GeorgsmarthuetteSensorDescription(key="parking_locations_total", name="GMH Parkplätze gesamt", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: _parking(d, "location_count"), attrs_fn=_parking_attrs),
    GeorgsmarthuetteSensorDescription(key="parking_regular_total", name="GMH Stadtparkplätze", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: _parking(d, "regular_count"), attrs_fn=_parking_attrs),
    GeorgsmarthuetteSensorDescription(key="parking_hiking_total", name="GMH Wanderparkplätze", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: _parking(d, "hiking_count"), attrs_fn=_parking_attrs),
    GeorgsmarthuetteSensorDescription(key="vos_disruptions_relevant", name="GMH VOS relevante Störungen", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: (d.get("vos_disruptions") or {}).get("relevant_count"), attrs_fn=_vos_attrs),
    GeorgsmarthuetteSensorDescription(key="vos_latest_disruption", name="GMH VOS neueste relevante Störung", value_fn=_vos_latest, attrs_fn=_vos_attrs),
    GeorgsmarthuetteSensorDescription(key="charging_points_total", name="GMH Ladepunkte gesamt", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: _charging(d, "charging_points"), attrs_fn=_charging_attrs),
    GeorgsmarthuetteSensorDescription(key="charging_stations_total", name="GMH Ladeeinrichtungen gesamt", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: _charging(d, "station_count"), attrs_fn=_charging_attrs),
    GeorgsmarthuetteSensorDescription(key="charging_locations_total", name="GMH Ladestandorte gesamt", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: _charging(d, "location_count"), attrs_fn=_charging_attrs),
    GeorgsmarthuetteSensorDescription(key="charging_fast_points", name="GMH Schnellladepunkte", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: _charging(d, "fast_charging_points"), attrs_fn=_charging_attrs),
    GeorgsmarthuetteSensorDescription(key="charging_normal_points", name="GMH Normalladepunkte", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: _charging(d, "normal_charging_points"), attrs_fn=_charging_attrs),
    GeorgsmarthuetteSensorDescription(key="charging_max_power", name="GMH maximale Ladeleistung", native_unit_of_measurement="kW", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: _charging(d, "max_power_kw"), attrs_fn=_charging_attrs),
    GeorgsmarthuetteSensorDescription(key="latest_city_news", name="GMH neueste Stadtmeldung", value_fn=_latest_rss, attrs_fn=_latest_rss_attrs),
    GeorgsmarthuetteSensorDescription(key="next_council_session", name="GMH nächste Rats-/Ausschusssitzung", value_fn=lambda d: (d.get("ris") or {}).get("summary"), attrs_fn=lambda d: d.get("ris") or {}),
    *[GeorgsmarthuetteSensorDescription(key=f"city_source_{key}", name=f"GMH Datenquelle {key.replace('_', ' ')}", value_fn=lambda d, key=key: "online" if ((d.get("city_links") or {}).get(key) or {}).get("available") else "offline", attrs_fn=lambda d, key=key: ((d.get("city_links") or {}).get(key) or {"url": GMH_LINK_SOURCES[key]})) for key in GMH_LINK_SOURCES],
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: GeorgsmarthuetteCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GeorgsmarthuetteSensor(coordinator, description) for description in SENSOR_DESCRIPTIONS])

class GeorgsmarthuetteSensor(CoordinatorEntity[GeorgsmarthuetteCoordinator], SensorEntity):
    entity_description: GeorgsmarthuetteSensorDescription

    def __init__(self, coordinator: GeorgsmarthuetteCoordinator, description: GeorgsmarthuetteSensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"georgsmarthuette_{description.key}"

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data or {})

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        attrs = self.entity_description.attrs_fn(data)
        errors = data.get("errors") or {}
        if errors:
            attrs = dict(attrs)
            attrs["source_errors"] = errors
        return attrs
