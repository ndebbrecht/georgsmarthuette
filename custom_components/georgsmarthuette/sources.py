from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from html import unescape
import asyncio
import csv
import io
import math
import re
import xml.etree.ElementTree as ET
from typing import Any

import aiohttp

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=30)
LINK_CHECK_TIMEOUT = aiohttp.ClientTimeout(total=10)
CSV_DOWNLOAD_TIMEOUT = aiohttp.ClientTimeout(total=120)
CAMERA_TIMEOUT = aiohttp.ClientTimeout(total=10)

AWIGO_BASE_URL = "https://www.awigo.de/index.php"
AWIGO_REFERER = "https://www.awigo.de/haushalt/abfallinformationen/abfuhrtermine"
AWIGO_GMH_CITY_ID = "5348001"

AWIGO_WASTE_TYPES = {
    1: "Restmüll",
    2: "Papiermüll",
    3: "Biomüll",
    4: "Gelber Sack",
    5: "Schadstoffmobil",
}

OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
DWD_POLLEN_URL = "https://opendata.dwd.de/climate_environment/health/alerts/s31fg.json"

NLWKN_BASE_URL = "https://bis.azure-api.net/PegelonlineNeu/REST"
# Public read-only subscription key for NLWKN BIS (PegelOnline) API — free public governmental water level data.
NLWKN_SUBSCRIPTION_KEY = "19094e54510d4e89b140ff2d3abf715f"
NLWKN_DUETE_WERSEN_STATION_ID = 116

GMH_NEWS_RSS_URL = "https://www.georgsmarienhuette.de/portal/rss.xml"
GMH_RIS_URL = "https://gmh.ris.itebo.de/bi/infobi.asp"
GMH_EVENTS_URL = "https://www.georgsmarienhuette.de/stadt/veranstaltungen/"
GMH_ANNOUNCEMENTS_URL = "https://www.georgsmarienhuette.de/rathaus/aktuelles/bekanntmachungen/"
GMH_PARKING_URL = "https://www.georgsmarienhuette.de/stadt/erster-ueberblick/parkplaetze/"
GMH_E_MOBILITY_URL = "https://www.georgsmarienhuette.de/stadt/daten-fakten-mobilitaet/e-mobilitaet/"
GMH_SWIMMING_URL = "https://www.georgsmarienhuette.de/stadt/sport/schwimmbaeder/"
GMH_SOLAR_CADASTRE_URL = "https://www.georgsmarienhuette.de/stadt/umwelt/klimaschutz/solardachkataster/"
GMH_HEAT_PLANNING_URL = "https://www.georgsmarienhuette.de/stadt/umwelt/klimaschutz/kommunale-waermeplanung/"
GMH_SPORTS_HALLS_URL = "https://www.georgsmarienhuette.de/seiten/sportstaettenmanagement.php"
GMH_CITY_MAP_URL = "http://navigator.georgsmarienhuette.de"
VOS_TIMETABLE_URL = "https://www.vos.info/"
VOS_DISRUPTIONS_URL = "https://www.vos.info/fahrplan/stoerungen-baustellen/"
DB_TRAVEL_URL = "https://www.bahn.de/"
FINALREWIND_OESEDE_URL = "https://dbf.finalrewind.org/HOES.json"
FINALREWIND_KLOSTER_OESEDE_URL = "https://dbf.finalrewind.org/HKOE.json"
COUNTY_ROADWORKS_URL = "https://www.landkreis-osnabrueck.de/fachthemen/ordnung-und-verkehr/baustellen-und-blitzplan"
GMH_ROADWORKS_URL = "https://www.georgsmarienhuette.de/portal/seiten/aktuelle-strassenbaumassnahmen-914001552-22600.html"
STADTWERKE_CHARGING_URL = "https://www.sw-gmhuette.de/de/Mobilitaet-Zukunft/E-Ladestation/"
BNETZA_CHARGING_REGISTER_CSV_URL = "https://data.bundesnetzagentur.de/Bundesnetzagentur/DE/Fachthemen/ElektrizitaetundGas/E-Mobilitaet/Ladesaeulenregister_BNetzA_2026-04-22.csv"
BNETZA_CHARGING_REGISTER_PAGE_URL = "https://www.bundesnetzagentur.de/DE/Fachthemen/ElektrizitaetundGas/E-Mobilitaet/DownloadundKontakt.html"
DWD_WARNINGS_URL = "https://www.dwd.de/DE/wetter/warnungen_gemeinden/warnkarten/warnWetter_nib_node.html?bundesland=nib"
NINA_WARNINGS_URL = "https://warnung.bund.de/"
NINA_DASHBOARD_URL = "https://warnung.bund.de/api31/dashboard/{ars}.json"
# NINA/warnung.bund.de dashboard data is exposed by county ARS. The Landkreis
# Osnabrück ARS is the narrowest stable public endpoint that covers GMH.
NINA_LANDKREIS_OSNABRUECK_ARS = "034590000000"
SMARD_URL = "https://www.smard.de/"
MARKTSTAMMDATENREGISTER_URL = "https://www.marktstammdatenregister.de/MaStR"
SENSOR_COMMUNITY_URL = "https://sensor.community/"

