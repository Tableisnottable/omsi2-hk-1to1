# Hong Kong 1:1 OpenOMSI Map

免費、非商業用途的香港 1:1 OpenOMSI／OMSI 2 map project。Repository
包含 map data、route catalogue、HOF、browser viewer、OSM source snapshots
和一個整合安裝包 (single installation ZIP)。

## Project status / 目前狀態

Current version 是可安裝的 data-driven scaffold，可用來查看 roads、
bus stops、building footprints、routes 及測試 OpenOMSI package。

**Included / 已包括**

- 19 個 `HP1C_*` map areas：`CW`, `WCH`, `EAS`, `SOU`, `YTM`, `SSP`,
  `KCT`, `WTS`, `KTN`, `KWT`, `TWW`, `TMM`, `YLN`, `NTH`, `TPO`, `STN`,
  `SKG`, `ISL`, `HZMB`
- OSM roads、buildings、bus stops 和 building metadata
- Franchised、NR Residents' Service 及 other non-franchised route data
- Searchable route details：route map、timetable、vehicle type、fare、depot
- Basic Hong Kong `HK_Routes.hof`
- Browser map、route search page 和 optional Cesium 3D preview
- One ZIP containing all 19 map folders

**Still in progress / 尚在製作**

完成版仍需要 drivable OMSI road splines、terrain、collision、AI traffic、
high-detail scenery、完整逐站 HOF、timetable 和 vehicle assets。Current
release 是 development scaffold，不是 final high-detail territory-wide map。

## Download and install / 下載及安裝

全部地圖在**一個 ZIP**，不是 19 個獨立下載：

```text
release\omsi2-hk-1to1-openomsi.zip
```

Package contents：

- `maps\HP1C_*` — all 19 map areas
- `Sceneryobjects` — scenery object folders
- `Vehicles` — vehicle and HOF folders
- `Vehicles\Annan_HK\HK_Routes.hof` — current shared HOF

Installation process：

1. Download the single ZIP。
2. Open your OpenOMSI／OMSI 2 game directory。
3. Extract `maps`、`Sceneryobjects` 和 `Vehicles` into that directory。
4. Allow Windows to merge folders。
5. Start the simulator and select an `HP1C_*` Hong Kong map。

如需自行建立 package：

```powershell
powershell.exe -File .\src\scripts\Test-Map.ps1
powershell.exe -File .\src\scripts\Build-Release.ps1
```

## Website / Web viewer

- [Homepage and map](web/index.html)
- [Interactive map section](web/index.html#map)
- [Route detail search](web/routes.html)
- [Route catalogue CSV](routes/route_details.csv)
- [Cesium 3D reference preview](preview/cesium/index.html)

Browser viewer 會顯示 OSM roads、stops、building footprints、HP1C area
選擇、route search 和 HOF download。It is a data viewer, not a replacement
for the OpenOMSI game engine。

## OSM / Overpass source

`HP1C_NTH` 使用指定的 Overpass source：

<https://overpass-api.de/api/map?bbox=114.0568,22.3364,114.2185,22.4180>

Snapshot approximately contains **545,450 nodes、37,462 road ways、3,729
stops、16,601 building ways**。Compressed source：

```text
src\osm\hong-kong-northwest.osm.gz
```

Other stored source snapshots are under `src\osm`。OSM data is used according
to the applicable OpenStreetMap attribution and licence requirements。

## Routes and HOF / 路線資料

`routes\route_details.csv` 是統一 searchable catalogue，主要欄位包括：

| Field | Description |
| --- | --- |
| `route_id`, `route_number` | Route/service identifier |
| `service_group`, `service_type` | Franchised、NR、contract-hire、hotel 等 |
| `operator`, `origin`, `destination` | Service information |
| `route_map`, `timetable` | Map and timetable status/source |
| `vehicle_type`, `fare`, `depot` | Vehicle、fare、depot information |
| `source`, `data_status` | Source URL and data completeness |

Source 未提供的資料會標示 `pending`、`unspecified` 或 `not published`，
不會自行猜測。Current HOF 是 basic shared HOF；complete stop-by-stop
route、timetable and AI traffic 會逐步加入。

## Data sources / 資料來源

本 project free and not for sale。主要 public sources：

- [OpenStreetMap](https://www.openstreetmap.org/) — roads、buildings、stops
- [Overpass API](https://overpass-api.de/) — OSM extraction
- [HK Bus Crawling](https://hkbus.github.io/hk-bus-crawling/) — bus route data
- [Hong Kong Transport Department](https://www.td.gov.hk/en/transport_in_hong_kong/public_transport/non_franchised/) — non-franchised services
- [HKeMobility](https://www.hkemobility.gov.hk/en/route-search/pt) — route reference
- [Hong Kong CSDI](https://portal.csdi.gov.hk/csdi-webpage/) — public geospatial data
- [Lands Department 3D API documentation](https://portal.csdi.gov.hk/csdi-webpage/apidoc/3d-spatial-data-api)

Public API source formats（只顯示 source，不顯示 real key）：

```text
https://data.map.gov.hk/api/3d-data/3dsd/WGS84/building/tileset.json?key=<YOUR_KEY>
https://data.map.gov.hk/api/3d-data/3dsd/WGS84/infrastructure/tileset.json?key=<YOUR_KEY>
https://data.map.gov.hk/api/3d-data/3dsd/WGS84/terrain/tileset.json?key=<YOUR_KEY>
https://mapapi.geodata.gov.hk/gs/api/v1.0.0/xyz/imagery/WGS84/{z}/{x}/{y}.png
https://hkbus.github.io/hk-bus-crawling/routeFareList.min.json
https://www.hkemobility.gov.hk/api/em
```

API keys must stay local in `LANDSD_3D_API_KEY`。They are never committed to
GitHub、website、CSV 或 release ZIP。Google Maps／Google Earth imagery 也不
會被 packaged as distributable map assets。

## Repository layout / 檔案結構

| Path | Contents |
| --- | --- |
| `maps\HP1C_*` | 19 map areas and OSM-derived CSV data |
| `routes\` | Route CSV files and source metadata |
| `Vehicles\Annan_HK\HK_Routes.hof` | Basic OMSI HOF |
| `Sceneryobjects\HK_Objects` | Hong Kong scenery object location |
| `web\` | Homepage, Leaflet map and route page |
| `preview\cesium\` | Lands Department 3D reference viewer |
| `src\osm\` | OSM source snapshots |
| `src\scripts\` | Generate、validate、package、launch scripts |
| `release\` | Locally generated installation ZIP |

## Validation / 測試

Run the offline validator：

```powershell
powershell.exe -File .\src\scripts\Test-Map.ps1
```

It checks all 19 map folders、route files、HOF、website assets 和 required
package structure。Actual driving still requires a local OpenOMSI／OMSI 2
installation; no simulator executable is included in this repository。

For attribution and licence notes, see [`ATTRIBUTION.md`](ATTRIBUTION.md)。
For the intended high-fidelity target, see [`QUALITY_TARGET.md`](QUALITY_TARGET.md)。

## Report a problem / 回報問題

Please include the `HP1C_*` area、route or stop name、expected result、actual
result，以及 screenshot or log。This is an independent community project,
not an official OpenOMSI／OMSI 2 product。
