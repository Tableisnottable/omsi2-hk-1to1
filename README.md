# OMSI 2 - Hong Kong 1:1 Scale Map Project

This repository is an **OpenOMSI-compatible scaffold** for a 1:1 Hong Kong map
using the HP1C tile naming scheme. It deliberately contains the package
structure and route/map metadata needed to begin authoring; terrain, scenery
meshes, textures, and timetable data are added incrementally.

The visual target is modern high-fidelity simulator quality. OpenOMSI's 64-bit
engine gives the project more memory headroom than the original 32-bit OMSI,
but it does not automatically create Assetto Corsa-level assets. See
`QUALITY_TARGET.md` for the required terrain, meshes, PBR materials, LOD,
collision, and profiling stages.

## Layout

- `maps/HP1C_<code>/` contains one map tile scaffold for each of the 19
  planned areas (`CW`, `WCH`, `EAS`, `SOU`, `YTM`, `SSP`, `KCT`, `WTS`, `KTN`,
  `KWT`, `TWW`, `TMM`, `YLN`, `NTH`, `TPO`, `STN`, `SKG`, `ISL`, `HZMB`).
- `Sceneryobjects/HK_Objects/` is reserved for Hong Kong scenery and generated
  `.sco` definitions.
- `Sceneryobjects/HK_Objects/texture/` is reserved for authored, redistributable
  OMSI textures.
- `Vehicles/Annan_HK/` contains the route `.hof` placeholder.
- `routes/` contains the normalized public-transport route catalogue and
  separate NR and other non-franchised service files.
- `src/scripts/` contains setup, validation, generation, packaging, and launch
  helpers.

## Validate and package

Run from the repository root in PowerShell:

```powershell
powershell.exe -File .\src\scripts\Test-Map.ps1
powershell.exe -File .\src\scripts\Build-Release.ps1
```

The validator is offline and does not require OMSI. The release script writes
the default OpenOMSI installation package
`release\omsi2-hk-1to1-openomsi.zip`; generated archives are ignored by Git.
This is the default zip to download and install.
It is one combined download: the archive contains all 19 `maps\HP1C_*`
directories, not 19 separate downloads.

## Open the project web page

The repository includes a static project website under `web\`. It provides
project information, release/install instructions, route search, validation
status, and links to the Cesium preview:

```powershell
python -m http.server 8080 --directory .
```

Then open `http://localhost:8080/web/`. Use an HTTP server rather than
double-clicking `web\index.html`, because browsers block the CSV route files
when they are loaded from `file://`.

## Install the map from the zip

1. Run `powershell.exe -File .\src\scripts\Build-Release.ps1`.
2. Open `release\omsi2-hk-1to1-openomsi.zip`.
3. Extract the `maps`, `Sceneryobjects`, and `Vehicles` folders into the
   OpenOMSI game root, for example
   `C:\Program Files (x86)\Steam\steamapps\common\OMSI 2\`.
4. Allow Windows to merge the folders, then start OpenOMSI and select an
   installed HP1C map.

The archive is an install package, not a backup of the repository. It does not
include scripts, source OSM files, API keys, or the OpenOMSI executable.
To keep the previous development-package name, pass an explicit output path:

```powershell
powershell.exe -File .\src\scripts\Build-Release.ps1 `
  -OutputPath .\release\omsi2-hk-1to1-full.zip
```

## Generate from OpenStreetMap

The repository can import an `.osm` export into the matching map folder. This
keeps the local save files inside the same repository path and creates
deterministic CSV source data for roads, nodes, and bus stops:

```powershell
powershell.exe -File .\src\scripts\Generate-OsmMap.ps1 `
  -OsmPath .\src\osm\hong-kong.osm `
  -MapCode CW
```

For a small permitted OSM API/Overpass export URL, use `-Download`:

```powershell
powershell.exe -File .\src\scripts\Generate-OsmMap.ps1 `
  -OsmPath "https://overpass-api.de/api/map?bbox=114.10,22.25,114.20,22.35" `
  -MapCode CW -Download
```

