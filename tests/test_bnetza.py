from __future__ import annotations

import re
from datetime import datetime

import pytest
from aioresponses import aioresponses

from custom_components.georgsmarthuette.sources import (
    BNETZA_CHARGING_REGISTER_CSV_URL,
    BNETZA_CHARGING_REGISTER_PAGE_URL,
    BnetzaChargingClient,
)

_PAGE_URL = re.compile(r"https://www\.bundesnetzagentur\.de/.*")
_CSV_URL = re.compile(r"https://data\.bundesnetzagentur\.de/.*")

_CSV_HEADER = (
    "Ladeeinrichtungs-ID;Betreiber;Anzeigename (Karte);Status;"
    "Art der Ladeeinrichtung;Anzahl Ladepunkte;Nennleistung Ladeeinrichtung [kW];"
    "Inbetriebnahmedatum;Straße;Hausnummer;Postleitzahl;Ort;Breitengrad;Längengrad;"
    "Standortbezeichnung;Informationen zum Parkraum;Bezahlsysteme;Öffnungszeiten;"
    "Steckertypen1;Nennleistung Stecker1;Public Key1;"
    "Steckertypen2;Nennleistung Stecker2;Public Key2;"
    "Steckertypen3;Nennleistung Stecker3;Public Key3;"
    "Steckertypen4;Nennleistung Stecker4;Public Key4;"
    "Steckertypen5;Nennleistung Stecker5;Public Key5;"
    "Steckertypen6;Nennleistung Stecker6;Public Key6"
)

_CSV_GMH_ROW = (
    "DE001;Test GmbH;Teststation GMH;In Betrieb;Normalladeeinrichtung;2;22,0;"
    "01.01.2023;Bahnhofstraße;1;49124;Georgsmarienhütte;52,2020;8,0440;"
    "Bahnhof;Öffentlich;Girocard;24/7;"
    "Typ2;22,0;;;;;;;;;;;;;;;"
)

_CSV_OTHER_ROW = (
    "DE002;Other GmbH;Berlin Station;In Betrieb;Schnellladeeinrichtung;1;50,0;"
    "01.01.2024;Hauptstraße;5;12345;Berlin;52,5200;13,4050;"
    "Zentrum;Öffentlich;Alle;24/7;"
    "CCS;50,0;;;;;;;;;;;;;;;"
)

_MINIMAL_CSV = f"Preamble line\n{_CSV_HEADER}\n{_CSV_GMH_ROW}\n{_CSV_OTHER_ROW}\n"

_PAGE_WITH_CSV_LINK = (
    '<a href="https://data.bundesnetzagentur.de/Bundesnetzagentur/DE/Fachthemen/'
    'ElektrizitaetundGas/E-Mobilitaet/Ladesaeulenregister_BNetzA_2026-04-22.csv">CSV</a>'
)


class TestBnetzaDecimal:
    def test_converts_german_decimal(self):
        assert BnetzaChargingClient._decimal("22,5") == 22.5

    def test_converts_dot_decimal(self):
        assert BnetzaChargingClient._decimal("22.5") == 22.5

    def test_returns_none_for_empty(self):
        assert BnetzaChargingClient._decimal("") is None

    def test_returns_none_for_none(self):
        assert BnetzaChargingClient._decimal(None) is None


class TestBnetzaInt:
    def test_converts_integer_string(self):
        assert BnetzaChargingClient._int("2") == 2

    def test_returns_zero_for_empty(self):
        assert BnetzaChargingClient._int("") == 0

    def test_returns_zero_for_none(self):
        assert BnetzaChargingClient._int(None) == 0


class TestGetGeorgsmarienhuetteCharging:
    async def test_filters_by_postleitzahl(self, session):
        with aioresponses() as m:
            m.get(_CSV_URL, body=_MINIMAL_CSV.encode("latin1"))
            result = await BnetzaChargingClient(session).get_georgsmarienhuette_charging()
        assert result["station_count"] == 1

    async def test_accepts_utf8_encoded_csv(self, session):
        with aioresponses() as m:
            m.get(_CSV_URL, body=_MINIMAL_CSV.encode("utf-8"))
            result = await BnetzaChargingClient(session).get_georgsmarienhuette_charging()
        assert result["station_count"] == 1
        assert result["locations"][0]["address"] == "Bahnhofstraße 1"

    async def test_aggregates_charging_points(self, session):
        with aioresponses() as m:
            m.get(_CSV_URL, body=_MINIMAL_CSV.encode("latin1"))
            result = await BnetzaChargingClient(session).get_georgsmarienhuette_charging()
        assert result["charging_points"] == 2
        assert result["normal_charging_points"] == 2
        assert result["fast_charging_points"] == 0

    async def test_location_grouped_by_address(self, session):
        with aioresponses() as m:
            m.get(_CSV_URL, body=_MINIMAL_CSV.encode("latin1"))
            result = await BnetzaChargingClient(session).get_georgsmarienhuette_charging()
        assert result["location_count"] == 1
        assert result["locations"][0]["address"] == "Bahnhofstraße 1"

    async def test_caches_result_on_second_call(self, session):
        with aioresponses() as m:
            m.get(_CSV_URL, body=_MINIMAL_CSV.encode("latin1"))
            client = BnetzaChargingClient(session)
            first = await client.get_georgsmarienhuette_charging()
            # Second call must NOT make another HTTP request (no mock registered)
            second = await client.get_georgsmarienhuette_charging()
        assert first is second

    async def test_includes_coordinates(self, session):
        with aioresponses() as m:
            m.get(_CSV_URL, body=_MINIMAL_CSV.encode("latin1"))
            result = await BnetzaChargingClient(session).get_georgsmarienhuette_charging()
        loc = result["locations"][0]
        assert abs(loc["latitude"] - 52.2020) < 0.001
        assert abs(loc["longitude"] - 8.0440) < 0.001


class TestCurrentCsvUrl:
    async def test_discovers_url_from_page(self, session):
        with aioresponses() as m:
            m.get(_PAGE_URL, body=_PAGE_WITH_CSV_LINK)
            url = await BnetzaChargingClient(session)._current_csv_url()
        assert "Ladesaeulenregister_BNetzA_2026-04-22.csv" in url

    async def test_falls_back_to_constant_on_http_error(self, session):
        with aioresponses() as m:
            m.get(_PAGE_URL, status=503)
            url = await BnetzaChargingClient(session)._current_csv_url()
        assert url == BNETZA_CHARGING_REGISTER_CSV_URL

    async def test_falls_back_when_no_csv_link_found(self, session):
        with aioresponses() as m:
            m.get(_PAGE_URL, body="<html>Kein Link hier</html>")
            url = await BnetzaChargingClient(session)._current_csv_url()
        assert url == BNETZA_CHARGING_REGISTER_CSV_URL
