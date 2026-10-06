# Hong Kong 1:1 OpenOMSI Map

Free, non-commercial Hong Kong 1:1 map project for OpenOMSI and OMSI 2.
The repository contains the map package, route catalogues, HOF data, browser
viewer, source snapshots and validation tools.

## Project status

The project is an installable data-driven map scaffold. It is useful for
previewing the imported Hong Kong road network, checking route data and
testing the OpenOMSI package.

Included now:

- 19 HP1C regional map folders;
- OSM road and building data;
- bus-stop locations;
- franchised bus route records;
- NR Residents' Service records;
- other non-franchised and hotel-service records;
- a searchable route detail catalogue;
- a basic Hong Kong HOF file;
- a combined OpenOMSI ZIP containing all 19 maps;
- a browser map viewer and Cesium reference preview.

Still in progress:

- complete drivable OMSI spline conversion;
- final terrain and collision data;
- high-detail buildings, signs, objects and textures;
- complete stop-by-stop HOF data;
- timetables and AI traffic;
- final vehicle and sound assets.

The current package should therefore be treated as a development release,
not as the finished high-detail version of the entire territory.

## Repository layout

| Path | Contents |
| --- | --- |
| `maps\HP1C_*` | 19 OpenOMSI map areas and imported road/stop/building CSV files |
| `routes\hk_bus_routes.csv` | Franchised/public bus route-direction records |
| `routes\nr_routes.csv` | Approved Residents' Service records |
| `routes\other_routes.csv` | Contract-hire and regular hotel-service records |
| `routes\route_details.csv` | Unified searchable route detail table |
| `routes\sources.json` | Route source and generation metadata |
| `Vehicles\Annan_HK\HK_Routes.hof` | Current basic HOF route file |
| `Sceneryobjects\HK_Objects` | Hong Kong scenery-object package location |
| `preview\cesium` | Optional Lands Department 3D reference viewer |
| `web` | Browser website, interactive map and route detail page |
| `src\osm` | Committed OSM source snapshots |
| `src\scripts` | Map generation, route import, validation, packaging and launch tools |
| `release` | Locally generated release ZIP files |

## The 19 map areas

The combined package contains these `HP1C_*` areas:

`CW`, `WCH`, `EAS`, `SOU`, `YTM`, `SSP`, `KCT`, `WTS`, `KTN`, `KWT`,
`TWW`, `TMM`, `YLN`, `NTH`, `TPO`, `STN`, `SKG`, `ISL`, `HZMB`.

The current `HP1C_NTH` source uses a larger Overpass snapshot covering the
requested northwest New Territories bounding box:

<https://overpass-api.de/api/map?bbox=114.0568,22.3364,114.2185,22.4180>

That snapshot currently contains approximately 545,450 nodes, 37,462 road
ways, 3,729 stops and 16,601 building ways. The compressed source is stored
as `src\osm\hong-kong-northwest.osm.gz`.

## Download and install

The map is distributed as one combined ZIP, not 19 separate downloads:

`release\omsi2-hk-1to1-openomsi.zip`

The package contains:

- all `maps\HP1C_*` folders;
- `Sceneryobjects`;
- `Vehicles`;
- the current `HK_Routes.hof`.

Install it as follows:

1. Download the single ZIP.
2. Open the OpenOMSI or OMSI 2 game directory.
3. Extract `maps`, `Sceneryobjects` and `Vehicles` into that directory.
4. Accept folder merging when Windows asks.
5. Start the simulator.
6. Select one of the installed `HP1C_*` Hong Kong maps.

The archive does not include the simulator executable, development source
files, private API keys or unlicensed third-party imagery.

## Website and data viewer

