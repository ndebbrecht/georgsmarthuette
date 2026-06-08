# Georgsmarthütte

Home-Assistant/HACS custom integration for public local data around Georgsmarienhütte, Germany.

The integration collects scattered public data sources and exposes them in Home Assistant as normal sensors, binary sensors, cameras and geo-location entities. It is inspired by municipal Smart-City approaches such as Solingen's Open SmartCity stack, but intentionally uses sources that are already publicly reachable for Georgsmarienhütte.

> Status: prototype / early public release. Syntax checks pass, but live testing inside a Home Assistant dev instance is still the next important step.

## Features

### AWIGO waste collection calendar

Address-based collection calendar using AWIGO's public AJAX endpoints:

- next collection overall
- next collection per waste type
- attributes for date, waste type, delay flag, mobile collection location and generated ICS URL

### Weather and air quality

Open-Meteo based sensors for configured GMH coordinates:

- temperature, apparent temperature, humidity, pressure
- wind speed, gusts and direction
- rain, precipitation and precipitation probability
- UV index and cloud cover
- EU AQI, PM10, PM2.5, NO₂ and ozone

### Pollen

DWD pollen data for the Niedersachsen/Bremen region:

- Hasel, Erle, Birke, Gräser, Roggen, Beifuß, Ambrosia

### Düte / flood monitoring

NLWKN Pegelonline integration for the Düte station Wersen:

- current water level when available
- warning-level attributes
- flood warning binary sensor

### City cameras

Still-image camera entities for public GMH webcam snapshots:

- Rathaus / Oeseder Straße
- Rathausplatz / Oeseder Kirmes
- Hochwasser Breenbach
- Hochwasser Suttmeyers Wiesen
- Hochwasser Malbergen
- Hochwasser Eisenbahnstraße

### Rail / public transport

Finalrewind departure-board JSON for the RB75 / Haller Willem stations:

- Oesede: next departure, next toward Osnabrück, next toward Bielefeld
- Kloster Oesede: next departure, next toward Osnabrück, next toward Bielefeld

VOS disruption/roadworks notices:

- public VOS disruption page parsed conservatively from visible HTML
- filtered for GMH-relevant place names and regular local lines
- count sensor, latest relevant notice sensor and problem binary sensor
- attributes include affected lines, description, links and source URL

Landkreis Osnabrück roadworks notices:

- public Landkreis traffic/roadworks accordion page parsed conservatively from visible HTML
- filtered for GMH-relevant place and road terms such as Georgsmarienhütte, Oesede, Harderberg, B51 and Osnabrück-Nahne
- count sensor, latest relevant roadwork sensor and problem binary sensor
- attributes include title, period, summary and source URL

### Parking and charging, Home-Assistant style

The integration exposes parking and charging in two layers:

1. Aggregate sensors for dashboards and automations.
2. `geo_location` entities so the locations appear on the Home Assistant map like other POI-style integrations.

Parking data:

- scraped from the city's public parking POI page
- 16 known parking locations, including regular and hiking parking locations
- coordinates resolved from the NOLIS Navigator detail endpoint
- no live occupancy data available

Charging data:

- official Bundesnetzagentur Ladesäulenregister CSV
- filtered to `49124 Georgsmarienhütte`
- 24h in-memory cache to avoid repeatedly downloading the large CSV
- total charging points, station entries, locations, fast/normal charging points and max power
- location/station attributes: operators, address, coordinates, connector types, payment methods and opening hours
- no live free/busy status available from this source

### City information and source health

- latest city RSS item
- next RIS council/committee session where parseable
- availability/link sensors for relevant public data sources
- NINA/warnung.bund.de warning count, latest official warning and warning binary sensor
- source-error binary sensor

## Installation via HACS custom repository

Until the integration is accepted into any default HACS repository list:

1. In Home Assistant, open HACS.
2. Open the three-dot menu.
3. Choose **Custom repositories**.
4. Add this repository URL.
5. Category: **Integration**.
6. Install **Georgsmarthütte**.
7. Restart Home Assistant.
8. Add the integration via **Settings → Devices & services → Add integration**.

## Manual installation

Copy this folder into your Home Assistant config directory:

```text
custom_components/georgsmarthuette
```

Then restart Home Assistant and add the integration through the UI.

## Configuration

The config flow asks for:

- AWIGO city, default: `Georgsmarienhütte`
- AWIGO street
- AWIGO house number
- optional house-number suffix
- latitude/longitude for weather, defaulting to GMH
- optional custom camera URL

Example AWIGO values known to work during research:

- city ID: `5348001`
- Oeseder Straße street ID: `13655001`
- Oeseder Straße 85 location ID: `656422001`

You normally do not need to enter these IDs manually; the integration resolves them from the address.

## Entity model

Platforms:

- `sensor`
- `binary_sensor`
- `camera`
- `geo_location`

The `geo_location` platform is used for static POIs such as parking and charging locations because this fits Home Assistant's map model better than pretending every POI is a live sensor. Aggregate counts remain normal sensors.

## Limitations

- Parking: static POI data only; no free/busy count.
- Charging: official master data only; no live availability or defect status.
- Düte: NLWKN may return no current water-level value for Wersen; warning levels are still exposed.
- NINA warnings are exposed via the official county-level Landkreis Osnabrück ARS endpoint, so a warning may cover the wider county rather than only Georgsmarienhütte.
- Some city sources are exposed as availability/link sensors because no stable public API was found.
- The Bundesnetzagentur CSV URL changes over time; the integration tries to discover the current CSV from the official download page and falls back to the last known URL.

## Development

Run a syntax check:

```bash
python3 -m py_compile custom_components/georgsmarthuette/*.py
```

Recommended next runtime check:

1. Copy or symlink the integration into a Home Assistant dev config.
2. Start Home Assistant Core.
3. Add the integration via UI.
4. Verify config flow, entity creation and coordinator refresh.

## Documentation

- `docs/data-sources.md` — endpoints and technical source notes
- `docs/smart-city-research.md` — Smart-City comparison and future data-source ideas
- `docs/home-assistant-model.md` — why data is modeled as sensors, binary sensors, cameras or geo-location entities
- `docs/next-steps.md` — recommended next implementation steps
- `docs/maintenance.md` — maintenance cadence, source criteria and boundaries

## License

MIT
