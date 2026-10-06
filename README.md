# 香港 1:1 OpenOMSI 地圖 / Hong Kong 1:1 OpenOMSI Map

這是免費、非商業用途的香港 1:1 OpenOMSI／OMSI 2 map project，提供 map data、route catalogue、HOF、browser viewer、OSM source snapshots 和 single installation ZIP。

## 專案狀態 / Project status

目前版本是可安裝的 data-driven map scaffold，可查看 roads、bus stops、building footprints、routes 並測試 OpenOMSI package。

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

## 下載及安裝 / Download and install

全部地圖放在**一個 ZIP**內，不是 19 個獨立下載 / All maps are distributed in **one ZIP**, not 19 separate downloads：

```text
release\omsi2-hk-1to1-openomsi.zip
```

Package contents / 套件內容：

- `maps\HP1C_*` — 全部 19 個 map areas / all 19 map areas。
- `Sceneryobjects` — scenery object folders / scenery 物件資料夾。
- `Vehicles` — vehicle and HOF folders / vehicle 及 HOF 資料夾。
- `Vehicles\Annan_HK\HK_Routes.hof` — current shared HOF / 目前共用 HOF。

Installation process / 安裝流程：

1. 下載 single ZIP / Download the single ZIP。
2. 開啟 OpenOMSI／OMSI 2 game directory / Open your OpenOMSI or OMSI 2 game directory。
3. 將 `maps`、`Sceneryobjects` 和 `Vehicles` 解壓到該目錄 / Extract these folders into that directory。
4. 允許 Windows merge folders / Allow Windows to merge the folders。
5. 啟動 simulator 並選擇 `HP1C_*` 香港地圖 / Start the simulator and select an `HP1C_*` Hong Kong map。

如需自行建立 package，先執行 validator，再執行 release builder / To build the package locally, run the validator first and then the release builder：

```powershell
powershell.exe -File .\src\scripts\Test-Map.ps1
powershell.exe -File .\src\scripts\Build-Release.ps1
```

## 網站及 Web viewer / Website and Web viewer

- [網站首頁及 map / Homepage and map](web/index.html)
- [互動地圖區域 / Interactive map section](web/index.html#map)
- [路線詳細搜尋 / Route detail search](web/routes.html)
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

Keys 絕不會放入 GitHub、website、CSV 或 release ZIP / Keys are never committed to GitHub or included in the website, CSV files or release ZIP。

Google Maps／Google Earth imagery 不會 packaged as distributable map assets / Google imagery is not included as distributable map assets。

## Repository 結構 / Repository layout

| Path / 路徑 | Contents / 內容 |
| --- | --- |
| `maps\HP1C_*` | 19 map areas and OSM-derived CSV data / 19 個地圖區域及 OSM CSV 資料 |
| `routes\` | Route CSV files and source metadata / 路線 CSV 及 source metadata |
| `Vehicles\Annan_HK\HK_Routes.hof` | Basic OMSI HOF / 基本 OMSI HOF |
| `Sceneryobjects\HK_Objects` | Hong Kong scenery object location / 香港 scenery object 位置 |
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

它會檢查 all 19 map folders、route files、HOF、website assets 和 required package structure / It checks the complete package structure。

Actual driving 仍需要本機 OpenOMSI／OMSI 2 installation / Actual driving still requires a local simulator installation；repository 不包含 simulator executable / no simulator executable is included。

Attribution and licence notes 請參閱 [`ATTRIBUTION.md`](ATTRIBUTION.md) / See the attribution and licence notes there。

High-fidelity target 請參閱 [`QUALITY_TARGET.md`](QUALITY_TARGET.md) / See the intended high-fidelity target there。

## 問題回報 / Report a problem

請提供 `HP1C_*` area、route or stop name、expected result、actual result，以及 screenshot or log / Please include these details in a report。

This is an independent community project，不是 official OpenOMSI／OMSI 2 product / It is not an official product。