The website files are in `web\`:

- [`web\index.html`](web/index.html) — project homepage, download area,
  status and quick route search;
- [`web\app.js`](web/app.js) — CSV loading, Leaflet map layers and area
  switching;
- [`web\styles.css`](web/styles.css) — website and map layout;
- [`web\routes.html`](web/routes.html) — full route-detail search page;
- [`web\route-data.js`](web/route-data.js) — route detail filtering logic.

The website displays:

- OSM roads;
- bus stops;
- building footprints;
- selectable HP1C areas;
- route and destination searches;
- HOF download links;
- package and validation status.

The browser viewer is a data viewer similar to a community map site. It does
not replace the OpenOMSI game engine and does not by itself make the map
drivable.

## Route data and HOF

The route catalogues are separated by service group:

1. **Franchised public buses** — `hk_bus_routes.csv`;
2. **NR Residents' Service** — `nr_routes.csv`;
3. **Other non-franchised services** — `other_routes.csv`.

`route_details.csv` combines the imported records into one searchable table
with these fields:

- route ID and route number;
- service group and service type;
- operator;
- origin and destination;
- route map;
- timetable;
- vehicle type;
- fare;
- depot;
- source;
- data status.

The source catalogues do not provide every detailed field for every service.
Missing values are explicitly marked as pending, unspecified or not published;
they are not guessed.

The current HOF is:

`Vehicles\Annan_HK\HK_Routes.hof`

It is a basic shared route file for package and development testing. Complete
stop-by-stop routes, destinations, schedules and AI traffic remain future
work.

## Data sources

This project is free and is not sold. The main public data sources are:

- [OpenStreetMap](https://www.openstreetmap.org/) — roads, building
  footprints and bus-stop locations; attribution is
  `© OpenStreetMap contributors`;
- [Overpass API](https://overpass-api.de/) — OSM source extraction service;
- [HK Bus Crawling](https://hkbus.github.io/hk-bus-crawling/) — franchised bus
  route and direction data;
- [Hong Kong Transport Department non-franchised services](https://www.td.gov.hk/en/transport_in_hong_kong/public_transport/non_franchised/)
  — NR, contract-hire and hotel-service listings;
- [HKeMobility](https://www.hkemobility.gov.hk/en/route-search/pt) — public
  transport route reference;
- [Hong Kong CSDI](https://portal.csdi.gov.hk/csdi-webpage/) — official
  mapping, terrain and 3D reference data;
- [Lands Department 3D Spatial Data API](https://portal.csdi.gov.hk/csdi-webpage/apidoc/3d-spatial-data-api)
  — official 3D building, infrastructure and terrain service.

## API source endpoints

These are public source URLs and URL formats only. They do not contain a real
API key:

```text
https://data.map.gov.hk/api/3d-data/3dsd/WGS84/building/tileset.json?key=<YOUR_KEY>
https://data.map.gov.hk/api/3d-data/3dsd/WGS84/infrastructure/tileset.json?key=<YOUR_KEY>
https://data.map.gov.hk/api/3d-data/3dsd/WGS84/terrain/tileset.json?key=<YOUR_KEY>
https://mapapi.geodata.gov.hk/gs/api/v1.0.0/xyz/imagery/WGS84/{z}/{x}/{y}.png
https://hkbus.github.io/hk-bus-crawling/routeFareList.min.json
https://www.hkemobility.gov.hk/en/route-search/pt
https://www.hkemobility.gov.hk/api/em
```

API keys remain local to the person using the service. They are not committed
to GitHub, included in the website, placed in CSV files or packaged in the
OpenOMSI ZIP.

## Preview and testing

The repository has three preview levels:

1. **Browser website** — inspect roads, stops, buildings and route data.
2. **Cesium reference preview** — inspect optional Lands Department 3D
   buildings and infrastructure when the user supplies their own local key.
3. **OpenOMSI/OMSI 2** — install the ZIP and test actual map loading and
   driving on a local simulator installation.

The project can verify map files, route files, package folders, source XML,
website assets and the combined ZIP. Actual driving requires OpenOMSI or OMSI
2 to be installed on the testing computer.

## Attribution and usage

Use each source according to its current licence and attribution requirements.
Google Maps and Google Earth screenshots, tiles and extracted imagery are not
included in the package. Official API data is not automatically
redistributable simply because it can be viewed online.

See [`ATTRIBUTION.md`](ATTRIBUTION.md) for source attribution details and
[`QUALITY_TARGET.md`](QUALITY_TARGET.md) for the planned high-fidelity asset
target.

This is an independent community project and is not an official
OpenOMSI/OMSI 2 product.

## Report a problem

When reporting a problem, include:

- HP1C map area;
- route or stop name;
- expected result;
- actual result;
- screenshot or log, if available.

Use the repository's GitHub Issues page to report errors or missing data.
