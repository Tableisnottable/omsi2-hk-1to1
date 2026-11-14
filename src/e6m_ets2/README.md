# Local E6M conversion for ETS2

Version 0.2.1 targets the locally installed ETS2 1.62.3.3. It adds an experimental
native Coach Mode E6M alongside the truck prototype. Dealer preview, purchasing,
driving, doors, and passenger boarding still need runtime verification.

## Crash investigation

The most recent available normal-home log is from November 14, 2026 at 02:16.
It loaded version 0.1.1 and reported missing wheel instances 4 and 5, an incorrect
rear wheel definition, and failure to create a 2x2 image. These logs do not
establish whether a later build has been tested.

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

## Build inputs

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

Restart ETS2, use a separate test profile, activate the E6M mod, then switch to
Coach Mode. Look for ADL / Enviro500 MMC E6M in the coach dealer or bus browser.
This menu route is inferred from the installed dealer registration and still
needs a runtime check. The old truck prototype remains at Access Mod Dealer /
Scania. Use F2 virtual mirrors and automatic transmission. Dashboard, steering
wheel, doors, displays, wipers, and boarding remain unfinished.

After a failure, preserve `game.log.txt` and `game.crash.txt` from the game home
before restarting. Check the mod version in that log and record the exact stage
(activation, dealer list, preview, purchase, or driving).
