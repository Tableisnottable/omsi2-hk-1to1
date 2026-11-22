# HK_BigMap — one continuous Hong Kong map

`maps/HK_BigMap/` is a single OMSI map that covers **all 19 HP1C districts plus the
Central overview extract** as one contiguous tile grid, built by
`src/scripts/Convert-OsmToBigMap.py`.

## Why this and not `maps/HP1C_*`

`Convert-OsmToMap.py` clips a district into **one** 300 m tile. The OSM extracts are
about 1.2 km square, so that threw away ~94 % of every extract and left 19 islands of
map separated by kilometres of nothing.

`Convert-OsmToBigMap.py` keeps each extract's whole extent and emits **every** 300 m
cell it covers, so roads run on across tile borders and neighbouring districts join up
where their extracts overlap.

## What is in the map

| | |
|---|---|
| tiles | 483 (`tile_<TX>_<TY>.map`, each with a `.map.terrain`) |
| splines (roads) | 46,898 |
| buildings | 12,311, baked into 408 per-tile meshes |
| bus stops | 2,177 (also written to `TTData/Busstops.cfg`) |
| entrypoints | 20 — one per district, at each extract's centre |

Tile grid spans X 4…113, Y 12…110. Tile indices are non-negative: the whole HK extent
is shifted by `OFFSET_X/OFFSET_Y` (24 km / 18 km) instead of using negative indices.

### Terrain

Every tile's `.map.terrain` holds a real 61×61 ASTER 30 m height lattice
(0 m at the harbour up to 391.7 m), not a flat grid:

- The lattice is row-major south→north, so row *j* is `y = j/60 · 300 m` and
  column *i* is `x = i/60 · 300 m`.
- Each tile samples every district grid whose bbox covers it; where grids overlap the
  **highest** wins, so a hill is not flattened by a coastal neighbour.
- Verified: **46,665 border sample pairs across all 483 tiles differ by 0.000 m**, so the
  terrain is seamless — a single continuous surface, not 483 separate plates.

Everything that sits on the ground uses that same "highest covering grid" rule, so the
three layers agree:

| layer | rule | verified |
|---|---|---|
| terrain lattice | highest of every covering grid | 46,665 border pairs, 0.000 m |
| road splines | ground at both ends, `[spline_h]` = the difference | spot check of 161 splines, 0 off by >3 m; roads sit ~0.6 m proud |
| building bases | **lowest** ground under the footprint, each vertex lifted by it | 1,493 tile meshes, 0 outside the tile's terrain band |

Two bugs this fixed, both found by measuring rather than eyeballing:

- The elevation grid used to be a fixed 10×10 over the whole extract, i.e. samples
  1.2 km apart on the 12 km Central extract. Bilinear interpolation dragged the 515 m
  Peak down onto the harbour (a footprint in the middle of Central was being placed at
  ~400 m). The grid is now sized to the extract at ~250 m spacing.
- `ElevationGrid.at` extrapolated outside its bbox instead of clamping, which produced
  heights hundreds of metres off for any point just outside a district.

### Ground textures

`global.cfg` declares three `[groundtex]` layers (grass, asphalt, pavement, each with a
detail texture generated into `Sceneryobjects/HK_Objects/texture/`) so the terrain shows
a surface instead of the engine default.

### Road widths

Roads get their width from OSM's `lanes` tag rather than from the highway class
default, because HK tags lane counts on almost every road:

- `lanes` counts **both** directions, so the spline is `lanes × 3.25 m + 0.5 m`
  (2 lanes → 7.0 m, 3 → 10.2 m), clamped to 3.5–30 m.
- One `.sli` per width used (`Splines/HK_Roads/w7.0.sli`, `w10.2.sli`, …), 22 files;
  a single file per highway type cannot draw a 2-lane and a 6-lane road correctly.
- Resulting spread: 7.0 m ×15,250 · 4.5 m ×12,778 · 3.8 m ×9,718 · 10.2 m ×4,550 ·
  13.5 m ×1,315 — i.e. mostly 2-lane streets with service lanes and a few trunks,
  which is what Hong Kong looks like.

## How it is built

```
python src/scripts/Convert-OsmToBigMap.py --root .
```

Options: `--no-elevation` (skip the ASTER fetch), `--max-districts N` (debug subset).

Steps per district:

