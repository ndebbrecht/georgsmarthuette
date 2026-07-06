# Home Assistant entity model

Georgsmarthütte uses Home Assistant platforms according to the kind of data being exposed.

## Sensors

Sensors are used for values that can be displayed or automated against:

- next AWIGO collection dates
- weather and air-quality values
- pollen values
- Düte water level
- next train departures
- aggregate parking counts
- aggregate charging counts and maximum power
- latest city news / next council session
- source availability checks

## Binary sensors

Binary sensors represent alert/problem state:

- weather warning proxy
- Düte flood warning
- air-quality warning
- GMH-relevant VOS disruption notices
- GMH-relevant Landkreis roadworks
- city RSS traffic/construction notices
- NINA/warnung.bund.de warnings
- source errors

## Cameras

Public JPEG snapshots are exposed as still-image camera entities.

## Geo-location

Static map-relevant points are exposed as `geo_location` entities instead of being modeled as dozens of pseudo-sensors.

Currently included:

- city parking POIs
- charging locations from the Bundesnetzagentur register

This better matches the Home Assistant map UX and keeps dashboard sensors focused on aggregate values.

## What is intentionally not modeled as live state

- Parking occupancy is not available from the city source.
- Charging free/busy/defect status is not available from the Bundesnetzagentur register.

Those sources are therefore marked with `live_status_available: false`.
