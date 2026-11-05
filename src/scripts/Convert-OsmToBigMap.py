#!/usr/bin/env python3
"""Build one continuous multi-tile OMSI map from the per-district OSM extracts.

`Convert-OsmToMap.py` squeezes a district into a single 300 m tile. This tool
keeps each extract's whole extent (the fetched extracts are ~1.2 km square) and
emits every 300 m cell it covers, so each district becomes a genuinely
contiguous block of tiles whose roads run on across the tile borders.

Output under <root>/maps/HK_BigMap/:
  global.cfg                    every [map] record + one entrypoint per district
  tile_<TX>_<TY>.map            one per 300 m cell that carries content
  tile_<TX>_<TY>.map.terrain    61x61 height grid for that cell
  TTData/Busstops.cfg           every named bus stop of every district

Global frame: equirectangular metres around (22.37, 114.17); a tile's index is
floor(global_metre / 300). Object and spline IDs come from one counter for the
whole map, so no two tiles share an IDCode.

Usage:
  python src/scripts/Convert-OsmToBigMap.py --root . [--no-elevation] [--max-districts N]
"""

import argparse
import importlib.util
import json
import math
import os
import shutil
import struct
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict


def _load_converter():
    """Import Convert-OsmToMap.py (its name is not a valid module identifier)."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Convert-OsmToMap.py")
    spec = importlib.util.spec_from_file_location("convert_osm_to_map", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


conv = _load_converter()
BUILDING_MATERIALS = conv.BUILDING_MATERIALS
DRIVABLE = conv.DRIVABLE
ROAD_CATS = conv.ROAD_CATS
building_footprint_mesh = conv.building_footprint_mesh
clip_segment = conv.clip_segment
polygon_area = conv.polygon_area
write_ascii = conv.write_ascii
write_bmp = conv.write_bmp
write_facade_texture = conv.write_facade_texture
write_o3d = conv.write_o3d
write_utf16 = conv.write_utf16

TILE = 300.0
CELLS = 60
VERSION = 14
LAT0, LON0 = 22.37, 114.17
MPDLAT = 110574.0
MPDLON = 111320.0 * math.cos(math.radians(LAT0))
# HK spans roughly -22.5 km .. +11.8 km around the centroid; shift it into the
# positive quadrant so tile indices start at 0 like OMSI's own maps do.
OFFSET_X = 24_000.0
OFFSET_Y = 18_000.0
DEFAULT_MATERIAL = ((0.76, 0.72, 0.66, 1.0), "facade_residential.bmp")


def to_global(lat, lon):
    """WGS84 -> global map metres (x east, y north), shifted so every tile index is >= 0.

    OMSI's own maps number tiles from 0 upwards and the editor's world-coordinate
    conversion assumes the same, so the whole HK extent is translated into the
    positive quadrant (OFFSET_X/OFFSET_Y) instead of using negative tile indices.
    """
    x = (lon - LON0) * MPDLON
    y = (lat - LAT0) * MPDLAT
    return x + OFFSET_X, y + OFFSET_Y


def to_latlon(gx, gy):
    """Global map metres -> WGS84 (undoes the OFFSET shift)."""
    return LAT0 + (gy - OFFSET_Y) / MPDLAT, LON0 + (gx - OFFSET_X) / MPDLON


def fetch_elevation_grid(lat_min, lon_min, lat_max, lon_max, n=None):
    """ASTER elevations over the bbox, row-major south-to-north; None on failure.

    The grid is sized to the extract: a fixed 10x10 lattice over a 12 km extract
    puts samples 1.2 km apart, so interpolation dragged a 500 m peak down onto
    the harbour. ~250 m spacing keeps the relief local.
    """
    if n is None:
        height_m = (lat_max - lat_min) * MPDLAT
        width_m = (lon_max - lon_min) * MPDLON
        n = max(4, min(16, int(math.ceil(max(height_m, width_m) / 250.0)) + 1))
    # OpenTopoData accepts 100 locations per request
    if n * n > 100:
        n = 10
    locs = [
        f"{lat_min + (lat_max - lat_min) * (j / (n - 1)):.6f},"
        f"{lon_min + (lon_max - lon_min) * (i / (n - 1)):.6f}"
        for j in range(n) for i in range(n)
    ]
    body = urllib.parse.urlencode({"locations": "|".join(locs), "interpolation": "bilinear"}).encode()
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                "https://api.opentopodata.org/v1/aster30m", data=body,
                headers={"User-Agent": "omsi2-hk-1to1/1.0"})
            with urllib.request.urlopen(req, timeout=90) as resp:
                payload = json.loads(resp.read().decode())
            out = [r.get("elevation") for r in payload.get("results", [])]
            if len(out) == n * n and all(v is not None for v in out):
                return [float(v) for v in out], n
            return None
        except Exception as exc:  # noqa: BLE001  (the network is best-effort)
            print(f"    elevation attempt {attempt + 1} failed: {exc}")
    return None


class ElevationGrid:
    """Bilinear sampler over a coarse lat/lon elevation grid."""

    def __init__(self, lat_min, lon_min, lat_max, lon_max, values, n=10):
        self.lat_min, self.lon_min = lat_min, lon_min
        self.lat_max, self.lon_max = lat_max, lon_max
        self.n, self.v = n, values

    def at(self, lat, lon):
        # Clamp to the grid rather than extrapolating: a bilinear formula run
        # outside the bbox produces wild heights (hundreds of metres off).
        if not (self.lat_min - 1e-9 <= lat <= self.lat_max + 1e-9
                and self.lon_min - 1e-9 <= lon <= self.lon_max + 1e-9):
            lat = min(max(lat, self.lat_min), self.lat_max)
            lon = min(max(lon, self.lon_min), self.lon_max)
        fx = (lon - self.lon_min) / (self.lon_max - self.lon_min) * (self.n - 1)
        fy = (lat - self.lat_min) / (self.lat_max - self.lat_min) * (self.n - 1)
        fx = max(0.0, min(self.n - 1 - 1e-9, fx))
        fy = max(0.0, min(self.n - 1 - 1e-9, fy))
        ix, iy = int(fx), int(fy)
        tx, ty = fx - ix, fy - iy
        g, w = self.v, self.n
        h00, h10 = g[iy * w + ix], g[iy * w + ix + 1]
        h01, h11 = g[(iy + 1) * w + ix], g[(iy + 1) * w + ix + 1]
        return (h00 * (1 - tx) + h10 * tx) * (1 - ty) + (h01 * (1 - tx) + h11 * tx) * ty

    def covers(self, lat, lon):
        return (self.lat_min - 1e-9 <= lat <= self.lat_max + 1e-9
                and self.lon_min - 1e-9 <= lon <= self.lon_max + 1e-9)


class TileBuilder:
    __slots__ = ("tx", "ty", "splines", "objects")

    def __init__(self, tx, ty):
        self.tx, self.ty = tx, ty
        self.splines = []
        self.objects = []


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    ap.add_argument("--no-elevation", action="store_true", help="skip the ASTER fetch (flat)")
    ap.add_argument("--max-districts", type=int, default=0, help="debug: only the first N districts")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    osm_dir = os.path.join(root, "src", "osm")
    out = os.path.join(root, "maps", "HK_BigMap")
    splines_dir = os.path.join(root, "Splines", "HK_Roads")
    sco_dir = os.path.join(root, "Sceneryobjects", "HK_Objects")
    model_dir = os.path.join(sco_dir, "model")
    tex_dir = os.path.join(sco_dir, "texture")

    # Start from a clean slate: a previous, larger run would otherwise leave
    # tiles behind that this run's global.cfg does not list.
    if os.path.isdir(out):
        for name in os.listdir(out):
            path = os.path.join(out, name)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
    for folder in (sco_dir, model_dir):
        for name in os.listdir(folder):
            if name.startswith("HK_Tile_"):
                os.remove(os.path.join(folder, name))

    for d in (out, splines_dir, os.path.join(splines_dir, "texture"), sco_dir, model_dir,
              tex_dir, os.path.join(out, "TTData")):
        os.makedirs(d, exist_ok=True)

    # ---- shared road splines + facade textures ----
    write_bmp(os.path.join(splines_dir, "texture", "asphalt.bmp"), 256, 256,
              lambda x, y: (90 + (x % 17) - 8, 90 + (y % 17) - 8, 88 + ((x + y) % 17) - 8))
    # One .sli per width actually used. A single file per road type cannot
    # express a 2-lane and a 6-lane road, so the widths come from the lane
    # counts in the data; the type defaults are added for untagged roads.
    widths = {round(v[1], 1) for v in ROAD_CATS.values()}
    for n in range(1, 19):
        widths.add(round(max(3.5, min(n * 3.25 + 0.5, 30.0)), 1))
    for width in sorted(widths):
        half = width / 2.0
        write_ascii(os.path.join(splines_dir, f"w{width:.1f}.sli"), [
            "[texture]", "texture\\asphalt.bmp", "",
            "[profile]", "0",
            "[profilepnt]", f"{-half:.4f}", "0", "0", "1",
            "[profilepnt]", f"{half:.4f}", "0", "1", "1",
            "",
            "[path]", "0", "0", "0", f"{width:.4f}", "2",
            "",
            "[terrainholeprofile]",
            "[terrainholeprofilepnt]", f"{-half - 0.3:.4f}", "-0.1", "1",
            "[terrainholeprofilepnt]", f"{half + 0.3:.4f}", "-0.1", "1",
        ])
    for _diffuse, tex in set(BUILDING_MATERIALS.values()) | {DEFAULT_MATERIAL}:
        write_facade_texture(os.path.join(tex_dir, tex), tex)

    # Terrain ground layers (see [groundtex] in global.cfg): a walking surface,
    # asphalt and pavement, each with its detail texture.
    def ground_pattern(base, spread, kind):
        def px(x, y):
            if kind == "grass":
                v = base + ((x * 7 + y * 13) % spread) - spread // 2
                return (max(0, v - 18), min(255, v + 12), max(0, v - 30))
            if kind == "asphalt":
                v = base + ((x * 11 + y * 5) % spread) - spread // 2
                return (v, v, v - 3)
            v = base + ((x // 8 + y // 8) % 2) * spread // 2 - spread // 4
            return (v, v - 4, v - 10)
        return px

    for name, base, spread, kind in (
        ("ground_grass", 86, 26, "grass"),
        ("ground_asphalt", 92, 18, "asphalt"),
        ("ground_pavement", 132, 22, "pavement"),
    ):
        write_bmp(os.path.join(tex_dir, name + ".bmp"), 128, 128, ground_pattern(base, spread, kind))
        write_bmp(os.path.join(tex_dir, name + "_det.bmp"), 64, 64,
                  ground_pattern(base + 8, spread // 2, kind))

    districts = sorted(
        f[:-4] for f in os.listdir(osm_dir)
        if f.endswith(".osm") and os.path.getsize(os.path.join(osm_dir, f)) > 100_000
    )
    if args.max_districts:
        districts = districts[: args.max_districts]
    print(f"districts ({len(districts)}): {', '.join(districts)}\n")

    tiles = {}
    next_object_id = 1_000_000
    next_spline_id = 1
    entry_points = []
    stop_cfg = []
    spline_total = building_total = stop_total = 0
    building_verts = {}          # object id -> (verts, tris, material key)
    footprint_xy = {}            # object id -> (tx, ty, [(x, y) ...] tile-local)
    MATERIAL_LOOKUP = dict(BUILDING_MATERIALS)
    grids = []                   # every district's ElevationGrid, for terrain writing

    # A spawn object per district: OMSI reads a map's entry points from the
    # [entrypoint] scenery objects placed in its tiles, so each district needs
    # one to be selectable on the map screen.
    spawn_mesh = conv.building_box_mesh(0.5, 0.5, 0.1)
    write_o3d(os.path.join(model_dir, "HK_Spawn.o3d"), spawn_mesh[0], spawn_mesh[1], b"")
    write_ascii(os.path.join(sco_dir, "HK_Spawn.sco"), [
        "[friendlyname]", "HK Spawn Point", "",
        "[groups]", "2", "Hong Kong", "Spawn", "",
        "[entrypoint]",
        "[mesh]", "model\\HK_Spawn.o3d",
    ])

    for code in districts:
        print(f"[{code}]")
        osm = ET.parse(os.path.join(osm_dir, f"{code}.osm")).getroot()
        nodes = {n.get("id"): (float(n.get("lat")), float(n.get("lon"))) for n in osm.findall("node")}
        if not nodes:
            print("    no nodes, skipped")
            continue
        lats = [v[0] for v in nodes.values()]
        lons = [v[1] for v in nodes.values()]
        lat_min, lat_max = min(lats), max(lats)
        lon_min, lon_max = min(lons), max(lons)

        grid = None
        if not args.no_elevation:
            fetched = fetch_elevation_grid(lat_min, lon_min, lat_max, lon_max)
            if fetched:
                values, grid_n = fetched
                grid = ElevationGrid(lat_min, lon_min, lat_max, lon_max, values, grid_n)
                grids.append(grid)
                print(f"    ASTER {min(values):.0f}-{max(values):.0f} m on a {grid_n}x{grid_n} grid")
            else:
                print("    ASTER unavailable -> flat")

        def elev(lat, lon, _g=grid):
            if _g is None:
                return 0.0
            return _g.at(lat, lon)   # at() clamps to the bbox instead of extrapolating

        # Roads and stops must match the terrain, and the terrain takes the
        # highest of every covering grid (see the tile writer), so they do too.
        def ground(lat, lon):
            best = None
            for g_ in grids:
                if g_.covers(lat, lon):
                    hv = g_.at(lat, lon)
                    if best is None or hv > best:
                        best = hv
            if best is None:
                return elev(lat, lon)
            return best

        # ---- bus stops ----
        for n in osm.findall("node"):
            tags = {t.get("k"): t.get("v") for t in n.findall("tag")}
            if tags.get("highway") != "bus_stop" and tags.get("public_transport") != "platform":
                continue
            name = tags.get("name") or tags.get("ref") or f"stop {n.get('id')}"
            lat, lon = float(n.get("lat")), float(n.get("lon"))
            gx, gy = to_global(lat, lon)
            tx, ty = math.floor(gx / TILE), math.floor(gy / TILE)
            tile = tiles.setdefault((tx, ty), TileBuilder(tx, ty))
            tile.objects.append({
                "file": "Sceneryobjects\\HK_Objects\\HK_BusStop.sco",
                "id": next_object_id,
                "pos": (gx - tx * TILE, gy - ty * TILE, elev(lat, lon)),
                "heading": 0.0,
                "labels": [name],
            })
            stop_cfg.append(f"[busstop]\n{name}\n0\n{next_object_id}\n0\n0\n0\n")
            next_object_id += 1
            stop_total += 1

        # ---- roads ----
        for w in osm.findall("way"):
            tags = {t.get("k"): t.get("v") for t in w.findall("tag")}
            hw = tags.get("highway")
            if hw not in DRIVABLE:
                continue
            # Prefer the real lane count: OSM tags lanes on most HK roads, and a
            # 4-lane trunk drawn 12 m wide (the type default) looks wrong next to
            # a 2-lane residential road at 6 m.
            base_width = ROAD_CATS[hw][1]
            try:
                n_lanes = int(tags.get("lanes", ""))
            except ValueError:
                n_lanes = 0
            if n_lanes > 0:
                # OSM's `lanes` counts both directions: 3.25 m per lane plus a
                # 0.5 m edge margin, so a 2-lane street comes out at 7 m.
                width = round(max(3.5, min(n_lanes * 3.25 + 0.5, 30.0)), 1)
            else:
                width = round(base_width, 1)
            pts = [to_global(*nodes[r]) for r in (nd.get("ref") for nd in w.findall("nd")) if r in nodes]
            for i in range(len(pts) - 1):
                ax, ay = pts[i]
                bx, by = pts[i + 1]
                for tx in range(math.floor(min(ax, bx) / TILE), math.floor(max(ax, bx) / TILE) + 1):
                    for ty in range(math.floor(min(ay, by) / TILE), math.floor(max(ay, by) / TILE) + 1):
                        ox, oy = tx * TILE, ty * TILE
                        seg = clip_segment((ax - ox, ay - oy), (bx - ox, by - oy), 0.0, TILE)
                        if seg is None:
                            continue
                        (x0, y0), (x1, y1) = seg
                        length = math.hypot(x1 - x0, y1 - y0)
                        if length < 0.15:
                            continue
                        z0 = elev(*to_latlon(ox + x0, oy + y0))
                        z1 = elev(*to_latlon(ox + x1, oy + y1))
                        tile = tiles.setdefault((tx, ty), TileBuilder(tx, ty))
                        tile.splines.append({
                            "file": f"Splines\\HK_Roads\\w{width:.1f}.sli",
                            "id": next_spline_id,
                            "pos": (x0, y0, z0),
                            "heading": math.degrees(math.atan2(x1 - x0, y1 - y0)),
                            "length": length,
                            "grad": (z1 - z0) / length * 100.0,
                            # [spline_h]: the height gained across the spline
                            "delta_h": z1 - z0,
                            "ends": (to_latlon(ox + x0, oy + y0), to_latlon(ox + x1, oy + y1)),
                            "tile": (tx, ty),
                        })
                        next_spline_id += 1
                        spline_total += 1

        # ---- buildings ----
        for w in osm.findall("way"):
            tags = {t.get("k"): t.get("v") for t in w.findall("tag")}
            if "building" not in tags:
                continue
            pts = [to_global(*nodes[r]) for r in (nd.get("ref") for nd in w.findall("nd")) if r in nodes]
            if len(pts) < 3 or polygon_area(pts) < 9.0:
                continue
            height = 10.0
            try:
                if tags.get("height"):
                    height = float(tags["height"])
                elif tags.get("building:levels"):
                    height = float(tags["building:levels"]) * 3.2
            except ValueError:
                pass
            height = min(max(height, 3.0), 400.0)

            cx = sum(p[0] for p in pts) / len(pts)
            cy = sum(p[1] for p in pts) / len(pts)
            tx, ty = math.floor(cx / TILE), math.floor(cy / TILE)
            ox, oy = tx * TILE, ty * TILE
            local = [(p[0] - ox, p[1] - oy) for p in pts]
            # a footprint crossing a tile edge would be cut; drop it instead
            if any(px < 0.0 or px > TILE or py < 0.0 or py > TILE for px, py in local):
                continue
            # A footprint's base follows the lowest ground under it. The ground is
            # resolved later, once every district's elevation grid is known, with
            # the same "highest covering grid" rule the tile terrain uses.
            ground_z = elev(*to_latlon(cx, cy))
            verts, tris = building_footprint_mesh(local, height)
            if not tris:
                continue
            verts = [(v[0], v[1], v[2] + ground_z) + tuple(v[3:]) for v in verts]
            material_key = (tags.get("building") or "yes").lower()
            bldg_id = next_object_id
            building_verts[bldg_id] = (verts, tris, material_key)
            footprint_xy[bldg_id] = (tx, ty, local)
            tile = tiles.setdefault((tx, ty), TileBuilder(tx, ty))
            tile.objects.append({
                "file": f"Sceneryobjects\\HK_Objects\\HK_Placeholder_{bldg_id}.sco",
                "id": bldg_id,
                "pos": (0.0, 0.0, 0.0),
                "heading": 0.0,
                "labels": [],
                "building": True,
            })
            next_object_id += 1
            building_total += 1

        # ---- one entrypoint per district at the extract centre ----
        clat, clon = (lat_min + lat_max) / 2.0, (lon_min + lon_max) / 2.0
        gx, gy = to_global(clat, clon)
        tx, ty = math.floor(gx / TILE), math.floor(gy / TILE)
        lx, ly = gx - tx * TILE, gy - ty * TILE
        z = elev(clat, clon)
        tile = tiles.setdefault((tx, ty), TileBuilder(tx, ty))
        tile.objects.append({
            "file": "Sceneryobjects\\HK_Objects\\HK_Spawn.sco",
            "id": next_object_id,
            "pos": (lx, ly, z),
            "heading": 0.0,
            "labels": [f"HK {code}"],
        })
        # global.cfg stores an entry point's position as (x, height, y)
        entry_points.append((tx, ty, lx, ly, z, next_object_id, f"HK {code}"))
        next_object_id += 1
        print(f"    entrypoint {code} at tile ({tx},{ty}) local ({lx:.0f},{ly:.0f})")

    # ---- resolve building bases against the complete terrain ----
    # Every district grid is known now, so a footprint's base can use the same
    # "highest covering grid" rule the tile terrain used. Without this a building
    # sinks when a neighbouring district's grid is higher at the same spot.
    def ground_at(lat, lon):
        best = None
        for g_ in grids:
            if g_.covers(lat, lon):
                hv = g_.at(lat, lon)
                if best is None or hv > best:
                    best = hv
        return best if best is not None else 0.0

    for bid, (btx, bty, blocal) in footprint_xy.items():
        want = min(ground_at(*to_latlon(btx * TILE + px, bty * TILE + py)) for px, py in blocal)
        verts, tris, material = building_verts[bid]
        # the stored verts already carry the provisional ground; shift by the delta
        have = verts[0][2] if verts else 0.0
        delta = want - have
        if abs(delta) > 1e-6:
            building_verts[bid] = (
                [(v[0], v[1], v[2] + delta) + tuple(v[3:]) for v in verts], tris, material)

    # Spline ends ride the final ground too, so a road never sinks below the
    # terrain or floats above it.
    for tile in tiles.values():
        for s in tile.splines:
            (lat0, lon0), (lat1, lon1) = s["ends"]
            z0 = ground_at(lat0, lon0)
            z1 = ground_at(lat1, lon1)
            s["pos"] = (s["pos"][0], s["pos"][1], z0)
            s["grad"] = (z1 - z0) / s["length"] * 100.0 if s["length"] else 0.0
            s["delta_h"] = z1 - z0

    # ---- one merged building mesh per tile ----
    # 12k separate .sco files made OMSI crawl on startup, so each tile's
    # buildings are baked into a single mesh/SCO pair instead.
    print("\nbaking per-tile building meshes ...")
    baked = 0
    for (tx, ty), tile in sorted(tiles.items()):
        merged_v, merged_t, by_material = [], [], defaultdict(list)
        for obj in tile.objects:
            if obj["id"] not in building_verts:
                continue
            verts, tris, material = building_verts[obj["id"]]
            offset = len(merged_v)
            merged_v.extend(verts)
            by_material[material].extend((a + offset, b + offset, c + offset) for a, b, c in tris)
        if not by_material:
            continue
        mesh_name = f"HK_Tile_{tx}_{ty}"
        # one .o3d per material, and one .sco whose [mesh] entries reference them
        sco_lines = ["[friendlyname]", f"HK tile {tx},{ty} buildings", "",
                     "[groups]", "2", "Hong Kong", "Buildings", ""]
        for k, (material, tris) in enumerate(sorted(by_material.items())):
            diffuse, tex = MATERIAL_LOOKUP.get(material, DEFAULT_MATERIAL)
            part = f"{mesh_name}_{k}"
            write_o3d(os.path.join(model_dir, part + ".o3d"), merged_v, tris, tex.encode(), diffuse)
            sco_lines += ["[mesh]", f"model\\{part}.o3d", ""]
            sco_lines += ["[collision_mesh]", f"model\\{part}.o3d", ""]
        write_ascii(os.path.join(sco_dir, mesh_name + ".sco"), sco_lines)
        tile.objects = [o for o in tile.objects if o["id"] not in building_verts]
        # Every vertex already carries its own absolute terrain height, so the
        # object sits at z = 0 and the buildings follow the ground exactly.
        tile.objects.append({
            "file": f"Sceneryobjects\\HK_Objects\\{mesh_name}.sco",
            "id": next_object_id,
            "pos": (0.0, 0.0, 0.0),
            "heading": 0.0,
            "labels": [],
        })
        next_object_id += 1
        baked += 1
    print(f"  {baked} tile meshes")

    # ---- tiles ----
    order = sorted(tiles)
    print(f"\nwriting {len(order)} tiles")
    for tx, ty in order:
        tile = tiles[(tx, ty)]
        ids = [s["id"] for s in tile.splines]
        lines = ["[version]", str(VERSION), "", "[terrain]", ""]
        for i, s in enumerate(tile.splines):
            # OMSI's own tiles write 19 numbers per [spline] and no per-record
            # keyword: the 19th is [spline_h], the height gained over the length.
            lines += [
                "[spline]", "0", s["file"], str(s["id"]),
                str(ids[i - 1] if i else -1), str(ids[i + 1] if i + 1 < len(ids) else -1),
                f"{s['pos'][0]:.6f}", f"{s['pos'][2]:.6f}", f"{s['pos'][1]:.6f}",
                f"{s['heading']:.6f}", f"{s['length']:.6f}", "0",
                f"{s['grad']:.6f}", f"{s['grad']:.6f}",
                "0", "0", "0", "0", "0",
                f"{s['delta_h']:.6f}", "",
            ]
        for o in tile.objects:
            if o.get("building"):
                continue          # replaced by the tile's merged building mesh
            lines += [
                "[object]", "0", o["file"], str(o["id"]),
                f"{o['pos'][0]:.4f}", f"{o['pos'][1]:.4f}", f"{o['pos'][2]:.4f}",
                f"{o['heading']:.4f}", "0", "0", str(len(o["labels"])),
            ]
            lines += o["labels"]
            lines.append("")
        write_utf16(os.path.join(out, f"tile_{tx}_{ty}.map"), lines)

        # Real terrain: sample every district grid at this tile's 61x61 lattice.
        # The lattice is row-major south->north, so row j maps to
        # y = j/CELLS * TILE and column i to x = i/CELLS * TILE. Where several
        # district grids overlap the highest wins, which keeps a hill from being
        # flattened by a coastal neighbour.
        heights = [None] * ((CELLS + 1) ** 2)
        for j in range(CELLS + 1):
            gy = ty * TILE + j / CELLS * TILE
            for i in range(CELLS + 1):
                gx = tx * TILE + i / CELLS * TILE
                lat, lon = to_latlon(gx, gy)
                best = None
                for grid in grids:
                    if not grid.covers(lat, lon):
                        continue
                    h = grid.at(lat, lon)
                    if best is None or h > best:
                        best = h
                heights[j * (CELLS + 1) + i] = best if best is not None else 0.0
        with open(os.path.join(out, f"tile_{tx}_{ty}.map.terrain"), "wb") as f:
            f.write(struct.pack("<I", CELLS))
            f.write(struct.pack(f"<{len(heights)}f", *heights))
    # ---- global.cfg ----
    gl = [
        "[name]", "HK_BigMap", "",
        "[friendlyname]", "Hong Kong 1:1 - all districts (multi-tile)", "",
        "[description]",
        f"{len(order)} tiles carrying OSM roads, buildings and bus stops for {len(districts)} Hong Kong districts.",
        "[end]", "",
        "[version]", str(VERSION), "",
        "[NextIDCode]", str(next_object_id), "",
        "[LHT]", "",
    ]
    # Ground layers: OMSI paints the terrain with the first one, so the map does
    # not show the engine's default blank surface.
    gl += [
        "[groundtex]", "Sceneryobjects\\HK_Objects\\texture\\ground_grass.bmp",
        "Sceneryobjects\\HK_Objects\\texture\\ground_grass_det.bmp", "0", "1", "60",
        "[groundtex]", "Sceneryobjects\\HK_Objects\\texture\\ground_asphalt.bmp",
        "Sceneryobjects\\HK_Objects\\texture\\ground_asphalt_det.bmp", "4", "40", "12",
        "[groundtex]", "Sceneryobjects\\HK_Objects\\texture\\ground_pavement.bmp",
        "Sceneryobjects\\HK_Objects\\texture\\ground_pavement_det.bmp", "6", "40", "12",
    ]
    gl += [
        "[entrypoints]", str(len(entry_points)),
    ]
    for i, (tx, ty, lx, ly, z, oid, name) in enumerate(entry_points):
        gl += [
            str(i), str(oid), "0",
            # OMSI stores the position in the object frame order: x, height, y
            f"{lx:.4f}", f"{z:.4f}", f"{ly:.4f}",
            "0", "0", "0", "1",
            str(i), name,
        ]
    gl.append("")
    for tx, ty in order:
        gl += ["[map]", str(tx), str(ty), f"tile_{tx}_{ty}.map"]
    write_utf16(os.path.join(out, "global.cfg"), gl)

    # ---- side files ----
    if stop_cfg:
        write_utf16(os.path.join(out, "TTData", "Busstops.cfg"), "\n".join(stop_cfg))
    write_utf16(os.path.join(out, "drivers.txt"), ["DefaultDriver"])
    write_utf16(os.path.join(out, "ailists.cfg"), ["[sorts]", "1", "0", "", "[ailist]", "0", "-1"])

    print(f"\ndone -> {out}")
    print(f"  tiles       {len(order)}")
    print(f"  splines     {spline_total}")
    print(f"  buildings   {building_total}")
    print(f"  bus stops   {stop_total}")
    print(f"  entrypoints {len(entry_points)}")


if __name__ == "__main__":
    main()
