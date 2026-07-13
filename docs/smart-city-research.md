# Smart-City-Recherche: GMH Datenquellen nach Solingen-Vorbild

Stand: 2026-05-24.

## Solingen als Referenz

Solingen bietet mit Open SmartCity Hub / Open SmartCity Home eine deutlich reifere Architektur:

- urbane Datenplattform aus unterschiedlichen Quellen
- App und öffentliche Displays
- Masterportal/Kartenportal
- RabbitMQ → MQTT → Home Assistant/OpenHAB/ioBroker über Open SmartCity Home
- Sensorik für Mobilität, Umwelt, Entsorgung, Beleuchtung/Sicherheit und Warnungen

Für Georgsmarienhütte ist nicht dieselbe zentrale Plattform auffindbar. Stattdessen gibt es verstreute, teils gut nutzbare öffentliche Quellen.

## Bahnhöfe / RB75 Haller Willem

Stadtseite bestätigt:

- Bahnhöfe Oesede und Kloster Oesede
- RB75 / Haller Willem
- tagsüber stündlich Richtung Osnabrück bzw. Bielefeld
- Betreiber/Info: NordWestBahn

Quelle Stadt:

- https://www.georgsmarienhuette.de/stadt/daten-fakten-mobilitaet/mit-dem-oepnv-unterwegs/

Gefundene technische Daten:

### Oesede

- DS100: `HOES`
- IBNR/EVA: `8004628`
- Koordinaten: ca. `52.2087, 8.0642`
- Finalrewind JSON: `https://dbf.finalrewind.org/HOES.json`
- DB-Tafel alt: `http://reiseauskunft.bahn.de/bin/bhftafel.exe/dn?evaId=8004628&boardType=dep&time=actual&productsDefault=1111101&rt=1&start=yes`

### Kloster Oesede

- DS100: `HKOE`
- Koordinaten: ca. `52.2006, 8.1116`
- Finalrewind JSON: `https://dbf.finalrewind.org/HKOE.json`

Die Finalrewind-JSON liefert u.a.:

- `scheduledDeparture`
- `destination`
- `train` / `trainNumber`
- `delayDeparture`
- `isCancelled`
- `via`
- `missingRealtime`

Umsetzung im Plugin: Sensoren für nächste Abfahrt insgesamt sowie Richtung Osnabrück und Richtung Bielefeld je Bahnhof.

## Bus / VOS

Stadtseite nennt Linien:

- 451 AnrufBus
- 452 RegioBus
- 463/464 Hagen/Tannenkamp - Oesede - Osnabrück
- 465/466 Bad Rothenfelde/Glandorf - Bad Laer - Bad Iburg - Osnabrück
- 467 Bad Rothenfelde - Dissen - Kloster Oesede - Oesede - Osnabrück
- 468 Borgloh - Kloster Oesede - Dröper - Oesede - Osnabrück
- M3 Hagen - Holzhausen - Osnabrück
- S40 Bad Laer - Glandorf - Bad Iburg - Georgsmarienhütte - Osnabrück

VOS-Störungen/Baustellen sind öffentlich als Webseite verfügbar:

- https://www.vos.info/fahrplan/stoerungen-baustellen/

Diese Seite enthält GMH-relevante Baustellen/Umleitungen, z.B. Harderberg/Nordstraße, B51 Richtung Oesede und Oeseder Straße.

Plugin-Umsetzung 25.05.2026:

- konservatives HTML-Parsing der sichtbaren Akkordeon-Einträge
- Filter nach GMH-Ortsbegriffen und regelmäßig relevanten Linien
- Sensoren für relevante Anzahl und neuesten relevanten Hinweis
- Binary-Sensor für aktuelle relevante VOS-Verkehrsstörung

Recherche-Update 22.06.2026:

- Der VBN dokumentiert offene GTFS-Static-Daten über Connect Fahrplanauskunft und GTFS-Realtime-Prognosedaten unter `http://gtfsr.vbn.de/gtfsr_connect.json` und `.bin`.
- GTFS.DE nennt VBN als enthaltene Agentur im freien GTFS-RT-Stream.
- Der direkte VBN-JSON-Smoke-Test lieferte HTTP 200, war aber ca. 20 MB groß und enthält ohne lokale GTFS-Static-Zuordnung nur IDs (`routeId`, `tripId`, `stopId`).

