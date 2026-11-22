# Local E6M conversion for ETS2

Version 0.3.0 targets the locally installed ETS2 1.62.3.3. It contains the E6M
prototype plus a second drivable Coach Mode model, the ADL Enviro500 ATENU. The
ATENU uses the installed `ATENU.bus` configuration and a measured three-axle
layout. Dealer preview, purchasing, driving, doors, and passenger boarding still
need runtime verification.

## Crash investigation

The November 22, 2026 log reaches profile `trucksmp` without an E6M crash. It
scans the package in Mod Manager, but does not record the E6M mod becoming active.
It also warns that `bus` is an unknown package category, so version 0.2.2 removes
that category while retaining the native Coach Mode dealer definitions. The
separate crash file is from March 23, 2025 on ETS2 1.53.3.21, not this test.

The 0.1.2 repair added rear wheel accessories at offset 2 and resized seven
undersized textures to 4x4 before DDS compilation. This version also fixes
unfinished 0.2.0 coach integration:

- Separate `coach.pmg` and `truck.pmg` avoid mixing wheel groups.
- Coach locators match the installed stock Scania Touring: `wheel_a_0` through
  `wheel_a_3` and `wheel_b_0` through `wheel_b_1`, with identity rotations.
- Separate `adl.e6m.coach` unit IDs avoid global collisions with `adl.e6m`.
- Native coach dealer and browser registrations use the bus definition tree.
- Passenger capacity is provisionally 80 and suspension class is `bus`.
- Automatic coach jobs stay disabled until door/boarding support is tested.
- The ATENU has its own model and texture paths, coach definitions, dealer entry,
  camera IDs, and wheel locators. Engine and passenger capacity values are
  provisional copies from the E6M coach template.

## Build inputs

To see which installed OMSI packages are candidates for future drivable
conversions, run the inventory tool. It follows root-level `.bus` files to model
CFGs and O3D references, labels likely AI/traffic packages, and writes only a
local report; it does not copy or publish game assets.

```powershell
python .\src\e6m_ets2\inventory_buses.py
```

The report is written to `work/e6m_ets2/bus_inventory.json` by default. A
drivable candidate is only an inventory result; encrypted geometry, shared
dependencies, author permissions, cockpit setup, axle layouts, and ETS2 runtime
compatibility must still be checked before packaging each bus.

Before attempting a family, inspect a specific OMSI bus configuration with the
local O3D importer. This report checks each referenced mesh, flags encrypted or
unreadable geometry, measures mesh bounds, and lists missing textures. It does
not modify the source bus or package an ETS2 mod.

```powershell
$env:E6M_WORKSPACE = '<path to the existing E6M build workspace>'
python .\src\e6m_ets2\inspect_bus.py 'A:\SteamLibrary\steamapps\common\OMSI 2\Vehicles\ADL_E500MMC_KMB_ATENU\ATENU.bus'
```

The per-configuration report is written under `work/bus_audits/` in the local
build workspace unless `--output` is specified.

The current ATENU geometry was built from `ATENU.bus` after passing that audit.
To rebuild visible body geometry and measured two- or three-axle wheel locators
in the local SCS source tree:

```powershell
python .\src\e6m_ets2\build_bus_geometry.py 'A:\SteamLibrary\steamapps\common\OMSI 2\Vehicles\ADL_E500MMC_KMB_ATENU\ATENU.bus' --key adl_atenu
```

The first geometry build for a new family produces intermediate model files
only. After the model files exist, `build.ps1 -SkipMeshes` writes Coach Mode
definitions, compiles and packages the mod, then runs the preflight. The 0.3.0
package includes E6M and ATENU; the other inventoried buses still need their own
geometry and definitions.

Only the conversion scripts and reports belong in this repository. Locally
installed OMSI and SCS game meshes, textures, sounds, compiled packages, Blender
scenes, and downloaded conversion tools remain in the ignored build workspace.
Original asset rights remain with their authors. This repository does not supply
those assets or imply permission to redistribute them.

Python with NumPy and Pillow is required. Set `E6M_WORKSPACE` to the existing
conversion workspace, or prepare an ignored workspace at `work/e6m_ets2` beneath
this repository. It needs:

| Path inside the workspace | Local prerequisite |
| --- | --- |
| `work/vendor/Blender-O3D-IO-Public/o3d_io/o3dconvert.py` | OMSI O3D reader |
| `work/tools/conversion/` | SCS Conversion Tools with `extra_mount.txt` containing `e6m` |
| `work/tools/conversion/e6m` | Directory junction pointing to `work/scs_source` |
| `work/ets2_def/` | Definitions extracted from the installed ETS2 `def.scs` |
| `work/coach_dlc_extract/` | Installed `dlc_bus.scs` extracted locally |

The OMSI input defaults to
`A:\SteamLibrary\steamapps\common\OMSI 2\Vehicles\ADL_E500MMC_KMB_E6M`;
override with `E6M_OMSI_BUS`. `E6M_ETS2_HOME` overrides the normal Documents game
home. The source OMSI installation is read-only input.

```powershell
.\src\e6m_ets2\build.ps1 -Workspace '<existing conversion workspace>' -Install
```

Use `-SkipMeshes` only for definition-only edits with current compiled model
inputs. The validator rejects missing/stale models, duplicate global IDs,
incorrect wheel groups, incomplete axle accessories, invalid texture dimensions
or payload lengths, and stale manifest versions. Installation validates first,
requires ETS2 to be closed, backs up the old package, and checks the installed
SHA256. A static pass does not confirm playability.

## Test

Restart ETS2, use a separate test profile, activate **KMB Bus Conversion Pack -
E6M and ATENU**, then switch to Coach Mode. Look for E6M or ATENU in the ADL
coach dealer or bus browser. This menu route is inferred from the installed
dealer registration and still needs a runtime check. The old E6M truck prototype
remains at Access Mod Dealer / Scania. Use F2 virtual mirrors and automatic
transmission. Dashboard controls, destination displays, animated doors, wipers,
and passenger boarding remain unfinished for both coaches.

After a failure, preserve `game.log.txt` and `game.crash.txt` from the game home
before restarting. Check the mod version in that log and record the exact stage
(activation, dealer list, preview, purchase, or driving).