GMH_LINK_SOURCES = {
    "events": GMH_EVENTS_URL,
    "announcements": GMH_ANNOUNCEMENTS_URL,
    "parking": GMH_PARKING_URL,
    "e_mobility": GMH_E_MOBILITY_URL,
    "swimming": GMH_SWIMMING_URL,
    "solar_cadastre": GMH_SOLAR_CADASTRE_URL,
    "heat_planning": GMH_HEAT_PLANNING_URL,
    "sports_halls": GMH_SPORTS_HALLS_URL,
    "city_map": GMH_CITY_MAP_URL,
    "public_transport_vos": VOS_TIMETABLE_URL,
    "public_transport_vos_disruptions": VOS_DISRUPTIONS_URL,
    "public_transport_db": DB_TRAVEL_URL,
    "train_departures_oesede": FINALREWIND_OESEDE_URL,
    "train_departures_kloster_oesede": FINALREWIND_KLOSTER_OESEDE_URL,
    "roadworks_county": COUNTY_ROADWORKS_URL,
    "roadworks_city": GMH_ROADWORKS_URL,
    "charging_stadtwerke": STADTWERKE_CHARGING_URL,
    "charging_bnetza_register": BNETZA_CHARGING_REGISTER_PAGE_URL,
    "dwd_warnings": DWD_WARNINGS_URL,
    "nina_warnings": NINA_WARNINGS_URL,
    "energy_smard": SMARD_URL,
    "market_master_data_register": MARKTSTAMMDATENREGISTER_URL,
    "sensor_community_air_quality": SENSOR_COMMUNITY_URL,
}

TRAIN_STATIONS = {
    "oesede": {
        "name": "Oesede",
        "ds100": "HOES",
        "ibnr": "8004628",
        "line": "RB75 Haller Willem",
        "latitude": 52.2087,
        "longitude": 8.0642,
    },
    "kloster_oesede": {
        "name": "Kloster Oesede",
        "ds100": "HKOE",
        "ibnr": None,
        "line": "RB75 Haller Willem",
        "latitude": 52.2006,
        "longitude": 8.1116,
    },
}

FINALREWIND_BASE_URL = "https://dbf.finalrewind.org"

GMH_CAMERAS = {
    "oeseder_strasse_rathaus": "https://www.georgsmarienhuette.de/seiten/webcam/gmhuette.jpg",
    "rathausplatz": "https://www.georgsmarienhuette.de/seiten/webcam/webcamRP/gmhuette2.jpg",
    "hochwasser_breenbach": "https://www.webcam-georgsmarienhuette.de/hochwasserschutz/current/webcam_breenbach.jpg",
    "hochwasser_suttmeyer": "https://www.webcam-georgsmarienhuette.de/hochwasserschutz/current/webcam_suttmeyer.jpg",
    "hochwasser_malbergen": "https://www.webcam-georgsmarienhuette.de/hochwasserschutz/current/webcam_malbergen.jpg",
    "hochwasser_eisenbahn": "https://www.webcam-georgsmarienhuette.de/hochwasserschutz/current/webcam_eisenbahn.jpg",
}

POLLEN_REGION_HINTS = ("Niedersachsen", "Bremen")
GMH_TRANSPORT_RELEVANCE_TERMS = (
    "georgsmarienhütte",
    "georgsmarienhuette",
    "gmhütte",
    "gmhuette",
    "oesede",
    "kloster oesede",
    "harderberg",
    "holzhausen",
    "malbergen",
    "b51",
    "weghaus",
)

GMH_ROADWORKS_RELEVANCE_TERMS = (
    "georgsmarienhütte",
    "georgsmarienhuette",
    "gmhütte",
    "gmhuette",
    "oesede",
    "kloster oesede",
    "harderberg",
    "holzhausen",
    "malbergen",
    "b51",
    "b 51",
    "b51/b68",
    "b 51 / b 68",
    "osnabrück-nahne",
    "osnabrueck-nahne",
)

@dataclass(slots=True)
class AwigoCollectionDate:
    day: date
    waste_type: str
    delayed: bool
    mobile_location: str | None = None

@dataclass(slots=True)
class AwigoAddress:
    city_id: str
    street_id: str
    location_id: str
    city_label: str
    street_label: str
    number_label: str

@dataclass(slots=True)
class ParkingLocation:
    id: str
    name: str
    address: str
    category: str
    url: str
    latitude: float | None
    longitude: float | None

@dataclass(slots=True)
class RssItem:
    title: str
    link: str
    description: str
    published: str | None
    image: str | None