Bewertung: stabile öffentliche Forschungsrichtung für echte Bus-Echtzeitdaten, aber noch nicht einbauen. Nächster sinnvoller Schritt wäre eine lokale, gecachte Static-GTFS-Auswertung für GMH-relevante Haltestellen/Linien; erst danach lassen sich GTFS-RT-Delays sauber und ohne riesige Attribute modellieren.

## Straßenbaumaßnahmen / Verkehr

Gefundene Quellen:

- Stadtseite „Aktuelle Straßenbaumaßnahmen“: https://www.georgsmarienhuette.de/portal/seiten/aktuelle-strassenbaumassnahmen-914001552-22600.html
- Landkreis Osnabrück Verkehrs-/Baustellenmeldungen: https://www.landkreis-osnabrueck.de/fachthemen/ordnung-und-verkehr/baustellen-und-blitzplan
- VOS Baustellen/Umleitungen: https://www.vos.info/fahrplan/stoerungen-baustellen/

Bewertung:

- Stadtseite ist eher statisch/übersichtlich, aktuell ohne klar strukturierte Einzelmeldungen im Abruf.
- Landkreis-Seite enthält viele Meldungen als Text; nach `Georgsmarienhütte`, `Oesede`, `Harderberg`, `B51`, `Kloster Oesede` filterbar.
- VOS-Seite ist für konkrete ÖPNV-Auswirkungen sehr wertvoll.

Plugin-Umsetzung 08.06.2026:

- Landkreis-Baustellen werden konservativ aus der öffentlichen Akkordeonseite gelesen und nach GMH-Orts-/Straßenbegriffen gefiltert.
- Sensoren: relevante Anzahl und neueste relevante Landkreis-Baustelle.
- Binary-Sensor: relevante Landkreis-Baustelle/Verkehrseinschränkung vorhanden.
- Attribute: Quelle, Zeitraum, Beschreibung und gefilterte Einträge.

Live-Smoke-Test fand aktuell 2 relevante Einträge: A30-Anschlussstelle Osnabrück-Nahne Richtung B51/B68 und B51/B68 zwischen OS-Nahne und GMHütte.

## E-Mobilität / Ladepunkte

Stadtwerke-Seite:

- https://www.sw-gmhuette.de/de/Mobilitaet-Zukunft/E-Ladestation/

Stadtseite:

- https://www.georgsmarienhuette.de/stadt/daten-fakten-mobilitaet/e-mobilitaet/

Gefundene Ladeorte laut Stadt/Stadtwerke:

- Malberger Mühle, Malberger Straße 13
- Kundenzentrum Stadtwerke, Am Rathaus 12 / Stadtwerke Mobility-Point am Rathaus 16
- Adler Modemarkt, Brüsseler Straße 3, Schnellladestation
- Möbelhaus Dransmann, Im Loh 40
- AWIGO, Niedersachsenstraße 17
- Autohaus Hülsmann & Tegeler, Topsloh 2-6
- Panoramabad, Carl-Stahmer-Weg 37, E-Bike
- Marktplatz Kloster Oesede, Am Markt 1, E-Bike
- Zentrum Süd / Oeseder Straße / Ramat-Hasharon-Platz wird auf der Stadtwerke-Seite zusätzlich genannt

Offizielle maschinenlesbare Quelle:

- Bundesnetzagentur Ladesäulenregister Downloadseite: https://www.bundesnetzagentur.de/DE/Fachthemen/ElektrizitaetundGas/E-Mobilitaet/DownloadundKontakt.html
- CSV-Datenstand 22.04.2026: `Ladesaeulenregister_BNetzA_2026-04-22.csv`

Filter `Postleitzahl=49124`, `Ort=Georgsmarienhütte` ergab:

- 27 Ladeeinrichtungs-Einträge
- 54 Ladepunkte
- 14 zusammengefasste Ladeorte
- maximale Ladeleistung: 400 kW
- Betreiber u.a. Stadtwerke Georgsmarienhütte, Q1, EnBW, EWE Go, Vattenfall, VINCharge/eliso, Deutsche Primärenergie

Weitere auffindbare Drittquellen:

- ChargeFinder
- Chargemap
- GoingElectric
- ladenetz.de

Bewertung:

