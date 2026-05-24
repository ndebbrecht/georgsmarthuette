from __future__ import annotations

import re
from datetime import date

import pytest
from aioresponses import aioresponses

from custom_components.georgsmarthuette.sources import (
    AWIGO_BASE_URL,
    AWIGO_WASTE_TYPES,
    AwigoClient,
)

_AWIGO = re.compile(r"https://www\.awigo\.de/.*")

_CITIES_HTML = '<option value="5348001">Georgsmarienhütte (49124)</option>'
_STREETS_HTML = '<option value="53480001">Bahnhofstraße</option>'
_NUMBERS_HTML = '<option value="5348000101">1</option>'

_DATES_PAYLOAD = [
    {"dataDay": "26.05.2026", "type": "1", "delayed": "0"},
    {"dataDay": "02.06.2026", "type": "2", "delayed": "0"},
    {"dataDay": "15.06.2026", "type": "1", "delayed": "1"},
]


class TestNorm:
    def test_strips_whitespace(self):
        assert AwigoClient._norm("  Hauptstraße  ") == "hauptstrasse"

    def test_expands_strasse(self):
        assert AwigoClient._norm("Bahnhofstraße") == "bahnhofstrasse"

    def test_expands_str_abbreviation(self):
        assert AwigoClient._norm("Bahnhofstr.") == "bahnhofstrasse"

    def test_collapses_inner_whitespace(self):
        # _norm collapses all whitespace runs via re.sub(r"\s+", " ", ...)
        assert AwigoClient._norm("Haupt  Straße") == "haupt strasse"


class TestOptions:
    def test_parses_value_and_label(self):
        html = '<option value="abc">Einige Label</option>'
        assert AwigoClient._options(html) == [("abc", "Einige Label")]

    def test_skips_empty_value(self):
        html = '<option value="">-- Ort wählen --</option><option value="1">Ort</option>'
        assert AwigoClient._options(html) == [("1", "Ort")]

    def test_skips_waehlen_label(self):
        html = '<option value="x">Bitte wählen</option>'
        assert AwigoClient._options(html) == []

    def test_strips_html_from_label(self):
        html = '<option value="1"><b>Label</b></option>'
        assert AwigoClient._options(html) == [("1", "Label")]

    def test_decodes_html_entities_in_label(self):
        html = '<option value="1">Geor&shy;gen</option>'
        result = AwigoClient._options(html)
        assert result[0][1] == "Geor\xadgen"


class TestResolveAddress:
    async def test_success(self, session):
        with aioresponses() as m:
            m.post(_AWIGO, body=_CITIES_HTML)
            m.post(_AWIGO, body=_STREETS_HTML)
            m.post(_AWIGO, body=_NUMBERS_HTML)
            addr = await AwigoClient(session).resolve_address("Bahnhofstraße", "1")
        assert addr.city_id == "5348001"
        assert addr.street_id == "53480001"
        assert addr.location_id == "5348000101"

    async def test_street_not_found_raises(self, session):
        with aioresponses() as m:
            m.post(_AWIGO, body=_CITIES_HTML)
            m.post(_AWIGO, body="<select></select>")
            with pytest.raises(ValueError, match="street not found"):
                await AwigoClient(session).resolve_address("Nichtexistent", "1")

    async def test_number_not_found_raises(self, session):
        with aioresponses() as m:
            m.post(_AWIGO, body=_CITIES_HTML)
            m.post(_AWIGO, body=_STREETS_HTML)
            m.post(_AWIGO, body="<select></select>")
            with pytest.raises(ValueError, match="house number not found"):
                await AwigoClient(session).resolve_address("Bahnhofstraße", "99")

    async def test_uses_default_city_id_when_city_not_found(self, session):
        with aioresponses() as m:
            m.post(_AWIGO, body="<select></select>")  # no cities → fallback
            m.post(_AWIGO, body=_STREETS_HTML)
            m.post(_AWIGO, body=_NUMBERS_HTML)
            addr = await AwigoClient(session).resolve_address("Bahnhofstraße", "1")
        assert addr.city_id == "5348001"  # AWIGO_GMH_CITY_ID fallback

    async def test_suffix_matching(self, session):
        numbers_html = '<option value="99">1a</option>'
        with aioresponses() as m:
            m.post(_AWIGO, body=_CITIES_HTML)
            m.post(_AWIGO, body=_STREETS_HTML)
            m.post(_AWIGO, body=numbers_html)
            addr = await AwigoClient(session).resolve_address("Bahnhofstraße", "1", suffix="a")
        assert addr.location_id == "99"


class TestGetDates:
    async def test_parses_dates_correctly(self, session):
        with aioresponses() as m:
            m.post(_AWIGO, payload=_DATES_PAYLOAD)
            dates = await AwigoClient(session).get_dates("loc1")
        assert len(dates) == 3
        assert dates[0].day == date(2026, 5, 26)
        assert dates[0].waste_type == "Restmüll"
        assert dates[0].delayed is False
        assert dates[2].delayed is True

    async def test_results_sorted_by_date(self, session):
        payload = [
            {"dataDay": "10.06.2026", "type": "1", "delayed": "0"},
            {"dataDay": "01.06.2026", "type": "2", "delayed": "0"},
        ]
        with aioresponses() as m:
            m.post(_AWIGO, payload=payload)
            dates = await AwigoClient(session).get_dates("loc1")
        assert dates[0].day < dates[1].day

    async def test_unknown_waste_type_has_fallback_label(self, session):
        payload = [{"dataDay": "01.06.2026", "type": "99", "delayed": "0"}]
        with aioresponses() as m:
            m.post(_AWIGO, payload=payload)
            dates = await AwigoClient(session).get_dates("loc1")
        assert dates[0].waste_type == "Typ 99"


class TestGetIcsUrl:
    async def test_returns_url(self, session):
        with aioresponses() as m:
            m.post(_AWIGO, body="https://www.awigo.de/calendar.ics")
            url = await AwigoClient(session).get_ics_url("loc1")
        assert url == "https://www.awigo.de/calendar.ics"

    async def test_returns_none_for_non_https_response(self, session):
        with aioresponses() as m:
            m.post(_AWIGO, body="Kein Link vorhanden")
            url = await AwigoClient(session).get_ics_url("loc1")
        assert url is None