class AwigoClient:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def _request_text(self, params: dict[str, Any]) -> str:
        headers = {"Referer": AWIGO_REFERER, "User-Agent": "Georgsmarthuette/0.1"}
        async with self._session.post(AWIGO_BASE_URL, params=params, headers=headers, timeout=DEFAULT_TIMEOUT) as response:
            response.raise_for_status()
            return await response.text()

    @staticmethod
    def _options(html: str) -> list[tuple[str, str]]:
        matches = re.findall(r'<option\s+value="([^"]*)"[^>]*>(.*?)</option>', html, flags=re.I | re.S)
        result: list[tuple[str, str]] = []
        for value, label in matches:
            label = re.sub(r"\s+", " ", unescape(re.sub("<.*?>", "", label))).strip()
            if value and label and "wählen" not in label.lower():
                result.append((value.strip(), label))
        return result

    @staticmethod
    def _norm(value: str) -> str:
        value = value.strip().lower()
        value = value.replace("straße", "strasse").replace("str.", "strasse")
        value = re.sub(r"\s+", " ", value)
        return value

    async def get_cities(self) -> list[tuple[str, str]]:
        return self._options(await self._request_text({"legacy_eID": "awigoCalendar", "calendar[method]": "getCities"}))

    async def get_streets(self, city_id: str) -> list[tuple[str, str]]:
        return self._options(await self._request_text({"legacy_eID": "awigoCalendar", "calendar[method]": "getStreets", "calendar[cityID]": city_id}))

    async def get_numbers(self, street_id: str) -> list[tuple[str, str]]:
        return self._options(await self._request_text({"legacy_eID": "awigoCalendar", "calendar[method]": "getNumbers", "calendar[streetID]": street_id}))

    async def resolve_address(self, street: str, house_number: str, suffix: str = "", city: str = "Georgsmarienhütte") -> AwigoAddress:
        cities = await self.get_cities()
        city_norm = self._norm(city)
        city_match = next(((value, label) for value, label in cities if city_norm in self._norm(label)), None)
        if city_match is None:
            city_match = (AWIGO_GMH_CITY_ID, "Georgsmarienhütte (49124)")

        streets = await self.get_streets(city_match[0])
        street_norm = self._norm(street)
        street_match = next(((value, label) for value, label in streets if self._norm(label) == street_norm), None)
        if street_match is None:
            street_match = next(((value, label) for value, label in streets if street_norm in self._norm(label)), None)
        if street_match is None:
            raise ValueError(f"AWIGO street not found: {street}")

        numbers = await self.get_numbers(street_match[0])
        wanted = self._norm(f"{house_number} {suffix}".strip())
        number_match = next(((value, label) for value, label in numbers if self._norm(label) == wanted), None)
        if number_match is None and suffix:
            wanted_no_space = self._norm(f"{house_number}{suffix}".strip())
            number_match = next(((value, label) for value, label in numbers if self._norm(label) == wanted_no_space), None)
        if number_match is None:
            number_match = next(((value, label) for value, label in numbers if self._norm(label).startswith(self._norm(house_number))), None)
        if number_match is None:
            raise ValueError(f"AWIGO house number not found: {house_number} {suffix}".strip())

        return AwigoAddress(city_match[0], street_match[0], number_match[0], city_match[1], street_match[1], number_match[1])

    async def get_dates(self, location_id: str, city_id: str = AWIGO_GMH_CITY_ID) -> list[AwigoCollectionDate]:
        params: dict[str, Any] = {
            "legacy_eID": "awigoCalendar",
            "calendar[method]": "getDates",
            "calendar[locationID]": location_id,
            "calendar[cityID]": city_id,
            "calendar[rest]": "1",
            "calendar[paper]": "1",
            "calendar[yellow]": "1",
            "calendar[brown]": "1",
            "calendar[mobile]": "1",
        }
        headers = {"Referer": AWIGO_REFERER, "User-Agent": "Georgsmarthuette/0.1"}
        async with self._session.post(AWIGO_BASE_URL, params=params, headers=headers, timeout=DEFAULT_TIMEOUT) as response:
            response.raise_for_status()
            data = await response.json(content_type=None)

        items: list[AwigoCollectionDate] = []
        for item in data:
            parsed = datetime.strptime(item["dataDay"], "%d.%m.%Y").date()
            items.append(AwigoCollectionDate(parsed, AWIGO_WASTE_TYPES.get(int(item["type"]), f"Typ {item['type']}"), str(item.get("delayed", "0")) == "1", item.get("mobileLocation") or None))
        return sorted(items, key=lambda item: item.day)

    async def get_ics_url(self, location_id: str, city_id: str = AWIGO_GMH_CITY_ID) -> str | None:
        params = {
            "legacy_eID": "awigoCalendar",
            "calendar[method]": "getICSfile",
            "calendar[locationID]": location_id,
            "calendar[cityID]": city_id,
            "calendar[rest]": "1",
            "calendar[paper]": "1",
            "calendar[yellow]": "1",
            "calendar[brown]": "1",
            "calendar[mobile]": "1",
        }
        text = await self._request_text(params)
        return text.strip() if text.startswith("https://") else None