- Bundesnetzagentur ist die beste offizielle Stammdatenquelle und jetzt im Plugin eingebaut.
- Die CSV ist groß, daher cached der Plugin-Client die GMH-Auswertung für 24 Stunden.
- Live-Verfügbarkeit/frei/belegt/defekt ist dort nicht enthalten. Dafür bräuchte man ladenetz/OCPI/Hubject oder Anbieter-APIs; auf Stadt/Stadtwerke-Seite nicht direkt öffentlich dokumentiert.

Plugin-Umsetzung:

- Aggregat-Sensoren für Ladepunkte, Ladeeinrichtungen, Standorte, Schnellladepunkte, Normalladepunkte und maximale Ladeleistung.
- Standort- und Stationsdaten als Attribute: Adresse, Betreiber, Koordinaten, Ladeleistung, Steckertypen, Zahlungsarten und Öffnungszeiten.
- später Live-Verfügbarkeit, wenn eine öffentliche API zuverlässig nutzbar ist.

## Parkplätze

Stadtseite:

- https://www.georgsmarienhuette.de/stadt/erster-ueberblick/parkplaetze/

Bewertung:

- Öffentliche statische Parkplatzdaten/POIs ja.
- Keine Hinweise auf Live-Belegungssensorik wie in Solingen gefunden.

## Hochwasser / Düte

Bereits gefunden:

- NLWKN Pegelonline, Düte-Pegel Wersen `STA_ID=116`
- Stadt-Hochwasserschutzkameras

Das ist für GMH einer der stärksten realen Smart-City-Datenbereiche.

## Stadtwerke / Smart-City / LoRaWAN

Gesucht nach Stadtwerke GMH + Smart City, LoRaWAN, Sensoren, Parken, Ladesäulen-API.

Ergebnis:

- E-Ladestationen und Mobilitätskonzept auffindbar.
- Keine öffentliche Smart-City-, LoRaWAN-, Parkplatzsensorik- oder Umwelt-Sensor-API gefunden.
- Kein Open-SmartCity-Hub-Äquivalent wie in Solingen sichtbar.
- Stadtwerke Osnabrück / SWO Netz dokumentieren LoRaWAN in der Smart Region Osnabrück öffentlich. Das ist ein regionaler Hinweis, aber derzeit keine GMH-spezifische öffentliche Sensordatenquelle.

Schluss: Für echte Sensorik am Marktplatz/LoRaWAN müsste man Stadt oder Stadtwerke direkt fragen. Öffentlich versteckt auffindbar war sie bei dieser Recherche nicht.

## Sinnvolle nächste Plugin-Ausbaustufen

1. Bahnhöfe Oesede/Kloster Oesede: umgesetzt über Finalrewind JSON.
2. VOS-Störungen für GMH-relevante Linien/Haltestellen scrapen: umgesetzt.
3. Landkreis-Baustellen nach GMH-Ortsbegriffen filtern: umgesetzt.
4. E-Ladepunkte über Bundesnetzagentur-Stammdaten aufnehmen: umgesetzt; Live-Verfügbarkeit separat prüfen.
5. NINA/warnung.bund.de-Warnmeldungen: umgesetzt über Landkreis-Osnabrück-ARS; gemeindescharfe/DWD-Direktwarnungen weiter prüfen.
6. Parkplatz-POIs statisch aufnehmen.
7. VBN/Connect GTFS-Static lokal für GMH-Haltestellen/Linien auswerten und danach GTFS-RT-Delays prüfen.
8. Kamera-Datenfrische prüfen: Last-Modified/Content-Length/Hash.
9. Stadt/RSS-Meldungen klassifizieren: Verkehr, Baustelle, Hochwasser/Wetter/Wasser, Veranstaltung, Verwaltung. Ergänzt am 06.07.2026: Verkehrs-/Baumeldungen aus dem offiziellen Stadt-RSS werden zusätzlich als Problem-Binary-Sensor sichtbar gemacht. Ergänzt am 13.07.2026: Wetter-/Hochwasser-Klassifizierung erkennt auch Hitze-, Trockenheits- und Wassersparhinweise und wird als Safety-Binary-Sensor sichtbar.
10. Optional: Solingen-ähnlicher MQTT-Modus für Home-Assistant-Autodiscovery.
