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

## Authoring notes

Keep map folder names stable because OMSI references them directly. Add
terrain and objects to the relevant tile, then run the validator before
testing in OpenOMSI. `Run-OpenOmsi.ps1` accepts `-OmsiPath` when the game is
installed somewhere other than the default Steam location.