class OpenMeteoClient:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def get_weather(self, latitude: float, longitude: float) -> dict[str, Any]:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": ",".join(["temperature_2m", "relative_humidity_2m", "apparent_temperature", "precipitation", "rain", "showers", "weather_code", "cloud_cover", "pressure_msl", "surface_pressure", "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m"]),
            "hourly": "precipitation_probability,uv_index",
            "forecast_days": 1,
            "timezone": "Europe/Berlin",
        }
        async with self._session.get(OPEN_METEO_FORECAST_URL, params=params, timeout=DEFAULT_TIMEOUT) as response:
            response.raise_for_status()
            return await response.json()

    async def get_air_quality(self, latitude: float, longitude: float) -> dict[str, Any]:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "european_aqi,pm10,pm2_5,nitrogen_dioxide,ozone",
            "timezone": "Europe/Berlin",
        }
        async with self._session.get(OPEN_METEO_AIR_QUALITY_URL, params=params, timeout=DEFAULT_TIMEOUT) as response:
            response.raise_for_status()
            return await response.json()

class DwdClient:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def get_pollen(self) -> dict[str, Any]:
        async with self._session.get(DWD_POLLEN_URL, timeout=DEFAULT_TIMEOUT) as response:
            response.raise_for_status()
            data = await response.json(content_type=None)
        regions = data.get("content", []) if isinstance(data, dict) else []
        for region in regions:
            name = str(region.get("region_name", ""))
            part = str(region.get("partregion_name", ""))
            if any(hint in name or hint in part for hint in POLLEN_REGION_HINTS):
                return region
        return regions[0] if regions else {}

class NlwknClient:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def get_duete_wersen(self) -> dict[str, Any]:
        url = f"{NLWKN_BASE_URL}/station/{NLWKN_DUETE_WERSEN_STATION_ID}/datenspuren/parameter/1/tage/7/forecast/true"
        async with self._session.get(url, params={"subscription-key": NLWKN_SUBSCRIPTION_KEY}, timeout=DEFAULT_TIMEOUT) as response:
            response.raise_for_status()
            return await response.json()

class TrainDeparturesClient:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def get_departures(self, ds100: str) -> list[dict[str, Any]]:
        async with self._session.get(f"{FINALREWIND_BASE_URL}/{ds100}.json", headers={"User-Agent": "Georgsmarthuette/0.1"}, timeout=DEFAULT_TIMEOUT) as response:
            response.raise_for_status()
            data = await response.json(content_type=None)
        return data.get("departures", []) if isinstance(data, dict) else []


class VosDisruptionsClient:
    """Parse public VOS disruption/roadworks notices relevant to GMH.

    VOS exposes these notices as a public accordion page. There is no stable JSON
    endpoint visible, so the parser is deliberately conservative: it only extracts
    title, text, PDF/link targets and line classes from the visible HTML blocks.
    """

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    @staticmethod
    def _clean(value: str | None) -> str:
        if not value:
            return ""
        value = re.sub(r"<br\s*/?>", " ", value, flags=re.I)
        value = re.sub(r"<[^>]+>", " ", value)
        value = unescape(value).replace("&#62;", ">")
        return re.sub(r"\s+", " ", value).strip()

    @staticmethod
    def _line_ids(class_attr: str) -> list[str]:
        return sorted({match.upper().replace("_", "") for match in re.findall(r"\bbus_([a-z0-9]+)\b", class_attr, flags=re.I)})

    @staticmethod
    def _is_relevant(title: str, description: str, lines: list[str]) -> bool:
        haystack = f"{title} {description}".lower()
        if any(term in haystack for term in GMH_TRANSPORT_RELEVANCE_TERMS):
            return True
        # Lines with regular GMH relevance according to the city/VOS research notes.
        return bool({"411", "413", "451", "452", "454", "463", "464", "465", "466", "467", "468", "469", "M3", "S40"} & set(lines))

    @classmethod
    def parse_disruptions(cls, html: str) -> dict[str, Any]:
        notices: list[dict[str, Any]] = []
        blocks = re.findall(r'<li class="([^"]*accordion-item[^"]*)"[^>]*>(.*?)</li>', html, flags=re.I | re.S)
        for class_attr, block in blocks:
            title_match = re.search(r'<a[^>]*class="[^"]*accordion-title[^"]*"[^>]*>(.*?)</a>', block, flags=re.I | re.S)
            if not title_match:
                continue
            description_match = re.search(r'<div[^>]*class="[^"]*accordion-content[^"]*"[^>]*>(.*?)</div>', block, flags=re.I | re.S)
            links = [unescape(link) for link in re.findall(r'href="(https?://[^"]+)"', block)]
            title = cls._clean(title_match.group(1))
            description = cls._clean(description_match.group(1) if description_match else "")
            lines = cls._line_ids(class_attr)
            notice = {
                "title": title,
                "description": description,
                "lines": lines,
                "links": links,
                "source": VOS_DISRUPTIONS_URL,
            }
            notice["relevant"] = cls._is_relevant(title, description, lines)
            notices.append(notice)

        relevant = [notice for notice in notices if notice["relevant"]]
        return {
            "source": VOS_DISRUPTIONS_URL,
            "total_count": len(notices),
            "relevant_count": len(relevant),
            "items": notices,
            "relevant_items": relevant,
        }

    async def get_disruptions(self) -> dict[str, Any]:
        async with self._session.get(VOS_DISRUPTIONS_URL, headers={"User-Agent": "Georgsmarthuette/0.1"}, timeout=DEFAULT_TIMEOUT) as response:
            response.raise_for_status()
            html = await response.text()
        return self.parse_disruptions(html)