1. Parse `src/osm/<CODE>.osm`.
2. Sample a 10×10 ASTER 30 m elevation grid over the extract's bbox (OpenTopoData).
3. Every `highway` way is clipped per 300 m tile (Liang-Barsky) and written as one
   `[spline]` per surviving segment, with `grad_start`/`grad_end` from the terrain and
   the width from the road's `lanes` tag.
4. Every `building` way is extruded from its real OSM footprint (ear-clipped roof) and
   kept only if it fits inside a single tile, then **baked per tile** into one
   `.sco` + one `.o3d` per material. Baker: 12,311 buildings → 408 meshes
   (12k individual `.sco` files made OMSI crawl at startup).
5. Named `highway=bus_stop` / `public_transport=platform` nodes become bus stops.
6. One `[entrypoint]` spawn object per district.

Object and spline IDCodes come from **one counter for the whole map**, so no two tiles
share an ID — OMSI resolves entry-point object IDs globally, so per-tile numbering
collides.

## Tile record formats (as OMSI writes them)

Map files are UTF-16LE with BOM. Each `[spline]` carries **19 numbers and no trailing
keyword**:

```
[spline]
0                      kind
<file.sli>
<id> / <prev> / <next>
x / z / y              tile-local metres (x east, y north, z up)
heading / length / radius
grad_start / grad_end
cant_start / cant_end / skew_start / skew_end
<spline_h>             height gained across the spline
```

`[object]`:

```
[object]
0
<file.sco>
<id>
x / y / z
heading / pitch / bank
<label count>
<labels…>
```

`global.cfg` `[entrypoints]` stores each record as
`index, object_id, unknown, x, height, y, quat(4), group, name`, where `group` is the
0-based position of the owning tile in the `[map]` list, and the object's own position
is tile-local.

## Current status

The full local `HK_BigMap` package has been regenerated and installed into the
configured OMSI 2 directory. The current local package contains:

- 483 map tiles and 483 matching terrain files
- 46,898 road splines, 12,311 buildings and 2,177 bus stops
- 982 unique route timetable files (`.ttl`/`.ttp`) generated from 2,286 route
  records whose matched termini are present in the retained extracts
- AI traffic definitions generated from the vehicle files present in the local
  OMSI installation

The generated map and scenery remain local because they are large assets. The
repository stores the converter, route-data generator and documentation needed
to reproduce them.

The generated map passes structural validation:

- 483 `[map]` records ↔ 483 tile files ↔ 483 terrain files
- 2,605 object IDs and 46,898 spline IDs, **0 duplicates** across all tiles
- **0 missing** `Sceneryobjects` references from the tiles
- every `.sco`/`.o3d` written, every texture present

Loading it in the stock OMSI 2 on this machine is currently blocked by the **host
environment, not the map**. Two findings settle that:

1. **OMSI's own `Berlin-Spandau` behaves identically.** Launched the same way
   (`-map maps\Berlin-Spandau\global.cfg`) it also stalls with its log frozen at
   343 bytes right after `OMSI is working in fullscreen mode`. If the stock map cannot
   load either, the fault is not in this map's content.
2. **OMSI's Direct3D 9 device fails on this hybrid-GPU laptop.** It reports

   ```
   Fatal Error: Error while creating Direct3D-Device - Direct9 Error: D3DERR_NOTAVAILABLE
   Fatal Error: Error while creating Direct3D-Device - Direct9 Error: D3DERR_DEVICELOST
   ```

   The desktop is attached to the Intel Iris Xe iGPU while the RTX 4060 has no display
   output. `GpuPreference=2`, `[adapter] 1`, windowed mode and the `D3D9On12` shim were
   all tried; none fixed it. When the device does come up, OMSI drains the log
   (5882 bytes, full init, no error) and then stalls while loading tiles.

Launching with `-map maps\HK_BigMap\global.cfg` (a **path**, not a situation name)
does get OMSI past `The file … could not be loaded` and into
`Loading Situation maps\HK_BigMap\global.cfg…`, which is as far as it gets here.
`-map <situation name>` only works for names in `Situations\` — and even OMSI's own
`Mauerfall` fails that way, so use the `global.cfg` path form.

To see the map running, use a machine where OMSI can create its D3D9 device (a
single-GPU desktop, or force the dGPU as the sole display adapter), or use OpenOMSI,
which takes `-map` directly and does not use Steam DRM.
