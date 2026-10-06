# Hong Kong 1:1 OpenOMSI Map

## 中文

免費、非商業用途的香港 1:1 OpenOMSI／OMSI 2 地圖專案。Repository
包含地圖資料、路線資料、HOF、瀏覽器地圖、OSM source snapshot 和發布用
安裝包。

### 目前狀態

目前版本是可安裝的 data-driven map scaffold，適合預覽道路、巴士站、
建築輪廓、路線資料和測試 OpenOMSI 安裝包。

已包含：

- 19 個 `HP1C_*` 地圖區域；
- OSM 道路、建築和巴士站資料；
- 專營巴士、NR 居民巴士及其他非專營服務資料；
- 可搜尋的路線詳細資料表；
- 基本香港 HOF；
- 一個包含全部 19 個地圖的 OpenOMSI ZIP；
- 瀏覽器互動地圖和 Cesium 3D 參考預覽。

仍在製作：

- 完整可駕駛 OMSI road spline；
- terrain、collision、交通和 AI；
- 高精度建築、街景、標誌、物件和 texture；
- 完整逐站 HOF、時刻表和車輛聲音。

所以目前版本是 development release，不是全港最終高精度成品。

### 19 個地圖區域

`CW`, `WCH`, `EAS`, `SOU`, `YTM`, `SSP`, `KCT`, `WTS`, `KTN`, `KWT`,
`TWW`, `TMM`, `YLN`, `NTH`, `TPO`, `STN`, `SKG`, `ISL`, `HZMB`。

`HP1C_NTH` 使用你提供的 Overpass source：

<https://overpass-api.de/api/map?bbox=114.0568,22.3364,114.2185,22.4180>

目前 snapshot 約有 545,450 nodes、37,462 road ways、3,729 stops 和
16,601 building ways，壓縮 source 位於
`src\osm\hong-kong-northwest.osm.gz`。

### 下載及安裝

全部地圖是**一個 ZIP**，不是 19 個獨立下載：

`release\omsi2-hk-1to1-openomsi.zip`

ZIP 包含：

- 全部 `maps\HP1C_*`；
- `Sceneryobjects`；
- `Vehicles`；
- `Vehicles\Annan_HK\HK_Routes.hof`。

安裝流程：

1. 下載單一 ZIP。
2. 開啟 OpenOMSI／OMSI 2 遊戲資料夾。
3. 將 `maps`、`Sceneryobjects` 和 `Vehicles` 解壓到遊戲資料夾。
4. Windows 詢問時允許合併資料夾。
5. 啟動遊戲並選擇一個 `HP1C_*` 香港地圖。

### Website 和資料查看

