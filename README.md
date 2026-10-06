# OMSI 2 - Hong Kong 1:1 Scale Map Project

This repository is an **OpenOMSI-compatible scaffold** for a 1:1 Hong Kong map
using the HP1C tile naming scheme. It deliberately contains the package
structure and route/map metadata needed to begin authoring; terrain, scenery
meshes, textures, and timetable data are added incrementally.

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
  separate NR route ingestion file.
- `src/scripts/` contains setup, validation, generation, packaging, and launch
  helpers.

## Validate and package

Run from the repository root in PowerShell:

```powershell
pwsh -File .\src\scripts\Test-Map.ps1
pwsh -File .\src\scripts\Build-Release.ps1
```

The validator is offline and does not require OMSI. The release script writes
`release\omsi2-hk-1to1-full.zip`; generated archives are ignored by Git.

## Generate from OpenStreetMap

The repository can import an `.osm` export into the matching map folder. This
keeps the local save files inside the same repository path and creates
deterministic CSV source data for roads, nodes, and bus stops:

```powershell
pwsh -File .\src\scripts\Generate-OsmMap.ps1 `
  -OsmPath .\src\osm\hong-kong.osm `
  -MapCode CW
```

For a small permitted OSM API/Overpass export URL, use `-Download`:

```powershell
pwsh -File .\src\scripts\Generate-OsmMap.ps1 `
  -OsmPath "https://overpass-api.de/api/map?bbox=114.10,22.25,114.20,22.35" `
  -MapCode CW -Download
```

The importer creates `osm_nodes.csv`, `osm_ways.csv`, `osm_stops.csv`, and
`osm_import.json` under `maps\HP1C_<code>`. These are source/import files;
the OMSI tile still needs a scenery/spline conversion step before it becomes a
fully drivable map.

## Bus routes

Run `python .\src\scripts\Import-BusRoutes.py` to refresh
`routes\hk_bus_routes.csv` from the HK Bus Crawling public snapshot. The
snapshot currently contains 3,777 route-direction records. NR (Residents'
Service) routes are kept in `routes\nr_routes.csv`; their official approval
lists are published separately by the Transport Department and are not mixed
with the franchised-route feed. HKeMobility is recorded as the manual route
search reference, but its interactive backend does not expose a permitted
bulk download for this generator. See `routes\README.md` and
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