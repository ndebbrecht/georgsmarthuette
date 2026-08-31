# Datenquellen Georgsmarthütte

Stand: 2026-06-01, laufende technische Recherche.

## AWIGO Abfuhrkalender

Quelle: https://www.awigo.de/haushalt/abfallinformationen/abfuhrtermine/

Die AWIGO-Seite nutzt eine TYPO3/AJAX-Schnittstelle. Sie ist nicht als öffentliche API dokumentiert, aber klar aus dem Frontend ableitbar.

Basis:

```text
https://www.awigo.de/index.php?legacy_eID=awigoCalendar
```

Methoden:

- `calendar[method]=getCities`
- `calendar[method]=getStreets&calendar[cityID]=...`
- `calendar[method]=getNumbers&calendar[streetID]=...`
- `calendar[method]=getDates&calendar[locationID]=...&calendar[cityID]=...`
- `calendar[method]=getICSfile&calendar[locationID]=...&calendar[cityID]=...`

Gefundene IDs:

- Stadt Georgsmarienhütte: `5348001`
- Beispiel Straße Oeseder Straße: `13655001`
- Beispiel Hausnummer Oeseder Straße 85: `656422001`

Abfallarten als Parameter:

- `calendar[rest]=1` → Restmüll, type `1`
- `calendar[paper]=1` → Papiermüll, type `2`
- `calendar[brown]=1` → Biomüll, type `3`
- `calendar[yellow]=1` → Gelber Sack, type `4`
- `calendar[mobile]=1` → Schadstoffmobil, type `5`

`getDates` liefert JSON, z.B.:

```json
[{"dataDay":"28.05.2026","type":1,"delayed":"1","mobileLocation":""}]
```

`getICSfile` liefert eine erzeugte ICS-URL, z.B.:

```text
https://www.awigo.de/fileadmin/kalender/AWIGO_Kalender_Rest_Papier_Gelb_Bio_Schadstoffmobil_656355001.ics
```

Bewertung: bester MVP-Baustein. Adresse kann per Config Flow eingegeben werden; Integration resolved intern city → street → house number → Termine.

## Wetterdaten Georgsmarienhütte

Koordinaten aus Stadtseite/Meta: `52.199996, 8.050056`; Projektdefault: `52.2020, 8.0440`.

Geeignete Quelle: Open-Meteo API, ohne API-Key.

Basis:

```text
https://api.open-meteo.com/v1/forecast
```

Sinnvolle Werte:

- aktuelle Temperatur `temperature_2m`
- gefühlte Temperatur `apparent_temperature`
- Luftfeuchte `relative_humidity_2m`
- Taupunkt `dew_point_2m`
- Luftdruck `pressure_msl` / `surface_pressure`
- Bewölkung `cloud_cover`
- Wind `wind_speed_10m`, `wind_gusts_10m`, `wind_direction_10m`
- Niederschlag `precipitation`, `rain`, `showers`
- Niederschlagswahrscheinlichkeit `precipitation_probability`
- UV-Index `uv_index`

Ergänzend: DWD-Warnungen für amtliche Warnlage. Für den ersten Schritt reicht Open-Meteo + später DWD-Warnungen.


## VOS Störungen und Baustellen

Quelle: https://www.vos.info/fahrplan/stoerungen-baustellen/

Die VOS-Seite veröffentlicht aktuelle ÖPNV-Störungen, Baustellen und Umleitungen als öffentliche HTML-Akkordeonliste. Eine eigene JSON-Schnittstelle für genau diese sichtbaren Störungsmeldungen war weiterhin nicht sichtbar. Die Integration parst deshalb konservativ nur die sichtbaren Listeneinträge:

- Titel
- Beschreibungstext
- betroffene Linien aus CSS-Klassen wie `bus_454`
- PDF-/Info-Links

