from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from aiohttp import ClientSession

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, GMH_LATITUDE, GMH_LONGITUDE
from .sources import AwigoClient, BnetzaChargingClient, DwdClient, GmhCityClient, NlwknClient, OpenMeteoClient, TRAIN_STATIONS, TrainDeparturesClient

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=30)

class GeorgsmarthuetteCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.entry = entry
        self.session: ClientSession = async_get_clientsession(hass)
        self.awigo = AwigoClient(self.session)
        self.weather = OpenMeteoClient(self.session)
        self.dwd = DwdClient(self.session)
        self.nlwkn = NlwknClient(self.session)
        self.city = GmhCityClient(self.session)
        self.trains = TrainDeparturesClient(self.session)
        self.charging = BnetzaChargingClient(self.session)
        self._awigo_address = None

    async def _async_update_data(self) -> dict[str, Any]:
        data: dict[str, Any] = {"errors": {}}
        latitude = float(self.entry.data.get("latitude", GMH_LATITUDE))
        longitude = float(self.entry.data.get("longitude", GMH_LONGITUDE))

        try:
            if self._awigo_address is None:
                self._awigo_address = await self.awigo.resolve_address(
                    self.entry.data.get("awigo_street", ""),
                    self.entry.data.get("awigo_house_number", ""),
                    self.entry.data.get("awigo_house_number_suffix", ""),
                    self.entry.data.get("awigo_city", "Georgsmarienhütte"),
                )
            data["awigo_address"] = self._awigo_address
            data["awigo_dates"] = await self.awigo.get_dates(self._awigo_address.location_id, self._awigo_address.city_id)
            data["awigo_ics_url"] = await self.awigo.get_ics_url(self._awigo_address.location_id, self._awigo_address.city_id)
        except Exception as err:  # noqa: BLE001
            data["errors"]["awigo"] = str(err)

        for key, loader in {
            "weather": lambda: self.weather.get_weather(latitude, longitude),
            "air_quality": lambda: self.weather.get_air_quality(latitude, longitude),
            "pollen": self.dwd.get_pollen,
            "duete": self.nlwkn.get_duete_wersen,
            "rss_items": self.city.get_rss_items,
            "ris": self.city.get_ris_summary,
            "city_links": self.city.check_link_sources,
            "parking": self.city.get_parking_locations,
            "charging": self.charging.get_georgsmarienhuette_charging,
        }.items():
            try:
                data[key] = await loader()
            except Exception as err:  # noqa: BLE001
                data["errors"][key] = str(err)

        train_departures: dict[str, Any] = {}
        for station_key, station in TRAIN_STATIONS.items():
            try:
                train_departures[station_key] = await self.trains.get_departures(station["ds100"])
            except Exception as err:  # noqa: BLE001
                data["errors"][f"train_{station_key}"] = str(err)
        data["train_departures"] = train_departures

        if len(data) <= 1:
            raise UpdateFailed("No Georgsmarthütte data source could be updated")
        return data
