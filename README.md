# OMSI 2 - Hong Kong 1:1 Scale Map Project

This repository is an **OpenOMSI-compatible scaffold** for a 1:1 Hong Kong map
using the HP1C tile naming scheme. It deliberately contains the package
structure and route/map metadata needed to begin authoring; terrain, scenery
meshes, textures, and timetable data are added incrementally.

## Layout

- `maps/HK_HP1C_<code>/` contains one map tile scaffold for each of the 19
  planned areas (`CW`, `WCH`, `EAS`, `SOU`, `YTM`, `SSP`, `KCT`, `WTS`, `KTN`,
  `KWT`, `TWW`, `TMM`, `YLN`, `NTH`, `TPO`, `STN`, `SKG`, `ISL`, `HZMB`).
- `Sceneryobjects/HK_Objects/` is reserved for Hong Kong scenery and generated
  `.sco` definitions.
- `Vehicles/Annan_HK/` contains the route `.hof` placeholder.
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
`osm_import.json` under `maps\HK_HP1C_<code>`. These are source/import files;
the OMSI tile still needs a scenery/spline conversion step before it becomes a
fully drivable map.

## Authoring notes

Keep map folder names stable because OMSI references them directly. Add
terrain and objects to the relevant tile, then run the validator before
testing in OpenOMSI. `Run-OpenOmsi.ps1` accepts `-OmsiPath` when the game is
installed somewhere other than the default Steam location.