The importer creates `osm_nodes.csv`, `osm_ways.csv`, `osm_stops.csv`,
`osm_buildings.csv`, and `osm_import.json` under `maps\HP1C_<code>`.
Building footprints include available OSM building tags, levels, heights, and
polygon coordinates. These are source/import files;
the OMSI tile still needs a scenery/spline conversion step before it becomes a
fully drivable map.

## Optional Hong Kong 3D reference data

The Lands Department publishes territory-wide 3D Visualisation Map datasets
through CSDI. The documented machine-readable access format is Cesium 3D
Tiles in WGS84; the 3D Spatial Data API requires a free API key requested
from `3dmap@landsd.gov.hk` and is subject to fair-use limits. The
individualised-model dataset includes geometry and texture data, while the
non-textured dataset provides geometry without texture.

These datasets are useful for authoring reference and for a future
coordinate-based scenery conversion step. They are not currently downloaded
or copied into this repository: the current generator remains reproducible
from OSM, and converting a full-territory 3D Tiles service into OMSI meshes
requires a separate, licence-aware conversion pipeline. The official pages
do not establish FBX, OBJ, IFC, OSGB, or indoor-map downloads, so those
formats are not assumed.

The building tileset endpoint can be checked locally without committing the
key or downloaded metadata:

```powershell
$env:LANDSD_3D_API_KEY = "your-new-key"
powershell.exe -File .\src\scripts\Get-Landsd3dTileset.ps1 -Dataset building
```

The script reads the key only from `LANDSD_3D_API_KEY`, writes downloaded
metadata under the ignored `src\landsd3d\` directory, and does not convert
the remote 3D Tiles into OMSI assets.

For a local Cesium preview with the Lands Department imagery basemap plus
building and infrastructure tiles:

```powershell
$env:LANDSD_3D_API_KEY = "your-new-key"
powershell.exe -File .\src\scripts\Serve-CesiumPreview.ps1
```

Open `http://localhost:8080/`. The preview is temporary and the generated
key-bearing HTML is removed when the server stops; it is not an OMSI asset
generator.

Official links and attribution requirements are recorded in
`ATTRIBUTION.md`.

## Bus routes

Run `python .\src\scripts\Import-BusRoutes.py` to refresh
`routes\hk_bus_routes.csv` from the HK Bus Crawling public snapshot. The
snapshot currently contains 3,777 route-direction records. NR (Residents'
Service) routes are kept in `routes\nr_routes.csv`; their official approval
lists are published separately by the Transport Department and are not mixed
with the franchised-route feed. HKeMobility is recorded as the manual route
search reference, but its interactive backend does not expose a permitted
bulk download for this generator. Approved contract-hire and regular hotel
services are in `routes\other_routes.csv`. See `routes\README.md` and
`routes\sources.json` for source and coverage details.

## Texture and imagery policy

Do **not** package Google Maps or Google Earth screenshots, tiles, or extracted
imagery in this project. Use them only as private visual reference if needed.
Google Maps Platform is also not an offline map-export source for this
generator: live API use requires the user's own Google Cloud credentials,
billing, and attribution, and standard terms do not permit turning rendered
Google content into redistributable OMSI map assets.

The preferred workflow is:

1. Use OpenStreetMap for roads, buildings, and stop locations.
2. Use Hong Kong Lands Department open orthophotos or HK Map Service data for
   local reference imagery, following their current attribution and licence
   terms.
3. Author simplified road, terrain, building, and signage textures in
   `Sceneryobjects\HK_Objects\texture\` rather than redistributing raw aerial
   imagery.
4. Record the exact source and attribution in `ATTRIBUTION.md` before adding
   generated textures to a release.

See `ATTRIBUTION.md` for the project attribution template and source links.

## Authoring notes

Keep map folder names stable because OMSI references them directly. Add
terrain and objects to the relevant tile, then run the validator before
testing in OpenOMSI. `Run-OpenOmsi.ps1` accepts `-OmsiPath` when the game is
installed somewhere other than the default Steam location.