class CountyRoadworksClient:
    """Parse Landkreis Osnabrück roadworks notices relevant to GMH.

    The county publishes traffic/roadworks notices as public accordion cards. This
    parser intentionally keeps only conservative headline/date/summary attributes
    and filters by GMH-specific place/road terms to avoid turning the broad county
    page into noisy Home Assistant entities.
    """

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    @staticmethod
    def _clean(value: str | None) -> str:
        if not value:
            return ""
        value = re.sub(r"<br\s*/?>", " ", value, flags=re.I)
        value = re.sub(r"<[^>]+>", " ", value)
        return re.sub(r"\s+", " ", unescape(value)).strip()

    @staticmethod
    def _is_relevant(title: str, description: str) -> bool:
        haystack = f"{title} {description}".lower()
        return any(term in haystack for term in GMH_ROADWORKS_RELEVANCE_TERMS)

    @classmethod
    def parse_roadworks(cls, html: str) -> dict[str, Any]:
        notices: list[dict[str, Any]] = []
        blocks = re.findall(
            r'<div class="card card-accordion"[^>]*id="([^"]+)"[^>]*>(.*?)(?=<div class="card card-accordion"|#### Geschwindigkeitsmessplan|</main>|$)',
            html,
            flags=re.I | re.S,
        )
        for node_id, block in blocks:
            title_match = re.search(r'<h6 class="headline-title">\s*(.*?)\s*</h6>', block, flags=re.I | re.S)
            if not title_match:
                continue
            dates = re.findall(r'<time[^>]*datetime="([^"]+)"[^>]*>(.*?)</time>', block, flags=re.I | re.S)
            body_match = re.search(r'<div class="card-body">(.*?)</div>\s*</div>\s*</div>', block, flags=re.I | re.S)
            title = cls._clean(title_match.group(1))
            description = cls._clean(body_match.group(1) if body_match else "")
            if len(description) > 1200:
                description = description[:1197].rstrip() + "..."
            notice = {
                "id": node_id,
                "title": title,
                "description": description,
                "start": dates[0][0] if dates else None,
                "end": dates[1][0] if len(dates) > 1 else None,
                "start_label": cls._clean(dates[0][1]) if dates else None,
                "end_label": cls._clean(dates[1][1]) if len(dates) > 1 else None,
                "source": COUNTY_ROADWORKS_URL,
            }
            notice["relevant"] = cls._is_relevant(title, description)
            notices.append(notice)

        relevant = [notice for notice in notices if notice["relevant"]]
        return {
            "source": COUNTY_ROADWORKS_URL,
            "total_count": len(notices),
            "relevant_count": len(relevant),
            "items": notices,
            "relevant_items": relevant,
            "filter_terms": GMH_ROADWORKS_RELEVANCE_TERMS,
        }

    async def get_roadworks(self) -> dict[str, Any]:
        async with self._session.get(COUNTY_ROADWORKS_URL, headers={"User-Agent": "Georgsmarthuette/0.1"}, timeout=DEFAULT_TIMEOUT) as response:
            response.raise_for_status()
            html = await response.text()
        return self.parse_roadworks(html)


class NinaWarningsClient:
    """Load official NINA/warnung.bund.de warnings for Landkreis Osnabrück.

    The public NINA dashboard API currently serves warnings by county-level ARS.
    That is broader than Georgsmarienhütte, so exposed attributes explicitly keep
    the coverage label instead of pretending that every warning is GMH-specific.
    """

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    @staticmethod
    def _normalise_warning(item: dict[str, Any]) -> dict[str, Any]:
        payload = item.get("payload") or {}
        data = payload.get("data") or {}
        info = data.get("info") or []
        first_info = info[0] if info and isinstance(info[0], dict) else {}
        return {
            "id": item.get("id") or payload.get("id"),
            "provider": data.get("provider") or payload.get("source"),
            "headline": data.get("headline") or first_info.get("headline"),
            "severity": data.get("severity") or first_info.get("severity"),
            "urgency": data.get("urgency") or first_info.get("urgency"),
            "msg_type": data.get("msgType") or data.get("msg_type"),
            "sent": data.get("sent"),
            "effective": data.get("effective") or first_info.get("effective"),
            "onset": data.get("onset") or first_info.get("onset"),
            "expires": data.get("expires") or first_info.get("expires"),
            "description": data.get("description") or first_info.get("description"),
            "instruction": data.get("instruction") or first_info.get("instruction"),
            "web": data.get("web") or first_info.get("web"),
        }

    @classmethod
    def parse_warnings(cls, items: list[dict[str, Any]]) -> dict[str, Any]:
        warnings = [cls._normalise_warning(item) for item in items]
        warnings = [item for item in warnings if item.get("id") or item.get("headline")]
        warnings.sort(key=lambda item: item.get("sent") or item.get("effective") or "", reverse=True)
        return {
            "source": NINA_DASHBOARD_URL.format(ars=NINA_LANDKREIS_OSNABRUECK_ARS),
            "coverage": "Landkreis Osnabrück (enthält Georgsmarienhütte)",
            "ars": NINA_LANDKREIS_OSNABRUECK_ARS,
            "warning_count": len(warnings),
            "warnings": warnings,
        }

    async def get_warnings(self) -> dict[str, Any]:
        url = NINA_DASHBOARD_URL.format(ars=NINA_LANDKREIS_OSNABRUECK_ARS)
        headers = {"User-Agent": "Georgsmarthuette/0.1", "Accept": "application/json"}
        async with self._session.get(url, headers=headers, timeout=DEFAULT_TIMEOUT) as response:
            response.raise_for_status()
            data = await response.json(content_type=None)
        return self.parse_warnings(data if isinstance(data, list) else [])