GMH-Relevanz wird über Ortsbegriffe und regelmäßig relevante Linien gefiltert, u.a. `Georgsmarienhütte`, `GMHütte`, `Oesede`, `Kloster Oesede`, `Harderberg`, `Holzhausen`, `Malbergen`, `B51`, `Weghaus` sowie Linien `411`, `413`, `451`, `452`, `454`, `463` bis `469`, `M3` und `S40`.

Live-Smoke-Test am 25.05.2026 ergab mehrere relevante Einträge, u.a. Oesede/Harderberg/Nordstraße, B51 Richtung Oesede und Oeseder Straße.

Bewertung: nützliche öffentliche Quelle für Home-Assistant-Warnungen. Einschränkung: HTML-Scraping statt offizieller API; deshalb nur robuste Kurzattribute und Quelllink, keine tiefe Zeit-/Routenmodellierung.

### VBN / Connect GTFS-Realtime

Quelle: https://www.vbn.de/service/entwicklerinfos/open-data-und-open-service

Der VBN dokumentiert öffentliche GTFS-Realtime-Prognosedaten im JSON- und ProtoBuf-Format. Die Entwicklerseite wurde im Juli 2026 unter eine neue URL verschoben; der Feed selbst blieb unverändert erreichbar:

```text
http://gtfsr.vbn.de/gtfsr_connect.json
http://gtfsr.vbn.de/gtfsr_connect.bin
```

Der VBN beschreibt die Daten als Prognosedaten mit planmäßiger An-/Abfahrt und Verspätung; sie werden alle 60 Sekunden aktualisiert und stehen unter CC BY-SA 4.0. GTFS.DE führt VBN ebenfalls als enthaltene Agentur in seinem freien GTFS-RT-Stream:

```text
https://realtime.gtfs.de/realtime-free.pb
```

Live-Smoke-Test am 20.07.2026:

- `http://gtfsr.vbn.de/gtfsr_connect.json` antwortete weiterhin mit HTTP 200 und `content-type: application/json`.
- Der JSON-Feed war ca. 20 MB groß.
- Die Einträge enthalten `tripUpdate`, `routeId`, `tripId`, `stopId` und Verspätungen, aber ohne lokale GTFS-Static-Zuordnung keine direkt sprechenden GMH-Haltestellen- oder Liniennamen.

Bewertung: technisch interessant und offiziell dokumentiert, aber noch nicht als Home-Assistant-Quelle eingebaut. Für robuste GMH-Sensoren müsste zuerst eine stabile, lokal gecachte GTFS-Static-Zuordnung für relevante VOS-/GMH-Haltestellen und Linien erstellt werden. Den kompletten 20-MB-Feed alle 30 Minuten nur für ungemappte IDs zu laden, wäre aktuell nicht verhältnismäßig.

## Landkreis Osnabrück Verkehrs- und Baustellenmeldungen

Quelle: https://www.landkreis-osnabrueck.de/fachthemen/ordnung-und-verkehr/baustellen-und-blitzplan

Die Landkreis-Seite veröffentlicht aktuelle Verkehrs- und Baustellenmeldungen als öffentliche HTML-Akkordeonliste mit Titel, Zeitraum und Beschreibung. Eine JSON- oder Feed-Schnittstelle war nicht sichtbar. Die Integration parst deshalb konservativ nur die sichtbaren Karten und filtert nach GMH-relevanten Orts- und Straßenbegriffen, u.a. `Georgsmarienhütte`, `GMHütte`, `Oesede`, `Harderberg` und `Osnabrück-Nahne`. Reine `B51`-Nennungen werden nur noch mit zusätzlichem GMH-seitigem Kontext wie `Bad Iburg`, `Oesede`, `Weghaus`, `B68` oder `Osnabrück-Nahne` gewertet, weil die Landkreis-Seite die B51 auch bei nicht lokalen Maßnahmen erwähnt.

Live-Smoke-Test am 08.06.2026 ergab 12 Landkreis-Meldungen, davon 2 GMH-relevant:

