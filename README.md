# OMSI 2 / OpenOMSI Hong Kong 1:1 Foundation

This repository is a **practical starter project** for a true-scale (1:1) Hong Kong OMSI map that can be iterated for OMSI 2 and OpenOMSI.

It currently provides a loadable scaffold map and tooling, **not** a finished real-world recreation. Real GIS processing, asset production, and route authoring are still required.

## Project goals

- Keep map development in open, version-controlled source formats.
- Maintain a reproducible workflow from source files to installed OMSI/OpenOMSI map files.
- Enforce safe packaging and path validation to avoid common OMSI installation mistakes.
- Support incremental development of a true 1:1 map without committing proprietary game assets.

## Supported simulator targets

- OMSI 2 map directory layout (`maps/*`, optional `Sceneryobjects/*`, `Vehicles/*`)
- OpenOMSI executable launch flow (`OpenOMSI.exe`)

> Compatibility note: OpenOMSI is still evolving. This project sticks to simple OMSI-style text map files for the scaffold and validates only structure-level expectations.

## Repository layout

- `/maps/HK_HP1C_DEV` — minimal scaffold map (load test target)
- `/maps/HK_HP1C_*` — existing placeholder map folders kept for compatibility
- `/src/scripts` — PowerShell validation/build/install/run tooling
- `/src/extensions` — extension points for terrain, splines, scenery, tiles, AI, stops, routes, and reference data
- `/src/extensions/reference-data/SOURCES.template.csv` — attribution/source registry template

## 1:1 coordinate and scale conventions

- **Scale**: 1 OMSI world unit = 1 meter (target convention for all generated geometry and placements).
- **Tiles**: maintain tile-indexed outputs (`tile_X_Y.map`) and deterministic generation metadata in `src/extensions/tiles`.
- **Source CRS policy**: keep original CRS in source metadata; document conversion to OMSI-local coordinates in committed generation configs.
- **Reproducibility**: generated map content should be rebuildable from source data committed under `src/extensions` plus documented external datasets.

## Required OMSI/OpenOMSI install layout (Windows)

Point scripts at your simulator root, e.g.:

- `C:\Program Files (x86)\Steam\steamapps\common\OMSI 2`

Expected target subfolders:

- `<SimulatorRoot>\maps`
- `<SimulatorRoot>\Sceneryobjects` (optional until custom assets exist)
- `<SimulatorRoot>\Vehicles` (optional until custom vehicles/HOF assets exist)

## Local development workflow (Windows PowerShell)

From repository root:

1. Initialize folders and validate scaffold:
   ```powershell
   .\setup.ps1
   ```
2. Validate map/package structure at any time:
   ```powershell
   .\src\scripts\Test-MapStructure.ps1
   ```
3. Install scaffold map into OMSI/OpenOMSI:
   ```powershell
   .\src\scripts\Install-Map.ps1 -SimulatorRoot "C:\Program Files (x86)\Steam\steamapps\common\OMSI 2"
   ```
   To copy all map folders in this repo:
   ```powershell
   .\src\scripts\Install-Map.ps1 -SimulatorRoot "C:\Program Files (x86)\Steam\steamapps\common\OMSI 2" -IncludeAllMaps
   ```
4. Launch OpenOMSI:
   ```powershell
   .\src\scripts\Run-OpenOmsi.ps1 -SimulatorRoot "C:\Program Files (x86)\Steam\steamapps\common\OMSI 2"
   ```
5. Build reproducible zip package:
   ```powershell
   .\src\scripts\Build-Release.ps1
   ```

## Extension points

Use `src/extensions/EXTENSION_POINTS.txt` as the authoritative guide for:

- terrain
- splines
- scenery
- tiles
- AI traffic
- bus stops
- routes
- real-world reference data

## Licensing and attribution guidance

- Do **not** commit OMSI 2 proprietary assets from paid DLC/base game.
- Prefer open data/licenses (e.g., ODbL/CC BY compatible) and record each source in `src/extensions/reference-data/SOURCES.template.csv`.
- Keep third-party license texts and attribution notes with imported source datasets/assets.

## What is still required for a real 1:1 map

- Confirmed OpenOMSI runtime behavior for advanced OMSI map features beyond this scaffold
- Real GIS/source data import pipeline
- Terrain, roads/splines, stop cubes, AI routes/timetables, and scenery asset production
- Route and HOF data validated against actual operations
