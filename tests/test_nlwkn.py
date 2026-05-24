from __future__ import annotations

import re
import pytest
from aioresponses import aioresponses

from custom_components.georgsmarthuette.sources import NLWKN_BASE_URL, NlwknClient

_URL = re.compile(r"https://bis\.azure-api\.net/.*")

_STATION_PAYLOAD = {
    "getPegelDatenspurenResult": {
        "Name": "Wersen",
        "GewaesserName": "Düte",
        "STA_ID": 116,
        "Parameter": [
            {
                "Datenspuren": [
                    {
                        "AktuellerMesswert": 72.5,
                        "Meldestufen": [
                            {"Wert": 100, "Name": "Meldestufe 1"},
                            {"Wert": 200, "Name": "Meldestufe 2"},
                        ],
                    }
                ]
            }
        ],
    }
}


class TestNlwknClient:
    async def test_returns_station_data(self, session):
        with aioresponses() as m:
            m.get(_URL, payload=_STATION_PAYLOAD)
            result = await NlwknClient(session).get_duete_wersen()
        station = result["getPegelDatenspurenResult"]
        assert station["Name"] == "Wersen"
        assert station["GewaesserName"] == "Düte"

    async def test_current_measurement_accessible(self, session):
        with aioresponses() as m:
            m.get(_URL, payload=_STATION_PAYLOAD)
            result = await NlwknClient(session).get_duete_wersen()
        station = result["getPegelDatenspurenResult"]
        level = station["Parameter"][0]["Datenspuren"][0]["AktuellerMesswert"]
        assert level == 72.5

    async def test_warning_levels_present(self, session):
        with aioresponses() as m:
            m.get(_URL, payload=_STATION_PAYLOAD)
            result = await NlwknClient(session).get_duete_wersen()
        levels = result["getPegelDatenspurenResult"]["Parameter"][0]["Datenspuren"][0]["Meldestufen"]
        assert len(levels) == 2
        assert levels[0]["Wert"] == 100

    async def test_raises_on_http_error(self, session):
        import aiohttp
        with aioresponses() as m:
            m.get(_URL, status=403)
            with pytest.raises(aiohttp.ClientResponseError):
                await NlwknClient(session).get_duete_wersen()