- [網站首頁](web/index.html)
- [互動道路地圖](web/index.html#map)
- [路線詳細搜尋](web/routes.html)
- [完整路線 CSV](routes/route_details.csv)
- [Cesium 3D 預覽](preview/cesium/index.html)

網站可查看 OSM roads、bus stops、building footprints、HP1C area、
route search、HOF 下載和目前狀態。Browser viewer 是資料查看工具，
不會取代 OpenOMSI game engine。

### Repository 結構

| 路徑 | 內容 |
| --- | --- |
| `maps\HP1C_*` | 19 個地圖區域和道路/巴士站/建築 CSV |
| `routes\hk_bus_routes.csv` | 專營巴士路線方向資料 |
| `routes\nr_routes.csv` | NR 居民巴士資料 |
| `routes\other_routes.csv` | 合約租賃和酒店服務資料 |
| `routes\route_details.csv` | 統一路線搜尋表 |
| `routes\sources.json` | 路線 source metadata |
| `Vehicles\Annan_HK\HK_Routes.hof` | 基本 HOF |
| `Sceneryobjects\HK_Objects` | 香港 scenery 位置 |
| `web` | Website、互動地圖、路線頁 |
| `preview\cesium` | Lands Department 3D reference viewer |
| `src\osm` | OSM source snapshots |
| `src\scripts` | 生成、驗證、打包和啟動工具 |
| `release` | 產生的安裝 ZIP |

### 路線和 HOF

`route_details.csv` 欄位包括 route ID、route number、service group、
operator、origin、destination、route map、timetable、vehicle type、
fare、depot、source 和 data status。

來源沒有提供的欄位會標示為 pending、unspecified 或 not published，不會
自行猜測。現有 HOF 是基本共享 HOF，完整逐站路線、時刻表和 AI traffic
仍會逐步加入。

### 資料來源和 API

本專案免費提供，不作出售。資料來源：

- [OpenStreetMap](https://www.openstreetmap.org/) — roads、buildings、stops；
- [Overpass API](https://overpass-api.de/) — OSM source extraction；
- [HK Bus Crawling](https://hkbus.github.io/hk-bus-crawling/) — 巴士路線；
- [香港運輸署非專營服務](https://www.td.gov.hk/en/transport_in_hong_kong/public_transport/non_franchised/)；
- [HKeMobility](https://www.hkemobility.gov.hk/en/route-search/pt)；
- [香港 CSDI](https://portal.csdi.gov.hk/csdi-webpage/)；
- [Lands Department 3D API](https://portal.csdi.gov.hk/csdi-webpage/apidoc/3d-spatial-data-api)。

公開 API source URL 格式：

```text
https://data.map.gov.hk/api/3d-data/3dsd/WGS84/building/tileset.json?key=<YOUR_KEY>
https://data.map.gov.hk/api/3d-data/3dsd/WGS84/infrastructure/tileset.json?key=<YOUR_KEY>
https://data.map.gov.hk/api/3d-data/3dsd/WGS84/terrain/tileset.json?key=<YOUR_KEY>
https://mapapi.geodata.gov.hk/gs/api/v1.0.0/xyz/imagery/WGS84/{z}/{x}/{y}.png
https://hkbus.github.io/hk-bus-crawling/routeFareList.min.json
https://www.hkemobility.gov.hk/api/em
```

只公開 source URL，不公開實際 API key。API key 不會放入 GitHub、website、
CSV 或 OpenOMSI ZIP。Google Maps／Google Earth imagery 不包含在 package。

### 驗證和問題回報

每次發布會檢查 19 個 map folders、route files、HOF、website assets、
source XML 和 combined ZIP。實際駕駛測試需要本機安裝 OpenOMSI／OMSI 2。

回報問題時請提供 HP1C area、route/stop name、預期結果、實際結果和
screenshot 或 log。這是獨立社群專案，不是 OpenOMSI／OMSI 2 官方產品。

---

## English

Free, non-commercial Hong Kong 1:1 map project for OpenOMSI and OMSI 2.
The repository contains map data, route data, HOF data, a browser viewer,
OSM source snapshots and the release installation package.

### Current status

The current release is an installable data-driven map scaffold for previewing
roads, bus stops, building footprints, route data and the OpenOMSI package.

Included:

- 19 `HP1C_*` map areas;
- OSM roads, buildings and bus stops;
- franchised, NR Residents' Service and other non-franchised data;
- searchable route details;
- a basic Hong Kong HOF;
- one OpenOMSI ZIP containing all 19 maps;
- a browser map and optional Cesium 3D reference preview.

Still in progress:

- complete drivable OMSI road splines;
- terrain, collision, traffic and AI;
- high-detail buildings, streets, signs, objects and textures;
- complete stop-by-stop HOF, timetables and vehicle sounds.

This is a development release, not the final high-detail map of the entire
territory.

### Map areas and Overpass source

The package contains:

`CW`, `WCH`, `EAS`, `SOU`, `YTM`, `SSP`, `KCT`, `WTS`, `KTN`, `KWT`,
`TWW`, `TMM`, `YLN`, `NTH`, `TPO`, `STN`, `SKG`, `ISL`, `HZMB`.

`HP1C_NTH` uses this requested Overpass source:

<https://overpass-api.de/api/map?bbox=114.0568,22.3364,114.2185,22.4180>

The snapshot contains approximately 545,450 nodes, 37,462 road ways, 3,729
stops and 16,601 building ways. The compressed source is stored at
`src\osm\hong-kong-northwest.osm.gz`.

### Download and installation

All maps are distributed as **one ZIP**, not 19 separate downloads:

`release\omsi2-hk-1to1-openomsi.zip`

It contains all `maps\HP1C_*` folders, `Sceneryobjects`, `Vehicles` and the
current `Vehicles\Annan_HK\HK_Routes.hof`.

Installation:

1. Download the single ZIP.
2. Open the OpenOMSI or OMSI 2 game directory.
3. Extract `maps`, `Sceneryobjects` and `Vehicles` there.
4. Allow Windows to merge folders.
5. Start the simulator and select an `HP1C_*` Hong Kong map.

### Website and data viewer

- [Website homepage](web/index.html)
- [Interactive road map](web/index.html#map)
- [Route detail search](web/routes.html)
- [Complete route CSV](routes/route_details.csv)
- [Cesium 3D preview](preview/cesium/index.html)

The website displays OSM roads, bus stops, building footprints, selectable
HP1C areas, route search, HOF download links and project status. It is a data
viewer and does not replace the OpenOMSI game engine.

### Repository layout

| Path | Contents |
| --- | --- |
| `maps\HP1C_*` | 19 map areas and road/stop/building CSV data |
| `routes\hk_bus_routes.csv` | Franchised bus route-direction records |
| `routes\nr_routes.csv` | NR Residents' Service records |
| `routes\other_routes.csv` | Contract-hire and hotel-service records |
| `routes\route_details.csv` | Unified searchable route table |
| `routes\sources.json` | Route source metadata |
| `Vehicles\Annan_HK\HK_Routes.hof` | Basic HOF |
| `Sceneryobjects\HK_Objects` | Hong Kong scenery location |
| `web` | Website, interactive map and route page |
| `preview\cesium` | Lands Department 3D reference viewer |
| `src\osm` | OSM source snapshots |
| `src\scripts` | Generation, validation, packaging and launch tools |
| `release` | Generated installation ZIP |

### Routes and HOF

`route_details.csv` contains route ID, route number, service group, operator,
origin, destination, route map, timetable, vehicle type, fare, depot, source
and data status fields.

When a source does not provide a field, it is marked pending, unspecified or
not published. Values are not guessed. The current HOF is a basic shared HOF;
complete stop-by-stop routes, timetables and AI traffic are future work.

### Data sources and APIs

This project is free and not for sale. Sources include:

- [OpenStreetMap](https://www.openstreetmap.org/) — roads, buildings and stops;
- [Overpass API](https://overpass-api.de/) — OSM source extraction;
- [HK Bus Crawling](https://hkbus.github.io/hk-bus-crawling/) — bus routes;
- [Hong Kong Transport Department non-franchised services](https://www.td.gov.hk/en/transport_in_hong_kong/public_transport/non_franchised/);
- [HKeMobility](https://www.hkemobility.gov.hk/en/route-search/pt);
- [Hong Kong CSDI](https://portal.csdi.gov.hk/csdi-webpage/);
- [Lands Department 3D API](https://portal.csdi.gov.hk/csdi-webpage/apidoc/3d-spatial-data-api).

Public API source URL formats:

```text
https://data.map.gov.hk/api/3d-data/3dsd/WGS84/building/tileset.json?key=<YOUR_KEY>
https://data.map.gov.hk/api/3d-data/3dsd/WGS84/infrastructure/tileset.json?key=<YOUR_KEY>
https://data.map.gov.hk/api/3d-data/3dsd/WGS84/terrain/tileset.json?key=<YOUR_KEY>
https://mapapi.geodata.gov.hk/gs/api/v1.0.0/xyz/imagery/WGS84/{z}/{x}/{y}.png
https://hkbus.github.io/hk-bus-crawling/routeFareList.min.json
https://www.hkemobility.gov.hk/api/em
```

Only source URL formats are published; real API keys are not. Keys are never
placed in GitHub, the website, CSV files or the OpenOMSI ZIP. Google Maps and
Google Earth imagery are not included in the package.

### Verification and reports

Each release checks the 19 map folders, route files, HOF, website assets,
source XML and combined ZIP. Actual driving requires OpenOMSI or OMSI 2 to be
installed locally.

When reporting a problem, include the HP1C area, route or stop, expected
result, actual result and a screenshot or log. This is an independent
community project and is not an official OpenOMSI/OMSI 2 product.

See [`ATTRIBUTION.md`](ATTRIBUTION.md) for attribution details and
[`QUALITY_TARGET.md`](QUALITY_TARGET.md) for the high-fidelity target.
