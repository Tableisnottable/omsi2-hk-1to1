# 香港 1:1 OMSI 地圖 / Hong Kong 1:1 OMSI Map

Hong Kong map-generation tools, route catalogues, HOF data and browser previews for OMSI 2 / OpenOMSI.

**Current status / 目前進度** · 26 November 2026

**Tsing Yi / 青衣** (`HK_TsingYi`) is the first area built from real-world terrain and OpenStreetMap data. The latest rebuild corrects the imported road elevations and includes the provisional `248M_TEST` timetable. The offline validator passed. OMSI loading, driving, passenger operation and frame rate still need in-game checks.

## Choose the correct build / 選擇正確版本

| Build / 版本 | Purpose / 用途 | Guide / 文件 |
| --- | --- | --- |
| `HK_TsingYi` | Tsing Yi development build with corrected road elevations, road-contact repair and provisional 248M test service | [Tsing Yi build, installation and test guide](TSING_YI.md) |
| `HK_BigMap` | Experimental map built from partial district extracts, with gaps between areas | [BigMap implementation notes](BIGMAP.md) |
| `HP1C_*` | Earlier 19-area data scaffold and district converter; separate from the Tsing Yi build | Earlier HP1C workflow below |

## Real-world import workflow / 真實地圖匯入

The Tsing Yi builder converts OpenStreetMap roads, building footprints and
coastline, along with Skadi terrain heights, into native OMSI 2 assets. The
workflow takes inspiration from real-world map imports in Cities: Skylines II.
The current tools build Tsing Yi and let you select other areas for road coverage
planning. Building other areas from a browser selection is still in development.
[Earth2Cities reference](https://mods.paradoxplaza.com/mods/140919/Windows)

The cached Hong Kong extract contains **6,342 road-bearing 300 m tiles** for
the road classes measured by the planner. Of these, **481** intersect the
registered `HK_BigMap` grid and **5,861** are outside it. This measures where
source roads overlap the existing grid. Individual road coverage and
connectivity within each registered tile still need checking.

Use the Python environment and cached extract from the Tsing Yi instructions below
to plan expansion of the Hong Kong grid:

```powershell
.\work\venv\Scripts\python.exe src/scripts/Plan-HongKongImport.py
```

Open `work/hk-import/road-tiles.geojson` in a GIS viewer. Each 300 m tile reports
source road length by surface, bridge and tunnel, and whether the tile is registered
in `HK_BigMap`. Use `--bounds WEST SOUTH EAST NORTH` to measure a smaller area
in WGS84 longitude and latitude. Without that option, the planner measures the
full extract, including roads beyond Hong Kong's administrative boundary.

The older district extracts do not establish complete Hong Kong road coverage. A route appearing in the CSV catalogue or HOF is not proof that its road path, timetable or passenger service is playable.

## Build Tsing Yi locally / 本機建立青衣

Use **Python 3.11 or newer**. From the repository root:

```powershell
py -m venv work/venv
.\work\venv\Scripts\python.exe -m pip install -r src/scripts/requirements-tsingyi.txt
.\work\venv\Scripts\python.exe src/scripts/Fetch-TsingYi.py
.\work\venv\Scripts\python.exe src/scripts/Build-TsingYi.py
.\work\venv\Scripts\python.exe src/scripts/Validate-TsingYi.py
.\work\venv\Scripts\python.exe src/scripts/Package-TsingYi.py --output release/tsingyi
```

Fetching downloads the geographic inputs; later builds can reuse the retained cache offline. The builder replaces only the dedicated `HK_TsingYi` map, scenery and spline folders and preserves their previous versions under `work/`. It also generates the test timetable and runs the road-contact repair. See [TSING_YI.md](TSING_YI.md) for prerequisites, backups and the repair command for an existing build.

The latest build has **321 tiles, 8,022 road splines, 1,163 buildings, 166 bus stops and six entrypoints**. The elevation fix removed a sign error that placed 4,334 spline starts more than 1 m below sea level in the previous build. The rebuilt map has zero such starts. Offline checks passed for road grades, terrain seams, road clearance and timetable references. See the generated `build_manifest.json` for counts from your source snapshot.

`248M_TEST` connects Tsing Yi Station and Cheung Wang with two duties and provisional 30-minute departures. Departure times and running times are generated for testing. Road tracks and stop approaches still need in-game checks. `249M` remains an authoring reference.

### Install or test / 安裝及測試

The dedicated packager writes `OMSI2-TsingYi-development.zip` under the chosen output folder, together with an HTML preview and an offline validation report. These generated files and geographic/mesh/texture assets remain local and are excluded from Git. A clone alone is not a ready-to-drive installation.

Extract the dedicated ZIP into the OMSI 2 game folder, merging `maps`, `Splines`, `Sceneryobjects` and the supplied HOF locations. Use your own installed bus; no bus model is redistributed. Select **Tsing Yi 1:1 - development**. Follow the simulator-specific steps and HOF instructions in [TSING_YI.md](TSING_YI.md) before choosing `248M_TEST`.

Remaining work includes authored junction connectors/signals, continuous bridge profiles, tunnel portals/interiors and terrain cuts, road-width/grade review, recognizable scenery, passenger/HOF tests and memory/FPS profiling. The retained build omits **54 tagged tunnel ways**, and bridge heights are estimates. Offline structural checks do not certify a drivable route.

## OMSI 2 buses in ETS2 / 巴士轉換

The experimental **KMB Bus Conversion Pack** `0.3.0` includes the **ADL Enviro500 MMC E6M** and **ADL Enviro500 ATENU** for ETS2 Coach Mode. The build targets ETS2 `1.62.3.3` and passed offline checks for vehicle definitions, dealer presets, models, and wheel locators. In-game dealer preview, purchase, and driving still need verification. Animated doors and passenger boarding are unfinished, so coach jobs are disabled. The rest of the OMSI fleet is still pending.

Build the `.scs` locally from your installed OMSI 2 bus assets using the SCS Conversion Tools. GitHub hosts the conversion scripts and instructions. The generated mod, models, and textures stay local. For prerequisites and test steps, see the [ETS2 bus conversion guide](src/e6m_ets2/README.md).

## Earlier HP1C scaffold / 早期地區骨架

The remaining HP1C instructions describe the earlier district scaffold, route catalogue, HOF and browser viewer. Its combined ZIP is generated locally; use the dedicated Tsing Yi workflow above for the current island build.

## 專案狀態 / Project status

早期 HP1C 版本是 data-driven map scaffold，可查看 roads、bus stops、building footprints 和 routes；package structure 並不代表模擬器載入或駕駛已驗證 / The earlier HP1C scaffold is a data and packaging experiment, with runtime operation still unverified.

**已包括 / Included**

- 19 個 `HP1C_*` map areas：`CW`, `WCH`, `EAS`, `SOU`, `YTM`, `SSP`, `KCT`, `WTS`, `KTN`, `KWT`, `TWW`, `TMM`, `YLN`, `NTH`, `TPO`, `STN`, `SKG`, `ISL`, `HZMB`。
- OSM roads、buildings、bus stops 和 building metadata。
- Franchised、NR Residents' Service 及 other non-franchised route data。
- Searchable route details，包括 route map、timetable、vehicle type、fare 和 depot。
- Basic Hong Kong `HK_Routes.hof`。
- Browser map、route search page 和 optional Cesium 3D preview。
- One ZIP containing all 19 map folders。

**尚在製作 / Still in progress**

完成版仍需要 drivable OMSI road splines、terrain、collision、AI traffic、high-detail scenery、完整逐站 HOF、timetable 和 vehicle assets。

目前版本是 development scaffold，不是 final high-detail territory-wide map。

## 建立及安裝早期套件 / Build and install the earlier package

早期 packager 會在本機建立**一個 ZIP**，包含全部 19 個 HP1C areas，而非 19 個獨立下載 / The earlier packager creates one local ZIP containing the 19 HP1C areas. The ZIP is ignored by Git and is not a downloadable asset in a fresh source checkout:

```text
release\omsi2-hk-1to1-openomsi.zip
```

Package contents / 套件內容：

- `maps\HP1C_*` — 全部 19 個 map areas / all 19 map areas。
- `Sceneryobjects` — scenery object folders / scenery 物件資料夾。
- `Splines` — road spline definitions / 道路 spline 定義。
- `Vehicles` — vehicle and HOF folders / vehicle 及 HOF 資料夾。
- `Vehicles\Annan_HK\HK_Routes.hof` — current shared HOF / 目前共用 HOF。

Installation process / 安裝流程：

1. 使用下方指令建立本機 ZIP，或使用已保留的本機 package / Build the local ZIP with the commands below, or use a retained local package。
2. 開啟 OpenOMSI／OMSI 2 game directory / Open your OpenOMSI or OMSI 2 game directory。
3. 將 `maps`、`Sceneryobjects`、`Splines` 和 `Vehicles` 解壓到該目錄 / Extract these folders into that directory。
4. 允許 Windows merge folders / Allow Windows to merge the folders。
5. 啟動 simulator 並選擇 `HP1C_*` 香港地圖 / Start the simulator and select an `HP1C_*` Hong Kong map。

如需自行建立 package，先執行 validator，再執行 release builder / To build the package locally, run the validator first and then the release builder：

```powershell
powershell.exe -File .\src\scripts\Test-Map.ps1
powershell.exe -File .\src\scripts\Build-Release.ps1
```

`Build-Release.ps1` archives the current `maps`, `Sceneryobjects`, `Splines` and `Vehicles` trees after checking for the 19 HP1C folders. Other generated maps present in those trees can be included too. Use `Package-TsingYi.py` for a focused Tsing Yi package.

## 網站及 Web viewer / Website and Web viewer

Serve the **repository root** so the viewer can fetch the sibling route CSVs and map data:

```powershell
py -m http.server 8000
```

Open `http://localhost:8000/web/` or `http://localhost:8000/web/routes.html`. An internet connection is needed for the external basemap and CDN libraries. The links below open viewer source files on GitHub; they do not run the viewer there. The website’s ZIP button only works where the corresponding local release file is also served.

- [網站首頁及 map 原始碼 / Homepage and map source](web/index.html)
- [互動地圖區域 / Interactive map section](web/index.html#map)
- [路線搜尋原始碼 / Route detail search source](web/routes.html)
- [路線 catalogue CSV / Route catalogue CSV](routes/route_details.csv)
- [Cesium 3D reference preview / Cesium 3D 參考預覽](preview/cesium/index.html)

Browser viewer 會顯示 OSM roads、stops、building footprints、HP1C area selection、route search 和 HOF download；它是 data viewer，不會取代 OpenOMSI game engine。

## OSM／Overpass source / OSM／Overpass 資料來源

`HP1C_NTH` 使用指定的 Overpass source / `HP1C_NTH` uses the requested Overpass source：

<https://overpass-api.de/api/map?bbox=114.0568,22.3364,114.2185,22.4180>

Snapshot 約有 **545,450 nodes、37,462 road ways、3,729 stops、16,601 building ways** / The snapshot contains approximately these records。

Compressed source 儲存在 / The compressed source is stored at：

```text
src\osm\hong-kong-northwest.osm.gz
```

其他 stored source snapshots 位於 `src\osm` / Other stored source snapshots are under `src\osm`。

OSM data 會按照適用的 OpenStreetMap attribution and licence requirements 使用 / OSM data is used under the applicable attribution and licence requirements。

## 路線及 HOF / Routes and HOF

`routes\route_details.csv` 是統一 searchable catalogue / This is the unified searchable route catalogue：

| Field / 欄位 | Description / 說明 |
| --- | --- |
| `route_id`, `route_number` | Route/service identifier / 路線或服務識別碼 |
| `service_group`, `service_type` | Franchised、NR、contract-hire、hotel 等服務類型 / Service category |
| `operator`, `origin`, `destination` | Operator and service endpoints / 營辦商、起點及終點 |
| `route_map`, `timetable` | Map and timetable status/source / 路線圖及時間表狀態或來源 |
| `vehicle_type`, `fare`, `depot` | Vehicle、fare、depot information / 車型、票價及車廠資料 |
| `source`, `data_status` | Source URL and data completeness / 資料來源及完整度 |

Source 未提供的資料會標示 `pending`、`unspecified` 或 `not published` / Missing source fields are marked explicitly and are not guessed。

Current HOF 是 basic shared HOF / The current HOF is a basic shared HOF；complete stop-by-stop routes、timetables and AI traffic 會逐步加入 / will be added progressively。

## 資料來源 / Data sources

本 project free and not for sale / 本專案免費提供並不作出售。

- [OpenStreetMap](https://www.openstreetmap.org/) — roads、buildings、stops / 道路、建築及巴士站。
- [Overpass API](https://overpass-api.de/) — OSM extraction / OSM 資料擷取。
- [HK Bus Crawling](https://hkbus.github.io/hk-bus-crawling/) — bus route data / 巴士路線資料。
- [Hong Kong Transport Department](https://www.td.gov.hk/en/transport_in_hong_kong/public_transport/non_franchised/) — non-franchised services / 非專營服務。
- [HKeMobility](https://www.hkemobility.gov.hk/en/route-search/pt) — route reference / 路線參考資料。
- [Hong Kong CSDI](https://portal.csdi.gov.hk/csdi-webpage/) — public geospatial data / 公開地理空間資料。
- [Lands Department 3D API documentation](https://portal.csdi.gov.hk/csdi-webpage/apidoc/3d-spatial-data-api) — 3D data API documentation / 3D 資料 API 文件。

Public API source formats 只顯示 source，不顯示 real key / These formats show only the source, never a real API key：

```text
https://data.map.gov.hk/api/3d-data/3dsd/WGS84/building/tileset.json?key=<YOUR_KEY>
https://data.map.gov.hk/api/3d-data/3dsd/WGS84/infrastructure/tileset.json?key=<YOUR_KEY>
https://data.map.gov.hk/api/3d-data/3dsd/WGS84/terrain/tileset.json?key=<YOUR_KEY>
https://mapapi.geodata.gov.hk/gs/api/v1.0.0/xyz/imagery/WGS84/{z}/{x}/{y}.png
https://hkbus.github.io/hk-bus-crawling/routeFareList.min.json
https://www.hkemobility.gov.hk/api/em
```

API keys 必須留在 local environment variable `LANDSD_3D_API_KEY` / API keys must stay local in that environment variable。

## Legacy district generation / 早期地區生成器

The earlier converter processes each HP1C extract into a single 300 m district tile, clipping roads to that tile. This is not the Tsing Yi builder or complete cross-district coverage. Generated records still require simulator/editor checks:

```powershell
# 1. Fetch a real OSM extract per district (src\osm\<code>.osm)
powershell.exe -File .\src\scripts\Fetch-HkDistricts.ps1

# 2. Convert one district (CW shown); repeat with the matching code and centre for others
python .\src\scripts\Convert-OsmToMap.py --osm .\src\osm\CW.osm --mapcode CW --centre 22.2825,114.1580 --root .

# 3. Add real elevation from the Copernicus DEM (Open-Meteo, free)
python .\src\scripts\Add-TerrainElevation.py --all --root .
```

Convert-OsmToMap.py writes:

- `maps/HP1C_<code>/tile_0_0.map` (UTF-16LE), with `[spline]` and `[object]` records, version 14.
- `maps/HP1C_<code>/tile_0_0.map.terrain` (61 × 61 height grid).
- `Splines/HK_Roads/*.sli` road splines and their `texture/asphalt.bmp`.
- `Sceneryobjects/HK_Objects/bldg_*.sco`, `model/bldg_*.o3d` building meshes and bus-stop objects.
- `maps/HP1C_<code>/osm_*.csv` source data and the `osm_import.json` manifest.

The tile is centred on the district's HP1C sheet centre; each tile is
300 m x 300 m and uses plain (non-world-coordinate) local coordinates. The
converter is deterministic and offline once the OSM extracts are present.

OSM data is used under the applicable attribution and licence requirements.

Keys are never committed to GitHub or included in the website, CSV files or release ZIP。

Google Maps／Google Earth imagery 不會 packaged as distributable map assets / Google imagery is not included as distributable map assets。

## Repository 結構 / Repository layout

| Path / 路徑 | Contents / 內容 |
| --- | --- |
| `maps\HK_TsingYi` | Generated current island build; ignored by Git / 本機生成的青衣地圖 |
| `maps\HK_BigMap` | Experimental combined district grid / 實驗性合併地圖 |
| `maps\HP1C_*` | Earlier 19 district areas and OSM-derived CSV data / 早期地區及 CSV 資料 |
| `routes\` | Route CSV files and source metadata / 路線 CSV 及 source metadata |
| `Vehicles\Annan_HK\HK_Routes.hof` | Basic OMSI HOF / 基本 OMSI HOF |
| `Sceneryobjects\HK_Objects` | Earlier Hong Kong scenery objects / 早期 scenery 物件 |
| `Splines\HK_TsingYi`, `Sceneryobjects\HK_TsingYi` | Generated island splines and scenery; local only / 青衣生成資產，保留本機 |
| `web\` | Homepage, Leaflet map and route page / 首頁、Leaflet map 及路線頁 |
| `preview\cesium\` | Lands Department 3D reference viewer / Lands Department 3D 參考 viewer |
| `src\osm\` | OSM source snapshots / OSM source snapshot |
| `src\scripts\` | Generate、validate、package、launch scripts / 生成、驗證、打包及啟動 scripts |
| `release\` | Locally generated installation ZIP / 本機產生的安裝 ZIP |

## 驗證及測試 / Validation and testing

執行 offline validator / Run the offline validator：

```powershell
powershell.exe -File .\src\scripts\Test-Map.ps1
```

此 validator 主要檢查 19 個 HP1C map folders、required files、JSON 及 route CSV structure / This validator checks the earlier HP1C folder/file and route-data structure. It does not validate the Tsing Yi road network, website runtime or simulator driving. Use `Validate-TsingYi.py` for the island build, followed by a separate manual in-engine test。

Actual driving 仍需要本機 OpenOMSI／OMSI 2 installation / Actual driving still requires a local simulator installation；repository 不包含 simulator executable / no simulator executable is included。

Attribution and licence notes 請參閱 [`ATTRIBUTION.md`](ATTRIBUTION.md) / See the attribution and licence notes there。

High-fidelity target 請參閱 [`QUALITY_TARGET.md`](QUALITY_TARGET.md) / See the intended high-fidelity target there。

## 問題回報 / Report a problem

請提供 map ID (`HK_TsingYi`, `HK_BigMap` or `HP1C_*`)、route/stop or nearby entrypoint、expected result、actual result，以及 screenshot 和 relevant simulator `logfile.txt` / Include the build stage and whether the problem occurs in the browser, editor, loading screen or while driving。

This is an independent community project，不是 official OpenOMSI／OMSI 2 product / It is not an official product。
