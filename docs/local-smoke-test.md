# Local smoke test

Last run: 2026-05-24.

The local machine does not currently have Home Assistant or aiohttp installed, so this smoke test validates the external data sources and parsing logic with the Python standard library where possible.

Result: 9/9 checks passed.

Checked live sources:

- Open-Meteo weather: temperature, humidity, wind returned.
- Open-Meteo air quality: AQI, PM10 and PM2.5 returned.
- Finalrewind Oesede: 6 departures returned; next departure toward Osnabrück.
- Finalrewind Kloster Oesede: 6 departures returned; next departure toward Osnabrück.
- AWIGO example address IDs: 16 future collection items returned; next example date 2026-05-27, type 4.
- GMH RSS: 10 items returned.
- GMH parking page/NOLIS detail parsing: sample coordinates resolved successfully, e.g. Oesede Bahnhof P+R around 52.20849, 8.06490.
- Bundesnetzagentur charging CSV: 27 rows for 49124 Georgsmarienhütte, 54 charging points, 28 fast-charging points, max 400 kW, 14 locations.
- Camera samples: Rathaus and Rathausplatz images returned valid JPEG bytes.

Known local limitation:

- Full Home Assistant runtime import/entity setup was not executed locally because `homeassistant` and `aiohttp` are not installed in the current standalone Python environment.
- Syntax validation still passes via `python3 -m py_compile custom_components/georgsmarthuette/*.py`.
