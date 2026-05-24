# Maintenance

This project is proactively maintained for public Georgsmarienhütte / Smart-City data sources that are useful in Home Assistant.

## Maintenance cadence

A weekly maintenance check looks for new or changed public sources, especially:

- Stadt Georgsmarienhütte pages, RSS and RIS
- Stadtwerke Georgsmarienhütte mobility/energy/water information
- local newspaper leads from Neue Osnabrücker Zeitung (NOZ) and Blickpunkt, used only as discovery signals and not as republished article content
- VOS public transport disruptions, GTFS or GTFS-RT possibilities
- Landkreis Osnabrück roadworks and traffic notices
- DWD/NINA warning endpoints
- EV charging live-status possibilities
- parking, flood/water, weather, events and road closures
- Smart-City, LoRaWAN, Open-Data or sensor projects around GMH

## Criteria for adding a source

A source should be added when it is:

- public and legally/ethically reasonable to poll
- stable enough for a Home Assistant integration
- locally relevant to Georgsmarienhütte
- useful as a sensor, binary sensor, camera or geo-location entity
- documented with source URL and limitations

Avoid adding data that only looks live but is actually stale/static. Prefer clear attributes like `live_status_available: false` over fake availability.

## Maintenance workflow

1. Inspect repository status.
2. Check existing source documentation.
3. Research public source changes.
4. Implement only if the source passes the criteria above.
5. Update documentation.
6. Run at least:

```bash
python3 -m py_compile custom_components/georgsmarthuette/*.py
```

7. Run a lightweight live smoke check when source parsing changed.
8. Commit and push.

## Boundaries

Do not contact the city, Stadtwerke, operators or third parties without explicit approval. Repository maintenance and public-source research are okay; outbound messages are separate.