- A30-Ausfahrt Osnabrück-Nahne Richtung B51/B68 Bad Iburg/Georgsmarienhütte gesperrt, 18.05.2026 bis 24.07.2026
- B51/B68 Fahrbahn- und Radwegerneuerung zwischen OS-Nahne und GMHütte, 16.02.2026 bis 03.07.2026

Bewertung: nützliche öffentliche Quelle für regionale Verkehrswarnungen, wenn streng gefiltert. Einschränkung: HTML-Scraping statt offizieller API; deshalb nur Kurzattribute und Quelllink, keine tiefe Verkehrsmodellierung.

Umsetzung:

- Sensor für Anzahl relevanter Landkreis-Baustellen
- Sensor für neueste relevante Landkreis-Baustelle
- Binary-Sensor für aktuell vorhandene relevante Landkreis-Baustelle/Verkehrseinschränkung
- Attribute: Quelle, Gesamtzahl, gefilterte Treffer, Titel, Zeitraum, Beschreibung

## E-Mobilität / Ladesäulen

### Stadt/Stadtwerke-Seiten

Stadtseite:

```text
https://www.georgsmarienhuette.de/stadt/daten-fakten-mobilitaet/e-mobilitaet/
```

Stadtwerke-Seite:

```text
https://www.sw-gmhuette.de/de/Mobilitaet-Zukunft/E-Ladestation/
```

Diese Seiten nennen lokale Ladeorte, sind aber eher redaktionelle Informationen und liefern keine Live-API.

### Bundesnetzagentur Ladesäulenregister

Offizielle Downloadseite:

```text
https://www.bundesnetzagentur.de/DE/Fachthemen/ElektrizitaetundGas/E-Mobilitaet/DownloadundKontakt.html
```

Aktuell verwendete CSV:

```text
https://data.bundesnetzagentur.de/Bundesnetzagentur/DE/Fachthemen/ElektrizitaetundGas/E-Mobilitaet/Ladesaeulenregister_BNetzA_2026-07-28.csv
```

Filter im Plugin:

- `Postleitzahl == 49124`
- `Ort == Georgsmarienhütte`

Rechercheergebnis im Datenstand 28.07.2026:

- 27 Ladeeinrichtungs-Einträge
- 54 Ladepunkte
- 14 zusammengefasste Ladeorte
- 28 Schnellladepunkte, 26 Normalladepunkte
- maximale Ladeleistung: 400 kW

Gefundene Ladeorte u.a.:

- Am Rathaus 16 — Stadtwerke Georgsmarienhütte
- Brüsseler Str. 3 — Stadtwerke Georgsmarienhütte, Schnellladen
- Brüsseler Straße 1B — EnBW, Schnellladen
- Malberger Str. 5 — Q1 / VINCharge / eliso, bis 400 kW
- Klöcknerstraße 14 — EWE Go, Schnellladen
- Oeseder Str. 123 — Stadtwerke Georgsmarienhütte
- Am Markt 24 — Stadtwerke Georgsmarienhütte

Bewertung: gute offizielle Stammdatenquelle für Home Assistant. Die CSV ist groß, daher cached der Client die GMH-Auswertung 24 Stunden im Speicher. Der Datenstand 28.07.2026 wird als UTF-8 ausgeliefert; der Client akzeptiert deshalb UTF-8 und ältere Latin-1-Dateien. Wichtig: Das Register enthält keine Live-Belegung/frei-belegt/Defekt-Status. Für Live-Daten wären Anbieter-APIs oder OCPI/OICP-Zugänge nötig.

## Amtliche Warnmeldungen / NINA

Quelle: https://warnung.bund.de/

Öffentliche Dashboard-API:

```text
https://warnung.bund.de/api31/dashboard/034590000000.json
```

Verwendeter Gebietsschlüssel:

- `034590000000` — Landkreis Osnabrück, amtlicher Regionalschlüssel auf Landkreisebene
- Georgsmarienhütte hat AGS `03459019`; ein stabiler gemeindescharfer Dashboard-Endpunkt war nicht verfügbar.

Bewertung: stabile offizielle Warnquelle für Bevölkerungsschutz-, Wetter- und Lagewarnungen, aber räumlich breiter als nur GMH. Die Integration kennzeichnet deshalb die Abdeckung ausdrücklich als „Landkreis Osnabrück (enthält Georgsmarienhütte)“ und nutzt die Meldungen als amtlichen Sicherheits-/Warnindikator, nicht als rein stadtteilgenaue Sensorik.

Umsetzung:

- Warnungsanzahl
- neueste Warnmeldung
- Binary-Sensor für aktuell vorhandene amtliche Warnungen
- Attribute: Quelle, ARS, Abdeckung, bis zu zehn Meldungen mit Anbieter, Schwere, Dringlichkeit, Zeiten, Beschreibung/Handlungsempfehlung und Weblink

## Pegelstände Düte

Die Stadt verweist beim Hochwasserschutz auf NLWKN Pegelonline.

Quelle: https://www.pegelonline.nlwkn.niedersachsen.de/Start

Frontend-API:

```text
https://bis.azure-api.net/PegelonlineNeu/REST/
```

Subscription-Key aus öffentlichem Frontend-JS:

```text
19094e54510d4e89b140ff2d3abf715f
```

Stammdaten:

```text
stammdaten/stationen/AllePegel?subscription-key=...
```

Gefundener Düte-Pegel:

- `STA_ID`: `116`
- Name: `Wersen`
- Gewässer: `Düte`
- Pegelnummer Ansage: `3608`
- Koordinaten laut API sind feldmäßig offenbar vertauscht: `Latitude=7.952...`, `Longitude=52.320...`; geographisch also ca. `52.3205, 7.9523`.

Details/Datenspuren:

```text
station/116/datenspuren/parameter/1/tage/7/forecast/true?subscription-key=...
chart/station/116/datenspuren/parameter/1/tage/7/forecast/true?subscription-key=...
```

Aktueller Test ergab für Wasserstand beim Chart-Endpunkt keine Pegelstände (`HatPegelstaende=false`, `AktuellerMesswert=-888`), aber Meldestufen sind vorhanden:

- Meldestufe 1: 235 cm / NN + 53,54 m
- Meldestufe 2: 270 cm / NN + 53,89 m
- Meldestufe 3: 310 cm / NN + 54,29 m

Bewertung: als Sensor anlegen, aber robust mit `unavailable`, wenn NLWKN keinen aktuellen Messwert liefert.

## Kameras

### Rathaus / Oeseder Straße

Stadtseite: https://www.georgsmarienhuette.de/stadt/erster-ueberblick/webcam-georgsmarienhuette/

Bild-URL:

```text
https://www.georgsmarienhuette.de/seiten/webcam/gmhuette.jpg
```

Beschreibung: Webcam 1, Oeseder Straße, Standort Rathaus, Blickrichtung Süd. Aktualisierung laut Stadt jede Minute.

### Rathausplatz / Oeseder Kirmes

Stadtseite: https://www.georgsmarienhuette.de/stadt/freizeit/kirmes/oeseder-kirmes/webcam/

Bild-URL:

```text
https://www.georgsmarienhuette.de/seiten/webcam/webcamRP/gmhuette2.jpg
```

### Hochwasserschutz-Kameras

Stadtseite: https://www.georgsmarienhuette.de/stadt/natur/webcams-hochwasserschutz/

Bild-URLs:

```text
https://www.webcam-georgsmarienhuette.de/hochwasserschutz/current/webcam_breenbach.jpg
https://www.webcam-georgsmarienhuette.de/hochwasserschutz/current/webcam_suttmeyer.jpg
https://www.webcam-georgsmarienhuette.de/hochwasserschutz/current/webcam_malbergen.jpg
https://www.webcam-georgsmarienhuette.de/hochwasserschutz/current/webcam_eisenbahn.jpg
```

Standorte laut Stadt:

- Eisenbahnstraße in Oesede
- Straßenbrücke Am Breenbach in Oesede
- Hochwasserrückhaltebecken Suttmeyers Wiesen in Kloster Oesede
- Hochwasserrückhaltebecken Hinterm Schlohe in Malbergen

Bewertung: für Home Assistant besser als `camera` mit still-image polling statt Stream; es sind JPEG-Snapshots, kein echter Videostream.

## Stadt-Datenpunkte

### RSS: aktuelle Meldungen

```text
https://www.georgsmarienhuette.de/portal/rss.xml
```

Liefert NOLIS RSS mit aktuellen Stadtmeldungen inkl. Titel, Link, Beschreibung, Bild-Enclosure, PubDate.

Umsetzung:

- neueste Meldung
- Keyword-Zähler für Meldungsthemen:
  - Verkehr/Baustellen
  - Wetter/Hochwasser/Wasser-/Waldbrandhinweise
  - Veranstaltungen
  - Verwaltung
- Attribute mit Keywords, gefilterten Meldungen, neuestem Treffer und Quelllink
- Problem-Binary-Sensor für aktuelle Verkehrs-/Baumeldungen aus derselben offiziellen RSS-Quelle
- Safety-Binary-Sensor für aktuelle Wetter-, Hochwasser-, Hitze-, Trockenheits-, Wasserspar- oder Waldbrandgefahr-Hinweise aus derselben offiziellen RSS-Quelle

Bewertung: stabile offizielle Stadtquelle. Die Themenzuordnung ist bewusst einfache Keyword-Klassifizierung und keine amtliche Kategorisierung; sie eignet sich als Home-Assistant-Hinweis, nicht als alleinige Warnlogik. Die Binary-Sensoren ersetzen keine VOS-/Landkreis-Verkehrsdaten, NLWKN-Pegel oder NINA-Warnungen, sondern machen städtische Hinweise wie Vollsperrungen, Tiefbauarbeiten, Umleitungen, Wassersparaufrufe, Beregnungsverbote, Wasserentnahmeverbote, Trockenheitshinweise oder Waldbrandgefahr direkt automationstauglich.

### Ratsinformationssystem

Quelle:

```text
https://gmh.ris.itebo.de/bi/infobi.asp
```

Beim Abruf sichtbar: kommende Sitzungen, z.B. Rat, Verwaltungsausschuss, Betriebsausschuss, Zeiten und Orte.

Mögliche Sensoren:

- nächste öffentliche Sitzung
- nächster Ratstermin
- Sitzungsort
- Tagesordnung/Link, falls aus RIS technisch sauber extrahierbar

### Stadt-Navigation / potenzielle Sensoren

Aus der Stadtseite auffindbar:

- Veranstaltungen: `/stadt/veranstaltungen/`
- Bekanntmachungen: `/rathaus/aktuelles/bekanntmachungen/`
- Stellenangebote: `/rathaus/aktuelles/stellenangebote/`
- Ausschreibungen & Auftragsvergaben
- Parkplätze: `/stadt/erster-ueberblick/parkplaetze/`
- Stadtplan: `http://navigator.georgsmarienhuette.de`
- Hochwasserschutz und Überschwemmungsgebiet Düte
- E-Mobilität
- Schwimmbäder
- Sporthallenbelegungsplan
- Solardachkataster
- Kommunale Wärmeplanung
- Wochenmarkt
- Wirtschaftsdaten

Bewertung: RSS, RIS und bekannte Snapshot-Kameras zuerst. Der Rest ist eher Scraping/Link-Sensor, solange keine offene API gefunden ist.
