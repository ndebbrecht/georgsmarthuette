from __future__ import annotations

import pytest
from aioresponses import aioresponses

from custom_components.georgsmarthuette.sources import DWD_POLLEN_URL, DwdClient

_POLLEN_PAYLOAD = {
    "content": [
        {
            "region_name": "Bayern",
            "partregion_name": "",
            "Pollen": {"Hasel": {"today": "3"}},
        },
        {
            "region_name": "Niedersachsen",
            "partregion_name": "West",
            "Pollen": {
                "Hasel": {"today": "0"},
                "Erle": {"today": "2"},
                "Graeser": {"today": "1"},
            },
        },
        {
            "region_name": "Nordrhein-Westfalen",
            "partregion_name": "",
            "Pollen": {"Hasel": {"today": "1"}},
        },
    ]
}


class TestDwdClient:
    async def test_returns_niedersachsen_region(self, session):
        with aioresponses() as m:
            m.get(DWD_POLLEN_URL, payload=_POLLEN_PAYLOAD)
            result = await DwdClient(session).get_pollen()
        assert result["region_name"] == "Niedersachsen"
        assert result["Pollen"]["Erle"]["today"] == "2"

    async def test_matches_partregion_hint(self, session):
        payload = {
            "content": [
                {"region_name": "Nord", "partregion_name": "Bremen", "Pollen": {"X": {"today": "0"}}},
            ]
        }
        with aioresponses() as m:
            m.get(DWD_POLLEN_URL, payload=payload)
            result = await DwdClient(session).get_pollen()
        assert result["partregion_name"] == "Bremen"

    async def test_falls_back_to_first_region_when_no_hint_matches(self, session):
        payload = {
            "content": [
                {"region_name": "Bayern", "partregion_name": "Alpen", "Pollen": {}},
                {"region_name": "Hessen", "partregion_name": "", "Pollen": {}},
            ]
        }
        with aioresponses() as m:
            m.get(DWD_POLLEN_URL, payload=payload)
            result = await DwdClient(session).get_pollen()
        assert result["region_name"] == "Bayern"

    async def test_returns_empty_dict_when_no_regions(self, session):
        with aioresponses() as m:
            m.get(DWD_POLLEN_URL, payload={"content": []})
            result = await DwdClient(session).get_pollen()
        assert result == {}

    async def test_raises_on_http_error(self, session):
        import aiohttp
        with aioresponses() as m:
            m.get(DWD_POLLEN_URL, status=503)
            with pytest.raises(aiohttp.ClientResponseError):
                await DwdClient(session).get_pollen()
