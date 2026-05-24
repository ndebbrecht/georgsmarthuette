from __future__ import annotations

import re
import pytest
from aioresponses import aioresponses

from custom_components.georgsmarthuette.sources import (
    OPEN_METEO_AIR_QUALITY_URL,
    OPEN_METEO_FORECAST_URL,
    OpenMeteoClient,
)

_FORECAST = re.compile(r"https://api\.open-meteo\.com/.*")
_AIR = re.compile(r"https://air-quality-api\.open-meteo\.com/.*")

_WEATHER_PAYLOAD = {
    "current": {
        "temperature_2m": 18.3,
        "relative_humidity_2m": 72,
        "apparent_temperature": 16.8,
        "precipitation": 0.0,
        "rain": 0.0,
        "weather_code": 1,
        "cloud_cover": 25,
        "pressure_msl": 1015.2,
        "wind_speed_10m": 12.4,
        "wind_direction_10m": 245,
        "wind_gusts_10m": 28.8,
    },
    "hourly": {
        "precipitation_probability": [10, 15, 20],
        "uv_index": [2.1, 3.4, 4.0],
    },
}

_AIR_PAYLOAD = {
    "current": {
        "european_aqi": 22,
        "pm10": 8.4,
        "pm2_5": 4.1,
        "nitrogen_dioxide": 12.3,
        "ozone": 68.0,
    }
}


class TestOpenMeteoClient:
    async def test_get_weather_returns_current(self, session):
        with aioresponses() as m:
            m.get(_FORECAST, payload=_WEATHER_PAYLOAD)
            result = await OpenMeteoClient(session).get_weather(52.202, 8.044)
        assert result["current"]["temperature_2m"] == 18.3
        assert result["hourly"]["precipitation_probability"] == [10, 15, 20]

    async def test_get_weather_includes_all_current_variables(self, session):
        with aioresponses() as m:
            m.get(_FORECAST, payload=_WEATHER_PAYLOAD)
            result = await OpenMeteoClient(session).get_weather(52.202, 8.044)
        assert "current" in result
        assert "hourly" in result

    async def test_get_air_quality_returns_aqi(self, session):
        with aioresponses() as m:
            m.get(_AIR, payload=_AIR_PAYLOAD)
            result = await OpenMeteoClient(session).get_air_quality(52.202, 8.044)
        assert result["current"]["european_aqi"] == 22
        assert result["current"]["pm10"] == 8.4

    async def test_get_weather_raises_on_http_error(self, session):
        import aiohttp
        with aioresponses() as m:
            m.get(_FORECAST, status=500)
            with pytest.raises(aiohttp.ClientResponseError):
                await OpenMeteoClient(session).get_weather(52.202, 8.044)
