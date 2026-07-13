# Next steps

This project is useful already as a local public-data aggregator, but the next steps should focus on Home Assistant runtime quality before adding too many more sources.

## 1. Runtime hardening

- Test the config flow in a real Home Assistant dev instance.
- Verify entity creation for all platforms: sensor, binary_sensor, camera, geo_location.
- Confirm that static parking/charging geo-location entities are created after first coordinator refresh.
- Add issue handling if one source fails but the integration as a whole remains useful.

## 2. Better Home Assistant entity model

- Add device/entity categories where appropriate.
- Mark source-health/link sensors as diagnostic entities.
- Add icons and translations for all sensor descriptions.
- Consider disabled-by-default entities for very noisy/diagnostic sources.

## 3. Parking and charging live data

Current implementation exposes official/static data only.

Potential next research targets:

- ladenetz / Stadtwerke live status
- EnBW public app/API endpoints
- EWE Go endpoints
- eliso/VINCharge endpoints
- OCPI/OICP roaming data if a public route exists

Only add live availability if the endpoint is stable and acceptable to poll from a Home Assistant integration.

## 4. Traffic and public transport

- VOS disruptions/roadworks are implemented; monitor parser robustness and replace with GTFS-RT/API if VOS/VBN expose one.
- Landkreis Osnabrück roadworks are implemented with conservative GMH filtering; monitor parser robustness and noise level.
- VBN/Connect GTFS-Realtime is publicly documented and live at `http://gtfsr.vbn.de/gtfsr_connect.json`, but the feed is large and ID-based. Before adding entities, build a small cached GTFS-Static mapping for GMH-relevant stops/routes, then filter GTFS-RT updates against that mapping.

## 5. Warnings

- NINA/warnung.bund.de warnings are implemented via the official Landkreis Osnabrück ARS endpoint. Monitor whether a stable municipality-level endpoint becomes available.
- Replace the simple Open-Meteo weather-warning proxy with official direct DWD warning data if a stable endpoint/cell mapping is confirmed.

## 6. City data classification

- RSS item topic counts are implemented for traffic/construction, weather/flooding, events and administration.
- A problem binary sensor now exposes current traffic/construction matches from the same official city RSS feed.
- A safety binary sensor now exposes current city RSS matches for weather, flooding, heat, drought and water-saving advisories.
- Monitor whether the city RSS gains explicit categories; if so, prefer those over keyword classification.
- Consider binary sensors for high-impact categories only if the keyword results prove useful and not noisy.

## 7. Release hygiene

- Add proper tests once Home Assistant test dependencies are available.
- Add HACS validation if useful.
- Tag versions and maintain a changelog.