class BnetzaChargingClient:
    """Load official public charging-station master data for Georgsmarienhütte.

    The Bundesnetzagentur CSV is large and updated infrequently, so this client keeps
    an in-memory daily cache instead of downloading ~50 MB every coordinator refresh.
    It provides master data only; no live occupancy/status is available there.
    """

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session
        self._cache_until: datetime | None = None
        self._cache: dict[str, Any] | None = None

    @staticmethod
    def _decimal(value: str | None) -> float | None:
        if not value:
            return None
        try:
            return float(value.replace(",", "."))
        except ValueError:
            return None

    @staticmethod
    def _int(value: str | None) -> int:
        try:
            return int(value or 0)
        except ValueError:
            return 0

    @staticmethod
    def _charging_points(row: dict[str, str]) -> list[dict[str, Any]]:
        points: list[dict[str, Any]] = []
        for index in range(1, 7):
            connector = row.get(f"Steckertypen{index}") or ""
            power = row.get(f"Nennleistung Stecker{index}") or ""
            public_key = row.get(f"Public Key{index}") or ""
            if connector or power or public_key:
                points.append({"connector": connector, "power_kw": BnetzaChargingClient._decimal(power), "public_key": public_key})
        return points

    @staticmethod
    def _summarise(rows: list[dict[str, str]]) -> dict[str, Any]:
        stations: list[dict[str, Any]] = []
        locations: dict[str, dict[str, Any]] = {}
        total_points = 0
        fast_points = 0
        max_power = 0.0

        for row in rows:
            point_count = BnetzaChargingClient._int(row.get("Anzahl Ladepunkte"))
            station_power = BnetzaChargingClient._decimal(row.get("Nennleistung Ladeeinrichtung [kW]")) or 0.0
            is_fast = "schnell" in (row.get("Art der Ladeeinrichtung") or "").lower()
            total_points += point_count
            if is_fast:
                fast_points += point_count
            max_power = max(max_power, station_power)
            address = " ".join(part for part in [row.get("Straße"), row.get("Hausnummer")] if part).strip()
            station = {
                "id": row.get("Ladeeinrichtungs-ID"),
                "operator": row.get("Betreiber"),
                "display_name": row.get("Anzeigename (Karte)"),
                "status": row.get("Status"),
                "type": row.get("Art der Ladeeinrichtung"),
                "charging_points": point_count,
                "power_kw": station_power,
                "commissioning_date": row.get("Inbetriebnahmedatum"),
                "address": address,
                "postcode": row.get("Postleitzahl"),
                "city": row.get("Ort"),
                "latitude": BnetzaChargingClient._decimal(row.get("Breitengrad")),
                "longitude": BnetzaChargingClient._decimal(row.get("Längengrad")),
                "location_name": row.get("Standortbezeichnung"),
                "parking_info": row.get("Informationen zum Parkraum"),
                "payment": row.get("Bezahlsysteme"),
                "opening_hours": row.get("Öffnungszeiten"),
                "connectors": BnetzaChargingClient._charging_points(row),
            }
            stations.append(station)

            location = locations.setdefault(address, {"address": address, "entries": 0, "charging_points": 0, "operators": set(), "powers_kw": set(), "types": set(), "latitude": station["latitude"], "longitude": station["longitude"]})
            location["entries"] += 1
            location["charging_points"] += point_count
            if station["operator"]:
                location["operators"].add(station["operator"])
            if station_power:
                location["powers_kw"].add(station_power)
            if station["type"]:
                location["types"].add(station["type"])

        public_locations = []
        for location in locations.values():
            public_locations.append({
                "address": location["address"],
                "entries": location["entries"],
                "charging_points": location["charging_points"],
                "operators": sorted(location["operators"]),
                "powers_kw": sorted(location["powers_kw"]),
                "types": sorted(location["types"]),
                "latitude": location["latitude"],
                "longitude": location["longitude"],
            })

        return {
            "station_count": len(stations),
            "location_count": len(public_locations),
            "charging_points": total_points,
            "fast_charging_points": fast_points,
            "normal_charging_points": total_points - fast_points,
            "max_power_kw": max_power or None,
            "stations": sorted(stations, key=lambda item: (item["address"] or "", item["id"] or "")),
            "locations": sorted(public_locations, key=lambda item: item["address"]),
            "source": BNETZA_CHARGING_REGISTER_CSV_URL,
            "source_page": BNETZA_CHARGING_REGISTER_PAGE_URL,
            "live_status_available": False,
        }

    async def _current_csv_url(self) -> str:
        headers = {"User-Agent": "Georgsmarthuette/0.1"}
        try:
            async with self._session.get(BNETZA_CHARGING_REGISTER_PAGE_URL, headers=headers, timeout=DEFAULT_TIMEOUT) as response:
                response.raise_for_status()
                html = await response.text()
            match = re.search(r'https://data\.bundesnetzagentur\.de/[^"\']+Ladesaeulenregister_BNetzA_[^"\']+\.csv', html)
            if match:
                return unescape(match.group(0))
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError):
            pass
        return BNETZA_CHARGING_REGISTER_CSV_URL

    async def get_georgsmarienhuette_charging(self) -> dict[str, Any]:
        now = datetime.now()
        if self._cache is not None and self._cache_until is not None and now < self._cache_until:
            return self._cache

        headers = {"User-Agent": "Georgsmarthuette/0.1"}
        csv_url = await self._current_csv_url()
        async with self._session.get(csv_url, headers=headers, timeout=CSV_DOWNLOAD_TIMEOUT) as response:
            response.raise_for_status()
            raw = await response.read()

        text = raw.decode("latin1", errors="ignore")
        lines = text.splitlines()
        header_index = next((index for index, line in enumerate(lines) if line.startswith("Ladeeinrichtungs-ID;")), 10)
        reader = csv.DictReader(io.StringIO("\n".join(lines[header_index:])), delimiter=";")
        rows = [row for row in reader if row.get("Postleitzahl") == "49124" and row.get("Ort") == "Georgsmarienhütte"]

        self._cache = self._summarise(rows)
        self._cache["source"] = csv_url
        self._cache_until = now + timedelta(hours=24)
        return self._cache

