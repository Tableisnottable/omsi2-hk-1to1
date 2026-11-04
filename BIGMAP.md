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

## How it is built

```
python src/scripts/Convert-OsmToBigMap.py --root .
```

Options: `--no-elevation` (skip the ASTER fetch), `--max-districts N` (debug subset).

Steps per district:

1. Parse `src/osm/<CODE>.osm`.
2. Sample a 10×10 ASTER 30 m elevation grid over the extract's bbox (OpenTopoData).
3. Every `highway` way is clipped per 300 m tile (Liang-Barsky) and written as one
   `[spline]` per surviving segment, with `grad_start`/`grad_end` from the terrain.
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

The generated map passes structural validation:

- 483 `[map]` records ↔ 483 tile files ↔ 483 terrain files
- 2,605 object IDs and 46,898 spline IDs, **0 duplicates** across all tiles
- **0 missing** `Sceneryobjects` references from the tiles
- every `.sco`/`.o3d` written, every texture present

Loading it in the stock OMSI 2 on this machine is currently blocked by a
**host GPU problem, not a map problem**: OMSI reports

```
Fatal Error: Error while creating Direct3D-Device - Direct9 Error: D3DERR_NOTAVAILABLE
```

so it never gets as far as parsing map content. The desktop is attached to the Intel
Iris Xe iGPU while the RTX 4060 has no display output, and OMSI's Direct3D 9 device
creation fails in that hybrid arrangement (`GpuPreference=2`, `[adapter]`, windowed
mode and `D3D9On12` were all tried).

Launching with `-map maps\HK_BigMap\global.cfg` (a **path**, not a situation name)
does get OMSI past `The file … could not be loaded` and into
`Loading Situation maps\HK_BigMap\global.cfg…`, which is where the D3D failure stops it.
`-map <situation name>` only works for names in `Situations\` — and even OMSI's own
`Mauerfall` fails that way, so use the `global.cfg` path form.

To test the map itself, run it on a machine where OMSI can create its D3D9 device, or
use OpenOMSI, which takes `-map` directly and does not use Steam DRM.
