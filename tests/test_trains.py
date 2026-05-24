from __future__ import annotations

import re
import pytest
from aioresponses import aioresponses

from custom_components.georgsmarthuette.sources import FINALREWIND_BASE_URL, TrainDeparturesClient

_URL = re.compile(r"https://dbf\.finalrewind\.org/.*")

_DEPARTURES_PAYLOAD = {
    "departures": [
        {
            "scheduledDeparture": "08:15",
            "destination": "Osnabrück Hbf",
            "train": "RB 75",
            "trainNumber": 75123,
            "delayDeparture": 0,
            "isCancelled": False,
            "platform": "1",
        },
        {
            "scheduledDeparture": "09:15",
            "destination": "Bielefeld Hbf",
            "train": "RB 75",
            "trainNumber": 75124,
            "delayDeparture": 3,
            "isCancelled": False,
            "platform": "1",
        },
    ]
}


class TestTrainDeparturesClient:
    async def test_returns_departures_list(self, session):
        with aioresponses() as m:
            m.get(_URL, payload=_DEPARTURES_PAYLOAD)
            departures = await TrainDeparturesClient(session).get_departures("HOES")
        assert len(departures) == 2
        assert departures[0]["destination"] == "Osnabrück Hbf"
        assert departures[1]["delayDeparture"] == 3

    async def test_returns_empty_list_when_no_departures_key(self, session):
        with aioresponses() as m:
            m.get(_URL, payload={"other": "data"})
            departures = await TrainDeparturesClient(session).get_departures("HOES")
        assert departures == []

    async def test_returns_empty_list_when_response_is_not_dict(self, session):
        with aioresponses() as m:
            m.get(_URL, payload=[])
            departures = await TrainDeparturesClient(session).get_departures("HOES")
        assert departures == []

    async def test_raises_on_http_error(self, session):
        import aiohttp
        with aioresponses() as m:
            m.get(_URL, status=404)
            with pytest.raises(aiohttp.ClientResponseError):
                await TrainDeparturesClient(session).get_departures("HOES")