class GmhCityClient:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session
        self._parking_cache_until: datetime | None = None
        self._parking_cache: dict[str, Any] | None = None

    async def get_rss_items(self) -> list[RssItem]:
        async with self._session.get(GMH_NEWS_RSS_URL, timeout=DEFAULT_TIMEOUT) as response:
            response.raise_for_status()
            text = await response.text()
        root = ET.fromstring(text)
        items: list[RssItem] = []
        for item in root.findall("./channel/item"):
            enclosure = item.find("enclosure")
            items.append(RssItem(
                title=item.findtext("title", default=""),
                link=item.findtext("link", default=""),
                description=item.findtext("description", default=""),
                published=item.findtext("pubDate"),
                image=enclosure.attrib.get("url") if enclosure is not None else None,
            ))
        return items

    async def get_ris_summary(self) -> dict[str, Any]:
        async with self._session.get(GMH_RIS_URL, headers={"User-Agent": "Georgsmarthuette/0.1"}, timeout=DEFAULT_TIMEOUT) as response:
            response.raise_for_status()
            html = await response.text()
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", unescape(text)).strip()
        match = re.search(r"(Mo|Di|Mi|Do|Fr|Sa|So)\s+(\d{2}\.\d{2}\.\d{4})\s+([^\d]+?)\s+18:15-20:15\s+Uhr\s+-\s+([^\n]+?)(?=(Mo|Di|Mi|Do|Fr|Sa|So)\s+\d{2}\.\d{2}\.\d{4}|$)", text)
        if not match:
            return {"summary": None, "url": GMH_RIS_URL}
        return {"weekday": match.group(1), "date": match.group(2), "committee": match.group(3).strip(), "location": match.group(4).strip(), "summary": f"{match.group(2)} {match.group(3).strip()}", "url": GMH_RIS_URL}


    @staticmethod
    def _clean_html(value: str | None) -> str:
        if not value:
            return ""
        value = re.sub(r"<br\s*/?>", " ", value, flags=re.I)
        value = re.sub(r"<[^>]+>", " ", value)
        return re.sub(r"\s+", " ", unescape(value)).strip()

    @staticmethod
    def _utm32_to_latlon(easting: float, northing: float) -> tuple[float, float]:
        """Convert ETRS89/WGS84 UTM zone 32N to latitude/longitude.

        NOLIS Navigator exposes parking coordinates as UTM32 map coordinates.
        The ETRS89/WGS84 difference is irrelevant for HA map display here.
        """
        a = 6378137.0
        f = 1 / 298.257223563
        k0 = 0.9996
        e_sq = f * (2 - f)
        e_prime_sq = e_sq / (1 - e_sq)
        x = easting - 500000.0
        y = northing
        lon_origin = math.radians(9.0)

        m = y / k0
        mu = m / (a * (1 - e_sq / 4 - 3 * e_sq**2 / 64 - 5 * e_sq**3 / 256))
        e1 = (1 - math.sqrt(1 - e_sq)) / (1 + math.sqrt(1 - e_sq))

        j1 = 3 * e1 / 2 - 27 * e1**3 / 32
        j2 = 21 * e1**2 / 16 - 55 * e1**4 / 32
        j3 = 151 * e1**3 / 96
        j4 = 1097 * e1**4 / 512
        fp = mu + j1 * math.sin(2 * mu) + j2 * math.sin(4 * mu) + j3 * math.sin(6 * mu) + j4 * math.sin(8 * mu)

        sin_fp = math.sin(fp)
        cos_fp = math.cos(fp)
        tan_fp = math.tan(fp)
        c1 = e_prime_sq * cos_fp**2
        t1 = tan_fp**2
        n1 = a / math.sqrt(1 - e_sq * sin_fp**2)
        r1 = a * (1 - e_sq) / (1 - e_sq * sin_fp**2) ** 1.5
        d = x / (n1 * k0)

        lat = fp - (n1 * tan_fp / r1) * (
            d**2 / 2
            - (5 + 3 * t1 + 10 * c1 - 4 * c1**2 - 9 * e_prime_sq) * d**4 / 24
            + (61 + 90 * t1 + 298 * c1 + 45 * t1**2 - 252 * e_prime_sq - 3 * c1**2) * d**6 / 720
        )
        lon = lon_origin + (
            d
            - (1 + 2 * t1 + c1) * d**3 / 6
            + (5 - 2 * c1 + 28 * t1 - 3 * c1**2 + 8 * e_prime_sq + 24 * t1**2) * d**5 / 120
        ) / cos_fp

        return math.degrees(lat), math.degrees(lon)

    async def _parking_detail_coordinates(self, parking_id: str, owner: str = "22600") -> tuple[float | None, float | None]:
        async with self._session.post(
            "http://navigator.georgsmarienhuette.de/search/object-poi/",
            data={"id": parking_id, "owner": owner, "p": "0", "f": "0"},
            headers={"User-Agent": "Georgsmarthuette/0.1", "X-Requested-With": "XMLHttpRequest"},
            timeout=DEFAULT_TIMEOUT,
        ) as response:
            response.raise_for_status()
            html = await response.text()
        match = re.search(r"centerMarker\((\d+(?:\.\d+)?),(\d+(?:\.\d+)?)", html)
        if not match:
            return None, None
        return self._utm32_to_latlon(float(match.group(1)), float(match.group(2)))

    async def get_parking_locations(self) -> dict[str, Any]:
        now = datetime.now()
        if self._parking_cache is not None and self._parking_cache_until is not None and now < self._parking_cache_until:
            return self._parking_cache

        urls = [
            GMH_PARKING_URL,
            f"{GMH_PARKING_URL}?total=16&p0=2&naviID=914000621&brotID=914000621&id=851&no_search=1&ort=0&typ=1&site=81&owner=0&webcode_id=0&navi_typ=1",
        ]
        locations_by_id: dict[str, ParkingLocation] = {}
        for url in urls:
            async with self._session.get(url, headers={"User-Agent": "Georgsmarthuette/0.1"}, timeout=DEFAULT_TIMEOUT) as response:
                response.raise_for_status()
                html = await response.text()
            blocks = re.findall(r'<div class="style4 managerbox.*?(?=<div class="managertrenner|<div class="untere_pagination|<div class="pagination)', html, flags=re.S)
            for block in blocks:
                title_match = re.search(r"<span class='bezeichnung fn'>\s*(.*?)\s*</span>", block, flags=re.S)
                id_match = re.search(r'data-id="(\d+)"', block)
                owner_match = re.search(r'data-owner="(\d+)"', block)
                link_match = re.search(r'href="(http://navigator\.georgsmarienhuette\.de/poi-[^"]+)"', block)
                if not title_match or not id_match:
                    continue
                address_match = re.search(r"<span class='adr'>(.*?)</span>", block, flags=re.S)
                parking_id = id_match.group(1)
                owner = owner_match.group(1) if owner_match else "22600"
                latitude, longitude = await self._parking_detail_coordinates(parking_id, owner)
                name = self._clean_html(title_match.group(1))
                locations_by_id[parking_id] = ParkingLocation(
                    id=parking_id,
                    name=name,
                    address=self._clean_html(address_match.group(1) if address_match else ""),
                    category="Wanderparkplatz" if "wanderparkplatz" in name.lower() else "Parkplatz",
                    url=link_match.group(1) if link_match else f"http://navigator.georgsmarienhuette.de/poi-{parking_id}-{owner}.html",
                    latitude=latitude,
                    longitude=longitude,
                )

        locations = sorted(locations_by_id.values(), key=lambda item: item.name)
        self._parking_cache = {
            "location_count": len(locations),
            "regular_count": sum(1 for item in locations if item.category == "Parkplatz"),
            "hiking_count": sum(1 for item in locations if item.category == "Wanderparkplatz"),
            "locations": [asdict(item) for item in locations],
            "source": GMH_PARKING_URL,
            "live_status_available": False,
        }
        self._parking_cache_until = now + timedelta(hours=24)
        return self._parking_cache

    async def check_link_sources(self) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for key, url in GMH_LINK_SOURCES.items():
            try:
                async with self._session.get(url, headers={"User-Agent": "Georgsmarthuette/0.1"}, allow_redirects=True, timeout=LINK_CHECK_TIMEOUT) as response:
                    result[key] = {"url": str(response.url), "status": response.status, "available": response.status < 400}
            except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as err:
                result[key] = {"url": url, "status": None, "available": False, "error": str(err)}
        return result
